<template>
  <div class="mistake-clinic-page">
    <header class="page-header">
      <div>
        <h1>錯題診所</h1>
        <p>自動蒐集的錯題，可一鍵加入個人錯題本並重播學習過程</p>
      </div>
    </header>
    <div class="mistake-clinic">
    
    <div class="mistake-stats" v-if="mistakes.length > 0">
      <div class="stat-item">
        <span class="stat-label">總錯題數</span>
        <span class="stat-value">{{ mistakes.length }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">本週新增</span>
        <span class="stat-value">{{ thisWeekCount }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">最常錯單元</span>
        <span class="stat-value">{{ mostCommonUnit }}</span>
      </div>
    </div>

    <div class="mistake-list" v-if="mistakes.length > 0">
      <div v-for="mistake in mistakes" :key="mistake.id" class="mistake-card">
        <div class="mistake-header">
          <div>
            <h3>{{ mistake.subject }} - {{ mistake.unit }}</h3>
            <span class="mistake-date">{{ mistake.date }}</span>
          </div>
          <button 
            class="add-btn" 
            :class="{ 'added': mistake.inNotebook }"
            @click="toggleNotebook(mistake.id)"
          >
            {{ mistake.inNotebook ? '✓ 已在錯題本' : '+ 加入錯題本' }}
          </button>
        </div>
        <div class="mistake-content">
          <p class="mistake-question">{{ mistake.question }}</p>
          <div class="mistake-tags">
            <span
              v-for="tag in mistake.tags"
              :key="tag"
              class="tag"
              :class="`tag-${tag}`"
            >
              #{{ tag }}
            </span>
          </div>
        </div>
        <div class="mistake-actions">
          <button @click="reviewMistake(mistake.id)" class="review-btn">
            🔄 重播學習過程
          </button>
          <button @click="practiceAgain(mistake.id)" class="practice-btn">
            ✏️ 再次練習
          </button>
        </div>
      </div>
    </div>
    
    <div class="empty-state" v-else>
      <div class="empty-icon">📚</div>
      <h3>目前沒有錯題</h3>
      <p>繼續練習，系統會自動記錄錯題</p>
      <button class="go-practice-btn" @click="goToPractice">前往做題模式</button>
    </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';

export default {
  name: 'MistakeClinic',
  setup() {
    const router = useRouter();
    
    const mistakes = ref([
      {
        id: 1,
        subject: '數學',
        unit: '一元一次方程式',
        date: '2025-12-01',
        question: '解方程式：2x + 5 = 13',
        tags: ['觀念', '計算'],
        inNotebook: false
      },
      {
        id: 2,
        subject: '數學',
        unit: '因式分解',
        date: '2025-11-28',
        question: '因式分解：x² - 4',
        tags: ['觀念'],
        inNotebook: true
      },
      {
        id: 3,
        subject: '數學',
        unit: '一元一次方程式',
        date: '2025-12-02',
        question: '解方程式：3x - 7 = 14',
        tags: ['計算'],
        inNotebook: false
      }
    ]);

    const thisWeekCount = computed(() => {
      const oneWeekAgo = new Date();
      oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
      return mistakes.value.filter(m => new Date(m.date) >= oneWeekAgo).length;
    });

    const mostCommonUnit = computed(() => {
      const unitCounts = {};
      mistakes.value.forEach(m => {
        unitCounts[m.unit] = (unitCounts[m.unit] || 0) + 1;
      });
      return Object.keys(unitCounts).reduce((a, b) => 
        unitCounts[a] > unitCounts[b] ? a : b, '無'
      );
    });

    const toggleNotebook = (id) => {
      const mistake = mistakes.value.find(m => m.id === id);
      if (mistake) {
        mistake.inNotebook = !mistake.inNotebook;
        // TODO: 與後端 API 串接，實際加入/移除錯題本
      }
    };

    const reviewMistake = (id) => {
      // TODO: 跳轉到教學過程的確切時間點
      router.push({ 
        name: 'student-teaching',
        query: { mistakeId: id }
      });
    };

    const practiceAgain = (id) => {
      const mistake = mistakes.value.find(m => m.id === id);
      if (mistake) {
        router.push({ 
          name: 'student-practice',
          query: { 
            subject: mistake.subject,
            unit: mistake.unit,
            question: mistake.question
          }
        });
      }
    };

    const goToPractice = () => {
      router.push({ name: 'student-practice' });
    };

    return {
      mistakes,
      thisWeekCount,
      mostCommonUnit,
      toggleNotebook,
      reviewMistake,
      practiceAgain,
      goToPractice
    };
  }
};
</script>

<style scoped>
.mistake-clinic-page {
  padding: 2rem;
  background: #F8FAFC;
  min-height: 100vh;
}

.page-header {
  background: #FFFFFF;
  padding: 1.5rem;
  border-radius: 0.75rem;
  border: 2px solid #BFDBFE;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
  margin-bottom: 1.5rem;
}

.page-header h1 {
  color: #1e3a8a;
  margin: 0 0 0.5rem 0;
  font-size: 1.75rem;
}

.page-header p {
  color: #3b82f6;
  margin: 0;
  font-size: 0.95rem;
}

.mistake-clinic {
  color: #1e3a8a;
}

.mistake-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-item {
  background: #FFFFFF;
  border-radius: 0.75rem;
  padding: 1rem;
  border: 2px solid #BFDBFE;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.stat-label {
  color: #3b82f6;
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}

.stat-value {
  color: #1e3a8a;
  font-size: 1.5rem;
  font-weight: 700;
}

.mistake-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1.5rem;
}

.mistake-card {
  background: #FFFFFF;
  border-radius: 0.75rem;
  padding: 1.5rem;
  border: 2px solid #BFDBFE;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.mistake-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15);
}

.mistake-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
  gap: 1rem;
}

.mistake-header > div {
  flex: 1;
}

.mistake-header h3 {
  color: #1e3a8a;
  margin: 0 0 0.25rem 0;
  font-size: 1.1rem;
}

.mistake-date {
  color: #6B7280;
  font-size: 0.85rem;
}

.add-btn {
  padding: 0.4rem 0.8rem;
  border-radius: 0.5rem;
  border: 2px solid #BFDBFE;
  background: #EFF6FF;
  color: #2563eb;
  cursor: pointer;
  font-size: 0.85rem;
  white-space: nowrap;
  transition: all 0.2s;
}

.add-btn:hover {
  background: #DBEAFE;
  border-color: #2563eb;
}

.add-btn.added {
  background: #D1FAE5;
  border-color: #10B981;
  color: #065F46;
}

.mistake-question {
  margin-bottom: 1rem;
  font-size: 1.05rem;
  color: #374151;
  line-height: 1.6;
}

.mistake-tags {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.tag {
  padding: 0.35rem 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.85rem;
  font-weight: 500;
}

.tag-觀念 {
  background: #DBEAFE;
  color: #1e40af;
}

.tag-計算 {
  background: #FEF3C7;
  color: #92400e;
}

.mistake-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
}

.review-btn,
.practice-btn {
  flex: 1;
  padding: 0.6rem 1rem;
  border-radius: 0.5rem;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: background 0.2s;
}

.review-btn {
  background: #2563eb;
  color: white;
}

.review-btn:hover {
  background: #1d4ed8;
}

.practice-btn {
  background: #EFF6FF;
  color: #2563eb;
  border: 2px solid #BFDBFE;
}

.practice-btn:hover {
  background: #DBEAFE;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: #FFFFFF;
  border-radius: 0.75rem;
  border: 2px dashed #BFDBFE;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state h3 {
  color: #1e3a8a;
  margin: 0 0 0.5rem 0;
}

.empty-state p {
  color: #6B7280;
  margin-bottom: 1.5rem;
}

.go-practice-btn {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: background 0.2s;
}

.go-practice-btn:hover {
  background: #1d4ed8;
}
</style>

