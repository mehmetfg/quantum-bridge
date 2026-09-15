/**
 * Yapay zeka yönlendiricinin karar kartı.
 *
 * Kararın kendisi kadar, hangi seçeneklerin neden elendiği de gösterilir.
 * Bir yönlendiricinin dürüstlük ölçüsü, reddettiği seçenekleri söylemesidir.
 */

import type { RoutingDecision } from '../types';

export default function AiReasoningCard({ routing }: { routing: RoutingDecision }) {
  const cost = routing.cost_estimate as Record<string, any>;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Metric label="Kubit" value={String(routing.n_qubits)} />
        <Metric label="Atış (shot)" value={String(routing.shots)} />
        <Metric
          label="Hedef güven"
          value={
            routing.confidence_target > 0
              ? `${(routing.confidence_target * 100).toFixed(0)}%`
              : 'aranmıyor'
          }
        />
        <Metric label="Karar kaynağı" value={routing.source} />
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Kodlama (encoding)" value={routing.encoding} />
        <Field label="Strateji" value={routing.strategy} />
      </div>

      <section>
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-violet-300">
          Neden bu karar
        </h4>
        <ul className="space-y-1.5">
          {routing.reasoning.map((reason, index) => (
            <li key={index} className="flex gap-2 text-xs leading-relaxed text-slate-400">
              <span className="mt-[7px] h-1 w-1 shrink-0 rounded-full bg-violet-400/70" />
              <span>{reason}</span>
            </li>
          ))}
        </ul>
      </section>

      {routing.rejected_alternatives.length > 0 && (
        <section>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            Değerlendirilip elenen seçenekler
          </h4>
          <ul className="space-y-1.5">
            {routing.rejected_alternatives.map((item, index) => (
              <li key={index} className="flex gap-2 text-xs leading-relaxed text-slate-500">
                <span className="mt-[7px] h-1 w-1 shrink-0 rounded-full bg-slate-600" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {cost?.note && (
        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
          <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">
            Maliyet tahmini
          </h4>
          <p className="text-xs leading-relaxed text-slate-400">{cost.note}</p>
          {cost.hardware_note && (
            <p className="mt-2 text-xs leading-relaxed text-slate-500">{cost.hardware_note}</p>
          )}
        </div>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2">
      <p className="text-[10px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-0.5 text-sm font-semibold text-slate-100">{value}</p>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2">
      <p className="text-[10px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-0.5 text-xs leading-relaxed text-slate-300">{value}</p>
    </div>
  );
}
