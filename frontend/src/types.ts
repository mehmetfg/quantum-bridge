/**
 * Arka uçtan gelen veri biçimleri.
 * Bu tanımlar backend/app/core/models.py dosyasının aynadaki karşılığıdır.
 */

export type StageName =
  | 'INTAKE'
  | 'AI_ROUTING'
  | 'ENCODE_OPTIMIZE'
  | 'QUANTUM_EXEC'
  | 'DECODE'
  | 'CLASSICAL_MERGE';

export type Side = 'klasik' | 'yapay zeka' | 'kuantum';

export type JobStatus = 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED';

export interface StageInfo {
  stage: StageName;
  order: number;
  title: string;
  side: Side;
  summary: string;
  why: string;
}

export interface TraceEvent {
  stage: StageName;
  title: string;
  side: Side;
  summary: string;
  why: string;
  details: string[];
  data: Record<string, unknown>;
  duration_ms: number;
  timestamp: string;
  status: 'ok' | 'error';
}

export interface SchemaField {
  type: 'integer' | 'select' | 'bitstring' | 'string_list' | 'select_from_items';
  label: string;
  help?: string;
  min?: number;
  max?: number;
  default?: unknown;
  optional?: boolean;
  max_length?: number;
  min_items?: number;
  max_items?: number;
  options?: { value: string; label: string }[];
}

export interface ProblemInfo {
  id: string;
  title: string;
  category: string;
  short_description: string;
  description: string;
  quantum_advantage: string;
  classical_comparison: string;
  difficulty: string;
  default_input: Record<string, unknown>;
  input_schema: Record<string, SchemaField>;
  concepts: string[];
}

export interface RoutingDecision {
  use_quantum: boolean;
  n_qubits: number;
  shots: number;
  encoding: string;
  strategy: string;
  confidence_target: number;
  reasoning: string[];
  rejected_alternatives: string[];
  cost_estimate: Record<string, unknown>;
  source: string;
}

export interface Operation {
  name: string;
  qubits: number[];
  params: number[];
  label: string | null;
  description: string;
}

export interface CircuitData {
  name: string;
  n_qubits: number;
  operations: Operation[];
  measured_qubits: number[];
  metrics: {
    gate_count: number;
    two_qubit_gate_count: number;
    depth: number;
  };
}

export interface RawResultData {
  counts: Record<string, number>;
  shots: number;
  backend_name: string;
  probabilities: Record<string, number>;
  statevector: { re: number; im: number }[] | null;
  snapshots: {
    step: number;
    after_gate: string;
    qubits: number[];
    probabilities: Record<string, number>;
    note: string;
  }[];
  meta: Record<string, any>;
}

export interface FinalResult {
  answer: unknown;
  answer_label: string;
  confidence: number;
  verified: boolean | null;
  verification_note: string;
  classical_usage: string;
  details: Record<string, any>;
}

export interface JobRequest {
  problem_id: string;
  input: Record<string, unknown>;
  shots?: number | null;
  backend_id?: string | null;
  noise_level: 'ideal' | 'low' | 'medium' | 'high';
  seed?: number | null;
  stage_delay_ms?: number;
}

export interface Job {
  id: string;
  problem_id: string;
  problem_title: string;
  status: JobStatus;
  owner_id: string;
  request: JobRequest;
  created_at: string;
  completed_at: string | null;
  current_stage: StageName | null;
  events: TraceEvent[];
  routing: RoutingDecision | null;
  circuit: CircuitData | null;
  qasm: string | null;
  raw_result: RawResultData | null;
  result: FinalResult | null;
  error: string | null;
  total_duration_ms: number;
}

export interface JobSummary {
  id: string;
  problem_id: string;
  problem_title: string;
  status: JobStatus;
  created_at: string;
  answer_label: string | null;
  confidence: number | null;
  total_duration_ms: number;
}

export interface BackendInfo {
  id: string;
  name: string;
  kind: 'simulator' | 'hardware';
  max_qubits: number;
  available: boolean;
  description: string;
  supports_statevector: boolean;
  supports_noise: boolean;
  notes: string[];
}

export interface AuthStatus {
  mode: string;
  login_required: boolean;
  user: { id: string; display_name: string; is_demo: boolean };
  note: string;
}
