/**
 * Altı aşamalı ilerleme çubuğu.
 *
 * Projenin ana fikri burada görünür: altı adımdan yalnızca biri kuantum
 * tarafındadır. Renkler bunu her ekranda hatırlatır.
 */

import { SIDE_STYLES, STAGE_ICONS, cx } from '../lib/style';
import type { StageInfo, StageName, TraceEvent } from '../types';

interface Props {
  stages: StageInfo[];
  events: TraceEvent[];
  activeStage?: StageName | null;
  onSelect?: (stage: StageName) => void;
  selected?: StageName | null;
}

export default function PipelineStepper({
  stages,
  events,
  activeStage = null,
  onSelect,
  selected = null,
}: Props) {
  const byStage = new Map(events.map((event) => [event.stage, event]));

  return (
    <div className="flex flex-wrap items-stretch gap-2">
      {stages.map((stage, index) => {
        const event = byStage.get(stage.stage);
        const isDone = Boolean(event) && event!.status === 'ok';
        const isError = Boolean(event) && event!.status === 'error';
        const isActive = activeStage === stage.stage && !event;
        const isSelected = selected === stage.stage;
        const style = SIDE_STYLES[stage.side];

        return (
          <div key={stage.stage} className="flex flex-1 items-stretch gap-2">
            <button
              type="button"
              disabled={!event || !onSelect}
              onClick={() => event && onSelect?.(stage.stage)}
              className={cx(
                'relative flex min-w-[140px] flex-1 flex-col gap-1 rounded-lg border p-3 text-left transition',
                isError
                  ? 'border-rose-500/50 bg-rose-500/10'
                  : isDone
                    ? `${style.border} ${style.bg}`
                    : 'border-slate-800 bg-slate-900/40',
                isSelected && 'ring-2 ring-sky-500/60',
                event && onSelect && 'cursor-pointer hover:brightness-125',
              )}
            >
              <div className="flex items-center gap-2">
                <span
                  className={cx(
                    'flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold',
                    isError
                      ? 'bg-rose-500 text-white'
                      : isDone
                        ? `${style.dot} text-slate-950`
                        : 'bg-slate-700 text-slate-300',
                  )}
                >
                  {isError ? '!' : STAGE_ICONS[stage.stage]}
                </span>
                <span
                  className={cx(
                    'text-xs font-semibold leading-tight',
                    isDone || isError ? 'text-slate-100' : 'text-slate-400',
                  )}
                >
                  {stage.title}
                </span>
                {isActive && (
                  <span className="relative ml-auto flex h-2 w-2">
                    <span className="absolute inline-flex h-full w-full animate-pulseRing rounded-full bg-amber-400" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-400" />
                  </span>
                )}
              </div>
              <span className={cx('text-[10px] font-medium uppercase tracking-wide', style.text)}>
                {stage.side}
              </span>
              {event && (
                <span className="text-[10px] text-slate-500">
                  {event.duration_ms < 1
                    ? 'bir milisaniyeden az'
                    : `${event.duration_ms.toFixed(0)} ms`}
                </span>
              )}
            </button>

            {index < stages.length - 1 && (
              <div className="flex items-center text-slate-700" aria-hidden>
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                  <path
                    d="M2 1 L7 5 L2 9"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
