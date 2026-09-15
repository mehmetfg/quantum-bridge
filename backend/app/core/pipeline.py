"""Boru hattı (pipeline): altı aşamayı sırayla çalıştıran orkestratör.

Bu dosya projenin merkezi fikridir. Kuantum hesaplama burada tek başına bir
çözüm değil, klasik bir iş akışının ortasındaki özel bir duraktır:

    klasik giriş -> yapay zeka yönlendirme -> kodlama ve sadeleştirme
    -> kuantum çalıştırma -> çözümleme -> klasik birleştirme

Kuantum sadece dördüncü adımdır. Diğer beş adım klasik bilgisayarda çalışır.
Gerçek hibrit sistemlerin şeklini doğru anlamak açısından bu oran önemlidir.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import UTC, datetime

from ..ai.router import QuantumRouter
from ..classical import postprocess, preprocess
from ..problems.base import ValidationError
from ..problems.registry import get_problem
from ..quantum.backends.registry import get_backend
from ..quantum.qasm import to_qasm3
from ..quantum.transpiler import routing_report, transpile
from .models import Job, JobStatus, Stage, TraceEvent
from .trace import TraceCollector


class PipelineError(RuntimeError):
    """Boru hattı bir aşamada durduğunda fırlatılır."""

    def __init__(self, stage: Stage, message: str) -> None:
        super().__init__(message)
        self.stage = stage
        self.message = message


class Pipeline:
    """Bir işi baştan sona çalıştırır."""

    def __init__(self, router: QuantumRouter | None = None) -> None:
        self.router = router or QuantumRouter()

    def run(
        self,
        job: Job,
        on_event: Callable[[TraceEvent], None] | None = None,
    ) -> Job:
        """İşi çalıştırır ve her aşamada iz bırakır."""
        trace = TraceCollector(on_event=on_event)
        started = time.perf_counter()
        job.status = JobStatus.RUNNING

        try:
            spec, problem = self._stage_intake(job, trace)
            decision = self._stage_routing(job, trace, problem, spec)
            circuit, qasm = self._stage_encode(job, trace, problem, spec, decision)
            raw = self._stage_execute(job, trace, circuit, decision)
            decoded = self._stage_decode(job, trace, problem, spec, raw, decision)
            self._stage_merge(job, trace, problem, spec, decoded)
            job.status = JobStatus.COMPLETED
        except PipelineError as exc:
            trace.record_error(exc.stage, exc.message)
            job.status = JobStatus.FAILED
            job.error = exc.message
        except Exception as exc:  # beklenmeyen hata da ize yazılır
            stage = job.current_stage or Stage.INTAKE
            message = f"Beklenmeyen hata: {exc}"
            trace.record_error(stage, message)
            job.status = JobStatus.FAILED
            job.error = message

        job.events = trace.events
        job.total_duration_ms = round((time.perf_counter() - started) * 1000.0, 3)
        job.completed_at = datetime.now(UTC)
        return job

    # 1. Klasik giriş ---------------------------------------------------------

    def _stage_intake(self, job: Job, trace: TraceCollector):
        job.current_stage = Stage.INTAKE
        trace.start_stage()
        try:
            problem = get_problem(job.problem_id)
        except KeyError as exc:
            raise PipelineError(Stage.INTAKE, str(exc)) from exc

        job.problem_title = problem.title
        try:
            spec, details = preprocess.prepare(problem, job.request.input)
        except ValidationError as exc:
            raise PipelineError(Stage.INTAKE, f"Girdi geçersiz: {exc}") from exc

        trace.record(
            Stage.INTAKE,
            details=details,
            data={
                "problem_id": problem.id,
                "problem_title": problem.title,
                "params": spec.params,
                "classical_comparison": problem.classical_comparison,
            },
        )
        return spec, problem

    # 2. Yapay zeka yönlendirme ----------------------------------------------

    def _stage_routing(self, job: Job, trace: TraceCollector, problem, spec):
        job.current_stage = Stage.AI_ROUTING
        trace.start_stage()
        decision = self.router.decide(problem, spec, job.request)
        job.routing = decision

        trace.record(
            Stage.AI_ROUTING,
            details=decision.reasoning,
            data={
                "decision": decision.model_dump(),
                "rejected_alternatives": decision.rejected_alternatives,
                "quantum_advantage": problem.quantum_advantage,
            },
        )
        return decision

    # 3. Kodlama ve sadeleştirme ---------------------------------------------

    def _stage_encode(self, job: Job, trace: TraceCollector, problem, spec, decision):
        job.current_stage = Stage.ENCODE_OPTIMIZE
        trace.start_stage()
        try:
            raw_circuit = problem.build_circuit(spec, decision.n_qubits)
        except Exception as exc:
            raise PipelineError(
                Stage.ENCODE_OPTIMIZE, f"Devre kurulamadı: {exc}"
            ) from exc

        optimized, report = transpile(raw_circuit)
        routing = routing_report(optimized)
        qasm = to_qasm3(optimized)

        job.circuit = optimized.to_dict()
        job.qasm = qasm

        details = [
            f"Devre kuruldu: {raw_circuit.n_qubits} kubit, {raw_circuit.gate_count} kapı.",
            f"Sadeleştirme sonrası: {optimized.gate_count} kapı, derinlik {optimized.depth}.",
            *report.notes,
            routing["explanation"],
            "OpenQASM 3 metni üretildi. Bu metin, gerçek donanıma gönderilecek olanın aynısıdır.",
        ]

        trace.record(
            Stage.ENCODE_OPTIMIZE,
            details=details,
            data={
                "circuit": optimized.to_dict(),
                "original_circuit": raw_circuit.to_dict(),
                "transpile_report": report.to_dict(),
                "routing_report": routing,
                "qasm": qasm,
                "encoding": decision.encoding,
            },
        )
        return optimized, qasm

    # 4. Kuantum çalıştırma ---------------------------------------------------

    def _stage_execute(self, job: Job, trace: TraceCollector, circuit, decision):
        job.current_stage = Stage.QUANTUM_EXEC
        trace.start_stage()
        try:
            backend = get_backend(job.request.backend_id)
        except (KeyError, RuntimeError) as exc:
            raise PipelineError(Stage.QUANTUM_EXEC, str(exc)) from exc

        try:
            raw = backend.run(
                circuit,
                shots=decision.shots,
                seed=job.request.seed,
                noise_level=job.request.noise_level,
                collect_snapshots=True,
            )
        except Exception as exc:
            raise PipelineError(
                Stage.QUANTUM_EXEC, f"Kuantum çalıştırma başarısız: {exc}"
            ) from exc

        job.raw_result = raw.to_dict()

        details = [
            f"Arka uç: {raw.backend_name}.",
            f"{raw.shots} atış yapıldı, {len(raw.counts)} farklı sonuç gözlendi.",
            "Dönen veri bir cevap değil, bir olasılık dağılımıdır.",
        ]
        noise_meta = raw.meta.get("noise", {})
        if noise_meta.get("applied"):
            details.append(noise_meta["explanation"])
        else:
            details.append(
                "Gürültü kapalı: sonuç ideal koşulu gösteriyor. Gerçek donanımda "
                "bu kadar temiz bir dağılım beklenmez."
            )
        details.append(raw.meta.get("queue_note", ""))

        trace.record(
            Stage.QUANTUM_EXEC,
            details=[d for d in details if d],
            data={
                "counts": raw.counts,
                "probabilities": raw.probabilities,
                "shots": raw.shots,
                "backend": raw.backend_name,
                "meta": raw.meta,
                "snapshots": raw.snapshots[:24],
            },
        )
        return raw

    # 5. Çözümleme ------------------------------------------------------------

    def _stage_decode(self, job: Job, trace: TraceCollector, problem, spec, raw, decision):
        job.current_stage = Stage.DECODE
        trace.start_stage()
        try:
            decoded = problem.decode(raw, spec)
        except Exception as exc:
            raise PipelineError(Stage.DECODE, f"Çözümleme başarısız: {exc}") from exc

        stats = postprocess.distribution_stats(raw.counts)
        note = postprocess.reliability_note(stats, decision.confidence_target)

        trace.record(
            Stage.DECODE,
            details=[*decoded.explanation, note],
            data={
                "answer": decoded.answer,
                "answer_label": decoded.answer_label,
                "confidence": decoded.confidence,
                "statistics": stats,
                "details": decoded.details,
            },
        )
        return decoded

    # 6. Klasik birleştirme ---------------------------------------------------

    def _stage_merge(self, job: Job, trace: TraceCollector, problem, spec, decoded):
        job.current_stage = Stage.CLASSICAL_MERGE
        trace.start_stage()
        try:
            final = problem.merge(decoded, spec)
        except Exception as exc:
            raise PipelineError(
                Stage.CLASSICAL_MERGE, f"Klasik birleştirme başarısız: {exc}"
            ) from exc

        job.result = final
        details = [final.classical_usage]
        if final.verification_note:
            details.append(final.verification_note)
        details.append(
            "Hibrit döngü burada kapanır: kuantumdan gelen sonuç artık klasik "
            "programın sıradan bir değişkenidir."
        )

        trace.record(
            Stage.CLASSICAL_MERGE,
            details=details,
            data={"result": final.model_dump()},
        )
        return final
