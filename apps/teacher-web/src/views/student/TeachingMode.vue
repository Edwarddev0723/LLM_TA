<template>
  <div class="teaching-root">
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
                <p class="message-text">{{ msg.text }}</p>
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
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import WhiteboardCanvas from '@/components/teaching/WhiteboardCanvas.vue';

const router = useRouter();
const route = useRoute();

// Session state
const sessionId = ref(null);
const fsmState = ref('IDLE');
const conceptCoverage = ref(0);
const isLoading = ref(false);
const errorMessage = ref('');

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
  text: '解方程式：2x + 5 = 13，求 x 的值。',
  subject: '數學',
  difficulty: '基礎'
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
    const response = await fetch(`/api/sessions/${sessionId.value}/end`, {
      method: 'POST'
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '結束會話失敗');
    }
    
    const data = await response.json();
    
    // Show summary
    const summaryText = `
📊 講題總結：
• 時長：${Math.round(data.duration / 60)} 分鐘
• 完成度：${Math.round(data.concept_coverage * 100)}%
• 對話輪數：${data.total_turns}
• 使用提示：${data.hints_used.length} 次
    `.trim();
    
    addMessage('ai', summaryText, 'SUMMARY');
    
    // Reset session
    sessionId.value = null;
    fsmState.value = 'IDLE';
    conceptCoverage.value = 0;
    
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
    
    // Use AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      controller.abort();
      addMessage('system', '⏱️ 語音處理超時，請重試');
    }, 120000); // 120 second timeout
    
    let response;
    try {
      response = await fetch('/api/asr/transcribe', {
        method: 'POST',
        body: formData,
        signal: controller.signal
      });
    } catch (fetchError) {
      clearTimeout(timeoutId);
      if (fetchError.name === 'AbortError') {
        throw new Error('語音辨識超時，請縮短錄音長度後重試');
      }
      // Check if it's a network error (socket hang up)
      if (fetchError.message.includes('Failed to fetch') || fetchError.message.includes('NetworkError')) {
        throw new Error('網路連接中斷，請確認後端服務正常運行');
      }
      throw fetchError;
    }
    clearTimeout(timeoutId);
    
    // Check if response has content
    const contentType = response.headers.get('content-type');
    let responseText = '';
    
    try {
      responseText = await response.text();
    } catch (textError) {
      console.error('Failed to read response text:', textError);
      throw new Error('伺服器響應異常，請重試');
    }
    
    if (!response.ok) {
      // Try to parse error message
      let errorMsg = '語音辨識失敗';
      if (responseText) {
        try {
          const errorData = JSON.parse(responseText);
          errorMsg = errorData.detail || errorMsg;
        } catch {
          errorMsg = responseText || errorMsg;
        }
      }
      
      // Check for specific error codes
      if (response.status === 503) {
        errorMsg = 'ASR 服務尚未準備好，請稍後再試';
        // Trigger warmup again
        warmupAsr();
      } else if (response.status === 504 || response.status === 502) {
        errorMsg = '處理超時，請縮短錄音長度後重試';
      }
      
      throw new Error(errorMsg);
    }
    
    // Parse successful response
    if (!responseText) {
      throw new Error('伺服器返回空響應，請重試');
    }
    
    let data;
    try {
      data = JSON.parse(responseText);
    } catch (e) {
      console.error('Failed to parse ASR response:', responseText);
      throw new Error('無法解析伺服器響應，請重試');
    }
    
    // Remove processing message
    const processingIdx = chatMessages.value.findIndex(m => m.text === '🎤 正在處理語音...');
    if (processingIdx !== -1) {
      chatMessages.value.splice(processingIdx, 1);
    }
    
    if (data.text && data.text.trim()) {
      // Set transcribed text to input
      userInput.value = data.text.trim();
      
      // Show confidence indicator if low
      if (data.confidence < 0.7) {
        addMessage('system', `⚠️ 辨識信心度較低 (${Math.round(data.confidence * 100)}%)，請確認文字是否正確`);
      }
      
      // Auto-send the message
      await sendMessage();
    } else {
      errorMessage.value = '未能辨識到語音，請再試一次';
    }
    
  } catch (err) {
    console.error('Transcription error:', err);
    errorMessage.value = err.message || '語音辨識失敗';
    
    // Remove processing message on error
    const processingIdx = chatMessages.value.findIndex(m => m.text === '🎤 正在處理語音...');
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
  
  // Clean up session if still active
  if (sessionId.value) {
    fetch(`/api/sessions/${sessionId.value}/end`, { method: 'POST' }).catch(() => {});
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
</style>
