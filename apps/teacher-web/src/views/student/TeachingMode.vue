<template>
  <div class="teaching-root">
    <!-- Question Selection Modal -->
    <div v-if="showQuestionModal" class="modal-overlay" @click.self="showQuestionModal = false">
      <div class="question-modal">
        <div class="modal-header">
          <h2>選擇題目</h2>
          <button class="close-btn" @click="showQuestionModal = false">✕</button>
        </div>
        <div class="modal-filters">
          <select v-model="questionFilter.subject" class="filter-select">
            <option value="">全部科目</option>
            <option value="代數">代數</option>
            <option value="幾何">幾何</option>
            <option value="統計">統計</option>
          </select>
          <select v-model="questionFilter.difficulty" class="filter-select">
            <option value="">全部難度</option>
            <option value="基礎">基礎</option>
            <option value="中等">中等</option>
            <option value="進階">進階</option>
          </select>
        </div>
        <div class="question-list" v-if="!questionsLoading">
          <div 
            v-for="q in filteredQuestions" 
            :key="q.id" 
            class="question-item"
            :class="{ selected: currentProblem.id === q.id }"
            @click="selectQuestion(q)"
          >
            <div class="question-text">{{ q.content || q.text }}</div>
            <div class="question-meta">
              <span class="tag subject">{{ q.subject || '數學' }}</span>
              <span class="tag difficulty" :class="q.difficulty?.toLowerCase()">{{ q.difficulty || '基礎' }}</span>
            </div>
          </div>
          <div v-if="filteredQuestions.length === 0" class="no-questions">
            暫無題目
          </div>
        </div>
        <div v-else class="loading-questions">
          載入題目中...
        </div>
      </div>
    </div>

    <!-- Global Header with FSM State -->
    <header class="teaching-header">
      <div class="header-left">
        <button class="exit-btn" @click="exitTeaching">← 退出</button>
        <span class="phase-badge" :class="fsmStateClass">{{ fsmStateLabel }}</span>
      </div>
      <div class="header-center">
        <h1 class="title">講題模式</h1>
      </div>
      <div class="header-right">
        <div class="status-indicator" :class="status">
          <span class="status-dot"></span>
          <span class="status-text">{{ statusLabels[status] }}</span>
        </div>
      </div>
    </header>

    <!-- Main Two-Column Layout -->
    <div class="teaching-main">
      <!-- Left Sidebar: Problem + Chat -->
      <aside class="left-sidebar">
        <!-- Problem Statement Section -->
        <section class="problem-section">
          <div class="section-header">
            <span class="section-icon">📝</span>
            <span class="section-title">題目</span>
            <button 
              class="select-question-btn" 
              @click="openQuestionModal"
              :disabled="!!sessionId"
              :title="sessionId ? '請先結束當前講題' : '選擇題目'"
            >
              📋 選擇題目
            </button>
          </div>
          <div class="problem-content">
            <div class="problem-text">
              {{ currentProblem.text }}
            </div>
            <div class="problem-meta" v-if="currentProblem.subject">
              <span class="meta-tag">{{ currentProblem.subject }}</span>
              <span class="meta-tag">{{ currentProblem.difficulty }}</span>
            </div>
          </div>
        </section>

        <!-- AI Chat Section -->
        <section class="chat-section">
          <div class="section-header">
            <span class="section-icon">💬</span>
            <span class="section-title">AI 對話</span>
            <span class="coverage-badge" v-if="conceptCoverage > 0">
              完成度: {{ Math.round(conceptCoverage * 100) }}%
            </span>
          </div>
          <div class="chat-messages" ref="chatContainer">
            <div 
              v-for="(msg, idx) in chatMessages" 
              :key="idx" 
              class="chat-message"
              :class="msg.role"
            >
              <div class="message-avatar">
                {{ msg.role === 'ai' ? '🤖' : '👤' }}
              </div>
              <div class="message-content">
                <div v-if="msg.role === 'ai'" class="message-text markdown-content" v-html="renderMarkdown(msg.text)"></div>
                <p v-else class="message-text">{{ msg.text }}</p>
                <span class="message-time">{{ msg.time }}</span>
                <span class="message-type" v-if="msg.responseType">{{ msg.responseType }}</span>
              </div>
            </div>
            <!-- Typing indicator -->
            <div v-if="status === 'processing'" class="chat-message ai typing">
              <div class="message-avatar">🤖</div>
              <div class="message-content">
                <div class="typing-dots">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          </div>
          <!-- Chat Input -->
          <div class="chat-input-area">
            <button 
              class="voice-btn" 
              :class="{ active: isRecording, loading: asrLoading && !asrReady }"
              @click="toggleRecording"
              :disabled="!sessionId || status === 'processing' || (asrLoading && !asrReady)"
              :title="asrLoading && !asrReady ? 'ASR 模型載入中...' : (isRecording ? '點擊停止錄音' : '點擊開始錄音')"
            >
              <span v-if="asrLoading && !asrReady" class="loading-spinner">⏳</span>
              <span v-else>{{ isRecording ? '⏹️' : '🎙️' }}</span>
            </button>
            <div v-if="isRecording" class="recording-indicator">
              <span class="recording-dot"></span>
              <span class="recording-text">錄音中...</span>
            </div>
            <div v-else-if="asrLoading && !asrReady" class="asr-loading-indicator">
              <span class="loading-text">語音辨識載入中...</span>
            </div>
            <input 
              v-else
              type="text" 
              v-model="userInput"
              placeholder="輸入訊息或按住麥克風說話..."
              @keyup.enter="sendMessage"
              class="chat-input"
              :disabled="!sessionId || status === 'processing'"
            />
            <button 
              class="send-btn" 
              @click="sendMessage" 
              :disabled="!userInput.trim() || !sessionId || status === 'processing' || isRecording"
            >
              發送
            </button>
          </div>
        </section>
      </aside>

      <!-- Right Main Panel: Whiteboard -->
      <main class="right-panel">
        <WhiteboardCanvas 
          ref="whiteboardRef"
          :mode="fsmState === 'REPAIR' ? 'repair' : 'normal'" 
          :sessionId="sessionId"
          @save="onWhiteboardSave"
          @load="onWhiteboardLoad"
        />
      </main>
    </div>

    <!-- Session Controls -->
    <div class="session-controls">
      <button 
        v-if="!sessionId" 
        class="start-btn" 
        @click="startSession"
        :disabled="isLoading"
      >
        🎯 開始講題
      </button>
      <button 
        v-else 
        class="end-btn" 
        @click="endSession"
        :disabled="isLoading"
      >
        ✅ 結束講題
      </button>
    </div>

    <!-- Error Toast -->
    <div v-if="errorMessage" class="error-toast" @click="errorMessage = ''">
      {{ errorMessage }}
    </div>

    <!-- Stress Alert Notification -->
    <transition name="stress-alert">
      <div v-if="showStressAlert" class="stress-alert" @click="showStressAlert = false">
        <span class="stress-alert-icon">⚠️</span>
        <span class="stress-alert-message">{{ stressAlertMessage }}</span>
        <span class="stress-alert-count">壓力事件：{{ stressEventCount }} 次</span>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import WhiteboardCanvas from '@/components/teaching/WhiteboardCanvas.vue';
import { marked } from 'marked';
import katex from 'katex';
import 'katex/dist/katex.min.css';

const router = useRouter();
const route = useRoute();

// Configure marked for math rendering
const renderMath = (text) => {
  if (!text) return '';
  
  // Replace LaTeX display math \[...\] or $$...$$ with rendered KaTeX
  let result = text.replace(/\\\[([\s\S]*?)\\\]|\$\$([\s\S]*?)\$\$/g, (match, p1, p2) => {
    const math = p1 || p2;
    try {
      return katex.renderToString(math.trim(), { displayMode: true, throwOnError: false });
    } catch (e) {
      return match;
    }
  });
  
  // Replace inline math \(...\) or $...$ with rendered KaTeX
  result = result.replace(/\\\(([\s\S]*?)\\\)|\$([^\$\n]+?)\$/g, (match, p1, p2) => {
    const math = p1 || p2;
    try {
      return katex.renderToString(math.trim(), { displayMode: false, throwOnError: false });
    } catch (e) {
      return match;
    }
  });
  
  return result;
};

// Render markdown with math support
const renderMarkdown = (text) => {
  if (!text) return '';
  
  // First render math expressions
  const withMath = renderMath(text);
  
  // Then render markdown
  const html = marked.parse(withMath, {
    breaks: true,
    gfm: true
  });
  
  return html;
};

// Session state
const sessionId = ref(null);
const fsmState = ref('IDLE');
const conceptCoverage = ref(0);
const isLoading = ref(false);
const errorMessage = ref('');

// Grove Vision state (student attention monitoring)
const stressEventCount = ref(0);
const showStressAlert = ref(false);
const stressAlertMessage = ref('');
let groveVisionWs = null;

// Question selection state
const showQuestionModal = ref(false);
const questions = ref([]);
const questionsLoading = ref(false);
const questionFilter = ref({
  subject: '',
  difficulty: ''
});

// ASR state
const asrReady = ref(false);
const asrLoading = ref(false);

// UI state
const status = ref('listening'); // listening | processing | speaking
const isRecording = ref(false);
const userInput = ref('');
const chatContainer = ref(null);
const whiteboardRef = ref(null);

// Audio recording state
let mediaRecorder = null;
let audioChunks = [];
let recordingStream = null;

// FSM state mapping
const fsmStateLabels = {
  IDLE: '待機',
  LISTENING: '聆聽中',
  ANALYZING: '分析中',
  PROBING: '追問',
  HINTING: '提示',
  REPAIR: '修正',
  CONSOLIDATING: '總結'
};

const fsmStateClass = computed(() => fsmState.value.toLowerCase());
const fsmStateLabel = computed(() => fsmStateLabels[fsmState.value] || fsmState.value);

const statusLabels = {
  listening: '聆聽中',
  processing: '思考中',
  speaking: 'AI 回應中'
};

// Current problem data
const currentProblem = ref({
  id: '',
  text: '請選擇一道題目開始講題',
  subject: '',
  difficulty: ''
});

// Filtered questions based on filters
const filteredQuestions = computed(() => {
  return questions.value.filter(q => {
    if (questionFilter.value.subject && q.subject !== questionFilter.value.subject) {
      return false;
    }
    if (questionFilter.value.difficulty && q.difficulty !== questionFilter.value.difficulty) {
      return false;
    }
    return true;
  });
});

// Chat messages
const chatMessages = ref([]);

// Student ID (should come from auth context in production)
const studentId = ref('student-001');

function formatTime(date) {
  return date.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' });
}

function addMessage(role, text, responseType = null) {
  chatMessages.value.push({
    role,
    text,
    time: formatTime(new Date()),
    responseType
  });
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
    }
  });
  
  // Auto-clear system messages after 5 seconds
  if (role === 'system') {
    setTimeout(() => {
      const idx = chatMessages.value.findIndex(m => m.text === text && m.role === 'system');
      if (idx !== -1) {
        chatMessages.value.splice(idx, 1);
      }
    }, 5000);
  }
}

// API calls
async function startSession() {
  if (isLoading.value) return;
  
  isLoading.value = true;
  errorMessage.value = '';
  
  try {
    const response = await fetch('/api/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question_id: currentProblem.value.id || 'q-001',
        student_id: studentId.value
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '無法開始會話');
    }
    
    const data = await response.json();
    sessionId.value = data.session_id;
    fsmState.value = data.fsm_state;
    currentProblem.value.text = data.question_content || currentProblem.value.text;
    
    // Clear previous messages and add welcome message
    chatMessages.value = [];
    addMessage('ai', data.message || '歡迎來到講題模式！請開始講解你的解題思路。');
    
    // Start Grove Vision monitoring
    await startGroveVisionMonitoring(data.session_id);
    
    status.value = 'listening';
  } catch (err) {
    errorMessage.value = err.message || '開始會話失敗';
    console.error('Start session error:', err);
  } finally {
    isLoading.value = false;
  }
}

async function sendMessage() {
  if (!userInput.value.trim() || !sessionId.value || status.value === 'processing') return;
  
  const messageText = userInput.value.trim();
  userInput.value = '';
  
  // Add user message
  addMessage('user', messageText);
  status.value = 'processing';
  
  try {
    const response = await fetch(`/api/sessions/${sessionId.value}/input`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: messageText
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '處理輸入失敗');
    }
    
    const data = await response.json();
    
    // Update FSM state
    fsmState.value = data.fsm_state;
    
    // Add AI response
    status.value = 'speaking';
    addMessage('ai', data.text, data.response_type);
    
    // Update session state
    await updateSessionState();
    
    setTimeout(() => {
      status.value = 'listening';
    }, 500);
    
  } catch (err) {
    errorMessage.value = err.message || '發送訊息失敗';
    console.error('Send message error:', err);
    status.value = 'listening';
  }
}

async function updateSessionState() {
  if (!sessionId.value) return;
  
  try {
    const response = await fetch(`/api/sessions/${sessionId.value}`);
    if (response.ok) {
      const data = await response.json();
      fsmState.value = data.fsm_state;
      conceptCoverage.value = data.concept_coverage;
    }
  } catch (err) {
    console.error('Update session state error:', err);
  }
}

async function endSession() {
  if (!sessionId.value || isLoading.value) return;
  
  isLoading.value = true;
  
  try {
    // Stop Grove Vision monitoring first
    const groveVisionSummary = await stopGroveVisionMonitoring();
    
    const response = await fetch(`/api/sessions/${sessionId.value}/end`, {
      method: 'POST'
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '結束會話失敗');
    }
    
    const data = await response.json();
    
    // Show summary with stress events
    const summaryText = `
📊 講題總結：
• 時長：${Math.round(data.duration / 60)} 分鐘
• 完成度：${Math.round(data.concept_coverage * 100)}%
• 對話輪數：${data.total_turns}
• 使用提示：${data.hints_used.length} 次
• 學生壓力事件：${stressEventCount.value} 次
    `.trim();
    
    addMessage('ai', summaryText, 'SUMMARY');
    
    // Reset session
    sessionId.value = null;
    fsmState.value = 'IDLE';
    conceptCoverage.value = 0;
    stressEventCount.value = 0;
    
  } catch (err) {
    errorMessage.value = err.message || '結束會話失敗';
    console.error('End session error:', err);
  } finally {
    isLoading.value = false;
  }
}

function toggleRecording() {
  if (!sessionId.value) return;
  
  if (isRecording.value) {
    stopRecording();
  } else {
    startRecording();
  }
}

async function startRecording() {
  try {
    // Request microphone access
    recordingStream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        channelCount: 1,
        sampleRate: 16000,
        echoCancellation: true,
        noiseSuppression: true
      } 
    });
    
    // Determine supported MIME type
    let mimeType = 'audio/webm';
    if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
      mimeType = 'audio/webm;codecs=opus';
    } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
      mimeType = 'audio/mp4';
    } else if (MediaRecorder.isTypeSupported('audio/ogg')) {
      mimeType = 'audio/ogg';
    }
    
    mediaRecorder = new MediaRecorder(recordingStream, { mimeType });
    audioChunks = [];
    
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data);
      }
    };
    
    mediaRecorder.onstop = async () => {
      // Create blob from chunks
      const audioBlob = new Blob(audioChunks, { type: mimeType });
      
      // Send to ASR API
      await transcribeAudio(audioBlob);
      
      // Clean up
      if (recordingStream) {
        recordingStream.getTracks().forEach(track => track.stop());
        recordingStream = null;
      }
    };
    
    mediaRecorder.start();
    isRecording.value = true;
    
  } catch (err) {
    console.error('Failed to start recording:', err);
    if (err.name === 'NotAllowedError') {
      errorMessage.value = '請允許麥克風權限以使用語音輸入';
    } else if (err.name === 'NotFoundError') {
      errorMessage.value = '找不到麥克風裝置';
    } else {
      errorMessage.value = '無法啟動錄音：' + err.message;
    }
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  }
  isRecording.value = false;
}

async function transcribeAudio(audioBlob) {
  status.value = 'processing';
  addMessage('system', '🎤 正在處理語音...');
  
  try {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    // Add question context for better LLM correction
    formData.append('question_context', currentProblem.value.text || '');
    
    // Use streaming endpoint for better UX
    const response = await fetch('/api/asr/transcribe-stream', {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      let errorMsg = '語音辨識失敗';
      try {
        const errorData = JSON.parse(errorText);
        errorMsg = errorData.detail || errorMsg;
      } catch {
        errorMsg = errorText || errorMsg;
      }
      throw new Error(errorMsg);
    }
    
    // Process SSE stream
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let partialText = '';
    let finalText = '';
    let confidence = 0;
    
    // Update processing message to show partial results
    const updateProcessingMessage = (text, stage) => {
      const processingIdx = chatMessages.value.findIndex(m => m.text.startsWith('🎤'));
      if (processingIdx !== -1) {
        if (stage === 'llm') {
          chatMessages.value[processingIdx].text = `🔄 AI 優化中: "${text}"`;
        } else if (text) {
          chatMessages.value[processingIdx].text = `🎤 辨識中: "${text}"`;
        }
      }
    };
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            
            switch (data.event) {
              case 'start':
                // Transcription started
                break;
              case 'partial':
                partialText = data.text;
                confidence = data.confidence || 0;
                updateProcessingMessage(partialText, 'partial');
                break;
              case 'llm_processing':
                updateProcessingMessage(partialText, 'llm');
                break;
              case 'final':
                finalText = data.text;
                confidence = data.confidence || 0;
                break;
              case 'error':
                throw new Error(data.text || '語音辨識失敗');
            }
          } catch (parseError) {
            if (parseError.message !== '語音辨識失敗') {
              console.warn('Failed to parse SSE event:', line);
            } else {
              throw parseError;
            }
          }
        }
      }
    }
    
    // Remove processing message
    const processingIdx = chatMessages.value.findIndex(m => m.text.startsWith('🎤') || m.text.startsWith('🔄'));
    if (processingIdx !== -1) {
      chatMessages.value.splice(processingIdx, 1);
    }
    
    if (finalText && finalText.trim()) {
      userInput.value = finalText.trim();
      
      if (confidence < 0.7) {
        addMessage('system', `⚠️ 辨識信心度較低 (${Math.round(confidence * 100)}%)，請確認文字是否正確`);
      }
      
      await sendMessage();
    } else {
      errorMessage.value = '未能辨識到語音，請再試一次';
    }
    
  } catch (err) {
    console.error('Transcription error:', err);
    errorMessage.value = err.message || '語音辨識失敗';
    
    // Remove processing message on error
    const processingIdx = chatMessages.value.findIndex(m => m.text.startsWith('🎤') || m.text.startsWith('🔄'));
    if (processingIdx !== -1) {
      chatMessages.value.splice(processingIdx, 1);
    }
  } finally {
    status.value = 'listening';
  }
}

// Whiteboard handlers
function onWhiteboardSave(json) {
  console.log('Whiteboard saved:', json);
  // Could save to backend here if needed
}

function onWhiteboardLoad(json) {
  console.log('Whiteboard loaded:', json);
}

// Get whiteboard data for session summary
function getWhiteboardData() {
  if (whiteboardRef.value) {
    return whiteboardRef.value.getCanvasJSON();
  }
  return null;
}

const exitTeaching = async () => {
  if (sessionId.value) {
    await endSession();
  }
  router.push({ name: 'student-dashboard' });
};

// Question selection methods
async function loadQuestions() {
  questionsLoading.value = true;
  try {
    const response = await fetch('/api/questions');
    if (response.ok) {
      const data = await response.json();
      // Map API response to frontend format
      const difficultyMap = { 1: '基礎', 2: '中等', 3: '進階' };
      const subjectMap = { '代數': '代數', '幾何': '幾何', '統計': '統計' };
      
      const apiQuestions = data.questions || data || [];
      questions.value = apiQuestions.map(q => ({
        id: q.id,
        content: q.content,
        subject: q.unit || q.subject || '數學',  // Use unit as subject for display
        difficulty: difficultyMap[q.difficulty] || '基礎'
      }));
      
      // If no questions from API, use fallback
      if (questions.value.length === 0) {
        questions.value = getDefaultQuestions();
      }
    } else {
      // Fallback to sample questions if API fails
      questions.value = getDefaultQuestions();
    }
  } catch (err) {
    console.error('Failed to load questions:', err);
    // Use sample questions on error
    questions.value = getDefaultQuestions();
  } finally {
    questionsLoading.value = false;
  }
}

function getDefaultQuestions() {
  return [
    { id: 'q-001', content: '解方程式：3x + 5 = 20', subject: '代數', difficulty: '基礎' },
    { id: 'q-002', content: '解方程式：2(x - 3) = 10', subject: '代數', difficulty: '基礎' },
    { id: 'q-003', content: '小明有一些糖果，給了弟弟 5 顆後，剩下的是原來的 2/3。請問小明原來有幾顆糖果？', subject: '代數', difficulty: '中等' },
    { id: 'q-004', content: '解方程式：x² - 5x + 6 = 0', subject: '代數', difficulty: '中等' },
    { id: 'q-005', content: '解方程式：x² + 4x - 5 = 0', subject: '代數', difficulty: '中等' },
    { id: 'q-006', content: '使用公式解求解：2x² - 3x - 2 = 0', subject: '代數', difficulty: '進階' },
    { id: 'q-007', content: '一個直角三角形的兩股分別為 3 公分和 4 公分，求斜邊長度。', subject: '幾何', difficulty: '基礎' },
    { id: 'q-008', content: '一個圓的半徑為 7 公分，求圓的面積。（π 取 22/7）', subject: '幾何', difficulty: '基礎' },
    { id: 'q-009', content: '三角形 ABC 中，∠A = 50°，∠B = 70°，求 ∠C。', subject: '幾何', difficulty: '基礎' },
    { id: 'q-010', content: '求以下數據的平均數：12, 15, 18, 21, 24', subject: '統計', difficulty: '基礎' },
    { id: 'q-011', content: '求以下數據的中位數：7, 3, 9, 5, 11, 2, 8', subject: '統計', difficulty: '基礎' },
  ];
}

function openQuestionModal() {
  if (sessionId.value) {
    errorMessage.value = '請先結束當前講題再選擇新題目';
    return;
  }
  showQuestionModal.value = true;
  if (questions.value.length === 0) {
    loadQuestions();
  }
}

function selectQuestion(question) {
  currentProblem.value = {
    id: question.id,
    text: question.content || question.text,
    subject: question.subject || '數學',
    difficulty: question.difficulty || '基礎'
  };
  showQuestionModal.value = false;
}

// ASR warmup and status check
async function checkAsrStatus() {
  try {
    const response = await fetch('/api/asr/status');
    if (response.ok) {
      const data = await response.json();
      asrReady.value = data.ready;
      asrLoading.value = data.loading;
      if (data.error) {
        console.warn('ASR error:', data.error);
      }
      return data;
    }
  } catch (err) {
    console.error('Failed to check ASR status:', err);
  }
  return null;
}

async function warmupAsr() {
  try {
    const status = await checkAsrStatus();
    if (status?.ready) {
      asrReady.value = true;
      return;
    }
    
    // Start warmup
    asrLoading.value = true;
    const response = await fetch('/api/asr/warmup', { method: 'POST' });
    if (response.ok) {
      const data = await response.json();
      console.log('ASR warmup:', data.message);
      
      // Poll for status until ready
      const pollInterval = setInterval(async () => {
        const status = await checkAsrStatus();
        if (status?.ready) {
          asrReady.value = true;
          asrLoading.value = false;
          clearInterval(pollInterval);
          addMessage('system', '🎤 語音辨識已準備就緒');
        } else if (!status?.loading && status?.error) {
          asrLoading.value = false;
          clearInterval(pollInterval);
          console.error('ASR warmup failed:', status.error);
        }
      }, 3000); // Check every 3 seconds
      
      // Stop polling after 3 minutes
      setTimeout(() => {
        clearInterval(pollInterval);
        if (!asrReady.value) {
          asrLoading.value = false;
          console.warn('ASR warmup timeout');
        }
      }, 180000);
    }
  } catch (err) {
    console.error('Failed to warmup ASR:', err);
    asrLoading.value = false;
  }
}

// Grove Vision monitoring functions
async function startGroveVisionMonitoring(sessionId) {
  try {
    // Reset stress count
    stressEventCount.value = 0;
    
    // Start monitoring via API
    const response = await fetch('/api/grove-vision/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId })
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('Grove Vision started:', data.message);
      
      // Connect WebSocket for real-time notifications
      connectGroveVisionWebSocket();
    }
  } catch (err) {
    console.warn('Grove Vision start failed:', err);
    // Continue without Grove Vision - it's optional
  }
}

async function stopGroveVisionMonitoring() {
  try {
    // Disconnect WebSocket
    if (groveVisionWs) {
      groveVisionWs.close();
      groveVisionWs = null;
    }
    
    // Stop monitoring via API
    const response = await fetch('/api/grove-vision/stop', {
      method: 'POST'
    });
    
    if (response.ok) {
      const data = await response.json();
      stressEventCount.value = data.stress_event_count;
      return data;
    }
  } catch (err) {
    console.warn('Grove Vision stop failed:', err);
  }
  return { stress_event_count: stressEventCount.value };
}

function connectGroveVisionWebSocket() {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${wsProtocol}//${window.location.host}/api/grove-vision/ws`;
  
  try {
    groveVisionWs = new WebSocket(wsUrl);
    
    groveVisionWs.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'stress_event') {
          // Update stress count
          stressEventCount.value = data.total_count;
          
          // Show alert notification
          showStressNotification(data.label, data.confidence);
        }
      } catch (e) {
        console.warn('WebSocket message parse error:', e);
      }
    };
    
    groveVisionWs.onerror = (error) => {
      console.warn('Grove Vision WebSocket error:', error);
    };
    
    groveVisionWs.onclose = () => {
      console.log('Grove Vision WebSocket closed');
    };
  } catch (err) {
    console.warn('Failed to connect Grove Vision WebSocket:', err);
  }
}

function showStressNotification(label, confidence) {
  // Map label to friendly message
  const messages = {
    '閉眼': '😴 偵測到閉眼，要專心喔！',
    '打哈欠': '🥱 偵測到打哈欠，休息一下再繼續吧！'
  };
  
  stressAlertMessage.value = messages[label] || '⚠️ 要專心喔！';
  showStressAlert.value = true;
  
  // Auto hide after 3 seconds
  setTimeout(() => {
    showStressAlert.value = false;
  }, 3000);
}

onMounted(() => {
  // Load problem from route params if available
  if (route.query.questionId) {
    currentProblem.value.id = route.query.questionId;
  }
  if (route.query.questionText) {
    currentProblem.value.text = route.query.questionText;
  }
  
  // Start ASR warmup in background
  warmupAsr();
});

onUnmounted(() => {
  // Clean up recording resources
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  }
  if (recordingStream) {
    recordingStream.getTracks().forEach(track => track.stop());
  }
  
  // Clean up Grove Vision WebSocket
  if (groveVisionWs) {
    groveVisionWs.close();
    groveVisionWs = null;
  }
  
  // Clean up session if still active
  if (sessionId.value) {
    fetch(`/api/sessions/${sessionId.value}/end`, { method: 'POST' }).catch(() => {});
    fetch('/api/grove-vision/stop', { method: 'POST' }).catch(() => {});
  }
});
</script>


<style scoped>
/* Root Layout */
.teaching-root {
  width: 100vw;
  height: 100vh;
  background: #0b1220;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.teaching-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1.5rem;
  background: rgba(15, 23, 42, 0.95);
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.exit-btn {
  padding: 0.5rem 1rem;
  background: rgba(239, 68, 68, 0.15);
  color: #fca5a5;
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.exit-btn:hover {
  background: rgba(239, 68, 68, 0.25);
}

.phase-badge {
  padding: 0.4rem 0.8rem;
  border-radius: 0.5rem;
  font-weight: 600;
  font-size: 0.85rem;
}

.phase-badge.idle { background: rgba(100, 116, 139, 0.2); color: #94a3b8; }
.phase-badge.listening { background: rgba(34, 197, 94, 0.2); color: #86EFAC; }
.phase-badge.analyzing { background: rgba(59, 130, 246, 0.2); color: #93C5FD; }
.phase-badge.probing { background: rgba(245, 158, 11, 0.2); color: #FCD34D; }
.phase-badge.hinting { background: rgba(34, 197, 94, 0.2); color: #86EFAC; }
.phase-badge.repair { background: rgba(239, 68, 68, 0.2); color: #FCA5A5; }
.phase-badge.consolidating { background: rgba(168, 85, 247, 0.2); color: #C4B5FD; }

.header-center {
  flex: 1;
  text-align: center;
}

.title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #e5e7eb;
}

.header-right {
  display: flex;
  align-items: center;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.8rem;
  border-radius: 999px;
  font-size: 0.8rem;
}

.status-indicator.listening { background: rgba(34, 197, 94, 0.15); color: #86efac; }
.status-indicator.processing { background: rgba(245, 158, 11, 0.15); color: #fcd34d; }
.status-indicator.speaking { background: rgba(59, 130, 246, 0.15); color: #93c5fd; }

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

.status-indicator.listening .status-dot { background: #22c55e; }
.status-indicator.processing .status-dot { background: #f59e0b; }
.status-indicator.speaking .status-dot { background: #3b82f6; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Main Two-Column Layout */
.teaching-main {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* Left Sidebar */
.left-sidebar {
  width: 380px;
  min-width: 320px;
  display: flex;
  flex-direction: column;
  background: rgba(15, 23, 42, 0.6);
  border-right: 1px solid rgba(148, 163, 184, 0.2);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: rgba(30, 41, 59, 0.5);
  border-bottom: 1px solid rgba(148, 163, 184, 0.15);
}

.section-icon { font-size: 1rem; }
.section-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: #e5e7eb;
}

.coverage-badge {
  margin-left: auto;
  padding: 0.2rem 0.5rem;
  background: rgba(34, 197, 94, 0.2);
  color: #86efac;
  border-radius: 0.25rem;
  font-size: 0.7rem;
}

/* Problem Section */
.problem-section {
  flex-shrink: 0;
}

.problem-content {
  padding: 1rem;
}

.problem-text {
  color: #f1f5f9;
  font-size: 1rem;
  line-height: 1.6;
  margin-bottom: 0.75rem;
}

.problem-meta {
  display: flex;
  gap: 0.5rem;
}

.meta-tag {
  padding: 0.25rem 0.6rem;
  background: rgba(59, 130, 246, 0.15);
  color: #93c5fd;
  border-radius: 0.25rem;
  font-size: 0.75rem;
}

/* Chat Section */
.chat-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-top: 1px solid rgba(148, 163, 184, 0.15);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.chat-message {
  display: flex;
  gap: 0.75rem;
  max-width: 95%;
}

.chat-message.user {
  flex-direction: row-reverse;
  align-self: flex-end;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(30, 41, 59, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;
}

.message-content {
  background: rgba(30, 41, 59, 0.8);
  padding: 0.75rem 1rem;
  border-radius: 1rem;
  border-top-left-radius: 0.25rem;
}

.chat-message.user .message-content {
  background: rgba(59, 130, 246, 0.3);
  border-top-left-radius: 1rem;
  border-top-right-radius: 0.25rem;
}

.chat-message.system {
  align-self: center;
  max-width: 100%;
}

.chat-message.system .message-avatar {
  display: none;
}

.chat-message.system .message-content {
  background: rgba(245, 158, 11, 0.2);
  border-radius: 0.5rem;
  text-align: center;
}

.chat-message.system .message-text {
  color: #fcd34d;
  font-size: 0.85rem;
}

.chat-message.system .message-time {
  display: none;
}

.message-text {
  margin: 0;
  color: #e5e7eb;
  font-size: 0.9rem;
  line-height: 1.5;
  white-space: pre-wrap;
}

/* Markdown content styles */
.markdown-content {
  white-space: normal;
}

.markdown-content p {
  margin: 0 0 0.5rem 0;
}

.markdown-content p:last-child {
  margin-bottom: 0;
}

.markdown-content strong {
  color: #fbbf24;
  font-weight: 600;
}

.markdown-content em {
  color: #a5b4fc;
  font-style: italic;
}

.markdown-content ul, .markdown-content ol {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.markdown-content li {
  margin: 0.25rem 0;
}

.markdown-content li::marker {
  color: #60a5fa;
}

.markdown-content h1, .markdown-content h2, .markdown-content h3 {
  color: #f1f5f9;
  margin: 0.75rem 0 0.5rem 0;
  font-weight: 600;
}

.markdown-content h1 { font-size: 1.1rem; }
.markdown-content h2 { font-size: 1rem; }
.markdown-content h3 { font-size: 0.95rem; }

.markdown-content code {
  background: rgba(30, 41, 59, 0.8);
  padding: 0.15rem 0.4rem;
  border-radius: 0.25rem;
  font-family: 'Fira Code', monospace;
  font-size: 0.85rem;
  color: #86efac;
}

.markdown-content pre {
  background: rgba(15, 23, 42, 0.9);
  padding: 0.75rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin: 0.5rem 0;
}

.markdown-content pre code {
  background: none;
  padding: 0;
}

.markdown-content blockquote {
  border-left: 3px solid #60a5fa;
  margin: 0.5rem 0;
  padding-left: 0.75rem;
  color: #94a3b8;
}

/* KaTeX math styles */
.markdown-content .katex {
  font-size: 1em;
  color: #93c5fd;
}

.markdown-content .katex-display {
  margin: 0.5rem 0;
  overflow-x: auto;
  overflow-y: hidden;
}

.markdown-content .katex-display > .katex {
  text-align: left;
}

.message-time {
  display: inline-block;
  margin-top: 0.25rem;
  font-size: 0.7rem;
  color: #94a3b8;
}

.message-type {
  display: inline-block;
  margin-left: 0.5rem;
  padding: 0.1rem 0.4rem;
  background: rgba(168, 85, 247, 0.2);
  color: #c4b5fd;
  border-radius: 0.25rem;
  font-size: 0.65rem;
}

/* Typing indicator */
.typing-dots {
  display: flex;
  gap: 4px;
}

.typing-dots span {
  width: 8px;
  height: 8px;
  background: #94a3b8;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-4px); }
}

/* Chat Input */
.chat-input-area {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: rgba(30, 41, 59, 0.5);
  border-top: 1px solid rgba(148, 163, 184, 0.15);
}

.voice-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: rgba(59, 130, 246, 0.2);
  color: #93c5fd;
  cursor: pointer;
  font-size: 1.1rem;
  transition: all 0.2s;
}

.voice-btn:hover:not(:disabled) { background: rgba(59, 130, 246, 0.3); }
.voice-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.voice-btn.active {
  background: rgba(239, 68, 68, 0.3);
  animation: recording 1s infinite;
}
.voice-btn.loading {
  background: rgba(245, 158, 11, 0.2);
}

.loading-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes recording {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
}

.recording-indicator {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.6rem 1rem;
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 1.5rem;
}

.asr-loading-indicator {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.6rem 1rem;
  background: rgba(245, 158, 11, 0.15);
  border: 1px solid rgba(245, 158, 11, 0.3);
  border-radius: 1.5rem;
}

.loading-text {
  color: #fcd34d;
  font-size: 0.85rem;
}

.recording-dot {
  width: 10px;
  height: 10px;
  background: #ef4444;
  border-radius: 50%;
  animation: pulse-dot 1s infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

.recording-text {
  color: #fca5a5;
  font-size: 0.9rem;
  font-weight: 500;
}

.chat-input {
  flex: 1;
  padding: 0.6rem 1rem;
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: 1.5rem;
  background: rgba(15, 23, 42, 0.6);
  color: #e5e7eb;
  font-size: 0.9rem;
}

.chat-input::placeholder { color: #64748b; }
.chat-input:focus {
  outline: none;
  border-color: rgba(59, 130, 246, 0.5);
}
.chat-input:disabled { opacity: 0.5; }

.send-btn {
  padding: 0.6rem 1rem;
  background: rgba(59, 130, 246, 0.8);
  color: white;
  border: none;
  border-radius: 1.5rem;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.send-btn:hover:not(:disabled) { background: rgba(59, 130, 246, 1); }
.send-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* Right Panel - Whiteboard */
.right-panel {
  flex: 1;
  padding: 1rem;
  display: flex;
  flex-direction: column;
}

/* Session Controls */
.session-controls {
  position: fixed;
  bottom: 1.5rem;
  right: 1.5rem;
  z-index: 100;
}

.start-btn, .end-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.start-btn {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
}

.start-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
}

.end-btn {
  background: linear-gradient(135deg, #22c55e, #16a34a);
  color: white;
}

.end-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(34, 197, 94, 0.4);
}

.start-btn:disabled, .end-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* Error Toast */
.error-toast {
  position: fixed;
  bottom: 5rem;
  left: 50%;
  transform: translateX(-50%);
  padding: 0.75rem 1.5rem;
  background: rgba(239, 68, 68, 0.9);
  color: white;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  cursor: pointer;
  z-index: 200;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from { transform: translateX(-50%) translateY(20px); opacity: 0; }
  to { transform: translateX(-50%) translateY(0); opacity: 1; }
}

/* Stress Alert Notification */
.stress-alert {
  position: fixed;
  top: 5rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.95), rgba(234, 88, 12, 0.95));
  color: white;
  border-radius: 1rem;
  font-size: 1rem;
  cursor: pointer;
  z-index: 300;
  box-shadow: 0 8px 32px rgba(245, 158, 11, 0.4);
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.stress-alert-icon {
  font-size: 1.5rem;
  animation: shake 0.5s ease-in-out;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

.stress-alert-message {
  font-weight: 600;
}

.stress-alert-count {
  padding: 0.25rem 0.5rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 0.5rem;
  font-size: 0.8rem;
}

/* Stress alert transition */
.stress-alert-enter-active {
  animation: stressAlertIn 0.4s ease;
}

.stress-alert-leave-active {
  animation: stressAlertOut 0.3s ease;
}

@keyframes stressAlertIn {
  from {
    transform: translateX(-50%) translateY(-30px);
    opacity: 0;
  }
  to {
    transform: translateX(-50%) translateY(0);
    opacity: 1;
  }
}

@keyframes stressAlertOut {
  from {
    transform: translateX(-50%) translateY(0);
    opacity: 1;
  }
  to {
    transform: translateX(-50%) translateY(-30px);
    opacity: 0;
  }
}

/* Responsive Design */
@media (max-width: 1024px) {
  .left-sidebar {
    width: 320px;
    min-width: 280px;
  }
}

@media (max-width: 768px) {
  .teaching-main {
    flex-direction: column;
  }
  
  .left-sidebar {
    width: 100%;
    min-width: unset;
    max-height: 45vh;
    border-right: none;
    border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  }
  
  .right-panel {
    flex: 1;
    min-height: 0;
  }
  
  .header-center { display: none; }
  
  .problem-section {
    max-height: 120px;
    overflow-y: auto;
  }
}

@media (max-width: 480px) {
  .teaching-header {
    padding: 0.5rem 1rem;
  }
  
  .phase-badge {
    font-size: 0.75rem;
    padding: 0.3rem 0.6rem;
  }
  
  .status-text { display: none; }
  
  .left-sidebar {
    max-height: 50vh;
  }
}

/* Question Selection Button */
.select-question-btn {
  margin-left: auto;
  padding: 0.3rem 0.6rem;
  background: rgba(59, 130, 246, 0.2);
  color: #93c5fd;
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.75rem;
  transition: all 0.2s;
}

.select-question-btn:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.3);
}

.select-question-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Question Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.question-modal {
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  background: #1e293b;
  border-radius: 1rem;
  border: 1px solid rgba(148, 163, 184, 0.2);
  display: flex;
  flex-direction: column;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from { transform: translateY(-20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.1rem;
  color: #e5e7eb;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(239, 68, 68, 0.2);
  color: #fca5a5;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(239, 68, 68, 0.3);
}

.modal-filters {
  display: flex;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
}

.filter-select {
  flex: 1;
  padding: 0.5rem 0.75rem;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: 0.5rem;
  color: #e5e7eb;
  font-size: 0.85rem;
}

.filter-select:focus {
  outline: none;
  border-color: rgba(59, 130, 246, 0.5);
}

.question-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.question-item {
  padding: 1rem;
  margin: 0.5rem;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.15);
  border-radius: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.question-item:hover {
  background: rgba(30, 41, 59, 0.8);
  border-color: rgba(59, 130, 246, 0.3);
}

.question-item.selected {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.5);
}

.question-text {
  color: #e5e7eb;
  font-size: 0.9rem;
  line-height: 1.5;
  margin-bottom: 0.75rem;
}

.question-meta {
  display: flex;
  gap: 0.5rem;
}

.question-meta .tag {
  padding: 0.2rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.7rem;
}

.question-meta .tag.subject {
  background: rgba(59, 130, 246, 0.2);
  color: #93c5fd;
}

.question-meta .tag.difficulty {
  background: rgba(34, 197, 94, 0.2);
  color: #86efac;
}

.question-meta .tag.difficulty.中等 {
  background: rgba(245, 158, 11, 0.2);
  color: #fcd34d;
}

.question-meta .tag.difficulty.進階 {
  background: rgba(239, 68, 68, 0.2);
  color: #fca5a5;
}

.no-questions, .loading-questions {
  text-align: center;
  padding: 2rem;
  color: #94a3b8;
  font-size: 0.9rem;
}
</style>
