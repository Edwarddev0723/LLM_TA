/**
 * Type definitions for the AI Math Tutor frontend
 */

// Question types
export interface Question {
  id: string;
  content: string;
  type: QuestionType;
  subject: string;
  unit: string;
  difficulty: DifficultyLevel;
  standard_solution?: string;
  knowledge_nodes: string[];
  hints: HintContent[];
  misconceptions: Misconception[];
}

export type QuestionType = 'MULTIPLE_CHOICE' | 'FILL_BLANK' | 'CALCULATION' | 'PROOF';

export type DifficultyLevel = 1 | 2 | 3;

export interface HintContent {
  level: HintLevel;
  content: string;
}

export type HintLevel = 1 | 2 | 3;

export interface Misconception {
  id: string;
  description: string;
  error_type: ErrorType;
}

export type ErrorType = 'CALCULATION' | 'CONCEPT' | 'CARELESS';

export interface QuestionCriteria {
  subject?: string;
  unit?: string;
  difficulty?: DifficultyLevel;
  question_type?: QuestionType;
  knowledge_nodes?: string[];
  exclude_ids?: string[];
}

export interface QuestionListResponse {
  questions: Question[];
  total: number;
}

export interface ValidateAnswerRequest {
  question_id: string;
  answer: string;
}

export interface ValidateAnswerResponse {
  is_correct: boolean;
  correct_answer: string;
  student_answer: string;
  feedback?: string;
  response_time_ms?: number;
}

// Session types
export type FSMState = 
  | 'IDLE'
  | 'LISTENING'
  | 'ANALYZING'
  | 'PROBING'
  | 'HINTING'
  | 'REPAIR'
  | 'CONSOLIDATING';

export type ResponseType = 
  | 'PROBE'
  | 'HINT'
  | 'REPAIR'
  | 'CONSOLIDATE'
  | 'ACKNOWLEDGE';

export interface StartSessionRequest {
  question_id: string;
  student_id: string;
}

export interface StartSessionResponse {
  session_id: string;
  question_id: string;
  student_id: string;
  question_content: string;
  fsm_state: FSMState;
  message: string;
}

export interface StudentInputRequest {
  text: string;
  audio_duration?: number;
  word_count?: number;
  pause_count?: number;
  total_pause_duration?: number;
}

export interface TutorResponse {
  text: string;
  response_type: ResponseType;
  hint_level?: HintLevel;
  related_concepts: string[];
  suggested_next_step?: string;
  fsm_state: FSMState;
}

export interface SessionState {
  session_id: string;
  question_id: string;
  student_id: string;
  fsm_state: FSMState;
  concept_coverage: number;
  hints_used: number;
  turn_count: number;
  is_active: boolean;
}

export interface EndSessionResponse {
  session_id: string;
  duration: number;
  concepts_covered: string[];
  concept_coverage: number;
  hints_used: { timestamp: number; level: HintLevel; concept: string }[];
  total_turns: number;
  final_state: FSMState;
}

// Error Book types
export interface ErrorRecord {
  id: string;
  student_id: string;
  question_id: string;
  student_answer: string;
  correct_answer: string;
  error_type: ErrorType;
  error_tags: string[];
  timestamp: string;
  repaired: boolean;
  repaired_at?: string;
}

export interface ErrorListResponse {
  errors: ErrorRecord[];
  total: number;
}

export interface ErrorCriteria {
  error_type?: ErrorType;
  unit?: string;
  tags?: string[];
  repaired?: boolean;
  date_from?: string;
  date_to?: string;
}

export interface ErrorStatistics {
  total_errors: number;
  repaired_count: number;
  errors_by_type: Record<string, number>;
  errors_by_unit: Record<string, number>;
  most_frequent_misconceptions: string[];
}

// Dashboard types
export interface MetricsDataPoint {
  session_id: string;
  timestamp: string;
  wpm: number;
  pause_rate: number;
  hint_dependency: number;
  concept_coverage: number;
  focus_duration: number;
}

export interface MetricsResponse {
  student_id: string;
  metrics_history: MetricsDataPoint[];
  average_wpm: number;
  average_pause_rate: number;
  average_hint_dependency: number;
  average_concept_coverage: number;
  total_sessions: number;
  total_focus_duration: number;
}

export interface KnowledgeNodeMastery {
  node_id: string;
  node_name: string;
  subject: string;
  unit: string;
  mastery_level: 'red' | 'yellow' | 'green';
  mastery_score: number;
  error_count: number;
  total_attempts: number;
  concept_coverage: number;
}

export interface HeatmapResponse {
  student_id: string;
  nodes: KnowledgeNodeMastery[];
  weak_areas: string[];
  strong_areas: string[];
}

export interface SessionSummary {
  session_id: string;
  question_id: string;
  start_time: string;
  end_time?: string;
  concept_coverage: number;
  final_state?: string;
}

export interface DashboardOverviewResponse {
  student_id: string;
  total_sessions: number;
  completed_sessions: number;
  average_coverage: number;
  total_duration_minutes: number;
  recent_sessions: SessionSummary[];
  error_statistics: ErrorStatistics;
}

export interface PauseRecord {
  start_time: number;
  end_time: number;
  duration: number;
}

export interface SessionDetailResponse {
  session_id: string;
  question_id: string;
  student_id: string;
  start_time: string;
  end_time?: string;
  final_state?: string;
  concept_coverage: number;
  wpm?: number;
  pause_rate?: number;
  hint_dependency?: number;
  focus_duration?: number;
  pauses: PauseRecord[];
  total_pause_duration: number;
  hint_count: number;
}
