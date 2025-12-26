/**
 * Student Metrics Store
 * Manages real learning metrics data from backend API
 */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useStudentMetricsStore = defineStore('studentMetrics', () => {
  // State
  const isLoading = ref(false);
  const error = ref(null);
  const lastUpdated = ref(null);
  
  // Summary data
  const summary = ref(null);
  
  // Trends data
  const trends = ref(null);
  
  // Error analysis
  const errorAnalysis = ref(null);
  
  // Session history
  const recentSessions = ref([]);
  const sessionsPagination = ref({
    page: 1,
    pageSize: 10,
    totalCount: 0,
    hasMore: false
  });
  
  // Computed values for backward compatibility
  const weeklyStats = computed(() => {
    if (!trends.value) {
      return { avgWpm: [], avgAccuracy: [] };
    }
    return {
      avgWpm: trends.value.wpm_trend.map(d => d.value),
      avgAccuracy: trends.value.accuracy_trend.map(d => d.value)
    };
  });
  
  const avgWpmThisWeek = computed(() => {
    if (!summary.value) return 0;
    return Math.round(summary.value.avg_wpm.value);
  });
  
  const avgCorrectRate = computed(() => {
    if (!summary.value) return 0;
    return summary.value.accuracy_rate.value / 100;
  });
  
  const totalPracticeTime = computed(() => {
    if (!summary.value) return 0;
    return Math.round(summary.value.total_practice_time_minutes);
  });
  
  // API calls
  async function fetchSummary(studentId) {
    isLoading.value = true;
    error.value = null;
    
    try {
      const response = await fetch(`/api/student/metrics/summary?student_id=${studentId}`);
      
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || '無法載入指標摘要');
      }
      
      summary.value = await response.json();
      lastUpdated.value = new Date();
    } catch (err) {
      error.value = err.message;
      console.error('Fetch summary error:', err);
    } finally {
      isLoading.value = false;
    }
  }
  
  async function fetchTrends(studentId, period = 'week') {
    isLoading.value = true;
    error.value = null;
    
    try {
      const response = await fetch(
        `/api/student/metrics/trends?student_id=${studentId}&period=${period}`
      );
      
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || '無法載入趨勢數據');
      }
      
      trends.value = await response.json();
    } catch (err) {
      error.value = err.message;
      console.error('Fetch trends error:', err);
    } finally {
      isLoading.value = false;
    }
  }
  
  async function fetchErrorAnalysis(studentId) {
    isLoading.value = true;
    error.value = null;
    
    try {
      const response = await fetch(
        `/api/student/metrics/errors?student_id=${studentId}`
      );
      
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || '無法載入錯題分析');
      }
      
      errorAnalysis.value = await response.json();
    } catch (err) {
      error.value = err.message;
      console.error('Fetch error analysis error:', err);
    } finally {
      isLoading.value = false;
    }
  }
  
  async function fetchSessions(studentId, page = 1, pageSize = 10) {
    isLoading.value = true;
    error.value = null;
    
    try {
      const response = await fetch(
        `/api/student/metrics/sessions?student_id=${studentId}&page=${page}&page_size=${pageSize}`
      );
      
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || '無法載入學習紀錄');
      }
      
      const data = await response.json();
      
      // Transform to match existing format
      recentSessions.value = data.sessions.map(s => ({
        id: s.session_id,
        date: s.date,
        unit: s.unit,
        subject: s.subject,
        mode: s.mode,
        correctRate: s.correct_rate,
        durationMin: s.duration_minutes,
        wpm: s.wpm,
        pauseRatio: s.pause_ratio,
        hintUsed: s.hint_used,
        questionsCount: s.questions_count,
        mistakesCount: s.mistakes_count
      }));
      
      sessionsPagination.value = {
        page: data.page,
        pageSize: data.page_size,
        totalCount: data.total_count,
        hasMore: data.has_more
      };
    } catch (err) {
      error.value = err.message;
      console.error('Fetch sessions error:', err);
    } finally {
      isLoading.value = false;
    }
  }
  
  async function fetchAllData(studentId) {
    await Promise.all([
      fetchSummary(studentId),
      fetchTrends(studentId, 'week'),
      fetchErrorAnalysis(studentId),
      fetchSessions(studentId)
    ]);
  }
  
  function reset() {
    summary.value = null;
    trends.value = null;
    errorAnalysis.value = null;
    recentSessions.value = [];
    error.value = null;
    lastUpdated.value = null;
  }
  
  return {
    // State
    isLoading,
    error,
    lastUpdated,
    summary,
    trends,
    errorAnalysis,
    recentSessions,
    sessionsPagination,
    
    // Computed (backward compatibility)
    weeklyStats,
    avgWpmThisWeek,
    avgCorrectRate,
    totalPracticeTime,
    
    // Actions
    fetchSummary,
    fetchTrends,
    fetchErrorAnalysis,
    fetchSessions,
    fetchAllData,
    reset
  };
});
