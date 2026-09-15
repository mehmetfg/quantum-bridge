"""Problem testleri: her problem beklenen sonucu üretiyor mu?"""

from __future__ import annotations

import pytest

from app.ai.router import QuantumRouter
from app.core.models import JobRequest
from app.problems.base import ValidationError
from app.problems.registry import get_problem, list_problems
from app.quantum.backends.local_sim import LocalSimulatorBackend
from app.quantum.transpiler import transpile

BACKEND = LocalSimulatorBackend()
ROUTER = QuantumRouter()


def run_problem(problem_id: str, user_input: dict, seed: int = 123, shots: int | None = None):
    """Bir problemi uçtan uca çalıştırıp son sonucu döndürür."""
    problem = get_problem(problem_id)
    merged = dict(problem.default_input)
    merged.update(user_input)
    spec = problem.validate(merged)
    request = JobRequest(problem_id=problem_id, input=merged, shots=shots, seed=seed)
    decision = ROUTER.decide(problem, spec, request)
    circuit, _ = transpile(problem.build_circuit(spec, decision.n_qubits))
    raw = BACKEND.run(circuit, shots=decision.shots, seed=seed)
    decoded = problem.decode(raw, spec)
    return problem.merge(decoded, spec), decoded, raw, spec


class TestRegistry:
    def test_five_problems_registered(self):
        assert len(list_problems()) == 5

    def test_every_problem_exposes_complete_info(self):
        for problem in list_problems():
            info = problem.info()
            assert info.id and info.title and info.description
            assert info.quantum_advantage and info.classical_comparison
            assert info.input_schema, f"{info.id} için girdi şeması boş"
            assert info.default_input, f"{info.id} için varsayılan girdi boş"

    def test_default_input_always_validates(self):
        for problem in list_problems():
            spec = problem.validate(dict(problem.default_input))
            assert spec.problem_id == problem.id

    def test_unknown_problem_raises(self):
        with pytest.raises(KeyError):
            get_problem("olmayan-problem")


class TestRandomBits:
    def test_produces_requested_amount(self):
        final, decoded, raw, _ = run_problem("random-bits", {"bit_count": 3, "how_many": 40})
        assert len(final.details["numbers"]) == 40
        assert all(0 <= n < 8 for n in final.details["numbers"])

    def test_uses_result_in_classical_work(self):
        final, *_ = run_problem("random-bits", {"bit_count": 4, "how_many": 16})
        assert len(final.details["shuffled_list"]) == len(final.details["original_list"])
        assert sorted(final.details["shuffled_list"]) == sorted(final.details["original_list"])
        assert len(final.details["one_time_token"]) == 8

    def test_distribution_is_roughly_uniform(self):
        _, decoded, raw, _ = run_problem("random-bits", {"bit_count": 3, "how_many": 200})
        assert len(raw.counts) == 8
        assert decoded.details["uniformity"]["score"] > 0.9

    def test_rejects_invalid_bit_count(self):
        with pytest.raises(ValidationError):
            get_problem("random-bits").validate({"bit_count": 99, "how_many": 4})


class TestBellState:
    def test_phi_plus_is_perfectly_correlated(self):
        final, *_ = run_problem("bell-state", {"parties": 2, "state": "phi_plus"})
        assert final.verified is True
        assert final.details["correlation"] == 1.0

    def test_psi_plus_is_anti_correlated(self):
        _, decoded, raw, _ = run_problem("bell-state", {"parties": 2, "state": "psi_plus"})
        assert set(raw.counts) <= {"01", "10"}
        assert decoded.details["correlation"] == 1.0

    def test_individual_qubits_look_random(self):
        _, decoded, *_ = run_problem("bell-state", {"parties": 2, "state": "phi_plus"})
        for marginal in decoded.details["marginals"]:
            assert 0.4 < marginal["p_one"] < 0.6

    def test_ghz_with_four_parties(self):
        _, _, raw, _ = run_problem("bell-state", {"parties": 4, "state": "phi_plus"})
        assert set(raw.counts) == {"0000", "1111"}

    def test_rejects_non_phi_plus_for_many_parties(self):
        with pytest.raises(ValidationError):
            get_problem("bell-state").validate({"parties": 3, "state": "psi_plus"})


class TestDeutschJozsa:
    @pytest.mark.parametrize(
        "oracle,expected",
        [
            ("constant_0", "sabit"),
            ("constant_1", "sabit"),
            ("balanced_parity", "dengeli"),
            ("balanced_first_bit", "dengeli"),
        ],
    )
    def test_identifies_every_oracle_type(self, oracle, expected):
        final, *_ = run_problem("deutsch-jozsa", {"n_bits": 3, "oracle": oracle})
        assert final.answer == expected
        assert final.verified is True
        assert final.confidence > 0.99

    def test_reports_query_advantage(self):
        final, *_ = run_problem("deutsch-jozsa", {"n_bits": 5, "oracle": "balanced_parity"})
        assert final.details["quantum_queries"] == 1
        assert final.details["classical_worst_case_queries"] == 17

    def test_works_across_input_sizes(self):
        for n_bits in range(1, 6):
            final, *_ = run_problem("deutsch-jozsa", {"n_bits": n_bits, "oracle": "constant_0"})
            assert final.answer == "sabit"


class TestBernsteinVazirani:
    @pytest.mark.parametrize("secret", ["1", "01", "1011", "11111", "10101010"])
    def test_recovers_secret_exactly(self, secret):
        final, *_ = run_problem("bernstein-vazirani", {"secret": secret})
        assert final.answer == secret
        assert final.verified is True
        assert final.confidence == 1.0

    def test_single_quantum_query(self):
        final, *_ = run_problem("bernstein-vazirani", {"secret": "1101"})
        assert final.details["quantum_queries"] == 1
        assert final.details["classical_queries"] == 4

    def test_rejects_non_binary_input(self):
        with pytest.raises(ValidationError):
            get_problem("bernstein-vazirani").validate({"secret": "10a1"})

    def test_rejects_empty_secret(self):
        with pytest.raises(ValidationError):
            get_problem("bernstein-vazirani").validate({"secret": ""})


class TestGroverSearch:
    def test_finds_target_in_eight_item_list(self):
        items = ["a", "b", "c", "d", "e", "f", "g", "h"]
        final, *_ = run_problem("grover-search", {"items": items, "target": "f"})
        assert final.answer == "f"
        assert final.verified is True
        assert final.confidence > 0.9

    @pytest.mark.parametrize("target", ["elma", "armut", "kiraz", "muz"])
    def test_finds_every_target_in_four_item_list(self, target):
        items = ["elma", "armut", "kiraz", "muz"]
        final, *_ = run_problem("grover-search", {"items": items, "target": target})
        assert final.answer == target

    def test_optimal_iteration_count_is_computed(self):
        spec = get_problem("grover-search").validate(
            {"items": ["a", "b", "c", "d", "e", "f", "g", "h"], "target": "a"}
        )
        assert spec.params["optimal_iterations"] == 2
        assert spec.params["n_qubits"] == 3

    def test_too_many_iterations_reduces_success(self):
        """Fazla tekrar başarıyı düşürür.

        Genlik, hedefi aşıp geri dönmeye başlar. 8 öğelik listede en iyi
        tekrar sayısı 2'dir; 4 tekrarda başarı neredeyse sıfıra iner.
        İlginç bir ayrıntı: 6 tekrarda tam bir tur tamamlanır ve başarı
        yeniden yükselir, yani ilişki doğrusal değil salınımlıdır.
        """
        items = ["a", "b", "c", "d", "e", "f", "g", "h"]
        good, *_ = run_problem("grover-search", {"items": items, "target": "c", "iterations": 2})
        bad, *_ = run_problem("grover-search", {"items": items, "target": "c", "iterations": 4})
        assert good.confidence > 0.9
        assert bad.confidence < 0.2
        assert bad.verified is False

    def test_success_oscillates_with_iteration_count(self):
        """Tekrar sayısı arttıkça başarı bir yükselir bir düşer."""
        items = ["a", "b", "c", "d", "e", "f", "g", "h"]
        confidences = []
        for iterations in range(0, 7):
            final, *_ = run_problem(
                "grover-search", {"items": items, "target": "c", "iterations": iterations}
            )
            confidences.append(final.confidence)
        # 2 tekrarda tepe, 4 tekrarda dip, 6 tekrarda tekrar tepe.
        assert confidences[2] > confidences[4]
        assert confidences[6] > confidences[4]

    def test_reports_speedup_against_classical(self):
        items = ["a", "b", "c", "d", "e", "f", "g", "h"]
        final, *_ = run_problem("grover-search", {"items": items, "target": "h"})
        assert final.details["classical_average_steps"] == 4.5
        assert final.details["quantum_steps"] == 2

    def test_rejects_target_outside_list(self):
        with pytest.raises(ValidationError):
            get_problem("grover-search").validate({"items": ["a", "b"], "target": "z"})

    def test_rejects_oversized_list(self):
        with pytest.raises(ValidationError):
            get_problem("grover-search").validate(
                {"items": [str(i) for i in range(12)], "target": "1"}
            )


class TestRouter:
    def test_every_problem_gets_a_decision_with_reasoning(self):
        for problem in list_problems():
            spec = problem.validate(dict(problem.default_input))
            request = JobRequest(problem_id=problem.id, input=dict(problem.default_input))
            decision = ROUTER.decide(problem, spec, request)
            assert decision.n_qubits >= 1
            assert decision.shots >= 1
            assert len(decision.reasoning) >= 3, f"{problem.id} için gerekçe yetersiz"
            assert decision.cost_estimate["state_dimension"] == 2 ** decision.n_qubits

    def test_user_shots_override_is_honoured_and_explained(self):
        problem = get_problem("bell-state")
        spec = problem.validate(dict(problem.default_input))
        request = JobRequest(problem_id=problem.id, input={}, shots=77)
        decision = ROUTER.decide(problem, spec, request)
        assert decision.shots == 77
        assert any("77" in r for r in decision.reasoning)

    def test_small_problems_get_an_honest_warning(self):
        problem = get_problem("grover-search")
        spec = problem.validate(dict(problem.default_input))
        request = JobRequest(problem_id=problem.id, input={})
        decision = ROUTER.decide(problem, spec, request)
        assert any("klasik çözüm daha hızlı" in r.lower() for r in decision.reasoning)


class TestNoiseEffect:
    def test_noise_lowers_confidence(self):
        problem = get_problem("bernstein-vazirani")
        spec = problem.validate({"secret": "1011"})
        circuit, _ = transpile(problem.build_circuit(spec, 5))

        clean = BACKEND.run(circuit, shots=512, seed=5, noise_level="ideal")
        noisy = BACKEND.run(circuit, shots=512, seed=5, noise_level="high")

        clean_confidence = problem.decode(clean, spec).confidence
        noisy_confidence = problem.decode(noisy, spec).confidence
        assert clean_confidence == 1.0
        assert noisy_confidence < clean_confidence
