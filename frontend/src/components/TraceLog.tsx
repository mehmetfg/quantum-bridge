/**
 * Aşama anlatımı: her adımda ne yapıldı ve neden yapıldı.
 *
 * Bu bileşen projenin eğitim tarafının kalbidir. Sonuç kadar, sonuca
 * nasıl varıldığı da gösterilir.
 */

import { SIDE_STYLES, cx, formatDuration } from '../lib/style';
import type { TraceEvent } from '../types';

export default function TraceLog({
  events,
  onSelect,
  selected,
}: {
  events: TraceEvent[];
  onSelect?: (stage: TraceEvent['stage']) => void;
  selected?: string | null;
}) {
  if (!events.length) {
    return (
      <p className="text-sm text-slate-500">
        Henüz aşama kaydı yok. İş başlatıldığında adımlar buraya sırayla düşecek.
      </p>
    );
  }

  return (
    <ol className="space-y-3">
      {events.map((event, index) => {
        const style = SIDE_STYLES[event.side];
        const isError = event.status === 'error';

        return (
          <li
            key={`${event.stage}-${index}`}
            className={cx(
              'animate-slideIn rounded-lg border p-4',
              isError ? 'border-rose-500/50 bg-rose-500/5' : 'border-slate-800 bg-slate-900/40',
              selected === event.stage && 'ring-2 ring-sky-500/50',
              onSelect && 'cursor-pointer hover:border-slate-700',
            )}
            onClick={() => onSelect?.(event.stage)}
          >
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <span className={cx('h-2 w-2 rounded-full', isError ? 'bg-rose-400' : style.dot)} />
              <h4 className="text-sm font-semibold text-slate-100">
                {index + 1}. {event.title}
              </h4>
              <span className={cx('chip', style.bg, style.text)}>{event.side}</span>
              <span className="ml-auto text-xs text-slate-500">
                {formatDuration(event.duration_ms)}
              </span>
            </div>

            <p className="mb-2 text-sm text-slate-300">{event.summary}</p>

            {event.details.length > 0 && (
              <ul className="mb-3 space-y-1.5">
                {event.details.map((detail, i) => (
                  <li key={i} className="flex gap-2 text-xs leading-relaxed text-slate-400">
                    <span className="mt-[7px] h-1 w-1 shrink-0 rounded-full bg-slate-600" />
                    <span>{detail}</span>
                  </li>
                ))}
              </ul>
            )}

            {event.why && (
              <div className="rounded border-l-2 border-slate-700 bg-slate-950/50 py-2 pl-3 pr-2">
                <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                  Bu adım neden var
                </p>
                <p className="mt-1 text-xs leading-relaxed text-slate-400">{event.why}</p>
              </div>
            )}
          </li>
        );
      })}
    </ol>
  );
}
