/**
 * Arayüz genelinde tutarlı renk ve etiket kuralları.
 *
 * Boru hattının üç tarafı her ekranda aynı renkle gösterilir. Bu, hangi
 * adımın nerede çalıştığını tek bakışta anlatmanın en ucuz yoludur.
 */

import type { JobStatus, Side, StageName } from '../types';

export const SIDE_STYLES: Record<Side, { text: string; bg: string; border: string; dot: string }> = {
  klasik: {
    text: 'text-sky-300',
    bg: 'bg-sky-500/10',
    border: 'border-sky-500/40',
    dot: 'bg-sky-400',
  },
  'yapay zeka': {
    text: 'text-violet-300',
    bg: 'bg-violet-500/10',
    border: 'border-violet-500/40',
    dot: 'bg-violet-400',
  },
  kuantum: {
    text: 'text-emerald-300',
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/40',
    dot: 'bg-emerald-400',
  },
};

export const STAGE_ICONS: Record<StageName, string> = {
  INTAKE: '1',
  AI_ROUTING: '2',
  ENCODE_OPTIMIZE: '3',
  QUANTUM_EXEC: '4',
  DECODE: '5',
  CLASSICAL_MERGE: '6',
};

export const STATUS_LABELS: Record<JobStatus, string> = {
  QUEUED: 'Sırada',
  RUNNING: 'Çalışıyor',
  COMPLETED: 'Tamamlandı',
  FAILED: 'Başarısız',
};

export const STATUS_STYLES: Record<JobStatus, string> = {
  QUEUED: 'bg-slate-700/50 text-slate-300',
  RUNNING: 'bg-amber-500/15 text-amber-300',
  COMPLETED: 'bg-emerald-500/15 text-emerald-300',
  FAILED: 'bg-rose-500/15 text-rose-300',
};

export const DIFFICULTY_STYLES: Record<string, string> = {
  başlangıç: 'bg-emerald-500/15 text-emerald-300',
  orta: 'bg-amber-500/15 text-amber-300',
  ileri: 'bg-rose-500/15 text-rose-300',
};

/** Güven skorunu renge çevirir. */
export function confidenceStyle(value: number): string {
  if (value >= 0.9) return 'text-emerald-300';
  if (value >= 0.6) return 'text-amber-300';
  return 'text-rose-300';
}

export function formatPercent(value: number, digits = 1): string {
  return `yüzde ${(value * 100).toFixed(digits)}`;
}

export function formatDuration(ms: number): string {
  if (ms < 1) return 'bir milisaniyeden az';
  if (ms < 1000) return `${ms.toFixed(0)} ms`;
  return `${(ms / 1000).toFixed(2)} saniye`;
}

export function formatDateTime(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleString('tr-TR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function cx(...values: (string | false | null | undefined)[]): string {
  return values.filter(Boolean).join(' ');
}
