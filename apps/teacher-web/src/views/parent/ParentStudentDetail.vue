<template>
  <div class="parent-student-detail">
    <div class="header">
      <button @click="goBack" class="back-btn">← 返回</button>
      <h1>詳細學習報告</h1>
    </div>
    <div class="content">
      <div class="detail-section">
        <h2>口說表現</h2>
        <div class="metrics">
          <div class="metric-item">
            <span class="label">平均 WPM</span>
            <span class="value">{{ metrics.avgWPM }}</span>
          </div>
          <div class="metric-item">
            <span class="label">停頓比例</span>
            <span class="value">{{ metrics.pauseRatio }}%</span>
          </div>
          <div class="metric-item">
            <span class="label">提示依賴度</span>
            <span class="value">{{ metrics.hintDependency }}%</span>
          </div>
        </div>
      </div>
      <div class="detail-section">
        <h2>專注習慣</h2>
        <div class="focus-details">
          <p>平均每日專注時長: <strong>{{ focusDetails.dailyAvg }} 分鐘</strong></p>
          <p>最佳專注時段: <strong>{{ focusDetails.bestTime }}</strong></p>
        </div>
      </div>
      <div class="detail-section">
        <h2>弱點修復率</h2>
        <div class="weakness-stats">
          <div class="weakness-item">
            <span class="label">已修復弱點</span>
            <span class="value">{{ weaknessStats.fixed }}/{{ weaknessStats.total }}</span>
          </div>
          <div class="weakness-item">
            <span class="label">修復率</span>
            <span class="value">{{ weaknessStats.rate }}%</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

export default {
  name: 'ParentStudentDetail',
  setup() {
    const router = useRouter();

    const metrics = ref({
      avgWPM: 118,
      pauseRatio: 12,
      hintDependency: 25
    });

    const focusDetails = ref({
      dailyAvg: 42,
      bestTime: '晚上 7-9 點'
    });

    const weaknessStats = ref({
      fixed: 8,
      total: 12,
      rate: 67
    });

    const goBack = () => {
      router.push('/parent');
    };

    return {
      metrics,
      focusDetails,
      weaknessStats,
      goBack
    };
  }
};
</script>

<style scoped>
.parent-student-detail {
  background: white;
  border-radius: 8px;
  padding: 2rem;
}

.header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
}

.back-btn {
  background: #f3f4f6;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
}

.back-btn:hover {
  background: #e5e7eb;
}

.detail-section {
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid #e5e7eb;
}

.detail-section:last-child {
  border-bottom: none;
}

.metrics,
.focus-details,
.weakness-stats {
  margin-top: 1rem;
}

.metric-item,
.weakness-item {
  background: #f9fafb;
  padding: 1rem;
  border-radius: 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.label {
  color: #666;
  font-size: 0.9rem;
}

.value {
  font-size: 1.3rem;
  font-weight: bold;
  color: #2563eb;
}

.focus-details p {
  margin: 0.5rem 0;
  color: #374151;
}

.focus-details strong {
  color: #1e3a8a;
}
</style>

