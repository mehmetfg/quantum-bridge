"""Kuantum kapilarinin (quantum gates) matris tanimlari.

Her kapi, bir kubit durumunu donusturen uniter (unitary) bir matristir.
Uniter olmak sunu garanti eder: toplam olasilik her zaman 1 kalir,
yani bilgi kaybolmaz ve islem tersine cevrilebilir.

Bu dosya bilerek "kara kutu" degildir: her matrisi acikca goruyoruz ki
her kapinin duruma ne yaptigi izlenebilsin.
"""

from __future__ import annotations

import cmath
import math

import numpy as np

# Tek kubitlik temel kapilar -------------------------------------------------

# Kimlik (identity): hicbir sey yapmaz, referans noktasidir.
IDENTITY = np.array([[1, 0], [0, 1]], dtype=complex)

# Pauli-X (NOT kapisi): |0> ile |1> yer degistirir. Klasik NOT'un karsiligi.
X = np.array([[0, 1], [1, 0]], dtype=complex)

# Pauli-Y: hem bit hem faz cevirir.
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)

# Pauli-Z (faz kapisi): |1> bileseninin isaretini cevirir, |0> dokunulmaz.
Z = np.array([[1, 0], [0, -1]], dtype=complex)

# Hadamard: superpozisyon (superposition) yaratan kapi.
# |0> -> (|0> + |1>) / sqrt(2). Kuantum paralelliginin baslangic noktasi.
H = np.array([[1, 1], [1, -1]], dtype=complex) / math.sqrt(2)

# S kapisi: 90 derecelik faz kaydirmasi (Z'nin karekoku).
S = np.array([[1, 0], [0, 1j]], dtype=complex)
SDG = np.array([[1, 0], [0, -1j]], dtype=complex)

# T kapisi: 45 derecelik faz kaydirmasi (S'nin karekoku).
T = np.array([[1, 0], [0, cmath.exp(1j * math.pi / 4)]], dtype=complex)
TDG = np.array([[1, 0], [0, cmath.exp(-1j * math.pi / 4)]], dtype=complex)


def rx(theta: float) -> np.ndarray:
    """X ekseni etrafinda theta radyan dondurme (rotation)."""
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)
    return np.array([[c, -1j * s], [-1j * s, c]], dtype=complex)


def ry(theta: float) -> np.ndarray:
    """Y ekseni etrafinda theta radyan dondurme."""
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)
    return np.array([[c, -s], [s, c]], dtype=complex)


def rz(theta: float) -> np.ndarray:
    """Z ekseni etrafinda theta radyan dondurme (sadece faza dokunur)."""
    return np.array(
        [[cmath.exp(-1j * theta / 2), 0], [0, cmath.exp(1j * theta / 2)]],
        dtype=complex,
    )


def phase(theta: float) -> np.ndarray:
    """|1> bilesenine theta kadar faz ekler."""
    return np.array([[1, 0], [0, cmath.exp(1j * theta)]], dtype=complex)


# Kapi adindan matrise cozum tablosu -----------------------------------------

SINGLE_QUBIT_GATES: dict[str, np.ndarray] = {
    "i": IDENTITY,
    "id": IDENTITY,
    "x": X,
    "y": Y,
    "z": Z,
    "h": H,
    "s": S,
    "sdg": SDG,
    "t": T,
    "tdg": TDG,
}

PARAMETRIC_GATES = {
    "rx": rx,
    "ry": ry,
    "rz": rz,
    "p": phase,
}

# Cok kubitlik kapilar, simulatorde kontrol mantigi ile uygulanir.
# Buradaki isimler sadece dogrulama ve QASM cikisi icindir.
CONTROLLED_GATES: dict[str, tuple[str, int]] = {
    # ad: (hedefe uygulanan tek kubit kapisi, kontrol kubit sayisi)
    "cx": ("x", 1),
    "cnot": ("x", 1),
    "cy": ("y", 1),
    "cz": ("z", 1),
    "ch": ("h", 1),
    "ccx": ("x", 2),
    "toffoli": ("x", 2),
    "ccz": ("z", 2),
}

# SWAP ozel bir durumdur: iki kubitin durumunu takas eder.
SPECIAL_GATES = {"swap"}

ALL_GATE_NAMES = (
    set(SINGLE_QUBIT_GATES)
    | set(PARAMETRIC_GATES)
    | set(CONTROLLED_GATES)
    | SPECIAL_GATES
)


def is_unitary(matrix: np.ndarray, tolerance: float = 1e-10) -> bool:
    """Matrisin uniter olup olmadigini dogrular: U @ U_dagger = I."""
    product = matrix @ matrix.conj().T
    return bool(np.allclose(product, np.eye(matrix.shape[0]), atol=tolerance))


def gate_matrix(name: str, params: list[float] | None = None) -> np.ndarray:
    """Kapi adi ve parametrelerinden tek kubitlik matrisi dondurur."""
    key = name.lower()
    if key in SINGLE_QUBIT_GATES:
        return SINGLE_QUBIT_GATES[key]
    if key in PARAMETRIC_GATES:
        if not params:
            raise ValueError(f"'{name}' kapısı bir açı parametresi bekler.")
        return PARAMETRIC_GATES[key](params[0])
    raise ValueError(f"Bilinmeyen tek kubitlik kapı: {name}")


# Egitim amacli kisa aciklamalar; arayuzde kapi uzerine gelince gosterilir.
GATE_DESCRIPTIONS: dict[str, str] = {
    "h": "Hadamard: kubiti süperpozisyona sokar, yani aynı anda hem 0 hem 1 olma haline.",
    "x": "Pauli-X: klasik NOT gibi 0 ile 1'i takas eder.",
    "y": "Pauli-Y: hem bit değerini hem fazı çevirir.",
    "z": "Pauli-Z: sadece fazı çevirir, ölçüm olasılıklarını tek başına değiştirmez.",
    "s": "S: çeyrek tur faz kaydırması.",
    "t": "T: sekizde bir tur faz kaydırması.",
    "rx": "RX: X ekseni etrafında seçilen açıda döndürme.",
    "ry": "RY: Y ekseni etrafında seçilen açıda döndürme.",
    "rz": "RZ: Z ekseni etrafında seçilen açıda döndürme.",
    "cx": "CNOT: kontrol kubiti 1 ise hedef kubiti çevirir. Dolanıklığın (entanglement) ana aracı.",
    "cz": "CZ: her iki kubit de 1 ise fazı çevirir.",
    "ccx": "Toffoli: iki kontrol da 1 ise hedefi çevirir. Klasik AND'in tersinir hali.",
    "ccz": "CCZ: üç kubit de 1 ise fazı çevirir. Grover'ın oracle ve yayıcı adımlarında kullanılır.",
    "swap": "SWAP: iki kubitin durumunu takas eder.",
}
