<template>
  <div class="teacher-student-detail">
    <div class="header">
      <button @click="goBack" class="back-btn">← 返回</button>
      <h1>{{ student?.name || '學生詳情' }}</h1>
    </div>
    <div v-if="student" class="content">
      <div class="info-section">
        <h2>學習數據</h2>
        <div class="data-grid">
          <div class="data-item">
            <span class="label">正確率</span>
            <span class="value">{{ student.accuracy }}%</span>
          </div>
          <div class="data-item">
            <span class="label">總練習題數</span>
            <span class="value">{{ student.totalPractice }}</span>
          </div>
          <div class="data-item">
            <span class="label">錯題復發率</span>
            <span class="value">{{ student.recurrenceRate }}%</span>
          </div>
        </div>
      </div>
      <div class="behavior-section">
        <h2>行為數據</h2>
        <div class="behavior-stats">
          <div class="behavior-item">
            <span class="label">平均專注時長</span>
            <span class="value">{{ student.avgFocusMinutes }} 分鐘</span>
          </div>
          <div class="behavior-item">
            <span class="label">平均 WPM</span>
            <span class="value">{{ student.avgWPM }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';

export default {
  name: 'TeacherStudentDetail',
  setup() {
    const router = useRouter();
    const route = useRoute();
    const student = ref(null);

    const mockStudents = {
      1: {
        name: '張小明',
        accuracy: 85,
        totalPractice: 156,
        recurrenceRate: 15,
        avgFocusMinutes: 45,
        avgWPM: 120
      },
      2: {
        name: '李小花',
        accuracy: 72,
        totalPractice: 98,
        recurrenceRate: 28,
        avgFocusMinutes: 32,
        avgWPM: 95
      }
    };

    onMounted(() => {
      const studentId = route.params.id;
      student.value = mockStudents[studentId] || mockStudents[1];
    });

    const goBack = () => {
      router.push('/teacher');
    };

    return {
      student,
      goBack
    };
  }
};
</script>

<style scoped>
.teacher-student-detail {
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

.content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.data-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.data-item,
.behavior-item {
  background: #f9fafb;
  padding: 1rem;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.label {
  color: #666;
  font-size: 0.9rem;
}

.value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #2563eb;
}
</style>

