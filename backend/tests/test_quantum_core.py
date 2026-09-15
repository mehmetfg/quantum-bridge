"""Kuantum çekirdeği testleri: kapılar, simülatör, transpiler, QASM."""

from __future__ import annotations

import math

import numpy as np
import pytest

from app.quantum.circuit import Circuit
from app.quantum.gates import (
    SINGLE_QUBIT_GATES,
    H,
    X,
    is_unitary,
    rx,
    ry,
    rz,
)
from app.quantum.noise import NoiseModel
from app.quantum.qasm import to_qasm3
from app.quantum.simulator import StateVectorSimulator
from app.quantum.transpiler import routing_report, transpile


class TestGates:
    def test_all_named_gates_are_unitary(self):
        for name, matrix in SINGLE_QUBIT_GATES.items():
            assert is_unitary(matrix), f"{name} kapısı üniter değil"

    @pytest.mark.parametrize("theta", [0.0, 0.3, math.pi / 2, math.pi, 2.5])
    def test_rotations_are_unitary(self, theta):
        for func in (rx, ry, rz):
            assert is_unitary(func(theta))

    def test_hadamard_twice_is_identity(self):
        assert np.allclose(H @ H, np.eye(2))

    def test_x_flips_basis_states(self):
        zero = np.array([1, 0], dtype=complex)
        assert np.allclose(X @ zero, np.array([0, 1]))


class TestCircuit:
    def test_depth_counts_parallel_layers(self):
        circuit = Circuit(3)
        circuit.h(0).h(1).h(2)  # üçü paralel, tek katman
        assert circuit.depth == 1

    def test_depth_grows_with_dependency(self):
        circuit = Circuit(2)
        circuit.h(0).cx(0, 1).h(1)
        assert circuit.depth == 3

    def test_two_qubit_gate_count(self):
        circuit = Circuit(3)
        circuit.h(0).cx(0, 1).cx(1, 2)
        assert circuit.two_qubit_gate_count == 2

    def test_rejects_out_of_range_qubit(self):
        with pytest.raises(ValueError):
            Circuit(2).h(5)

    def test_rejects_duplicate_qubits_in_gate(self):
        with pytest.raises(ValueError):
            Circuit(2).cx(0, 0)


class TestSimulator:
    def setup_method(self):
        self.sim = StateVectorSimulator()

    def test_bell_state_is_perfectly_correlated(self):
        circuit = Circuit(2)
        circuit.h(0).cx(0, 1).measure_all()
        result = self.sim.run(circuit, shots=4000, seed=42)
        assert set(result.counts) == {"00", "11"}
        assert abs(result.counts["00"] / 4000 - 0.5) < 0.05

    def test_ghz_state_scales(self):
        circuit = Circuit(4)
        circuit.h(0)
        for q in range(1, 4):
            circuit.cx(0, q)
        circuit.measure_all()
        result = self.sim.run(circuit, shots=2000, seed=1)
        assert set(result.counts) == {"0000", "1111"}

    def test_bit_order_qubit_zero_is_leftmost(self):
        circuit = Circuit(3)
        circuit.x(1).measure_all()
        result = self.sim.run(circuit, shots=20, seed=1)
        assert result.counts == {"010": 20}

    def test_x_gate_is_deterministic(self):
        circuit = Circuit(1)
        circuit.x(0).measure_all()
        result = self.sim.run(circuit, shots=100, seed=3)
        assert result.counts == {"1": 100}

    def test_swap_exchanges_qubits(self):
        circuit = Circuit(2)
        circuit.x(0).swap(0, 1).measure_all()
        result = self.sim.run(circuit, shots=50, seed=5)
        assert result.counts == {"01": 50}

    def test_probabilities_sum_to_one(self):
        circuit = Circuit(3)
        circuit.h(0).h(1).cx(1, 2).measure_all()
        result = self.sim.run(circuit, shots=500, seed=9)
        assert abs(sum(result.probabilities.values()) - 1.0) < 1e-6

    def test_partial_measurement_reduces_bitstring(self):
        circuit = Circuit(3)
        circuit.x(0).x(2).measure(0, 2)
        result = self.sim.run(circuit, shots=30, seed=2)
        assert result.counts == {"11": 30}

    def test_rejects_too_many_qubits(self):
        sim = StateVectorSimulator(max_qubits=3)
        with pytest.raises(ValueError, match="kubit destekler"):
            sim.simulate_state(Circuit(4))

    def test_seed_makes_results_repeatable(self):
        circuit = Circuit(3)
        for q in range(3):
            circuit.h(q)
        circuit.measure_all()
        first = self.sim.run(circuit, shots=200, seed=77).counts
        second = self.sim.run(circuit, shots=200, seed=77).counts
        assert first == second


class TestTranspiler:
    def test_cancels_adjacent_self_inverse_gates(self):
        circuit = Circuit(1)
        circuit.h(0).h(0)
        optimized, report = transpile(circuit)
        assert optimized.gate_count == 0
        assert report.removed_gates == 2

    def test_does_not_cancel_across_intervening_gate(self):
        circuit = Circuit(1)
        circuit.h(0).x(0).h(0)
        optimized, _ = transpile(circuit)
        assert optimized.gate_count == 3

    def test_merges_rotations_on_same_axis(self):
        circuit = Circuit(1)
        circuit.rz(0.3, 0).rz(0.4, 0)
        optimized, report = transpile(circuit)
        assert optimized.gate_count == 1
        assert report.merged_rotations == 1
        assert abs(optimized.operations[0].params[0] - 0.7) < 1e-9

    def test_removes_rotations_that_cancel_out(self):
        circuit = Circuit(1)
        circuit.rz(0.5, 0).rz(-0.5, 0)
        optimized, _ = transpile(circuit)
        assert optimized.gate_count == 0

    def test_cancels_paired_cnots(self):
        circuit = Circuit(2)
        circuit.cx(0, 1).cx(0, 1)
        optimized, _ = transpile(circuit)
        assert optimized.gate_count == 0

    def test_optimization_preserves_measurement_outcome(self):
        circuit = Circuit(2)
        circuit.h(0).h(0).x(1).cx(0, 1).cx(0, 1).measure_all()
        optimized, _ = transpile(circuit)
        sim = StateVectorSimulator()
        before = sim.run(circuit, shots=200, seed=11).counts
        after = sim.run(optimized, shots=200, seed=11).counts
        assert before == after

    def test_routing_report_detects_distant_pairs(self):
        circuit = Circuit(3)
        circuit.cx(0, 2)  # doğrusal zincirde komşu değil
        report = routing_report(circuit)
        assert report["non_adjacent_two_qubit_gates"] == 1
        assert report["distant_pairs"] == [[0, 2]]


class TestQasm:
    def test_emits_valid_header_and_gates(self):
        circuit = Circuit(2, name="bell")
        circuit.h(0).cx(0, 1).measure_all()
        qasm = to_qasm3(circuit)
        assert "OPENQASM 3.0;" in qasm
        assert "qubit[2] q;" in qasm
        assert "h q[0];" in qasm
        assert "cx q[0], q[1];" in qasm
        assert "c[0] = measure q[0];" in qasm

    def test_parametric_gate_includes_angle(self):
        circuit = Circuit(1)
        circuit.rz(1.25, 0).measure_all()
        assert "rz(1.25) q[0];" in to_qasm3(circuit)


class TestNoise:
    def test_ideal_model_leaves_counts_untouched(self):
        counts = {"00": 500, "11": 500}
        result, meta = NoiseModel.preset("ideal").apply(counts, n_bits=2, gate_count=2, seed=1)
        assert result == counts
        assert meta["applied"] is False

    def test_noise_preserves_total_shots(self):
        counts = {"00": 500, "11": 500}
        result, meta = NoiseModel.preset("high").apply(counts, n_bits=2, gate_count=10, seed=1)
        assert sum(result.values()) == 1000
        assert meta["applied"] is True

    def test_higher_noise_produces_more_unique_outcomes(self):
        counts = {"000": 1000}
        low, _ = NoiseModel.preset("low").apply(counts, n_bits=3, gate_count=5, seed=3)
        high, _ = NoiseModel.preset("high").apply(counts, n_bits=3, gate_count=5, seed=3)
        assert len(high) >= len(low)

    def test_rejects_unknown_level(self):
        with pytest.raises(ValueError):
            NoiseModel.preset("bilinmeyen")
