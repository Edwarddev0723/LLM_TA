<template>
  <div class="parent-overview">
    <h1>學習報告總覽</h1>
    <div class="trend-section">
      <h2>長期趨勢</h2>
      <div class="trend-cards">
        <div class="trend-card">
          <h3>口說流暢度趨勢</h3>
          <div class="trend-placeholder">
            <p>WPM 趨勢圖將顯示在此</p>
            <div class="trend-bars">
              <div
                v-for="(wpm, index) in wpmTrend"
                :key="index"
                class="trend-bar"
                :style="{ height: `${(wpm / 150) * 100}%` }"
                :title="`週 ${index + 1}: ${wpm} WPM`"
              ></div>
            </div>
          </div>
        </div>
        <div class="trend-card">
          <h3>提示依賴度趨勢</h3>
          <div class="trend-placeholder">
            <p>提示依賴度趨勢圖將顯示在此</p>
            <div class="trend-bars">
              <div
                v-for="(dep, index) in dependencyTrend"
                :key="index"
                class="trend-bar dependency"
                :style="{ height: `${dep}%` }"
                :title="`週 ${index + 1}: ${dep}%`"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="focus-section">
      <h2>專注時長統計</h2>
      <div class="focus-stats">
        <div class="focus-item">
          <span class="label">本週平均</span>
          <span class="value">{{ focusStats.weeklyAvg }} 分鐘</span>
        </div>
        <div class="focus-item">
          <span class="label">本月總計</span>
          <span class="value">{{ focusStats.monthlyTotal }} 分鐘</span>
        </div>
        <div class="focus-item">
          <span class="label">最佳單日</span>
          <span class="value">{{ focusStats.bestDay }} 分鐘</span>
        </div>
      </div>
    </div>
    <div class="summary-section">
      <h2>本週學習摘要</h2>
      <div class="summary-content">
        <p>{{ weeklySummary }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';

export default {
  name: 'ParentOverview',
  setup() {
    const wpmTrend = ref([95, 105, 110, 115, 120, 118, 125]);
    const dependencyTrend = ref([45, 40, 35, 32, 28, 25, 22]);

    const focusStats = ref({
      weeklyAvg: 42,
      monthlyTotal: 168,
      bestDay: 65
    });

    const weeklySummary = ref(
      '本週學習表現穩定提升，口說流暢度持續改善，提示依賴度明顯下降。建議繼續保持每日練習習慣，並鼓勵主動思考解題步驟。'
    );

    return {
      wpmTrend,
      dependencyTrend,
      focusStats,
      weeklySummary
    };
  }
};
</script>

<style scoped>
.parent-overview {
  background: white;
  border-radius: 8px;
  padding: 2rem;
}

.trend-section,
.focus-section,
.summary-section {
  margin-bottom: 2rem;
}

.trend-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-top: 1rem;
}

.trend-card {
  background: #f9fafb;
  border-radius: 8px;
  padding: 1.5rem;
}

.trend-card h3 {
  margin: 0 0 1rem 0;
  color: #1e3a8a;
}

.trend-placeholder {
  min-height: 200px;
}

.trend-bars {
  display: flex;
  align-items: flex-end;
  gap: 0.5rem;
  height: 150px;
  margin-top: 1rem;
}

.trend-bar {
  flex: 1;
  background: #2563eb;
  border-radius: 4px 4px 0 0;
  min-height: 10px;
  transition: opacity 0.2s;
}

.trend-bar:hover {
  opacity: 0.8;
}

.trend-bar.dependency {
  background: #f59e0b;
}

.focus-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.focus-item {
  background: #eff6ff;
  padding: 1.5rem;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.focus-item .label {
  color: #666;
  font-size: 0.9rem;
}

.focus-item .value {
  font-size: 1.8rem;
  font-weight: bold;
  color: #2563eb;
}

.summary-content {
  background: #f9fafb;
  padding: 1.5rem;
  border-radius: 8px;
  margin-top: 1rem;
  line-height: 1.6;
  color: #374151;
}
</style>

