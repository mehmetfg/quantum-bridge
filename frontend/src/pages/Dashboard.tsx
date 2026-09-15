/** Genel bakış: boru hattı tanıtımı, problem kartları ve son işler. */

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { api } from '../api/client';
import {
  DIFFICULTY_STYLES,
  SIDE_STYLES,
  STAGE_ICONS,
  STATUS_LABELS,
  STATUS_STYLES,
  cx,
  formatDateTime,
} from '../lib/style';
import type { JobSummary, ProblemInfo, StageInfo } from '../types';

export default function Dashboard() {
  const [problems, setProblems] = useState<ProblemInfo[]>([]);
  const [stages, setStages] = useState<StageInfo[]>([]);
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.problems(), api.stages(), api.jobs(8)])
      .then(([p, s, j]) => {
        setProblems(p);
        setStages(s);
        setJobs(j);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <div className="space-y-10">
      <section>
        <h1 className="text-2xl font-bold text-slate-100">
          Kuantum, tek başına bir çözüm değil. Bir boru hattının içindeki özel bir duraktır.
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-400">
          Bu uygulama, klasik bir bilgisayarın bir problemi nasıl parçaladığını, yapay zeka
          katmanının hangi parçayı kuantuma göndereceğine nasıl karar verdiğini, kuantum
          tarafının ne döndürdüğünü ve sonucun klasik programa nasıl geri işlendiğini adım
          adım gösterir. Altı adımdan yalnızca biri kuantum tarafında çalışır.
        </p>
        {error && (
          <p className="mt-4 rounded-lg border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
            Arka uca ulaşılamadı: {error}
          </p>
        )}
      </section>

      {stages.length > 0 && (
        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
            Boru hattı
          </h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {stages.map((stage) => {
              const style = SIDE_STYLES[stage.side];
              return (
                <div key={stage.stage} className={cx('card', style.border)}>
                  <div className="mb-2 flex items-center gap-2">
                    <span
                      className={cx(
                        'flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold text-slate-950',
                        style.dot,
                      )}
                    >
                      {STAGE_ICONS[stage.stage]}
                    </span>
                    <h3 className="text-sm font-semibold text-slate-100">{stage.title}</h3>
                    <span className={cx('chip ml-auto', style.bg, style.text)}>{stage.side}</span>
                  </div>
                  <p className="text-xs leading-relaxed text-slate-400">{stage.summary}</p>
                </div>
              );
            })}
          </div>
        </section>
      )}

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
            Problemler
          </h2>
          <Link to="/laboratuvar" className="text-xs text-sky-400 hover:text-sky-300">
            Laboratuvara git
          </Link>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {problems.map((problem) => (
            <Link
              key={problem.id}
              to={`/laboratuvar/${problem.id}`}
              className="card card-hover flex flex-col"
            >
              <div className="mb-2 flex items-start justify-between gap-2">
                <h3 className="text-sm font-semibold leading-tight text-slate-100">
                  {problem.title}
                </h3>
                <span
                  className={cx(
                    'chip shrink-0',
                    DIFFICULTY_STYLES[problem.difficulty] ?? 'bg-slate-700/50 text-slate-300',
                  )}
                >
                  {problem.difficulty}
                </span>
              </div>
              <p className="mb-3 flex-1 text-xs leading-relaxed text-slate-400">
                {problem.short_description}
              </p>
              <div className="flex flex-wrap gap-1.5">
                {problem.concepts.slice(0, 3).map((concept) => (
                  <span key={concept} className="chip bg-slate-800/70 text-slate-400">
                    {concept}
                  </span>
                ))}
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
          Son işler
        </h2>
        {jobs.length === 0 ? (
          <div className="card text-sm text-slate-500">
            Henüz iş çalıştırılmadı. Laboratuvardan bir problem seçip başlatabilirsiniz.
          </div>
        ) : (
          <div className="overflow-hidden rounded-xl border border-slate-800">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-900 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-2.5 font-medium">Problem</th>
                  <th className="px-4 py-2.5 font-medium">Durum</th>
                  <th className="px-4 py-2.5 font-medium">Sonuç</th>
                  <th className="px-4 py-2.5 font-medium">Zaman</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70">
                {jobs.map((job) => (
                  <tr key={job.id} className="bg-slate-900/30 transition hover:bg-slate-900/70">
                    <td className="px-4 py-2.5">
                      <Link to={`/isler/${job.id}`} className="text-sky-400 hover:text-sky-300">
                        {job.problem_title}
                      </Link>
                    </td>
                    <td className="px-4 py-2.5">
                      <span className={cx('chip', STATUS_STYLES[job.status])}>
                        {STATUS_LABELS[job.status]}
                      </span>
                    </td>
                    <td className="max-w-[260px] truncate px-4 py-2.5 text-xs text-slate-400">
                      {job.answer_label ?? '—'}
                    </td>
                    <td className="whitespace-nowrap px-4 py-2.5 text-xs text-slate-500">
                      {formatDateTime(job.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
