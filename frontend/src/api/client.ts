/**
 * Arka uç ile konuşan tek yer.
 *
 * Tüm istekler buradan geçer. Giriş özelliği eklendiğinde jetonu isteklere
 * eklemek için değiştirilmesi gereken tek dosya budur.
 */

import type {
  AuthStatus,
  BackendInfo,
  Job,
  JobRequest,
  JobSummary,
  ProblemInfo,
  StageInfo,
  TraceEvent,
} from '../types';

const BASE = '/api';

/** İleride giriş eklenince jeton buraya yazılacak. */
let authToken: string | null = null;

export function setAuthToken(token: string | null): void {
  authToken = token;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) ?? {}),
  };
  if (authToken) {
    headers.Authorization = `Bearer ${authToken}`;
  }

  const response = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!response.ok) {
    let message = `İstek başarısız oldu (${response.status})`;
    try {
      const body = await response.json();
      if (body?.detail) message = String(body.detail);
    } catch {
      // Gövde okunamadıysa varsayılan mesaj kalır.
    }
    throw new Error(message);
  }
  return (await response.json()) as T;
}

export const api = {
  health: () => request<{ status: string; version: string }>('/health'),
  authStatus: () => request<AuthStatus>('/auth/status'),
  stages: () => request<StageInfo[]>('/stages'),
  backends: () => request<{ default: string; backends: BackendInfo[] }>('/backends'),
  problems: () => request<ProblemInfo[]>('/problems'),
  problem: (id: string) => request<ProblemInfo>(`/problems/${id}`),
  jobs: (limit = 20) => request<JobSummary[]>(`/jobs?limit=${limit}`),
  job: (id: string) => request<Job>(`/jobs/${id}`),

  /** İşi arka planda başlatır; aşamalar olay akışından izlenir. */
  startJob: (payload: JobRequest) =>
    request<Job>('/jobs?stream=true', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  /** İşi baştan sona çalıştırır ve bitmiş sonucu döndürür. */
  runJob: (payload: JobRequest) =>
    request<Job>('/jobs', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};

export interface JobStreamHandlers {
  onStage: (event: TraceEvent) => void;
  onDone: (job: Job) => void;
  onError: (message: string) => void;
}

/**
 * İşin aşamalarını canlı dinler (Server-Sent Events).
 *
 * Arka uç, geç bağlanan istemciye kaçırdığı aşamaları baştan gönderir,
 * bu yüzden bağlantı zamanlaması önemli değildir.
 *
 * Geriye, dinlemeyi durduran bir fonksiyon döner.
 */
export function streamJob(jobId: string, handlers: JobStreamHandlers): () => void {
  const source = new EventSource(`${BASE}/jobs/${jobId}/events`);
  let closed = false;

  const close = () => {
    if (!closed) {
      closed = true;
      source.close();
    }
  };

  source.onmessage = (message) => {
    try {
      const payload = JSON.parse(message.data);
      if (payload.type === 'stage') {
        handlers.onStage(payload.event as TraceEvent);
      } else if (payload.type === 'done') {
        handlers.onDone(payload.job as Job);
        close();
      }
    } catch {
      handlers.onError('Gelen olay çözümlenemedi.');
    }
  };

  source.onerror = () => {
    if (!closed) {
      handlers.onError('Canlı bağlantı koptu. Sonucu yenileyerek görebilirsiniz.');
      close();
    }
  };

  return close;
}
