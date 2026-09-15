/**
 * Ölçüm sayımlarının çubuk grafiği.
 *
 * Kuantum tarafının döndürdüğü tek şey budur: bir dağılım. Teorik olasılık
 * da aynı grafikte ince bir çizgiyle gösterilir, böylece gözlem ile teori
 * arasındaki fark doğrudan görülür.
 */

import { formatPercent } from '../lib/style';

interface Props {
  counts: Record<string, number>;
  probabilities?: Record<string, number>;
  highlight?: string | null;
  maxBars?: number;
}

export default function CountsHistogram({
  counts,
  probabilities = {},
  highlight = null,
  maxBars = 16,
}: Props) {
  const total = Object.values(counts).reduce((sum, value) => sum + value, 0);
  const entries = Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, maxBars);

  if (!entries.length) {
    return <p className="text-sm text-slate-500">Gösterilecek ölçüm yok.</p>;
  }

  const maxShare = Math.max(...entries.map(([, count]) => count / total));

  return (
    <div className="space-y-2">
      {entries.map(([bits, count]) => {
        const share = count / total;
        const theoretical = probabilities[bits];
        const isTop = highlight ? bits === highlight : false;

        return (
          <div key={bits} className="flex items-center gap-3">
            <span
              className={`w-24 shrink-0 font-mono text-xs ${
                isTop ? 'font-semibold text-emerald-300' : 'text-slate-400'
              }`}
            >
              {bits}
            </span>
            <div className="relative h-6 flex-1 overflow-hidden rounded bg-slate-800/60">
              <div
                className={`h-full rounded transition-all duration-500 ${
                  isTop ? 'bg-emerald-500/70' : 'bg-sky-500/50'
                }`}
                style={{ width: `${(share / maxShare) * 100}%` }}
              />
              {theoretical !== undefined && (
                <div
                  className="absolute top-0 h-full w-[2px] bg-amber-300/80"
                  style={{ left: `${(theoretical / maxShare) * 100}%` }}
                  title={`Teorik olasılık: ${formatPercent(theoretical)}`}
                />
              )}
            </div>
            <span className="w-28 shrink-0 text-right text-xs text-slate-400">
              {count} atış
              <span className="ml-1 text-slate-500">({(share * 100).toFixed(1)}%)</span>
            </span>
          </div>
        );
      })}

      <p className="pt-1 text-xs text-slate-500">
        Toplam {total} atış. Sarı dikey çizgi, gürültüsüz kuramsal olasılığı gösterir.
        Çubuk ile çizgi arasındaki fark, örneklem sayısının sınırlı olmasından ve varsa
        gürültüden kaynaklanır.
      </p>
    </div>
  );
}
