<template>
  <div class="teacher-overview">
    <h1>班級總覽</h1>
    <div class="class-stats">
      <div class="stat-card">
        <div class="stat-value">{{ classStats.totalStudents }}</div>
        <div class="stat-label">總學生數</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ classStats.avgScore }}%</div>
        <div class="stat-label">平均正確率</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ classStats.activeToday }}</div>
        <div class="stat-label">今日活躍</div>
      </div>
    </div>
    <div class="heatmap-section">
      <h2>單元掌握度熱力圖</h2>
      <div class="heatmap-placeholder">
        <p>熱力圖將顯示各單元的掌握度分布</p>
        <table class="heatmap-table">
          <thead>
            <tr>
              <th>學生</th>
              <th>一元一次方程式</th>
              <th>因式分解</th>
              <th>二次函數</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="student in students" :key="student.id">
              <td>{{ student.name }}</td>
              <td :class="getHeatmapClass(student.mastery.equation)">
                {{ student.mastery.equation }}%
              </td>
              <td :class="getHeatmapClass(student.mastery.factorization)">
                {{ student.mastery.factorization }}%
              </td>
              <td :class="getHeatmapClass(student.mastery.quadratic)">
                {{ student.mastery.quadratic }}%
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div class="students-list">
      <h2>學生列表</h2>
      <div class="students-grid">
        <div
          v-for="student in students"
          :key="student.id"
          class="student-card"
          @click="viewStudentDetail(student.id)"
        >
          <h3>{{ student.name }}</h3>
          <p>正確率: {{ student.accuracy }}%</p>
          <p>錯題復發率: {{ student.recurrenceRate }}%</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

export default {
  name: 'TeacherOverview',
  setup() {
    const router = useRouter();

    const classStats = ref({
      totalStudents: 28,
      avgScore: 78,
      activeToday: 22
    });

    const students = ref([
      {
        id: 1,
        name: '張小明',
        accuracy: 85,
        recurrenceRate: 15,
        mastery: { equation: 90, factorization: 75, quadratic: 80 }
      },
      {
        id: 2,
        name: '李小花',
        accuracy: 72,
        recurrenceRate: 28,
        mastery: { equation: 70, factorization: 65, quadratic: 80 }
      },
      {
        id: 3,
        name: '王大華',
        accuracy: 91,
        recurrenceRate: 9,
        mastery: { equation: 95, factorization: 90, quadratic: 88 }
      }
    ]);

    const getHeatmapClass = (value) => {
      if (value >= 80) return 'heatmap-high';
      if (value >= 60) return 'heatmap-medium';
      return 'heatmap-low';
    };

    const viewStudentDetail = (id) => {
      router.push(`/teacher/students/${id}`);
    };

    return {
      classStats,
      students,
      getHeatmapClass,
      viewStudentDetail
    };
  }
};
</script>

<style scoped>
.teacher-overview {
  background: white;
  border-radius: 8px;
  padding: 2rem;
}

.class-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin: 2rem 0;
}

.stat-card {
  background: #eff6ff;
  border-radius: 8px;
  padding: 1.5rem;
  text-align: center;
}

.stat-value {
  font-size: 2.5rem;
  font-weight: bold;
  color: #2563eb;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: #666;
  font-size: 0.9rem;
}

.heatmap-section {
  margin: 2rem 0;
}

.heatmap-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

.heatmap-table th,
.heatmap-table td {
  padding: 0.75rem;
  text-align: center;
  border: 1px solid #e5e7eb;
}

.heatmap-table th {
  background: #f3f4f6;
  font-weight: 600;
}

.heatmap-high {
  background: #d1fae5;
  color: #065f46;
}

.heatmap-medium {
  background: #fef3c7;
  color: #92400e;
}

.heatmap-low {
  background: #fee2e2;
  color: #991b1b;
}

.students-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.student-card {
  background: #f9fafb;
  border-radius: 8px;
  padding: 1.5rem;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.student-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.student-card h3 {
  margin: 0 0 0.5rem 0;
  color: #1e3a8a;
}

.student-card p {
  margin: 0.25rem 0;
  color: #666;
  font-size: 0.9rem;
}
</style>

