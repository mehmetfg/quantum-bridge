"""Devreyi OpenQASM 3 metnine cevirir.

OpenQASM, kuantum devrelerinin ortak yazi dilidir. IBM Quantum'a is
gonderirken devre bu formata cevrilir. Simulasyonda buna ihtiyacimiz yok
ama bilerek uretiyoruz: bugun ekranda gordugumuz metin, yarin gercek
donanima gidecek metnin aynisidir. "Gercek yol" tam olarak burada baslar.
"""

from __future__ import annotations

from .circuit import Circuit

#: Kendi ic adlarimizi OpenQASM karsiliklariyla eslestirir.
QASM_NAMES = {
    "cnot": "cx",
    "toffoli": "ccx",
    "i": "id",
}


def _format_param(value: float) -> str:
    return f"{value:.10g}"


def to_qasm3(circuit: Circuit, include_comments: bool = True) -> str:
    """Devreyi OpenQASM 3 kaynak metnine cevirir."""
    lines: list[str] = ["OPENQASM 3.0;", 'include "stdgates.inc";', ""]

    if include_comments:
        lines.insert(0, f"// Devre: {circuit.name}")
        lines.insert(1, f"// Kubit sayısı: {circuit.n_qubits}, derinlik: {circuit.depth}")

    measured = circuit.measured_qubits or list(range(circuit.n_qubits))
    lines.append(f"qubit[{circuit.n_qubits}] q;")
    if measured:
        lines.append(f"bit[{len(measured)}] c;")
    lines.append("")

    for op in circuit.operations:
        key = op.name.lower()
        if op.label is not None and key == "id":
            if include_comments:
                lines.append(f"// --- {op.label} ---")
            continue

        name = QASM_NAMES.get(key, key)
        args = ", ".join(f"q[{q}]" for q in op.qubits)
        if op.params:
            params = ", ".join(_format_param(p) for p in op.params)
            lines.append(f"{name}({params}) {args};")
        else:
            lines.append(f"{name} {args};")

    if measured:
        lines.append("")
        if include_comments:
            lines.append("// Ölçüm: kuantum durumu klasik bitlere çökertilir")
        for i, q in enumerate(measured):
            lines.append(f"c[{i}] = measure q[{q}];")

    return "\n".join(lines) + "\n"
