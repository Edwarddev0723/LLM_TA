<template>
  <div class="practice-root">
    <!-- Setup Screen -->
    <div v-if="!sessionStarted" class="setup-screen">
      <header class="setup-header">
        <h1>✍️ 做題模式</h1>
        <p>選擇練習範圍，開始你的數學練習！</p>
      </header>

      <div class="setup-form">
        <!-- Grade Selection -->
        <div class="form-section">
          <label class="form-label">📚 年級/程度</label>
          <div class="option-group">
            <button 
              v-for="grade in grades" 
              :key="grade.id"
              :class="{ active: selectedGrade === grade.id }"
              @click="selectedGrade = grade.id"
            >
              {{ grade.name }}
            </button>
          </div>
        </div>

        <!-- Topic Selection -->
        <div class="form-section">
          <label class="form-label">📐 範圍（可多選）</label>
          <div class="topic-grid">
            <button 
              v-for="topic in topics" 
              :key="topic.id"
              :class="{ active: selectedTopics.includes(topic.id) }"
              @click="toggleTopic(topic.id)"
            >
              {{ topic.name }}
            </button>
          </div>
        </div>

        <!-- Difficulty Selection -->
        <div class="form-section">
          <label class="form-label">⭐ 難度 ({{ difficultyLabel }})</label>
          <div class="difficulty-slider">
            <input 
              type="range" 
              v-model.number="selectedDifficulty" 
              min="1" 
              max="5" 
              step="1"
            />
            <div class="difficulty-marks">
              <span v-for="i in 5" :key="i" :class="{ active: selectedDifficulty >= i }">
                {{ i }}
              </span>
            </div>
          </div>
        </div>

        <!-- Topic Weights (Optional) -->
        <div class="form-section" v-if="selectedTopics.length > 1">
          <label class="form-label">📊 題型比例</label>
          <div class="weight-sliders">
            <div v-for="topic in selectedTopics" :key="topic" class="weight-item">
              <span class="weight-label">{{ getTopicName(topic) }}</span>
              <input 
                type="range" 
                v-model.number="topicWeights[topic]" 
                min="0" 
                max="100" 
                step="10"
              />
              <span class="weight-value">{{ topicWeights[topic] || 0 }}%</span>
            </div>
          </div>
        </div>

        <button class="start-btn" @click="startPractice" :disabled="!canStart || isLoading">
          {{ isLoading ? '載入中...' : '🎯 開始練習 (10題)' }}
        </button>
      </div>
    </div>

    <!-- Practice Screen -->
    <div v-else-if="!showResults" class="practice-screen">
      <header class="practice-header">
        <button class="exit-btn" @click="exitPractice">← 退出</button>
        <div class="progress-info">
          <span class="progress-text">第 {{ currentIndex + 1 }} / {{ questions.length }} 題</span>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
          </div>
        </div>
        <div class="timer" v-if="elapsedTime">
          ⏱️ {{ formatTime(elapsedTime) }}
        </div>
      </header>

      <div class="practice-main">
        <!-- Left: Question Panel -->
        <aside class="question-panel">
          <div class="question-card">
            <div class="question-meta">
              <span class="topic-badge">{{ currentQuestion?.topic_name }}</span>
              <span class="difficulty-badge">
                難度 {{ '⭐'.repeat(currentQuestion?.difficulty || 1) }}
              </span>
            </div>
            <div class="question-text">
              {{ currentQuestion?.question }}
            </div>
            <div class="options-list">
              <button 
                v-for="(option, idx) in currentQuestion?.options" 
                :key="idx"
                class="option-btn"
                :class="{ 
                  selected: selectedAnswer === optionLabels[idx],
                  correct: showAnswer && optionLabels[idx] === correctAnswer,
                  wrong: showAnswer && selectedAnswer === optionLabels[idx] && selectedAnswer !== correctAnswer
                }"
                @click="selectOption(optionLabels[idx])"
                :disabled="showAnswer"
              >
                <span class="option-label">{{ optionLabels[idx] }}</span>
                <span class="option-text">{{ option }}</span>
              </button>
            </div>

            <!-- Reasoning Input -->
            <div class="reasoning-section">
              <label class="reasoning-label">
                💭 解題邏輯（選填，AI 會根據你的邏輯評分）
              </label>
              <textarea 
                v-model="currentReasoning"
                placeholder="寫下你的解題思路..."
                rows="3"
                :disabled="showAnswer"
              ></textarea>
            </div>

            <!-- Action Buttons -->
            <div class="question-actions">
              <button 
                v-if="!showAnswer"
                class="submit-btn"
                @click="submitAnswer"
                :disabled="!selectedAnswer"
              >
                確認答案
              </button>
              <button 
                v-else
                class="next-btn"
                @click="nextQuestion"
              >
                {{ isLastQuestion ? '查看結果' : '下一題 →' }}
              </button>
            </div>

            <!-- Answer Feedback -->
            <div v-if="showAnswer" class="answer-feedback" :class="isCorrect ? 'correct' : 'wrong'">
              <div class="feedback-header">
                {{ isCorrect ? '✅ 答對了！' : '❌ 答錯了' }}
              </div>
              <div class="feedback-body">
                <p><strong>正確答案：</strong>{{ correctAnswer }}</p>
                <p><strong>解釋：</strong>{{ currentExplanation }}</p>
              </div>
            </div>
          </div>
        </aside>

        <!-- Right: Whiteboard -->
        <main class="whiteboard-panel">
          <WhiteboardCanvas ref="whiteboardRef" />
        </main>
      </div>
    </div>

    <!-- Results Screen -->
    <div v-else class="results-screen">
      <header class="results-header">
        <h1>📊 練習結果</h1>
        <div class="score-circle" :class="scoreClass">
          <span class="score-value">{{ Math.round(results?.score || 0) }}</span>
          <span class="score-label">分</span>
        </div>
      </header>

      <div class="results-summary">
        <div class="summary-card">
          <span class="summary-icon">✅</span>
          <span class="summary-value">{{ results?.correct_count || 0 }}</span>
          <span class="summary-label">答對</span>
        </div>
        <div class="summary-card">
          <span class="summary-icon">❌</span>
          <span class="summary-value">{{ (results?.total_questions || 0) - (results?.correct_count || 0) }}</span>
          <span class="summary-label">答錯</span>
        </div>
        <div class="summary-card">
          <span class="summary-icon">⏱️</span>
          <span class="summary-value">{{ formatTime(results?.time_spent_seconds || 0) }}</span>
          <span class="summary-label">用時</span>
        </div>
      </div>

      <div class="feedback-section">
        <h3>💬 AI 評語</h3>
        <p class="overall-feedback">{{ results?.overall_feedback }}</p>
      </div>

      <!-- Topic Breakdown -->
      <div class="topic-breakdown" v-if="results?.topic_breakdown">
        <h3>📐 各範圍表現</h3>
        <div class="topic-bars">
          <div v-for="(stats, topic) in results.topic_breakdown" :key="topic" class="topic-bar-item">
            <span class="topic-name">{{ stats.name }}</span>
            <div class="topic-bar-bg">
              <div 
                class="topic-bar-fill" 
                :style="{ width: stats.accuracy + '%' }"
                :class="getAccuracyClass(stats.accuracy)"
              ></div>
            </div>
            <span class="topic-accuracy">{{ stats.accuracy }}%</span>
          </div>
        </div>
      </div>

      <!-- Detailed Results -->
      <div class="detailed-results">
        <h3>📝 詳細結果</h3>
        <div class="result-list">
          <div 
            v-for="(result, idx) in results?.results" 
            :key="idx"
            class="result-item"
            :class="result.is_correct ? 'correct' : 'wrong'"
          >
            <div class="result-header">
              <span class="result-number">第 {{ idx + 1 }} 題</span>
              <span class="result-status">{{ result.is_correct ? '✅ 正確' : '❌ 錯誤' }}</span>
            </div>
            <div class="result-body">
              <p class="result-question">{{ questions[idx]?.question }}</p>
              <p class="result-answer">
                你的答案：<strong>{{ result.selected_answer }}</strong>
                <span v-if="!result.is_correct">（正確：{{ result.correct_answer }}）</span>
              </p>
              <p class="result-explanation">{{ result.explanation }}</p>
              
              <!-- Reasoning Feedback -->
              <div v-if="result.reasoning_score !== null" class="reasoning-result">
                <p class="reasoning-score">解題邏輯評分：<strong>{{ result.reasoning_score }}</strong>/100</p>
                <p class="reasoning-feedback">{{ result.reasoning_feedback }}</p>
              </div>
              
              <!-- AI Solution -->
              <div v-if="result.ai_solution" class="ai-solution">
                <p class="ai-solution-label">🤖 AI 解題：</p>
                <p class="ai-solution-text">{{ result.ai_solution }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="results-actions">
        <button class="retry-btn" @click="resetPractice">🔄 再練一次</button>
        <button class="home-btn" @click="goHome">🏠 返回首頁</button>
      </div>
    </div>

    <!-- Loading Overlay -->
    <div v-if="isSubmitting" class="loading-overlay">
      <div class="loading-content">
        <div class="spinner"></div>
        <p>AI 正在評估你的答案...</p>
      </div>
    </div>

    <!-- Error Toast -->
    <div v-if="errorMessage" class="error-toast" @click="errorMessage = ''">
      {{ errorMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import WhiteboardCanvas from '@/components/teaching/WhiteboardCanvas.vue';

const router = useRouter();

// Refs
const whiteboardRef = ref(null);

// State - Setup
const grades = ref([]);
const topics = ref([]);
const selectedGrade = ref('junior');
const selectedTopics = ref(['algebra', 'geometry']);
const selectedDifficulty = ref(3);
const topicWeights = ref({});
const isLoading = ref(false);
const errorMessage = ref('');

// State - Practice
const sessionStarted = ref(false);
const sessionId = ref('');
const questions = ref([]);
const currentIndex = ref(0);
const selectedAnswer = ref('');
const currentReasoning = ref('');
const showAnswer = ref(false);
const answers = ref([]);
const startTime = ref(null);
const elapsedTime = ref(0);
let timerInterval = null;

// State - Results
const showResults = ref(false);
const results = ref(null);
const isSubmitting = ref(false);
const currentAnswerResult = ref(null);

// Constants
const optionLabels = ['A', 'B', 'C', 'D'];
const difficultyLabels = ['非常簡單', '簡單', '中等', '困難', '非常困難'];

// Computed
const difficultyLabel = computed(() => difficultyLabels[selectedDifficulty.value - 1]);

const canStart = computed(() => selectedTopics.value.length > 0);

const currentQuestion = computed(() => questions.value[currentIndex.value] || null);

const correctAnswer = computed(() => currentAnswerResult.value?.correct_answer || '');

const currentExplanation = computed(() => currentAnswerResult.value?.explanation || '');

const isCorrect = computed(() => currentAnswerResult.value?.is_correct || false);

const isLastQuestion = computed(() => currentIndex.value >= questions.value.length - 1);

const progressPercent = computed(() => {
  if (questions.value.length === 0) return 0;
  return ((currentIndex.value + 1) / questions.value.length) * 100;
});

const scoreClass = computed(() => {
  const score = results.value?.score || 0;
  if (score >= 80) return 'excellent';
  if (score >= 60) return 'good';
  if (score >= 40) return 'fair';
  return 'poor';
});

// Methods
function getTopicName(topicId) {
  const topic = topics.value.find(t => t.id === topicId);
  return topic ? topic.name : topicId;
}

function toggleTopic(topicId) {
  const idx = selectedTopics.value.indexOf(topicId);
  if (idx >= 0) {
    selectedTopics.value.splice(idx, 1);
    delete topicWeights.value[topicId];
  } else {
    selectedTopics.value.push(topicId);
    topicWeights.value[topicId] = Math.floor(100 / (selectedTopics.value.length));
  }
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function getAccuracyClass(accuracy) {
  if (accuracy >= 80) return 'excellent';
  if (accuracy >= 60) return 'good';
  if (accuracy >= 40) return 'fair';
  return 'poor';
}

function selectOption(label) {
  if (!showAnswer.value) {
    selectedAnswer.value = label;
  }
}

// API Methods
async function fetchTopics() {
  try {
    const res = await fetch('/api/practice/topics');
    if (!res.ok) throw new Error('Failed to fetch topics');
    const data = await res.json();
    topics.value = data.topics || [];
    grades.value = data.grades || [];
  } catch (err) {
    console.error('Error fetching topics:', err);
    errorMessage.value = '無法載入題目範圍';
  }
}

async function startPractice() {
  if (!canStart.value) return;
  
  isLoading.value = true;
  errorMessage.value = '';
  
  try {
    const config = {
      grade: selectedGrade.value,
      topics: selectedTopics.value,
      difficulty: selectedDifficulty.value,
      question_count: 10
    };
    
    if (selectedTopics.value.length > 1 && Object.keys(topicWeights.value).length > 0) {
      const normalizedWeights = {};
      const total = Object.values(topicWeights.value).reduce((a, b) => a + b, 0) || 100;
      for (const [k, v] of Object.entries(topicWeights.value)) {
        normalizedWeights[k] = v / total;
      }
      config.topic_weights = normalizedWeights;
    }
    
    const res = await fetch('/api/practice/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to start practice');
    }
    
    const data = await res.json();
    sessionId.value = data.session_id;
    questions.value = data.questions;
    sessionStarted.value = true;
    startTime.value = Date.now();
    startTimer();
  } catch (err) {
    console.error('Error starting practice:', err);
    errorMessage.value = err.message || '無法開始練習';
  } finally {
    isLoading.value = false;
  }
}

async function submitAnswer() {
  if (!selectedAnswer.value) return;
  
  try {
    // Check answer via API
    const res = await fetch('/api/practice/check-answer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId.value,
        question_id: currentQuestion.value.id,
        selected_option: selectedAnswer.value
      })
    });
    
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to check answer');
    }
    
    currentAnswerResult.value = await res.json();
    
    // Store answer for final submission
    answers.value.push({
      question_id: currentQuestion.value.id,
      selected_option: selectedAnswer.value,
      reasoning: currentReasoning.value || null
    });
    
    showAnswer.value = true;
  } catch (err) {
    console.error('Error checking answer:', err);
    errorMessage.value = err.message || '驗證答案失敗';
  }
}

function nextQuestion() {
  if (isLastQuestion.value) {
    submitAllAnswers();
  } else {
    currentIndex.value++;
    selectedAnswer.value = '';
    currentReasoning.value = '';
    showAnswer.value = false;
    currentAnswerResult.value = null;
    
    // Clear whiteboard for next question (silent, no confirmation)
    if (whiteboardRef.value) {
      whiteboardRef.value.clearCanvasSilent();
    }
  }
}

async function submitAllAnswers() {
  isSubmitting.value = true;
  stopTimer();
  
  try {
    const res = await fetch('/api/practice/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId.value,
        answers: answers.value
      })
    });
    
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to submit answers');
    }
    
    results.value = await res.json();
    showResults.value = true;
  } catch (err) {
    console.error('Error submitting answers:', err);
    errorMessage.value = err.message || '提交失敗';
  } finally {
    isSubmitting.value = false;
  }
}

function startTimer() {
  timerInterval = setInterval(() => {
    elapsedTime.value = Math.floor((Date.now() - startTime.value) / 1000);
  }, 1000);
}

function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
}

function exitPractice() {
  if (confirm('確定要退出練習嗎？進度將不會保存。')) {
    resetPractice();
  }
}

function resetPractice() {
  stopTimer();
  sessionStarted.value = false;
  sessionId.value = '';
  questions.value = [];
  currentIndex.value = 0;
  selectedAnswer.value = '';
  currentReasoning.value = '';
  showAnswer.value = false;
  answers.value = [];
  showResults.value = false;
  results.value = null;
  elapsedTime.value = 0;
  currentAnswerResult.value = null;
}

function goHome() {
  router.push('/student/dashboard');
}

// Lifecycle
onMounted(() => {
  fetchTopics();
});

onUnmounted(() => {
  stopTimer();
});
</script>

<style scoped>
.practice-root {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  color: #e5e7eb;
}

/* Setup Screen */
.setup-screen {
  max-width: 600px;
  margin: 0 auto;
  padding: 2rem;
}

.setup-header {
  text-align: center;
  margin-bottom: 2rem;
}

.setup-header h1 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.setup-header p {
  color: #94a3b8;
}

.setup-form {
  background: rgba(30, 41, 59, 0.8);
  border-radius: 1rem;
  padding: 1.5rem;
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.form-section {
  margin-bottom: 1.5rem;
}

.form-label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.75rem;
  color: #f1f5f9;
}

.option-group {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.option-group button,
.topic-grid button {
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: rgba(15, 23, 42, 0.6);
  color: #e5e7eb;
  cursor: pointer;
  transition: all 0.2s;
}

.option-group button:hover,
.topic-grid button:hover {
  border-color: #3b82f6;
}

.option-group button.active,
.topic-grid button.active {
  background: rgba(59, 130, 246, 0.3);
  border-color: #3b82f6;
  color: #93c5fd;
}

.topic-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
}

.difficulty-slider {
  padding: 0 0.5rem;
}

.difficulty-slider input[type="range"] {
  width: 100%;
  margin-bottom: 0.5rem;
}

.difficulty-marks {
  display: flex;
  justify-content: space-between;
}

.difficulty-marks span {
  color: #64748b;
  font-size: 0.875rem;
}

.difficulty-marks span.active {
  color: #fbbf24;
}

.weight-sliders {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.weight-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.weight-label {
  width: 80px;
  font-size: 0.875rem;
}

.weight-item input[type="range"] {
  flex: 1;
}

.weight-value {
  width: 50px;
  text-align: right;
  font-size: 0.875rem;
  color: #94a3b8;
}

.start-btn {
  width: 100%;
  padding: 1rem;
  font-size: 1.125rem;
  font-weight: 600;
  border-radius: 0.75rem;
  border: none;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 1rem;
}

.start-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.start-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Practice Screen */
.practice-screen {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.practice-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
  background: rgba(15, 23, 42, 0.9);
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
}

.exit-btn {
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: transparent;
  color: #e5e7eb;
  cursor: pointer;
}

.exit-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: #ef4444;
}

.progress-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.progress-text {
  font-weight: 500;
  white-space: nowrap;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: rgba(148, 163, 184, 0.2);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
  transition: width 0.3s;
}

.timer {
  font-weight: 500;
  color: #94a3b8;
}

.practice-main {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  padding: 1rem;
  overflow: hidden;
}

.question-panel {
  overflow-y: auto;
}

.question-card {
  background: rgba(30, 41, 59, 0.8);
  border-radius: 1rem;
  padding: 1.5rem;
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.question-meta {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.topic-badge {
  padding: 0.25rem 0.75rem;
  background: rgba(59, 130, 246, 0.2);
  border-radius: 999px;
  font-size: 0.875rem;
  color: #93c5fd;
}

.difficulty-badge {
  padding: 0.25rem 0.75rem;
  background: rgba(251, 191, 36, 0.2);
  border-radius: 999px;
  font-size: 0.875rem;
  color: #fcd34d;
}

.question-text {
  font-size: 1.125rem;
  line-height: 1.6;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: rgba(15, 23, 42, 0.5);
  border-radius: 0.5rem;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.option-btn {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-radius: 0.75rem;
  border: 2px solid rgba(148, 163, 184, 0.3);
  background: rgba(15, 23, 42, 0.5);
  color: #e5e7eb;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.option-btn:hover:not(:disabled) {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.1);
}

.option-btn.selected {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.2);
}

.option-btn.correct {
  border-color: #22c55e;
  background: rgba(34, 197, 94, 0.2);
}

.option-btn.wrong {
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.2);
}

.option-btn:disabled {
  cursor: default;
}

.option-label {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(148, 163, 184, 0.2);
  border-radius: 50%;
  font-weight: 600;
}

.option-text {
  flex: 1;
}

.reasoning-section {
  margin-bottom: 1.5rem;
}

.reasoning-label {
  display: block;
  font-size: 0.875rem;
  color: #94a3b8;
  margin-bottom: 0.5rem;
}

.reasoning-section textarea {
  width: 100%;
  padding: 0.75rem;
  border-radius: 0.5rem;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: rgba(15, 23, 42, 0.5);
  color: #e5e7eb;
  resize: vertical;
  font-family: inherit;
}

.reasoning-section textarea:focus {
  outline: none;
  border-color: #3b82f6;
}

.question-actions {
  display: flex;
  gap: 1rem;
}

.submit-btn,
.next-btn {
  flex: 1;
  padding: 0.875rem;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 0.75rem;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.submit-btn {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.next-btn {
  background: linear-gradient(135deg, #22c55e, #16a34a);
  color: white;
}

.next-btn:hover {
  transform: translateY(-2px);
}

.answer-feedback {
  margin-top: 1.5rem;
  padding: 1rem;
  border-radius: 0.75rem;
}

.answer-feedback.correct {
  background: rgba(34, 197, 94, 0.15);
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.answer-feedback.wrong {
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.feedback-header {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
}

.feedback-body p {
  margin: 0.5rem 0;
  line-height: 1.5;
}

.whiteboard-panel {
  border-radius: 1rem;
  overflow: hidden;
}

/* Results Screen */
.results-screen {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

.results-header {
  text-align: center;
  margin-bottom: 2rem;
}

.results-header h1 {
  font-size: 1.75rem;
  margin-bottom: 1.5rem;
}

.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  border: 4px solid;
}

.score-circle.excellent {
  border-color: #22c55e;
  background: rgba(34, 197, 94, 0.15);
}

.score-circle.good {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.15);
}

.score-circle.fair {
  border-color: #f59e0b;
  background: rgba(245, 158, 11, 0.15);
}

.score-circle.poor {
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.15);
}

.score-value {
  font-size: 2.5rem;
  font-weight: 700;
}

.score-label {
  font-size: 0.875rem;
  color: #94a3b8;
}

.results-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 2rem;
}

.summary-card {
  background: rgba(30, 41, 59, 0.8);
  border-radius: 0.75rem;
  padding: 1rem;
  text-align: center;
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.summary-icon {
  font-size: 1.5rem;
  display: block;
  margin-bottom: 0.5rem;
}

.summary-value {
  font-size: 1.5rem;
  font-weight: 700;
  display: block;
}

.summary-label {
  font-size: 0.875rem;
  color: #94a3b8;
}

.feedback-section {
  background: rgba(30, 41, 59, 0.8);
  border-radius: 0.75rem;
  padding: 1.25rem;
  margin-bottom: 2rem;
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.feedback-section h3 {
  margin-bottom: 0.75rem;
}

.overall-feedback {
  color: #94a3b8;
  line-height: 1.6;
}

.topic-breakdown {
  background: rgba(30, 41, 59, 0.8);
  border-radius: 0.75rem;
  padding: 1.25rem;
  margin-bottom: 2rem;
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.topic-breakdown h3 {
  margin-bottom: 1rem;
}

.topic-bars {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.topic-bar-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.topic-name {
  width: 80px;
  font-size: 0.875rem;
}

.topic-bar-bg {
  flex: 1;
  height: 12px;
  background: rgba(148, 163, 184, 0.2);
  border-radius: 6px;
  overflow: hidden;
}

.topic-bar-fill {
  height: 100%;
  border-radius: 6px;
  transition: width 0.5s;
}

.topic-bar-fill.excellent {
  background: linear-gradient(90deg, #22c55e, #16a34a);
}

.topic-bar-fill.good {
  background: linear-gradient(90deg, #3b82f6, #2563eb);
}

.topic-bar-fill.fair {
  background: linear-gradient(90deg, #f59e0b, #d97706);
}

.topic-bar-fill.poor {
  background: linear-gradient(90deg, #ef4444, #dc2626);
}

.topic-accuracy {
  width: 50px;
  text-align: right;
  font-size: 0.875rem;
  font-weight: 500;
}

.detailed-results {
  background: rgba(30, 41, 59, 0.8);
  border-radius: 0.75rem;
  padding: 1.25rem;
  margin-bottom: 2rem;
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.detailed-results h3 {
  margin-bottom: 1rem;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.result-item {
  padding: 1rem;
  border-radius: 0.75rem;
  border: 1px solid;
}

.result-item.correct {
  border-color: rgba(34, 197, 94, 0.3);
  background: rgba(34, 197, 94, 0.05);
}

.result-item.wrong {
  border-color: rgba(239, 68, 68, 0.3);
  background: rgba(239, 68, 68, 0.05);
}

.result-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.result-number {
  font-weight: 600;
}

.result-body p {
  margin: 0.5rem 0;
  line-height: 1.5;
}

.result-question {
  color: #f1f5f9;
}

.result-answer {
  color: #94a3b8;
}

.result-explanation {
  color: #94a3b8;
  font-size: 0.875rem;
}

.reasoning-result {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 0.5rem;
}

.reasoning-score {
  color: #a78bfa;
}

.reasoning-feedback {
  font-size: 0.875rem;
  color: #94a3b8;
}

.ai-solution {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: rgba(59, 130, 246, 0.1);
  border-radius: 0.5rem;
}

.ai-solution-label {
  color: #93c5fd;
  font-weight: 500;
}

.ai-solution-text {
  font-size: 0.875rem;
  color: #94a3b8;
}

.results-actions {
  display: flex;
  gap: 1rem;
}

.retry-btn,
.home-btn {
  flex: 1;
  padding: 1rem;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 0.75rem;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.retry-btn {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
}

.home-btn {
  background: rgba(148, 163, 184, 0.2);
  color: #e5e7eb;
  border: 1px solid rgba(148, 163, 184, 0.3);
}

.retry-btn:hover,
.home-btn:hover {
  transform: translateY(-2px);
}

/* Loading Overlay */
.loading-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.loading-content {
  text-align: center;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(59, 130, 246, 0.2);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error Toast */
.error-toast {
  position: fixed;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  background: #ef4444;
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  cursor: pointer;
  z-index: 100;
}

/* Responsive */
@media (max-width: 768px) {
  .practice-main {
    grid-template-columns: 1fr;
    grid-template-rows: 1fr 1fr;
  }

  .topic-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .results-summary {
    grid-template-columns: repeat(3, 1fr);
  }

  .results-actions {
    flex-direction: column;
  }
}

@media (max-width: 480px) {
  .setup-screen,
  .results-screen {
    padding: 1rem;
  }

  .topic-grid {
    grid-template-columns: 1fr 1fr;
  }

  .question-card {
    padding: 1rem;
  }

  .option-btn {
    padding: 0.75rem;
  }
}
</style>
