/**
 * İş ayrıntısı: projenin ana ekranı.
 *
 * Altı aşama canlı olarak akar. Her aşamanın çıktısı, o aşamaya özgü
 * görselle birlikte gösterilir: yönlendirme kararı, devre çizimi,
 * ölçüm dağılımı, çözümleme istatistikleri ve klasik birleştirme.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { api, streamJob } from '../api/client';
import AiReasoningCard from '../components/AiReasoningCard';
import CircuitDiagram from '../components/CircuitDiagram';
import CountsHistogram from '../components/CountsHistogram';
import PipelineStepper from '../components/PipelineStepper';
import QasmViewer from '../components/QasmViewer';
import StateVectorTable from '../components/StateVectorTable';
import TraceLog from '../components/TraceLog';
import {
  STATUS_LABELS,
  STATUS_STYLES,
  confidenceStyle,
  cx,
  formatDuration,
} from '../lib/style';
import type { Job, StageInfo, StageName, TraceEvent } from '../types';

export default function JobDetail() {
  const { jobId } = useParams();
  const [job, setJob] = useState<Job | null>(null);
  const [stages, setStages] = useState<StageInfo[]>([]);
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [selectedStage, setSelectedStage] = useState<StageName | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [streaming, setStreaming] = useState(true);
  const closeRef = useRef<(() => void) | null>(null);

  const handleStage = useCallback((event: TraceEvent) => {
    setEvents((previous) => {
      if (previous.some((existing) => existing.stage === event.stage)) return previous;
      return [...previous, event];
    });
  }, []);

  useEffect(() => {
    if (!jobId) return;

    api.stages().then(setStages).catch(() => undefined);

    api
      .job(jobId)
      .then((initial) => {
        setJob(initial);
        setEvents(initial.events);
        if (initial.status === 'COMPLETED' || initial.status === 'FAILED') {
          setStreaming(false);
          return;
        }
        closeRef.current = streamJob(jobId, {
          onStage: handleStage,
          onDone: (finished) => {
            setJob(finished);
            setEvents(finished.events);
            setStreaming(false);
          },
          onError: (message) => {
            setError(message);
            setStreaming(false);
          },
        });
      })
      .catch((err: Error) => {
        setError(err.message);
        setStreaming(false);
      });

    return () => {
      closeRef.current?.();
      closeRef.current = null;
    };
  }, [jobId, handleStage]);

  const currentStage = useMemo<StageName | null>(() => {
    if (!stages.length) return null;
    const done = new Set(events.map((event) => event.stage));
    const next = stages.find((stage) => !done.has(stage.stage));
    return next ? next.stage : null;
  }, [stages, events]);

  const eventByStage = useMemo(
    () => new Map(events.map((event) => [event.stage, event])),
    [events],
  );

  if (error && !job) {
    return (
      <div className="card border-rose-500/40 bg-rose-500/5 text-sm text-rose-300">
        {error}{' '}
        <Link to="/laboratuvar" className="underline">
          Laboratuvara dön
        </Link>
      </div>
    );
  }

  if (!job) {
    return <div className="text-sm text-slate-500">Yükleniyor...</div>;
  }

  const result = job.result;
  const routing = job.routing;
  const circuit = job.circuit;
  const raw = job.raw_result;
  const encodeEvent = eventByStage.get('ENCODE_OPTIMIZE');
  const decodeEvent = eventByStage.get('DECODE');
  const transpileReport = encodeEvent?.data?.transpile_report as any;
  const routingReport = encodeEvent?.data?.routing_report as any;
  const statistics = decodeEvent?.data?.statistics as any;
  const topOutcome = statistics?.top_outcome as string | undefined;

  return (
    <div className="space-y-6">
      {/* Başlık */}
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="mb-1 flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-100">{job.problem_title}</h1>
            <span className={cx('chip', STATUS_STYLES[job.status])}>
              {STATUS_LABELS[job.status]}
            </span>
            {streaming && (
              <span className="chip bg-amber-500/15 text-amber-300">canlı akıyor</span>
            )}
          </div>
          <p className="font-mono text-xs text-slate-500">
            iş {job.id} · {formatDuration(job.total_duration_ms)} · {job.request.noise_level}{' '}
            gürültü
          </p>
        </div>
        <Link to={`/laboratuvar/${job.problem_id}`} className="btn-ghost">
          Yeniden çalıştır
        </Link>
      </header>

      {/* Aşama çubuğu */}
      {stages.length > 0 && (
        <PipelineStepper
          stages={stages}
          events={events}
          activeStage={streaming ? currentStage : null}
          onSelect={setSelectedStage}
          selected={selectedStage}
        />
      )}

      {job.error && (
        <div className="card border-rose-500/40 bg-rose-500/5">
          <h3 className="mb-1 text-sm font-semibold text-rose-300">İş durduruldu</h3>
          <p className="text-sm text-slate-300">{job.error}</p>
          <p className="mt-2 text-xs text-slate-500">
            Hata da öğrenmenin parçasıdır: yukarıdaki çubuk hangi aşamada durulduğunu gösterir.
          </p>
        </div>
      )}

      {/* Sonuç kartı */}
      {result && (
        <section className="card border-emerald-500/30 bg-gradient-to-br from-emerald-500/5 to-transparent">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">Sonuç</p>
              <p className="mt-1 text-xl font-bold text-slate-100">{result.answer_label}</p>
            </div>
            <div className="text-right">
              <p className="text-xs uppercase tracking-wide text-slate-500">Güven</p>
              <p className={cx('mt-1 text-xl font-bold', confidenceStyle(result.confidence))}>
                {(result.confidence * 100).toFixed(1)}%
              </p>
            </div>
            {result.verified !== null && (
              <div className="text-right">
                <p className="text-xs uppercase tracking-wide text-slate-500">Klasik doğrulama</p>
                <p
                  className={cx(
                    'mt-1 text-xl font-bold',
                    result.verified ? 'text-emerald-300' : 'text-rose-300',
                  )}
                >
                  {result.verified ? 'geçti' : 'geçmedi'}
                </p>
              </div>
            )}
          </div>

          {result.verification_note && (
            <p className="mt-4 text-sm leading-relaxed text-slate-400">
              {result.verification_note}
            </p>
          )}
          {result.classical_usage && (
            <div className="mt-3 rounded-lg border border-sky-500/30 bg-sky-500/5 p-3">
              <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-sky-300">
                Klasik programda nasıl kullanıldı
              </h3>
              <p className="text-xs leading-relaxed text-slate-400">{result.classical_usage}</p>
            </div>
          )}

          <ResultExtras details={result.details} />
        </section>
      )}

      <div className="grid gap-6 lg:grid-cols-[1fr_400px]">
        <div className="space-y-6">
          {/* Yönlendirme */}
          {routing && (
            <section className="card">
              <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-violet-300">
                <span className="h-2 w-2 rounded-full bg-violet-400" />
                Yapay zeka yönlendirme kararı
              </h2>
              <AiReasoningCard routing={routing} />
            </section>
          )}

          {/* Devre */}
          {circuit && (
            <section className="card">
              <h2 className="mb-1 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-sky-300">
                <span className="h-2 w-2 rounded-full bg-sky-400" />
                Kuantum devresi
              </h2>
              <div className="mb-3 flex flex-wrap gap-4 text-xs text-slate-500">
                <span>{circuit.n_qubits} kubit</span>
                <span>{circuit.metrics.gate_count} kapı</span>
                <span>{circuit.metrics.two_qubit_gate_count} iki kubitlik kapı</span>
                <span>derinlik {circuit.metrics.depth}</span>
              </div>
              <CircuitDiagram circuit={circuit} />

              {transpileReport && (
                <div className="mt-4 rounded-lg border border-slate-800 bg-slate-950/60 p-3">
                  <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                    Sadeleştirme raporu
                  </h3>
                  <p className="mb-2 text-xs text-slate-400">
                    {transpileReport.before.gate_count} kapıdan{' '}
                    {transpileReport.after.gate_count} kapıya indi
                    {transpileReport.saved_percent > 0 &&
                      ` (yüzde ${transpileReport.saved_percent} azalma)`}
                    .
                  </p>
                  <ul className="space-y-1">
                    {(transpileReport.notes as string[]).map((note, index) => (
                      <li key={index} className="flex gap-2 text-xs text-slate-500">
                        <span className="mt-[7px] h-1 w-1 shrink-0 rounded-full bg-slate-600" />
                        <span>{note}</span>
                      </li>
                    ))}
                  </ul>
                  {routingReport?.explanation && (
                    <p className="mt-2 border-t border-slate-800 pt-2 text-xs leading-relaxed text-slate-500">
                      {routingReport.explanation}
                    </p>
                  )}
                </div>
              )}
            </section>
          )}

          {/* Ölçüm sonuçları */}
          {raw && (
            <section className="card">
              <h2 className="mb-1 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-emerald-300">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                Ham ölçüm sonuçları
              </h2>
              <p className="mb-4 text-xs text-slate-500">
                {raw.backend_name} üzerinde {raw.shots} atış. Kuantum tarafının döndürdüğü tek
                şey budur: bir cevap değil, bir dağılım.
              </p>
              <CountsHistogram
                counts={raw.counts}
                probabilities={raw.probabilities}
                highlight={topOutcome ?? null}
              />

              {raw.meta?.noise?.applied && (
                <p className="mt-3 rounded-lg border border-amber-500/30 bg-amber-500/5 p-3 text-xs leading-relaxed text-amber-200/80">
                  {raw.meta.noise.explanation}
                </p>
              )}

              {raw.statevector && circuit && (
                <details className="mt-4">
                  <summary className="cursor-pointer text-xs font-medium text-slate-400 hover:text-slate-200">
                    Durum vektörünü göster (gerçek donanımda görülemez)
                  </summary>
                  <div className="mt-3">
                    <StateVectorTable
                      statevector={raw.statevector}
                      nQubits={circuit.n_qubits}
                    />
                  </div>
                </details>
              )}
            </section>
          )}

          {/* İstatistikler */}
          {statistics && (
            <section className="card">
              <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-400">
                Çözümleme istatistikleri
              </h2>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <Stat label="Toplam atış" value={String(statistics.total_shots)} />
                <Stat label="Farklı sonuç" value={String(statistics.unique_outcomes)} />
                <Stat
                  label="En olası sonucun payı"
                  value={`${(statistics.top_share * 100).toFixed(1)}%`}
                />
                <Stat
                  label="İkinciyle fark"
                  value={`${(statistics.margin * 100).toFixed(1)}%`}
                />
              </div>
              <p className="mt-3 text-xs text-slate-500">
                Yüzde 95 güven aralığı:{' '}
                {(statistics.confidence_interval_95[0] * 100).toFixed(1)}% ile{' '}
                {(statistics.confidence_interval_95[1] * 100).toFixed(1)}% arasında. Bu aralık,
                atış sayısı arttıkça daralır.
              </p>
            </section>
          )}

          {/* QASM */}
          {job.qasm && (
            <section className="card">
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
                OpenQASM 3 çıktısı
              </h2>
              <QasmViewer qasm={job.qasm} />
            </section>
          )}
        </div>

        {/* Sağ sütun: adım adım anlatım */}
        <aside className="space-y-3 lg:sticky lg:top-20 lg:self-start">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
            Adım adım ne oldu
          </h2>
          <div className="max-h-[calc(100vh-140px)] overflow-y-auto pr-1">
            <TraceLog events={events} onSelect={setSelectedStage} selected={selectedStage} />
          </div>
        </aside>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2">
      <p className="text-[10px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-0.5 text-sm font-semibold text-slate-100">{value}</p>
    </div>
  );
}

/** Sonuç ayrıntılarından, göstermeye değer olanları seçip gösterir. */
function ResultExtras({ details }: { details: Record<string, any> }) {
  const blocks: { label: string; content: string }[] = [];

  if (Array.isArray(details.shuffled_list)) {
    blocks.push({
      label: 'Kuantum rastgeleliğiyle karıştırılan liste',
      content: details.shuffled_list.join(' · '),
    });
  }
  if (typeof details.one_time_token === 'string') {
    blocks.push({ label: 'Tek kullanımlık şifre', content: details.one_time_token });
  }
  if (Array.isArray(details.numbers) && details.numbers.length) {
    blocks.push({
      label: 'Üretilen sayılar',
      content: details.numbers.slice(0, 32).join(', ') + (details.numbers.length > 32 ? '...' : ''),
    });
  }
  if (typeof details.speedup_factor === 'number' && details.speedup_factor > 0) {
    const classical =
      details.classical_worst_case_queries ??
      details.classical_queries ??
      details.classical_average_steps;
    const quantum = details.quantum_queries ?? details.quantum_steps;
    if (classical !== undefined && quantum !== undefined) {
      blocks.push({
        label: 'Sorgu karşılaştırması',
        content: `Klasik ${classical} adım, kuantum ${quantum} adım. Kazanç ${details.speedup_factor} kat.`,
      });
    }
  }
  if (typeof details.shared_key_preview === 'string') {
    blocks.push({
      label: 'Ortak anahtar önizlemesi',
      content: details.shared_key_preview,
    });
  }

  if (!blocks.length) return null;

  return (
    <div className="mt-4 grid gap-2 sm:grid-cols-2">
      {blocks.map((block) => (
        <div
          key={block.label}
          className="rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2"
        >
          <p className="text-[10px] uppercase tracking-wide text-slate-500">{block.label}</p>
          <p className="mt-1 break-words font-mono text-xs text-slate-300">{block.content}</p>
        </div>
      ))}
    </div>
  );
}
