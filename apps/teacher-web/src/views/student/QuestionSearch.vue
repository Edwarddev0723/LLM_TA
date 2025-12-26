<template>
  <div class="question-search-page">
    <header class="page-header">
      <div>
        <h1>搜題模式</h1>
        <p>搜尋題目後，在右側白板進行講解</p>
      </div>
    </header>

    <div class="search-layout">
      <!-- 左側：搜題面板 -->
      <div class="search-panel">
        <div class="search-controls">
          <div class="form-group">
            <label>科目</label>
            <select v-model="selectedSubject" class="select-input" @change="onSubjectChange">
              <option value="">請選擇科目</option>
              <option value="math">數學</option>
            </select>
          </div>

          <div class="form-group">
            <label>單元</label>
            <select v-model="selectedUnit" class="select-input" :disabled="!selectedSubject">
              <option value="">請選擇單元</option>
              <option v-for="unit in units" :key="unit.id" :value="unit.id">
                {{ unit.unit_name }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>難度</label>
            <select v-model="selectedDifficulty" class="select-input">
              <option value="">全部難度</option>
              <option value="easy">簡單</option>
              <option value="medium">中等</option>
              <option value="hard">困難</option>
            </select>
          </div>

          <button class="search-btn" @click="searchQuestions" :disabled="!selectedUnit">
            🔍 搜尋題目
          </button>
        </div>

        <!-- 題目列表 -->
        <div class="questions-list" v-if="questions.length > 0">
          <div 
            v-for="q in questions" 
            :key="q.id"
            class="question-item"
            :class="{ active: selectedQuestionId === q.id }"
            @click="selectQuestion(q)"
          >
            <div class="question-item-header">
              <span class="difficulty-badge" :class="`diff-${q.difficulty}`">
                {{ difficultyLabel(q.difficulty) }}
              </span>
              <span class="question-number">題{{ q.id }}</span>
            </div>
            <p class="question-preview">{{ truncate(q.question_text, 50) }}</p>
          </div>
        </div>

        <div class="no-results" v-else-if="searched">
          <p>找不到符合條件的題目</p>
        </div>
      </div>

      <!-- 右側：白板 + 題目顯示 -->
      <div class="teaching-area">
        <div v-if="selectedQuestion" class="question-display">
          <div class="question-header">
            <h3>題目 {{ selectedQuestion.id }}</h3>
            <span class="difficulty-badge" :class="`diff-${selectedQuestion.difficulty}`">
              {{ difficultyLabel(selectedQuestion.difficulty) }}
            </span>
          </div>

          <div class="question-content">
            <p class="question-text">{{ selectedQuestion.question_text }}</p>
            <div v-if="selectedQuestion.question_image" class="question-image">
              <img :src="selectedQuestion.question_image" alt="題目圖片" />
            </div>
          </div>

          <div class="teaching-controls">
            <button class="teach-btn" @click="startTeaching">
              🎤 開始講題
            </button>
            <button class="solution-btn" @click="toggleSolution">
              {{ showSolution ? '隱藏' : '查看' }} 解答
            </button>
            <button class="similar-btn" @click="getSimilarQuestions">
              🔄 AI 類似題
            </button>
          </div>

          <div v-if="showSolution" class="solution-box">
            <h4>📝 答案</h4>
            <p>{{ selectedQuestion.answer_text }}</p>
            <h4>📖 解析</h4>
            <p>{{ selectedQuestion.solution_text }}</p>
          </div>

          <div v-if="similarQuestions.length > 0" class="similar-questions">
            <h4>🔄 AI 生成的類似題</h4>
            <div class="similar-list">
              <button 
                v-for="sq in similarQuestions"
                :key="sq.id"
                class="similar-item"
                @click="selectQuestion(sq)"
              >
                <span class="similar-preview">{{ truncate(sq.question_text, 40) }}</span>
                <span class="ai-badge">AI</span>
              </button>
            </div>
          </div>
        </div>

        <div v-else class="no-question-selected">
          <p>請從左側選擇題目</p>
        </div>

        <!-- 白板 -->
        <div class="whiteboard-section" v-if="selectedQuestion">
          <h4>📐 白板</h4>
          <WhiteboardCanvas />
          <div class="whiteboard-actions">
            <button class="action-btn" @click="clearWhiteboard">清除白板</button>
            <button class="action-btn primary" @click="finishTeaching">完成講題</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 講題完成模態框 -->
    <div v-if="showMistakeReasonModal" class="modal-overlay" @click.stop="showMistakeReasonModal = false">
      <div class="modal" @click.stop>
        <h3>講題完成</h3>
        <p>這道題目你之前做錯了嗎？</p>
        
        <div class="reason-options">
          <button 
            v-for="reason in mistakeReasons"
            :key="reason.value"
            class="reason-btn"
            @click="selectMistakeReason(reason.value)"
          >
            {{ reason.label }}
          </button>
        </div>

        <div v-if="selectedReason === 'other'" class="other-reason">
          <textarea 
            v-model="otherReasonText" 
            placeholder="請說明原因..."
            rows="4"
          ></textarea>
        </div>

        <div class="modal-actions">
          <button class="cancel-btn" @click="showMistakeReasonModal = false">取消</button>
          <button class="confirm-btn" @click="saveMistakeReason">完成</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useSessionStore } from '@/stores/session';
import WhiteboardCanvas from '@/components/teaching/WhiteboardCanvas.vue';

const router = useRouter();
const sessionStore = useSessionStore();

// 搜尋相關
const selectedSubject = ref('math');
const selectedUnit = ref('');
const selectedDifficulty = ref('');
const units = ref([]);
const questions = ref([]);
const searched = ref(false);
const selectedQuestionId = ref(null);
const selectedQuestion = ref(null);
const showSolution = ref(false);

// 類似題相關
const similarQuestions = ref([]);

// 講題完成相關
const showMistakeReasonModal = ref(false);
const selectedReason = ref(null);
const otherReasonText = ref('');

const mistakeReasons = [
  { label: '✓ 做對了', value: 'correct' },
  { label: '❌ 看錯題目', value: 'misread' },
  { label: '❌ 概念不清', value: 'concept' },
  { label: '❌ 計算錯誤', value: 'calculation' },
  { label: '❌ 粗心大意', value: 'careless' },
  { label: '❌ 其他原因', value: 'other' }
];

// 初始化：獲取單元列表
const onSubjectChange = async () => {
  try {
    const response = await fetch('/api/units');
    const data = await response.json();
    // 只顯示數學科目的單元
    units.value = data.units.filter(u => u.subject_id === 1);
    selectedUnit.value = '';
    questions.value = [];
  } catch (error) {
    console.error('獲取單元失敗:', error);
  }
};

// 搜尋題目
const searchQuestions = async () => {
  if (!selectedUnit.value) return;

  try {
    let url = `/api/questions?unit_id=${selectedUnit.value}`;
    if (selectedDifficulty.value) {
      url += `&difficulty=${selectedDifficulty.value}`;
    }

    const response = await fetch(url);
    const data = await response.json();
    questions.value = data.questions || [];
    searched.value = true;
    selectedQuestionId.value = null;
    selectedQuestion.value = null;
  } catch (error) {
    console.error('搜尋題目失敗:', error);
  }
};

// 選擇題目
const selectQuestion = (question) => {
  selectedQuestionId.value = question.id;
  selectedQuestion.value = question;
  showSolution.value = false;
  similarQuestions.value = [];
};

// 獲取類似題
const getSimilarQuestions = async () => {
  if (!selectedQuestion.value) return;

  try {
    const response = await fetch(`/api/questions/${selectedQuestion.value.id}/similar`);
    const data = await response.json();
    similarQuestions.value = data.similarQuestions || [];
  } catch (error) {
    console.error('獲取類似題失敗:', error);
  }
};

// 開始講題
const startTeaching = () => {
  router.push({
    name: 'teaching-mode',
    query: { questionId: selectedQuestion.value.id }
  });
};

// 完成講題
const finishTeaching = () => {
  showMistakeReasonModal.value = true;
  selectedReason.value = null;
  otherReasonText.value = '';
};

// 選擇錯題原因
const selectMistakeReason = (reason) => {
  selectedReason.value = reason;
};

// 保存錯題原因
const saveMistakeReason = async () => {
  if (!selectedReason.value) return;

  try {
    await fetch('/api/student/mistake-reasons', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'user-id': sessionStore.userId
      },
      body: JSON.stringify({
        question_id: selectedQuestion.value.id,
        reason_type: selectedReason.value,
        reason_description: otherReasonText.value
      })
    });

    showMistakeReasonModal.value = false;
    alert('講題記錄已保存！');
  } catch (error) {
    console.error('保存失敗:', error);
  }
};

// 清除白板
const clearWhiteboard = () => {
  // 通過 ref 調用白板的清除方法
  const canvas = document.querySelector('canvas');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }
};

// 輔助函數
const truncate = (text, length) => {
  return text.length > length ? text.substring(0, length) + '...' : text;
};

const difficultyLabel = (difficulty) => {
  const labels = { easy: '簡單', medium: '中等', hard: '困難' };
  return labels[difficulty] || difficulty;
};

onMounted(() => {
  onSubjectChange();
});
</script>

<style scoped>
.question-search-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.page-header {
  padding: 2rem;
  color: white;
}

.page-header h1 {
  margin: 0;
  font-size: 2rem;
}

.page-header p {
  margin: 0.5rem 0 0 0;
  opacity: 0.9;
}

.search-layout {
  display: grid;
  grid-template-columns: 350px 1fr;
  gap: 1.5rem;
  flex: 1;
  padding: 1.5rem;
  overflow: hidden;
}

/* 左側搜題面板 */
.search-panel {
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.search-controls {
  padding: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #333;
  font-size: 0.9rem;
}

.select-input {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.95rem;
  transition: all 0.3s ease;
}

.select-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.search-btn {
  width: 100%;
  padding: 0.75rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.search-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
}

.search-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.questions-list {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

.question-item {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: all 0.3s ease;
}

.question-item:hover {
  background: #f8f9ff;
  border-left: 4px solid #667eea;
  padding-left: calc(1.5rem - 4px);
}

.question-item.active {
  background: #f0f2ff;
  border-left: 4px solid #667eea;
  padding-left: calc(1.5rem - 4px);
}

.question-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.difficulty-badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  text-transform: uppercase;
}

.diff-easy {
  background: #d4edda;
  color: #155724;
}

.diff-medium {
  background: #fff3cd;
  color: #856404;
}

.diff-hard {
  background: #f8d7da;
  color: #721c24;
}

.question-number {
  font-size: 0.85rem;
  color: #999;
}

.question-preview {
  margin: 0;
  font-size: 0.9rem;
  color: #666;
  line-height: 1.4;
}

.no-results {
  padding: 2rem 1.5rem;
  text-align: center;
  color: #999;
}

/* 右側教學區域 */
.teaching-area {
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.question-display {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 1.5rem;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f0f0f0;
}

.question-header h3 {
  margin: 0;
  color: #333;
}

.question-content {
  margin-bottom: 1.5rem;
}

.question-text {
  font-size: 1.1rem;
  line-height: 1.6;
  color: #333;
  margin-bottom: 1rem;
}

.question-image {
  text-align: center;
  margin-bottom: 1rem;
}

.question-image img {
  max-width: 100%;
  height: auto;
  border-radius: 6px;
}

.teaching-controls {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.teach-btn,
.solution-btn,
.similar-btn {
  flex: 1;
  padding: 0.75rem;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.teach-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.teach-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
}

.solution-btn,
.similar-btn {
  background: #f0f0f0;
  color: #333;
}

.solution-btn:hover,
.similar-btn:hover {
  background: #e0e0e0;
}

.solution-box {
  background: #f8f9ff;
  padding: 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
}

.solution-box h4 {
  margin: 0 0 0.5rem 0;
  color: #667eea;
  font-size: 0.95rem;
}

.solution-box p {
  margin: 0 0 1rem 0;
  color: #666;
  line-height: 1.6;
}

.similar-questions {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 2px solid #f0f0f0;
}

.similar-questions h4 {
  margin: 0 0 1rem 0;
  color: #333;
}

.similar-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.similar-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f8f9ff;
  border: 2px solid #e8eaff;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;
}

.similar-item:hover {
  border-color: #667eea;
  background: #f0f2ff;
}

.similar-preview {
  flex: 1;
  text-align: left;
  color: #666;
}

.ai-badge {
  background: #667eea;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  font-size: 0.75rem;
  font-weight: 600;
}

.no-question-selected {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: #999;
  font-size: 1.1rem;
}

.whiteboard-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-top: 1px solid #f0f0f0;
  padding: 1rem;
}

.whiteboard-section h4 {
  margin: 0 0 1rem 0;
  color: #333;
}

.whiteboard-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
}

.action-btn {
  flex: 1;
  padding: 0.75rem;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #f0f0f0;
  color: #333;
}

.action-btn:hover {
  background: #e0e0e0;
}

.action-btn.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.action-btn.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
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
  padding: 2rem;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal h3 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.modal p {
  margin: 0 0 1.5rem 0;
  color: #666;
}

.reason-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.reason-btn {
  padding: 0.75rem;
  background: #f0f0f0;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 500;
  font-size: 0.9rem;
}

.reason-btn:hover {
  border-color: #667eea;
  background: #f8f9ff;
}

.other-reason {
  margin-bottom: 1rem;
}

.other-reason textarea {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  font-family: inherit;
  font-size: 0.9rem;
  resize: none;
}

.other-reason textarea:focus {
  outline: none;
  border-color: #667eea;
}

.modal-actions {
  display: flex;
  gap: 1rem;
}

.cancel-btn,
.confirm-btn {
  flex: 1;
  padding: 0.75rem;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cancel-btn {
  background: #f0f0f0;
  color: #333;
}

.cancel-btn:hover {
  background: #e0e0e0;
}

.confirm-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.confirm-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
}

@media (max-width: 1024px) {
  .search-layout {
    grid-template-columns: 1fr;
  }
}
</style>
