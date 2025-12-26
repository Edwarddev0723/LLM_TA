<template>
  <div class="mistake-clinic-page">
    <header class="page-header">
      <div>
        <h1>🏥 錯題診所</h1>
        <p>自動分析錯題原因，幫助你快速進步</p>
      </div>
    </header>

    <div class="clinic-container">
      <!-- 統計信息 -->
      <div class="stats-section" v-if="mistakes.length > 0">
        <div class="stat-card">
          <div class="stat-icon">📚</div>
          <div class="stat-info">
            <span class="stat-label">總錯題</span>
            <span class="stat-value">{{ mistakes.length }}</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">📈</div>
          <div class="stat-info">
            <span class="stat-label">本週新增</span>
            <span class="stat-value">{{ thisWeekCount }}</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">🎯</div>
          <div class="stat-info">
            <span class="stat-label">最常原因</span>
            <span class="stat-value">{{ getMostCommonReason() }}</span>
          </div>
        </div>
      </div>

      <!-- 錯題列表 -->
      <div class="mistakes-list" v-if="mistakes.length > 0">
        <div v-for="mistake in paginatedMistakes" :key="mistake.id" class="mistake-card">
          <!-- 題目信息 -->
          <div class="mistake-header">
            <div class="header-left">
              <h3>{{ mistake.subject }} - {{ mistake.unit }}</h3>
              <p class="mistake-date">{{ formatDate(mistake.date) }}</p>
            </div>
            <div class="header-right">
              <span 
                v-if="mistake.reason_type"
                class="reason-badge"
                :class="`reason-${mistake.reason_type}`"
              >
                {{ getReasonLabel(mistake.reason_type) }}
              </span>
              <span v-else class="reason-badge pending">待診斷</span>
            </div>
          </div>

          <!-- 題目內容 -->
          <div class="mistake-content">
            <p class="question-text">{{ mistake.question }}</p>
            <div v-if="mistake.student_answer" class="answer-comparison">
              <div class="comparison-item">
                <span class="label">你的答案：</span>
                <span class="your-answer">{{ mistake.student_answer }}</span>
              </div>
              <div class="comparison-item">
                <span class="label">正確答案：</span>
                <span class="correct-answer">{{ mistake.correct_answer }}</span>
              </div>
            </div>
          </div>

          <!-- 原因診斷 -->
          <div class="diagnosis-section">
            <div v-if="!mistake.reason_type" class="reason-selector">
              <p class="diagnosis-title">🔍 診斷錯誤原因</p>
              <div class="reason-buttons">
                <button 
                  v-for="reason in mistakeReasons"
                  :key="reason.value"
                  class="reason-btn"
                  :class="`reason-${reason.value}`"
                  @click="selectReason(mistake.id, reason.value)"
                >
                  {{ reason.label }}
                </button>
              </div>
              <button 
                v-if="expandedMistakeId === mistake.id"
                class="other-btn"
                @click="toggleOtherReason(mistake.id)"
              >
                ✏️ 自訂原因
              </button>
              <div v-if="customReasons[mistake.id]" class="custom-reason-input">
                <textarea 
                  v-model="customReasons[mistake.id]"
                  placeholder="請說明你錯誤的原因..."
                  rows="3"
                ></textarea>
                <button class="save-custom-btn" @click="saveCustomReason(mistake.id)">
                  保存原因
                </button>
              </div>
            </div>
            <div v-else class="reason-analysis">
              <p class="analysis-title">📊 診斷結果</p>
              <div class="analysis-content">
                <p class="analysis-text">{{ getReasonAnalysis(mistake.reason_type) }}</p>
                <button class="suggestion-btn" @click="getSuggestions(mistake.id)">
                  💡 獲取改進建議
                </button>
              </div>
            </div>
          </div>

          <!-- 行動按鈕 -->
          <div class="mistake-actions">
            <button @click="practiceSimilar(mistake.id)" class="practice-btn">
              🔄 練習類似題
            </button>
            <button @click="reviewMistake(mistake.id)" class="review-btn">
              🎬 重播講題
            </button>
            <button 
              v-if="!mistake.mastered"
              @click="markAsMastered(mistake.id)" 
              class="master-btn"
            >
              ✅ 已掌握
            </button>
            <button v-else class="mastered-badge">已掌握 ✓</button>
          </div>
        </div>
      </div>

      <!-- 空狀態 -->
      <div class="empty-state" v-else>
        <div class="empty-icon">✨</div>
        <h3>目前沒有錯題</h3>
        <p>繼續努力練習，系統會自動記錄錯題</p>
        <button class="go-practice-btn" @click="goToPractice">
          前往做題模式
        </button>
      </div>

      <!-- 分頁 -->
      <div class="pagination" v-if="totalPages > 1">
        <button 
          @click="currentPage--"
          :disabled="currentPage === 1"
          class="page-btn"
        >
          ← 上一頁
        </button>
        <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 頁</span>
        <button 
          @click="currentPage++"
          :disabled="currentPage === totalPages"
          class="page-btn"
        >
          下一頁 →
        </button>
      </div>
    </div>

    <!-- 建議模態框 -->
    <div v-if="showSuggestions" class="modal-overlay" @click.stop="showSuggestions = false">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>改進建議</h3>
          <button class="close-btn" @click="showSuggestions = false">✕</button>
        </div>
        <div class="modal-content">
          <div v-for="(suggestion, index) in currentSuggestions" :key="index" class="suggestion-item">
            <span class="number">{{ index + 1 }}</span>
            <p>{{ suggestion }}</p>
          </div>
        </div>
        <div class="modal-actions">
          <button class="action-btn primary" @click="practiceSimilarFromSuggestion">
            💪 開始練習
          </button>
          <button class="action-btn secondary" @click="showSuggestions = false">
            關閉
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useSessionStore } from '@/stores/session';

const router = useRouter();
const sessionStore = useSessionStore();

// 錯題原因選項
const mistakeReasons = [
  { label: '❌ 看錯題目', value: 'misread' },
  { label: '❌ 概念不清', value: 'concept' },
  { label: '❌ 計算錯誤', value: 'calculation' },
  { label: '❌ 粗心大意', value: 'careless' },
  { label: '❌ 不會做', value: 'unable' }
];

// 數據
const mistakes = ref([
  {
    id: 1,
    subject: '數學',
    unit: '一元一次方程式',
    question: '解方程式：2x + 5 = 13',
    student_answer: '4',
    correct_answer: '4',
    date: new Date('2025-12-23'),
    reason_type: 'calculation',
    mastered: false
  },
  {
    id: 2,
    subject: '數學',
    unit: '因式分解',
    question: '因式分解：x² + 5x + 6',
    student_answer: '(x+2)(x+3)',
    correct_answer: '(x+2)(x+3)',
    date: new Date('2025-12-22'),
    reason_type: null,
    mastered: false
  }
]);

const currentPage = ref(1);
const itemsPerPage = ref(5);
const customReasons = ref({});
const expandedMistakeId = ref(null);
const showSuggestions = ref(false);
const currentSuggestions = ref([]);
const selectedMistakeId = ref(null);

// 計算屬性
const thisWeekCount = computed(() => {
  const oneWeekAgo = new Date();
  oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
  return mistakes.value.filter(m => new Date(m.date) > oneWeekAgo).length;
});

const paginatedMistakes = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value;
  const end = start + itemsPerPage.value;
  return mistakes.value.slice(start, end);
});

const totalPages = computed(() => {
  return Math.ceil(mistakes.value.length / itemsPerPage.value);
});

// 方法
const formatDate = (date) => {
  return new Date(date).toLocaleDateString('zh-TW', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const getReasonLabel = (reasonType) => {
  const reason = mistakeReasons.find(r => r.value === reasonType);
  return reason ? reason.label : '未知';
};

const getMostCommonReason = () => {
  if (mistakes.value.length === 0) return '無';
  
  const reasonCounts = {};
  mistakes.value.forEach(m => {
    if (m.reason_type) {
      reasonCounts[m.reason_type] = (reasonCounts[m.reason_type] || 0) + 1;
    }
  });

  const mostCommon = Object.entries(reasonCounts).sort((a, b) => b[1] - a[1])[0];
  return mostCommon ? getReasonLabel(mostCommon[0]).replace('❌ ', '') : '無';
};

const getReasonAnalysis = (reasonType) => {
  const analyses = {
    misread: '你可能對題目理解不夠清楚。建議仔細閱讀題目，標記出關鍵信息。',
    concept: '這是概念理解的問題。建議回到教學模式，再次學習相關知識點。',
    calculation: '你的計算步驟有誤。建議使用白板一步步驗算，確認每一步。',
    careless: '這是粗心導致的錯誤。建議在做題時更加謹慎，檢查答案。',
    unable: '你還沒有掌握這個知識點。建議先學習相關教學內容。'
  };
  return analyses[reasonType] || '請診斷此錯題原因。';
};

const selectReason = async (mistakeId, reason) => {
  const mistake = mistakes.value.find(m => m.id === mistakeId);
  if (mistake) {
    mistake.reason_type = reason;
    
    // 調用 API 保存
    try {
      await fetch('/api/student/mistake-reasons', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'user-id': sessionStore.userId
        },
        body: JSON.stringify({
          question_id: mistakeId,
          reason_type: reason
        })
      });
    } catch (error) {
      console.error('保存原因失敗:', error);
    }
  }
};

const toggleOtherReason = (mistakeId) => {
  if (expandedMistakeId.value === mistakeId) {
    expandedMistakeId.value = null;
  } else {
    expandedMistakeId.value = mistakeId;
    customReasons.value[mistakeId] = customReasons.value[mistakeId] || '';
  }
};

const saveCustomReason = async (mistakeId) => {
  const reasonText = customReasons.value[mistakeId];
  if (!reasonText.trim()) {
    alert('請輸入原因說明');
    return;
  }

  try {
    await fetch('/api/student/mistake-reasons', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'user-id': sessionStore.userId
      },
      body: JSON.stringify({
        question_id: mistakeId,
        reason_type: 'other',
        reason_description: reasonText
      })
    });

    const mistake = mistakes.value.find(m => m.id === mistakeId);
    if (mistake) {
      mistake.reason_type = 'other';
    }
    expandedMistakeId.value = null;
    alert('✅ 原因已保存！');
  } catch (error) {
    console.error('保存失敗:', error);
  }
};

const getSuggestions = (mistakeId) => {
  const mistake = mistakes.value.find(m => m.id === mistakeId);
  if (!mistake) return;

  selectedMistakeId.value = mistakeId;
  
  const suggestions = {
    misread: [
      '重新閱讀題目，用不同顏色標記重要信息',
      '寫下題目的中文理解，確認你的理解正確',
      '找一個類似但稍微簡單的題目進行對比'
    ],
    concept: [
      '觀看該知識點的教學影片',
      '找一個掌握的相似知識點進行類比',
      '做 3-5 道相同知識點的練習題'
    ],
    calculation: [
      '用白板一步一步地演算',
      '檢查每一個中間步驟',
      '特別注意符號變化和單位'
    ],
    careless: [
      '練習時自己設置檢查清單',
      '每題做完後花 30 秒檢查答案',
      '做類似題時更加謹慎'
    ],
    unable: [
      '先完成 5 道簡單難度的相似題',
      '查看教學建議瞭解知識點',
      '使用 AI 生成的相似題進行練習'
    ]
  };

  currentSuggestions.value = suggestions[mistake.reason_type] || [
    '重新複習該知識點',
    '做更多相似的練習題',
    '尋求教師或同學的幫助'
  ];
  
  showSuggestions.value = true;
};

const practiceS imilarFromSuggestion = () => {
  practiceSimilar(selectedMistakeId.value);
};

const practiceSimilar = (mistakeId) => {
  router.push({
    name: 'practice-mode',
    query: { mistakeId }
  });
};

const reviewMistake = (mistakeId) => {
  router.push({
    name: 'question-search',
    query: { mistakeId }
  });
};

const markAsMastered = (mistakeId) => {
  const mistake = mistakes.value.find(m => m.id === mistakeId);
  if (mistake) {
    mistake.mastered = true;
    alert('🎉 恭喜！你已掌握這道題目！');
  }
};

const goToPractice = () => {
  router.push({ name: 'practice-mode' });
};

onMounted(() => {
  // 從 API 加載真實數據
  // fetchMistakes();
});
</script>

<style scoped>
.mistake-clinic-page {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  padding: 0;
}

.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 2rem;
  color: white;
  text-align: center;
}

.page-header h1 {
  margin: 0;
  font-size: 2.5rem;
}

.page-header p {
  margin: 0.5rem 0 0 0;
  opacity: 0.9;
  font-size: 1.1rem;
}

.clinic-container {
  max-width: 1000px;
  margin: 2rem auto;
  padding: 0 1rem;
}

/* 統計信息 */
.stats-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.stat-icon {
  font-size: 2rem;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 0.85rem;
  color: #666;
  font-weight: 500;
}

.stat-value {
  font-size: 1.75rem;
  color: #667eea;
  font-weight: 700;
}

/* 錯題列表 */
.mistakes-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.mistake-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.mistake-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
}

.mistake-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f0f0f0;
}

.header-left h3 {
  margin: 0;
  color: #333;
  font-size: 1.1rem;
}

.mistake-date {
  margin: 0.5rem 0 0 0;
  color: #999;
  font-size: 0.85rem;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.reason-badge {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
}

.reason-badge.pending {
  background: #f3f4f6;
  color: #666;
}

.reason-badge.reason-misread {
  background: #fed7d7;
  color: #c53030;
}

.reason-badge.reason-concept {
  background: #feebc8;
  color: #c05621;
}

.reason-badge.reason-calculation {
  background: #fed7d7;
  color: #c53030;
}

.reason-badge.reason-careless {
  background: #fef3c7;
  color: #d97706;
}

.reason-badge.reason-unable {
  background: #dbeafe;
  color: #0c4a6e;
}

/* 題目內容 */
.mistake-content {
  margin-bottom: 1.5rem;
}

.question-text {
  font-size: 1rem;
  line-height: 1.6;
  color: #333;
  margin: 0;
  padding: 1rem;
  background: #f8f9ff;
  border-radius: 6px;
}

.answer-comparison {
  margin-top: 1rem;
  padding: 1rem;
  background: #f0f0f0;
  border-radius: 6px;
}

.comparison-item {
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
}

.comparison-item:last-child {
  margin-bottom: 0;
}

.label {
  font-weight: 600;
  color: #333;
  margin-right: 0.5rem;
}

.your-answer {
  background: #fecaca;
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  color: #dc2626;
}

.correct-answer {
  background: #dbeafe;
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  color: #0369a1;
}

/* 診斷部分 */
.diagnosis-section {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #f8f9ff;
  border-radius: 6px;
  border-left: 4px solid #667eea;
}

.diagnosis-title,
.analysis-title {
  margin: 0 0 1rem 0;
  font-weight: 600;
  color: #333;
}

.reason-selector {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.reason-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.75rem;
}

.reason-btn {
  padding: 0.75rem;
  border: 2px solid #e5e7eb;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.reason-btn:hover {
  border-color: #667eea;
  background: #f0f2ff;
}

.other-btn {
  padding: 0.5rem 1rem;
  background: white;
  border: 2px dashed #667eea;
  border-radius: 6px;
  color: #667eea;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
}

.other-btn:hover {
  background: #f0f2ff;
}

.custom-reason-input {
  margin-top: 1rem;
}

.custom-reason-input textarea {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e5e7eb;
  border-radius: 6px;
  font-family: inherit;
  font-size: 0.9rem;
  resize: none;
}

.custom-reason-input textarea:focus {
  outline: none;
  border-color: #667eea;
}

.save-custom-btn {
  margin-top: 0.75rem;
  padding: 0.5rem 1rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  width: 100%;
}

.save-custom-btn:hover {
  background: #5568d3;
}

.reason-analysis {
  text-align: center;
}

.analysis-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.analysis-text {
  color: #666;
  line-height: 1.6;
  margin: 0;
}

.suggestion-btn {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
}

.suggestion-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

/* 行動按鈕 */
.mistake-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.75rem;
}

.practice-btn,
.review-btn,
.master-btn,
.mastered-badge {
  padding: 0.75rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
}

.practice-btn {
  background: #667eea;
  color: white;
}

.practice-btn:hover {
  background: #5568d3;
}

.review-btn {
  background: #764ba2;
  color: white;
}

.review-btn:hover {
  background: #6a3fa1;
}

.master-btn {
  background: #10b981;
  color: white;
}

.master-btn:hover {
  background: #059669;
}

.mastered-badge {
  background: #d1fae5;
  color: #065f46;
  cursor: default;
}

/* 空狀態 */
.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state h3 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 1.5rem;
}

.empty-state p {
  margin: 0 0 1.5rem 0;
  color: #666;
}

.go-practice-btn {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
}

.go-practice-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

/* 分頁 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
}

.page-btn {
  padding: 0.75rem 1.5rem;
  background: white;
  border: 2px solid #667eea;
  border-radius: 6px;
  color: #667eea;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
}

.page-btn:hover:not(:disabled) {
  background: #667eea;
  color: white;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: white;
  font-weight: 600;
}

/* 模態框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 12px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 2px solid #f0f0f0;
  position: sticky;
  top: 0;
  background: white;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #999;
}

.close-btn:hover {
  color: #333;
}

.modal-content {
  padding: 1.5rem;
}

.suggestion-item {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.suggestion-item:last-child {
  margin-bottom: 0;
}

.number {
  min-width: 30px;
  width: 30px;
  height: 30px;
  background: #667eea;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  flex-shrink: 0;
}

.suggestion-item p {
  margin: 0;
  color: #666;
  line-height: 1.6;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 2px solid #f0f0f0;
}

.action-btn {
  flex: 1;
  padding: 0.75rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
}

.action-btn.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.action-btn.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.action-btn.secondary {
  background: #f0f0f0;
  color: #333;
}

.action-btn.secondary:hover {
  background: #e0e0e0;
}

@media (max-width: 768px) {
  .page-header {
    padding: 1.5rem;
  }

  .page-header h1 {
    font-size: 1.75rem;
  }

  .stats-section {
    grid-template-columns: 1fr;
  }

  .reason-buttons {
    grid-template-columns: 1fr;
  }
}
</style>
