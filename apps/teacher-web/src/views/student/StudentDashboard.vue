<template>
  <div class="student-dashboard">
    <header class="dashboard-header">
      <div>
        <h1>學生儀表板</h1>
        <p v-if="lastUpdated">最後更新：{{ formatDateTime(lastUpdated) }}</p>
        <p v-else>載入中...</p>
      </div>
      <button class="refresh-btn" @click="refreshData" :disabled="isLoading">
        {{ isLoading ? '更新中...' : '🔄 重新整理' }}
      </button>
    </header>

    <!-- Error Alert -->
    <div v-if="apiError" class="error-alert" @click="apiError = null">
      ⚠️ {{ apiError }}
      <span class="close-btn">×</span>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading && !summary" class="loading-state">
      <div class="spinner"></div>
      <p>載入數據中...</p>
    </div>

    <!-- Main Content -->
    <div v-else class="dashboard-content">
      <!-- KPI Cards Row -->
      <section class="kpi-section">
        <h2>📊 核心指標</h2>
        <div class="kpi-grid">
          <!-- 正確率 -->
          <div class="kpi-card" :class="getKPIClass(summary?.accuracy_rate)">
            <div class="kpi-header">
              <span class="kpi-icon">🎯</span>
              <span class="kpi-title">正確率</span>
              <span 
                v-if="summary?.accuracy_rate?.trend_direction" 
                class="kpi-trend"
                :class="summary.accuracy_rate.trend_direction"
              >
                {{ getTrendIcon(summary.accuracy_rate.trend_direction) }}
                {{ Math.abs(summary.accuracy_rate.trend || 0) }}%
              </span>
            </div>
            <div class="kpi-value">
              <template v-if="summary?.accuracy_rate?.confidence?.is_sufficient">
                {{ summary.accuracy_rate.value }}
                <span class="kpi-unit">{{ summary.accuracy_rate.unit }}</span>
              </template>
              <template v-else>
                <span class="no-data">{{ summary?.accuracy_rate?.confidence?.message || '尚無數據' }}</span>
              </template>
            </div>
            <div class="kpi-footer" v-if="summary?.accuracy_rate?.confidence">
              <span class="sample-info">
                樣本數: {{ summary.accuracy_rate.confidence.sample_count }}
              </span>
            </div>
          </div>

          <!-- 平均語速 -->
          <div class="kpi-card" :class="getKPIClass(summary?.avg_wpm)">
            <div class="kpi-header">
              <span class="kpi-icon">🗣️</span>
              <span class="kpi-title">平均語速</span>
              <span 
                v-if="summary?.avg_wpm?.trend_direction" 
                class="kpi-trend"
                :class="summary.avg_wpm.trend_direction"
              >
                {{ getTrendIcon(summary.avg_wpm.trend_direction) }}
                {{ Math.abs(summary.avg_wpm.trend || 0) }}%
              </span>
            </div>
            <div class="kpi-value">
              <template v-if="summary?.avg_wpm?.confidence?.is_sufficient">
                {{ summary.avg_wpm.value }}
                <span class="kpi-unit">{{ summary.avg_wpm.unit }}</span>
              </template>
              <template v-else>
                <span class="no-data">{{ summary?.avg_wpm?.confidence?.message || '尚無數據' }}</span>
              </template>
            </div>
            <div class="kpi-footer" v-if="summary?.avg_wpm?.confidence">
              <span class="sample-info">
                樣本數: {{ summary.avg_wpm.confidence.sample_count }}
              </span>
            </div>
          </div>

          <!-- 錯題復發率 -->
          <div class="kpi-card warning" :class="getKPIClass(summary?.error_recurrence_rate, true)">
            <div class="kpi-header">
              <span class="kpi-icon">🔄</span>
              <span class="kpi-title">錯題復發率</span>
            </div>
            <div class="kpi-value">
              <template v-if="summary?.error_recurrence_rate?.confidence?.is_sufficient">
                {{ summary.error_recurrence_rate.value }}
                <span class="kpi-unit">{{ summary.error_recurrence_rate.unit }}</span>
              </template>
              <template v-else>
                <span class="no-data">{{ summary?.error_recurrence_rate?.confidence?.message || '尚無數據' }}</span>
              </template>
            </div>
            <div class="kpi-footer" v-if="summary?.error_recurrence_rate?.confidence">
              <span class="sample-info">
                錯題數: {{ summary.error_recurrence_rate.confidence.sample_count }}
              </span>
            </div>
          </div>

          <!-- 今日專注時長 -->
          <div class="kpi-card">
            <div class="kpi-header">
              <span class="kpi-icon">⏱️</span>
              <span class="kpi-title">今日專注時長</span>
            </div>
            <div class="kpi-value">
              <template v-if="summary?.focus_duration_today">
                {{ summary.focus_duration_today.value }}
                <span class="kpi-unit">{{ summary.focus_duration_today.unit }}</span>
              </template>
              <template v-else>
                <span class="no-data">尚無數據</span>
              </template>
            </div>
            <div class="kpi-footer">
              <span class="sample-info">
                今日練習: {{ summary?.focus_duration_today?.confidence?.sample_count || 0 }} 次
              </span>
            </div>
          </div>
        </div>
      </section>

      <!-- Secondary Stats -->
      <section class="stats-section">
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-value">{{ summary?.total_sessions || 0 }}</div>
            <div class="stat-label">總練習次數</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ summary?.total_practice_time_minutes || 0 }}</div>
            <div class="stat-label">總學習時長 (分)</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ summary?.streak_days || 0 }}</div>
            <div class="stat-label">連續學習天數</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ summary?.hint_dependency?.value || 0 }}%</div>
            <div class="stat-label">提示依賴度</div>
          </div>
        </div>
      </section>

      <!-- Charts Section -->
      <section class="charts-section">
        <div class="chart-row">
          <!-- Accuracy Trend Chart -->
          <div class="chart-card">
            <div class="chart-header">
              <h3>📈 正確率趨勢</h3>
              <div class="period-selector">
                <button 
                  v-for="p in ['week', 'month']" 
                  :key="p"
                  :class="{ active: trendPeriod === p }"
                  @click="changePeriod(p)"
                >
                  {{ p === 'week' ? '本週' : '本月' }}
                </button>
              </div>
            </div>
            <div class="chart-body">
              <template v-if="trends?.accuracy_trend?.length > 0">
                <div class="line-chart">
                  <div class="chart-y-axis">
                    <span>100%</span>
                    <span>50%</span>
                    <span>0%</span>
                  </div>
                  <div class="chart-area">
                    <svg viewBox="0 0 100 50" preserveAspectRatio="none">
                      <polyline
                        :points="getLineChartPoints(trends.accuracy_trend, 100)"
                        fill="none"
                        stroke="#3b82f6"
                        stroke-width="2"
                      />
                      <g v-for="(point, idx) in trends.accuracy_trend" :key="idx">
                        <circle
                          :cx="getPointX(idx, trends.accuracy_trend.length)"
                          :cy="50 - (point.value / 100) * 50"
                          r="3"
                          fill="#3b82f6"
                          class="data-point"
                          @mouseenter="showTooltip($event, point)"
                          @mouseleave="hideTooltip"
                        />
                      </g>
                    </svg>
                    <div class="chart-x-axis">
                      <span v-for="(point, idx) in trends.accuracy_trend" :key="idx">
                        {{ formatDateShort(point.date) }}
                      </span>
                    </div>
                  </div>
                </div>
              </template>
              <template v-else>
                <div class="no-chart-data">
                  <span>📊</span>
                  <p>尚無足夠數據繪製圖表</p>
                </div>
              </template>
            </div>
          </div>

          <!-- WPM Trend Chart -->
          <div class="chart-card">
            <div class="chart-header">
              <h3>🗣️ 語速趨勢</h3>
            </div>
            <div class="chart-body">
              <template v-if="trends?.wpm_trend?.length > 0">
                <div class="bar-chart">
                  <div class="bars-container">
                    <div 
                      v-for="(point, idx) in trends.wpm_trend" 
                      :key="idx"
                      class="bar-item"
                      @mouseenter="showTooltip($event, point, 'WPM')"
                      @mouseleave="hideTooltip"
                    >
                      <div 
                        class="bar" 
                        :style="{ height: `${(point.value / 150) * 100}%` }"
                      ></div>
                      <span class="bar-label">{{ formatDateShort(point.date) }}</span>
                    </div>
                  </div>
                </div>
              </template>
              <template v-else>
                <div class="no-chart-data">
                  <span>📊</span>
                  <p>尚無足夠數據繪製圖表</p>
                </div>
              </template>
            </div>
          </div>
        </div>

        <!-- Error Analysis -->
        <div class="chart-card full-width">
          <div class="chart-header">
            <h3>🔴 錯題分析</h3>
          </div>
          <div class="chart-body">
            <template v-if="errorAnalysis && errorAnalysis.total_errors > 0">
              <div class="error-stats">
                <div class="error-stat">
                  <span class="error-stat-value">{{ errorAnalysis.total_errors }}</span>
                  <span class="error-stat-label">總錯題數</span>
                </div>
                <div class="error-stat">
                  <span class="error-stat-value">{{ errorAnalysis.repaired_errors }}</span>
                  <span class="error-stat-label">已修正</span>
                </div>
                <div class="error-stat">
                  <span class="error-stat-value">{{ (errorAnalysis.repair_rate * 100).toFixed(0) }}%</span>
                  <span class="error-stat-label">修正率</span>
                </div>
              </div>
              <div class="error-breakdown" v-if="errorAnalysis.errors_by_unit">
                <h4>各單元錯題分布</h4>
                <div class="unit-bars">
                  <div 
                    v-for="(count, unit) in errorAnalysis.errors_by_unit" 
                    :key="unit"
                    class="unit-bar-item"
                  >
                    <span class="unit-name">{{ unit }}</span>
                    <div class="unit-bar-bg">
                      <div 
                        class="unit-bar-fill" 
                        :style="{ width: `${(count / errorAnalysis.total_errors) * 100}%` }"
                      ></div>
                    </div>
                    <span class="unit-count">{{ count }}</span>
                  </div>
                </div>
              </div>
            </template>
            <template v-else>
              <div class="no-chart-data success">
                <span>✅</span>
                <p>太棒了！目前沒有錯題記錄</p>
              </div>
            </template>
          </div>
        </div>
      </section>

      <!-- Recent Sessions Table -->
      <section class="sessions-section">
        <div class="section-header">
          <h2>📝 近期學習紀錄</h2>
          <div class="confidence-badge" v-if="trends?.confidence">
            {{ trends.confidence.message }}
          </div>
        </div>
        <div class="table-wrapper">
          <table class="sessions-table" v-if="recentSessions.length > 0">
            <thead>
              <tr>
                <th>日期</th>
                <th>單元</th>
                <th>模式</th>
                <th>正確率</th>
                <th>時長</th>
                <th>詳細</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="session in recentSessions" :key="session.id">
                <td>{{ formatDate(session.date) }}</td>
                <td>
                  <div class="unit-cell">
                    <strong>{{ session.unit }}</strong>
                    <small>{{ session.subject }}</small>
                  </div>
                </td>
                <td>
                  <span class="mode-badge" :class="getModeClass(session.mode)">
                    {{ session.mode }}
                  </span>
                </td>
                <td>
                  <span class="rate-badge" :class="getRateClass(session.correctRate)">
                    {{ (session.correctRate * 100).toFixed(0) }}%
                  </span>
                </td>
                <td>{{ session.durationMin }} 分</td>
                <td>
                  <div class="session-details">
                    <span v-if="session.wpm" class="detail-tag">WPM: {{ session.wpm }}</span>
                    <span v-if="session.hintUsed" class="detail-tag">提示: {{ session.hintUsed }}</span>
                    <span v-if="session.mistakesCount" class="detail-tag warning">錯: {{ session.mistakesCount }}</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else class="no-sessions">
            <p>尚無學習紀錄，開始你的第一次練習吧！</p>
          </div>
        </div>
      </section>
    </div>

    <!-- Tooltip -->
    <div 
      v-if="tooltip.visible" 
      class="chart-tooltip"
      :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
    >
      <div class="tooltip-date">{{ tooltip.date }}</div>
      <div class="tooltip-value">{{ tooltip.value }} {{ tooltip.unit }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useStudentMetricsStore } from '@/stores/studentMetrics';
import { useSessionStore } from '@/stores/session';

const metricsStore = useStudentMetricsStore();
const sessionStore = useSessionStore();

// Use computed to access store state reactively
const isLoading = computed(() => metricsStore.isLoading);
const storeError = computed(() => metricsStore.error);
const lastUpdated = computed(() => metricsStore.lastUpdated);
const summary = computed(() => metricsStore.summary);
const trends = computed(() => metricsStore.trends);
const errorAnalysis = computed(() => metricsStore.errorAnalysis);
const recentSessions = computed(() => metricsStore.recentSessions);

const apiError = ref(null);
const trendPeriod = ref('week');
const tooltip = ref({
  visible: false,
  x: 0,
  y: 0,
  date: '',
  value: '',
  unit: ''
});

// Get student ID from session or use default
// For demo purposes, map logged-in student email to student-001
const studentId = computed(() => {
  // TEMPORARY: Force use student-001 for testing
  return 'student-001';
  
  const user = sessionStore.user;
  console.log('Computing studentId, user:', user);
  
  if (user) {
    // If user logged in via Login.vue, map to student-001 for demo data
    if (user.email === 'student@test.com' || user.id === 'student-001') {
      console.log('Mapping to student-001 (test account)');
      return 'student-001';
    }
    // For other students, use their ID
    console.log('Using user ID:', user.id);
    return user.id?.toString() || 'student-001';
  }
  console.log('No user, defaulting to student-001');
  return 'student-001';
});

// Watch for store errors
watch(storeError, (newError) => {
  if (newError) {
    apiError.value = newError;
  }
});

// Fetch data on mount
onMounted(async () => {
  console.log('StudentDashboard mounted, studentId:', studentId.value);
  console.log('Session user:', sessionStore.user);
  await refreshData();
});

async function refreshData() {
  console.log('Refreshing data for student:', studentId.value);
  console.log('Session user:', sessionStore.user);
  console.log('User ID:', sessionStore.user?.id);
  console.log('User email:', sessionStore.user?.email);
  apiError.value = null;
  
  // Test direct API call
  try {
    const testResponse = await fetch(`/api/student/metrics/summary?student_id=${studentId.value}`);
    const testData = await testResponse.json();
    console.log('Direct API test:', testData);
  } catch (err) {
    console.error('Direct API test failed:', err);
  }
  
  await metricsStore.fetchAllData(studentId.value);
  console.log('Data fetched, summary:', summary.value);
  console.log('Store summary:', metricsStore.summary);
  console.log('Total sessions:', summary.value?.total_sessions);
}

async function changePeriod(period) {
  trendPeriod.value = period;
  await metricsStore.fetchTrends(studentId.value, period);
}

// Chart helpers
function getLineChartPoints(data, maxValue) {
  if (!data || data.length === 0) return '';
  
  return data.map((point, idx) => {
    const x = (idx / (data.length - 1)) * 100;
    const y = 50 - (point.value / maxValue) * 50;
    return `${x},${y}`;
  }).join(' ');
}

function getPointX(idx, total) {
  if (total <= 1) return 50;
  return (idx / (total - 1)) * 100;
}

function showTooltip(event, point, unit = '%') {
  const rect = event.target.getBoundingClientRect();
  tooltip.value = {
    visible: true,
    x: rect.left + window.scrollX,
    y: rect.top + window.scrollY - 40,
    date: point.date,
    value: point.value,
    unit: unit
  };
}

function hideTooltip() {
  tooltip.value.visible = false;
}

// Formatting helpers
function formatDateTime(date) {
  if (!date) return '';
  return new Date(date).toLocaleString('zh-TW', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  
  if (date.toDateString() === today.toDateString()) return '今天';
  if (date.toDateString() === yesterday.toDateString()) return '昨天';
  
  return date.toLocaleDateString('zh-TW', { month: 'short', day: 'numeric' });
}

function formatDateShort(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return `${date.getMonth() + 1}/${date.getDate()}`;
}

// Style helpers
function getKPIClass(kpi, inverse = false) {
  if (!kpi?.confidence?.is_sufficient) return 'insufficient';
  
  const value = kpi.value;
  if (inverse) {
    // Lower is better (e.g., error rate)
    if (value <= 10) return 'excellent';
    if (value <= 25) return 'good';
    return 'warning';
  } else {
    // Higher is better
    if (value >= 80) return 'excellent';
    if (value >= 60) return 'good';
    return 'warning';
  }
}

function getTrendIcon(direction) {
  if (direction === 'up') return '↑';
  if (direction === 'down') return '↓';
  return '→';
}

function getModeClass(mode) {
  return mode === '講題模式' ? 'teaching' : 'practice';
}

function getRateClass(rate) {
  if (rate >= 0.8) return 'excellent';
  if (rate >= 0.6) return 'good';
  return 'warning';
}
</script>


<style scoped>
.student-dashboard {
  padding: 1.5rem;
  background: #f8fafc;
  min-height: 100vh;
}

/* Header */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 1.25rem 1.5rem;
  border-radius: 0.75rem;
  border: 2px solid #bfdbfe;
  margin-bottom: 1.5rem;
}

.dashboard-header h1 {
  margin: 0 0 0.25rem 0;
  color: #1e3a8a;
  font-size: 1.5rem;
}

.dashboard-header p {
  margin: 0;
  color: #64748b;
  font-size: 0.85rem;
}

.refresh-btn {
  padding: 0.5rem 1rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: #2563eb;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Error Alert */
.error-alert {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
}

.close-btn {
  font-size: 1.25rem;
  opacity: 0.7;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  color: #64748b;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* KPI Section */
.kpi-section {
  margin-bottom: 1.5rem;
}

.kpi-section h2 {
  color: #1e3a8a;
  font-size: 1.1rem;
  margin: 0 0 1rem 0;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}

.kpi-card {
  background: white;
  border-radius: 0.75rem;
  padding: 1.25rem;
  border: 2px solid #e2e8f0;
  transition: all 0.2s;
}

.kpi-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
}

.kpi-card.excellent {
  border-color: #22c55e;
  background: linear-gradient(135deg, #f0fdf4, white);
}

.kpi-card.good {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #eff6ff, white);
}

.kpi-card.warning {
  border-color: #f59e0b;
  background: linear-gradient(135deg, #fffbeb, white);
}

.kpi-card.insufficient {
  border-color: #94a3b8;
  background: #f8fafc;
}

.kpi-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.kpi-icon {
  font-size: 1.25rem;
}

.kpi-title {
  color: #64748b;
  font-size: 0.85rem;
  font-weight: 500;
}

.kpi-trend {
  margin-left: auto;
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  border-radius: 0.25rem;
}

.kpi-trend.up {
  background: #dcfce7;
  color: #16a34a;
}

.kpi-trend.down {
  background: #fef2f2;
  color: #dc2626;
}

.kpi-trend.stable {
  background: #f1f5f9;
  color: #64748b;
}

.kpi-value {
  font-size: 2rem;
  font-weight: 700;
  color: #1e3a8a;
  line-height: 1.2;
}

.kpi-unit {
  font-size: 0.9rem;
  font-weight: 400;
  color: #64748b;
  margin-left: 0.25rem;
}

.no-data {
  font-size: 0.9rem;
  color: #94a3b8;
  font-weight: 400;
}

.kpi-footer {
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid #e2e8f0;
}

.sample-info {
  font-size: 0.75rem;
  color: #94a3b8;
}

/* Stats Section */
.stats-section {
  margin-bottom: 1.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.stat-card {
  background: white;
  border-radius: 0.5rem;
  padding: 1rem;
  text-align: center;
  border: 1px solid #e2e8f0;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e3a8a;
}

.stat-label {
  font-size: 0.8rem;
  color: #64748b;
  margin-top: 0.25rem;
}

/* Charts Section */
.charts-section {
  margin-bottom: 1.5rem;
}

.chart-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.chart-card {
  background: white;
  border-radius: 0.75rem;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.chart-card.full-width {
  grid-column: 1 / -1;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
}

.chart-header h3 {
  margin: 0;
  font-size: 1rem;
  color: #1e3a8a;
}

.period-selector {
  display: flex;
  gap: 0.25rem;
}

.period-selector button {
  padding: 0.25rem 0.75rem;
  border: 1px solid #e2e8f0;
  background: white;
  border-radius: 0.25rem;
  font-size: 0.8rem;
  cursor: pointer;
  color: #64748b;
}

.period-selector button.active {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.chart-body {
  padding: 1.25rem;
  min-height: 200px;
}

.no-chart-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 150px;
  color: #94a3b8;
}

.no-chart-data span {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.no-chart-data.success {
  color: #22c55e;
}

/* Line Chart */
.line-chart {
  display: flex;
  gap: 0.5rem;
  height: 150px;
}

.chart-y-axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  font-size: 0.7rem;
  color: #94a3b8;
  padding: 0.25rem 0;
}

.chart-area {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chart-area svg {
  flex: 1;
  background: linear-gradient(to bottom, #f8fafc, white);
  border-radius: 0.25rem;
}

.data-point {
  cursor: pointer;
  transition: r 0.2s;
}

.data-point:hover {
  r: 5;
}

.chart-x-axis {
  display: flex;
  justify-content: space-between;
  font-size: 0.7rem;
  color: #94a3b8;
  padding-top: 0.5rem;
}

/* Bar Chart */
.bar-chart {
  height: 150px;
}

.bars-container {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 120px;
  padding: 0 0.5rem;
}

.bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 40px;
}

.bar {
  width: 100%;
  background: linear-gradient(to top, #2563eb, #3b82f6);
  border-radius: 0.25rem 0.25rem 0 0;
  min-height: 4px;
  transition: opacity 0.2s;
  cursor: pointer;
}

.bar:hover {
  opacity: 0.8;
}

.bar-label {
  font-size: 0.7rem;
  color: #94a3b8;
  margin-top: 0.5rem;
}

/* Error Analysis */
.error-stats {
  display: flex;
  gap: 2rem;
  margin-bottom: 1.5rem;
}

.error-stat {
  text-align: center;
}

.error-stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e3a8a;
}

.error-stat-label {
  font-size: 0.8rem;
  color: #64748b;
}

.error-breakdown h4 {
  margin: 0 0 0.75rem 0;
  font-size: 0.9rem;
  color: #475569;
}

.unit-bars {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.unit-bar-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.unit-name {
  width: 100px;
  font-size: 0.85rem;
  color: #475569;
  text-align: right;
}

.unit-bar-bg {
  flex: 1;
  height: 20px;
  background: #f1f5f9;
  border-radius: 0.25rem;
  overflow: hidden;
}

.unit-bar-fill {
  height: 100%;
  background: linear-gradient(to right, #ef4444, #f87171);
  border-radius: 0.25rem;
  transition: width 0.3s;
}

.unit-count {
  width: 30px;
  font-size: 0.85rem;
  color: #64748b;
}

/* Sessions Section */
.sessions-section {
  background: white;
  border-radius: 0.75rem;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.section-header h2 {
  margin: 0;
  font-size: 1rem;
  color: #1e3a8a;
}

.confidence-badge {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  background: #f1f5f9;
  color: #64748b;
  border-radius: 0.25rem;
}

.table-wrapper {
  overflow-x: auto;
}

.sessions-table {
  width: 100%;
  border-collapse: collapse;
}

.sessions-table th,
.sessions-table td {
  padding: 0.75rem 1rem;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
}

.sessions-table th {
  background: #f8fafc;
  color: #475569;
  font-weight: 600;
  font-size: 0.85rem;
}

.sessions-table td {
  color: #1e293b;
  font-size: 0.9rem;
}

.sessions-table tbody tr:hover {
  background: #f8fafc;
}

.unit-cell {
  display: flex;
  flex-direction: column;
}

.unit-cell strong {
  color: #1e3a8a;
}

.unit-cell small {
  color: #94a3b8;
  font-size: 0.75rem;
}

.mode-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.8rem;
}

.mode-badge.teaching {
  background: #dbeafe;
  color: #1e40af;
}

.mode-badge.practice {
  background: #fef3c7;
  color: #92400e;
}

.rate-badge {
  font-weight: 600;
}

.rate-badge.excellent {
  color: #16a34a;
}

.rate-badge.good {
  color: #3b82f6;
}

.rate-badge.warning {
  color: #f59e0b;
}

.session-details {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.detail-tag {
  padding: 0.15rem 0.4rem;
  background: #f1f5f9;
  color: #64748b;
  border-radius: 0.25rem;
  font-size: 0.75rem;
}

.detail-tag.warning {
  background: #fef2f2;
  color: #dc2626;
}

.no-sessions {
  padding: 2rem;
  text-align: center;
  color: #94a3b8;
}

/* Tooltip */
.chart-tooltip {
  position: fixed;
  background: #1e293b;
  color: white;
  padding: 0.5rem 0.75rem;
  border-radius: 0.25rem;
  font-size: 0.8rem;
  pointer-events: none;
  z-index: 100;
  transform: translateX(-50%);
}

.tooltip-date {
  color: #94a3b8;
  font-size: 0.7rem;
}

.tooltip-value {
  font-weight: 600;
}

/* Responsive */
@media (max-width: 768px) {
  .student-dashboard {
    padding: 1rem;
  }
  
  .chart-row {
    grid-template-columns: 1fr;
  }
  
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .error-stats {
    flex-wrap: wrap;
    gap: 1rem;
  }
}
</style>
