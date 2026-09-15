/** Laboratuvar: problem seç, girdileri ayarla, işi başlat. */

import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { api } from '../api/client';
import ProblemForm from '../components/ProblemForm';
import { DIFFICULTY_STYLES, cx } from '../lib/style';
import type { BackendInfo, JobRequest, ProblemInfo } from '../types';

const NOISE_OPTIONS: { value: JobRequest['noise_level']; label: string; help: string }[] = [
  { value: 'ideal', label: 'İdeal', help: 'Hiç hata yok. Algoritmanın saf davranışını gösterir.' },
  { value: 'low', label: 'Düşük', help: 'İyi kalibre edilmiş bir cihaza yakın.' },
  { value: 'medium', label: 'Orta', help: 'Bugünün tipik bulut cihazlarına yakın.' },
  { value: 'high', label: 'Yüksek', help: 'Kötü koşullar. Sonucun nasıl bozulduğunu gösterir.' },
];

export default function ProblemLab() {
  const { problemId } = useParams();
  const navigate = useNavigate();

  const [problems, setProblems] = useState<ProblemInfo[]>([]);
  const [backends, setBackends] = useState<BackendInfo[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(problemId ?? null);
  const [input, setInput] = useState<Record<string, unknown>>({});
  const [noiseLevel, setNoiseLevel] = useState<JobRequest['noise_level']>('ideal');
  const [backendId, setBackendId] = useState<string>('local-statevector');
  const [shots, setShots] = useState<number | null>(null);
  const [seed, setSeed] = useState<number | null>(null);
  const [demoPace, setDemoPace] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.problems(), api.backends()])
      .then(([p, b]) => {
        setProblems(p);
        setBackends(b.backends);
        setBackendId(b.default);
        if (!problemId && p.length) setSelectedId(p[0].id);
      })
      .catch((err: Error) => setError(err.message));
  }, [problemId]);

  const selected = useMemo(
    () => problems.find((p) => p.id === selectedId) ?? null,
    [problems, selectedId],
  );

  useEffect(() => {
    if (selected) {
      setInput({ ...selected.default_input });
      setShots(null);
    }
  }, [selected]);

  const start = async () => {
    if (!selected) return;
    setStarting(true);
    setError(null);
    try {
      const job = await api.startJob({
        problem_id: selected.id,
        input,
        shots,
        backend_id: backendId,
        noise_level: noiseLevel,
        seed,
        stage_delay_ms: demoPace ? 550 : 0,
      });
      navigate(`/isler/${job.id}`);
    } catch (err) {
      setError((err as Error).message);
      setStarting(false);
    }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
      <aside className="space-y-2">
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">
          Problemler
        </h2>
        {problems.map((problem) => (
          <button
            key={problem.id}
            type="button"
            onClick={() => {
              setSelectedId(problem.id);
              navigate(`/laboratuvar/${problem.id}`, { replace: true });
            }}
            className={cx(
              'w-full rounded-lg border p-3 text-left transition',
              selectedId === problem.id
                ? 'border-sky-500/60 bg-sky-500/10'
                : 'border-slate-800 bg-slate-900/40 hover:border-slate-700',
            )}
          >
            <div className="flex items-start justify-between gap-2">
              <span className="text-sm font-medium leading-tight text-slate-100">
                {problem.title}
              </span>
              <span
                className={cx(
                  'chip shrink-0',
                  DIFFICULTY_STYLES[problem.difficulty] ?? 'bg-slate-700/50 text-slate-300',
                )}
              >
                {problem.difficulty}
              </span>
            </div>
            <p className="mt-1 text-xs leading-relaxed text-slate-500">{problem.category}</p>
          </button>
        ))}
      </aside>

      <div className="space-y-6">
        {!selected ? (
          <div className="card text-sm text-slate-500">Bir problem seçin.</div>
        ) : (
          <>
            <section className="card">
              <h1 className="text-lg font-bold text-slate-100">{selected.title}</h1>
              <p className="mt-2 text-sm leading-relaxed text-slate-400">{selected.description}</p>

              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-3">
                  <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-emerald-300">
                    Kuantum ne kazandırıyor
                  </h3>
                  <p className="text-xs leading-relaxed text-slate-400">
                    {selected.quantum_advantage}
                  </p>
                </div>
                <div className="rounded-lg border border-sky-500/30 bg-sky-500/5 p-3">
                  <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-sky-300">
                    Klasik olarak nasıl yapılırdı
                  </h3>
                  <p className="text-xs leading-relaxed text-slate-400">
                    {selected.classical_comparison}
                  </p>
                </div>
              </div>
            </section>

            <section className="card">
              <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-400">
                Girdi
              </h2>
              <ProblemForm problem={selected} value={input} onChange={setInput} />
            </section>

            <section className="card">
              <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-400">
                Çalıştırma ayarları
              </h2>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="label" htmlFor="backend">
                    Kuantum arka ucu
                  </label>
                  <select
                    id="backend"
                    className="input"
                    value={backendId}
                    onChange={(event) => setBackendId(event.target.value)}
                  >
                    {backends.map((backend) => (
                      <option key={backend.id} value={backend.id} disabled={!backend.available}>
                        {backend.name}
                        {!backend.available && ' (yakında)'}
                      </option>
                    ))}
                  </select>
                  <p className="help-text">
                    {backends.find((b) => b.id === backendId)?.description ?? ''}
                  </p>
                </div>

                <div>
                  <label className="label" htmlFor="noise">
                    Gürültü seviyesi
                  </label>
                  <select
                    id="noise"
                    className="input"
                    value={noiseLevel}
                    onChange={(event) =>
                      setNoiseLevel(event.target.value as JobRequest['noise_level'])
                    }
                  >
                    {NOISE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <p className="help-text">
                    {NOISE_OPTIONS.find((o) => o.value === noiseLevel)?.help}
                  </p>
                </div>

                <div>
                  <label className="label" htmlFor="shots">
                    Atış sayısı (shots)
                  </label>
                  <input
                    id="shots"
                    type="number"
                    className="input"
                    min={1}
                    max={20000}
                    placeholder="Boş bırakılırsa yönlendirici karar verir"
                    value={shots ?? ''}
                    onChange={(event) =>
                      setShots(event.target.value === '' ? null : Number(event.target.value))
                    }
                  />
                  <p className="help-text">
                    Devrenin kaç kez çalıştırılacağı. Hassasiyet atış sayısının kareköküyle artar,
                    yani hatayı yarıya indirmek için atışı dörde katlamak gerekir.
                  </p>
                </div>

                <div>
                  <label className="label" htmlFor="seed">
                    Tohum değeri (seed)
                  </label>
                  <input
                    id="seed"
                    type="number"
                    className="input"
                    placeholder="Boş bırakılırsa her çalıştırma farklı olur"
                    value={seed ?? ''}
                    onChange={(event) =>
                      setSeed(event.target.value === '' ? null : Number(event.target.value))
                    }
                  />
                  <p className="help-text">
                    Aynı tohum aynı sonucu verir. Sunumda tekrarlanabilirlik için kullanışlıdır.
                  </p>
                </div>
              </div>

              <label className="mt-4 flex items-start gap-2.5 text-sm text-slate-300">
                <input
                  type="checkbox"
                  className="mt-0.5 h-4 w-4 rounded border-slate-700 bg-slate-950"
                  checked={demoPace}
                  onChange={(event) => setDemoPace(event.target.checked)}
                />
                <span>
                  Sunum hızı
                  <span className="block text-xs text-slate-500">
                    Aşamalar arasına yarım saniye bekleme koyar. Hesaba etkisi yoktur, sadece
                    adımların tek tek izlenmesini sağlar.
                  </span>
                </span>
              </label>

              {error && (
                <p className="mt-4 rounded-lg border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
                  {error}
                </p>
              )}

              <button
                type="button"
                onClick={start}
                disabled={starting}
                className="btn-primary mt-5 w-full sm:w-auto"
              >
                {starting ? 'Başlatılıyor...' : 'Boru hattını çalıştır'}
              </button>
            </section>
          </>
        )}
      </div>
    </div>
  );
}
