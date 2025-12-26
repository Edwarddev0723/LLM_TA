/**
 * API service for the AI Math Tutor frontend
 */

import type {
  Question,
  QuestionCriteria,
  QuestionListResponse,
  ValidateAnswerRequest,
  ValidateAnswerResponse,
  StartSessionRequest,
  StartSessionResponse,
  StudentInputRequest,
  TutorResponse,
  SessionState,
  EndSessionResponse,
  ErrorRecord,
  ErrorCriteria,
  ErrorListResponse,
  ErrorStatistics,
  MetricsResponse,
  HeatmapResponse,
  DashboardOverviewResponse,
  SessionDetailResponse,
} from '../types';

// Use relative URL for dev proxy, fallback to env variable for production
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

class ApiError extends Error {
  status: number;
  
  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      errorData.detail || `HTTP error ${response.status}`
    );
  }

  return response.json();
}

// Question API
export const questionApi = {
  async filterQuestions(criteria: QuestionCriteria): Promise<QuestionListResponse> {
    const params = new URLSearchParams();
    if (criteria.subject) params.append('subject', criteria.subject);
    if (criteria.unit) params.append('unit', criteria.unit);
    if (criteria.difficulty) params.append('difficulty', criteria.difficulty.toString());
    if (criteria.question_type) params.append('question_type', criteria.question_type);
    if (criteria.knowledge_nodes?.length) {
      params.append('knowledge_nodes', criteria.knowledge_nodes.join(','));
    }
    if (criteria.exclude_ids?.length) {
      params.append('exclude_ids', criteria.exclude_ids.join(','));
    }

    const queryString = params.toString();
    const endpoint = `/api/questions${queryString ? `?${queryString}` : ''}`;
    return fetchApi<QuestionListResponse>(endpoint);
  },

  async getQuestion(questionId: string): Promise<Question> {
    return fetchApi<Question>(`/api/questions/${questionId}`);
  },

  async validateAnswer(request: ValidateAnswerRequest): Promise<ValidateAnswerResponse> {
    return fetchApi<ValidateAnswerResponse>('/api/questions/validate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },
};

// Session API
export const sessionApi = {
  async startSession(request: StartSessionRequest): Promise<StartSessionResponse> {
    return fetchApi<StartSessionResponse>('/api/sessions', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  async processInput(
    sessionId: string,
    request: StudentInputRequest
  ): Promise<TutorResponse> {
    return fetchApi<TutorResponse>(`/api/sessions/${sessionId}/input`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  async getSessionState(sessionId: string): Promise<SessionState> {
    return fetchApi<SessionState>(`/api/sessions/${sessionId}`);
  },

  async endSession(sessionId: string): Promise<EndSessionResponse> {
    return fetchApi<EndSessionResponse>(`/api/sessions/${sessionId}/end`, {
      method: 'POST',
    });
  },
};

// Error Book API
export const errorApi = {
  async getErrors(
    studentId: string,
    criteria?: ErrorCriteria
  ): Promise<ErrorListResponse> {
    const params = new URLSearchParams();
    params.append('student_id', studentId);
    if (criteria?.error_type) params.append('error_type', criteria.error_type);
    if (criteria?.unit) params.append('unit', criteria.unit);
    if (criteria?.tags?.length) params.append('tags', criteria.tags.join(','));
    if (criteria?.repaired !== undefined) {
      params.append('repaired', criteria.repaired.toString());
    }
    if (criteria?.date_from) params.append('date_from', criteria.date_from);
    if (criteria?.date_to) params.append('date_to', criteria.date_to);

    return fetchApi<ErrorListResponse>(`/api/errors?${params.toString()}`);
  },

  async getError(errorId: string): Promise<ErrorRecord> {
    return fetchApi<ErrorRecord>(`/api/errors/${errorId}`);
  },

  async markAsRepaired(errorId: string): Promise<ErrorRecord> {
    return fetchApi<ErrorRecord>(`/api/errors/${errorId}/repair`, {
      method: 'POST',
    });
  },

  async getStatistics(studentId: string): Promise<ErrorStatistics> {
    return fetchApi<ErrorStatistics>(`/api/errors/statistics/${studentId}`);
  },
};

// Dashboard API
export const dashboardApi = {
  async getMetrics(studentId: string, limit: number = 10): Promise<MetricsResponse> {
    const params = new URLSearchParams();
    params.append('student_id', studentId);
    params.append('limit', limit.toString());
    return fetchApi<MetricsResponse>(`/api/dashboard/metrics?${params.toString()}`);
  },

  async getHeatmap(studentId: string, subject?: string): Promise<HeatmapResponse> {
    const params = new URLSearchParams();
    params.append('student_id', studentId);
    if (subject) params.append('subject', subject);
    return fetchApi<HeatmapResponse>(`/api/dashboard/heatmap?${params.toString()}`);
  },

  async getOverview(studentId: string): Promise<DashboardOverviewResponse> {
    const params = new URLSearchParams();
    params.append('student_id', studentId);
    return fetchApi<DashboardOverviewResponse>(`/api/dashboard/overview?${params.toString()}`);
  },

  async getSessionDetail(sessionId: string): Promise<SessionDetailResponse> {
    return fetchApi<SessionDetailResponse>(`/api/dashboard/session/${sessionId}`);
  },
};

export { ApiError };
