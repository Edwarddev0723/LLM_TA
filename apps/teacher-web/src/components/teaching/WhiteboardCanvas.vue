<template>
  <div class="whiteboard-container">
    <!-- Toolbar -->
    <header class="toolbar">
      <div class="tool-group">
        <button 
          :class="{ active: currentTool === 'pen' }"
          @click="setTool('pen')"
          title="鋼筆"
        >
          ✏️ 鋼筆
        </button>
        <button 
          :class="{ active: currentTool === 'eraser' }"
          @click="setTool('eraser')"
          title="橡皮擦"
        >
          🧼 橡皮擦
        </button>
        <button 
          :class="{ active: currentTool === 'select' }"
          @click="setTool('select')"
          title="選取"
        >
          👆 選取
        </button>
      </div>

      <div class="tool-group">
        <label class="color-picker">
          🎨
          <input type="color" v-model="brushColor" @change="updateBrushColor" />
        </label>
        <select v-model="brushWidth" @change="updateBrushWidth" class="width-select">
          <option :value="2">細</option>
          <option :value="5">中</option>
          <option :value="10">粗</option>
          <option :value="20">特粗</option>
        </select>
      </div>

      <div class="tool-group">
        <button @click="undo" :disabled="!canUndo" title="復原">
          ↩️ 復原
        </button>
        <button @click="redo" :disabled="!canRedo" title="重做">
          ↪️ 重做
        </button>
        <button @click="clearCanvas" title="清除全部">
          🗑️ 清除
        </button>
      </div>

      <div class="tool-group">
        <button @click="saveCanvas" title="儲存">
          💾 儲存
        </button>
        <button @click="triggerLoad" title="載入">
          📂 載入
        </button>
        <input 
          type="file" 
          ref="fileInput" 
          @change="loadCanvas" 
          accept=".json"
          style="display: none"
        />
      </div>

      <span class="mode" :class="modeClass">
        模式：{{ modeLabel }}
      </span>
    </header>

    <!-- Canvas Container -->
    <div class="canvas-wrapper" ref="canvasWrapper">
      <canvas ref="canvasEl" id="whiteboard-canvas"></canvas>
    </div>

    <!-- Status Bar -->
    <footer class="status-bar">
      <span class="status-item">
        工具: {{ toolLabels[currentTool] }}
      </span>
      <span class="status-item">
        筆刷: {{ brushWidth }}px
      </span>
      <span class="status-item" v-if="lastSaved">
        上次儲存: {{ lastSaved }}
      </span>
    </footer>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, computed, watch, nextTick } from 'vue';
import { Canvas, PencilBrush } from 'fabric';

const props = defineProps({
  mode: {
    type: String,
    default: 'normal' // normal | repair
  },
  sessionId: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['save', 'load']);

// Refs
const canvasEl = ref(null);
const canvasWrapper = ref(null);
const fileInput = ref(null);

// State
let fabricCanvas = null;
const currentTool = ref('pen');
const brushColor = ref('#1e3a8a');
const brushWidth = ref(5);
const canUndo = ref(false);
const canRedo = ref(false);
const lastSaved = ref('');

// History for undo/redo
const history = ref([]);
const historyIndex = ref(-1);
const maxHistory = 50;

// Tool labels
const toolLabels = {
  pen: '鋼筆',
  eraser: '橡皮擦',
  select: '選取'
};

// Mode computed
const modeLabel = computed(() =>
  props.mode === 'repair' ? '修正 Repair' : '一般'
);

const modeClass = computed(() =>
  props.mode === 'repair' ? 'repair' : 'normal'
);

// Initialize Fabric.js canvas
function initCanvas() {
  if (!canvasEl.value || !canvasWrapper.value) return;

  const wrapper = canvasWrapper.value;
  const width = wrapper.clientWidth;
  const height = wrapper.clientHeight;

  // Create Fabric canvas
  fabricCanvas = new Canvas(canvasEl.value, {
    width: width,
    height: height,
    backgroundColor: '#eff6ff',
    isDrawingMode: true,
    selection: false
  });

  // Set up pencil brush
  fabricCanvas.freeDrawingBrush = new PencilBrush(fabricCanvas);
  fabricCanvas.freeDrawingBrush.color = brushColor.value;
  fabricCanvas.freeDrawingBrush.width = brushWidth.value;

  // Event listeners for history
  fabricCanvas.on('path:created', saveToHistory);
  fabricCanvas.on('object:modified', saveToHistory);
  fabricCanvas.on('object:removed', saveToHistory);

  // Initial history state
  saveToHistory();

  // Handle window resize
  window.addEventListener('resize', handleResize);
}

function handleResize() {
  if (!fabricCanvas || !canvasWrapper.value) return;

  const wrapper = canvasWrapper.value;
  const width = wrapper.clientWidth;
  const height = wrapper.clientHeight;

  fabricCanvas.setDimensions({ width, height });
  fabricCanvas.renderAll();
}

// Tool functions
function setTool(tool) {
  currentTool.value = tool;

  if (!fabricCanvas) return;

  switch (tool) {
    case 'pen':
      fabricCanvas.isDrawingMode = true;
      fabricCanvas.freeDrawingBrush = new PencilBrush(fabricCanvas);
      fabricCanvas.freeDrawingBrush.color = brushColor.value;
      fabricCanvas.freeDrawingBrush.width = brushWidth.value;
      fabricCanvas.selection = false;
      break;
    case 'eraser':
      fabricCanvas.isDrawingMode = true;
      fabricCanvas.freeDrawingBrush = new PencilBrush(fabricCanvas);
      fabricCanvas.freeDrawingBrush.color = '#eff6ff'; // Background color
      fabricCanvas.freeDrawingBrush.width = brushWidth.value * 3;
      fabricCanvas.selection = false;
      break;
    case 'select':
      fabricCanvas.isDrawingMode = false;
      fabricCanvas.selection = true;
      break;
  }
}

function updateBrushColor() {
  if (!fabricCanvas || !fabricCanvas.freeDrawingBrush) return;
  if (currentTool.value === 'pen') {
    fabricCanvas.freeDrawingBrush.color = brushColor.value;
  }
}

function updateBrushWidth() {
  if (!fabricCanvas || !fabricCanvas.freeDrawingBrush) return;
  const width = currentTool.value === 'eraser' ? brushWidth.value * 3 : brushWidth.value;
  fabricCanvas.freeDrawingBrush.width = width;
}

// History functions
function saveToHistory() {
  if (!fabricCanvas) return;

  const json = fabricCanvas.toJSON();
  
  // Remove future history if we're not at the end
  if (historyIndex.value < history.value.length - 1) {
    history.value = history.value.slice(0, historyIndex.value + 1);
  }

  // Add new state
  history.value.push(JSON.stringify(json));
  historyIndex.value = history.value.length - 1;

  // Limit history size
  if (history.value.length > maxHistory) {
    history.value.shift();
    historyIndex.value--;
  }

  updateHistoryButtons();
}

function updateHistoryButtons() {
  canUndo.value = historyIndex.value > 0;
  canRedo.value = historyIndex.value < history.value.length - 1;
}

function undo() {
  if (!fabricCanvas || historyIndex.value <= 0) return;

  historyIndex.value--;
  loadFromHistory();
}

function redo() {
  if (!fabricCanvas || historyIndex.value >= history.value.length - 1) return;

  historyIndex.value++;
  loadFromHistory();
}

function loadFromHistory() {
  if (!fabricCanvas || !history.value[historyIndex.value]) return;

  const json = JSON.parse(history.value[historyIndex.value]);
  fabricCanvas.loadFromJSON(json).then(() => {
    fabricCanvas.renderAll();
    updateHistoryButtons();
  });
}

function clearCanvas() {
  if (!fabricCanvas) return;

  if (confirm('確定要清除所有內容嗎？')) {
    doClearCanvas();
  }
}

function doClearCanvas() {
  if (!fabricCanvas) return;
  fabricCanvas.clear();
  fabricCanvas.backgroundColor = '#eff6ff';
  fabricCanvas.renderAll();
  saveToHistory();
}

// Silent clear without confirmation (for programmatic use)
function clearCanvasSilent() {
  doClearCanvas();
}

// Save/Load functions
function saveCanvas() {
  if (!fabricCanvas) return;

  const json = fabricCanvas.toJSON();
  const dataStr = JSON.stringify(json, null, 2);
  const blob = new Blob([dataStr], { type: 'application/json' });
  const url = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = url;
  link.download = `whiteboard-${props.sessionId || Date.now()}.json`;
  link.click();

  URL.revokeObjectURL(url);
  lastSaved.value = new Date().toLocaleTimeString('zh-TW');

  emit('save', json);
}

function triggerLoad() {
  fileInput.value?.click();
}

function loadCanvas(event) {
  const file = event.target.files?.[0];
  if (!file || !fabricCanvas) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const json = JSON.parse(e.target.result);
      fabricCanvas.loadFromJSON(json).then(() => {
        fabricCanvas.renderAll();
        saveToHistory();
        emit('load', json);
      });
    } catch (err) {
      console.error('Failed to load canvas:', err);
      alert('載入失敗：檔案格式不正確');
    }
  };
  reader.readAsText(file);

  // Reset file input
  event.target.value = '';
}

// Export functions for parent component
function getCanvasJSON() {
  if (!fabricCanvas) return null;
  return fabricCanvas.toJSON();
}

function loadCanvasJSON(json) {
  if (!fabricCanvas || !json) return;
  fabricCanvas.loadFromJSON(json).then(() => {
    fabricCanvas.renderAll();
    saveToHistory();
  });
}

// Expose methods to parent
defineExpose({
  getCanvasJSON,
  loadCanvasJSON,
  clearCanvas,
  clearCanvasSilent,
  saveCanvas
});

// Watch for mode changes
watch(() => props.mode, (newMode) => {
  if (newMode === 'repair') {
    brushColor.value = '#dc2626'; // Red for repair mode
    updateBrushColor();
  } else {
    brushColor.value = '#1e3a8a'; // Blue for normal mode
    updateBrushColor();
  }
});

// Lifecycle
onMounted(() => {
  nextTick(() => {
    initCanvas();
  });
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  if (fabricCanvas) {
    fabricCanvas.dispose();
    fabricCanvas = null;
  }
});
</script>


<style scoped>
.whiteboard-container {
  background: #020617;
  border-radius: 0.75rem;
  border: 1px solid rgba(148, 163, 184, 0.4);
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* Toolbar */
.toolbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid rgba(148, 163, 184, 0.4);
  background: rgba(15, 23, 42, 0.8);
  flex-wrap: wrap;
}

.tool-group {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding-right: 0.75rem;
  border-right: 1px solid rgba(148, 163, 184, 0.2);
}

.tool-group:last-of-type {
  border-right: none;
}

.toolbar button {
  border-radius: 0.5rem;
  border: 1px solid rgba(148, 163, 184, 0.3);
  padding: 0.4rem 0.75rem;
  background: rgba(15, 23, 42, 0.9);
  color: #e5e7eb;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s;
  white-space: nowrap;
}

.toolbar button:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.5);
}

.toolbar button.active {
  background: rgba(59, 130, 246, 0.3);
  border-color: #3b82f6;
  color: #93c5fd;
}

.toolbar button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Color picker */
.color-picker {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  cursor: pointer;
  padding: 0.3rem 0.5rem;
  background: rgba(15, 23, 42, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: 0.5rem;
}

.color-picker input[type="color"] {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  padding: 0;
  background: transparent;
}

.color-picker input[type="color"]::-webkit-color-swatch-wrapper {
  padding: 0;
}

.color-picker input[type="color"]::-webkit-color-swatch {
  border: 1px solid rgba(148, 163, 184, 0.5);
  border-radius: 0.25rem;
}

/* Width select */
.width-select {
  padding: 0.4rem 0.5rem;
  background: rgba(15, 23, 42, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: 0.5rem;
  color: #e5e7eb;
  font-size: 0.8rem;
  cursor: pointer;
}

.width-select:focus {
  outline: none;
  border-color: rgba(59, 130, 246, 0.5);
}

/* Mode badge */
.mode {
  margin-left: auto;
  font-size: 0.8rem;
  padding: 0.3rem 0.75rem;
  border-radius: 999px;
  font-weight: 500;
}

.mode.normal {
  background: rgba(37, 99, 235, 0.15);
  color: #93c5fd;
}

.mode.repair {
  background: rgba(239, 68, 68, 0.15);
  color: #fecaca;
}

/* Canvas wrapper */
.canvas-wrapper {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: #eff6ff;
}

.canvas-wrapper canvas {
  display: block;
  cursor: crosshair;
}

/* Status bar */
.status-bar {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 0.4rem 0.75rem;
  background: rgba(15, 23, 42, 0.8);
  border-top: 1px solid rgba(148, 163, 184, 0.4);
  font-size: 0.75rem;
  color: #94a3b8;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

/* Responsive */
@media (max-width: 768px) {
  .toolbar {
    padding: 0.4rem;
    gap: 0.5rem;
  }

  .tool-group {
    padding-right: 0.5rem;
  }

  .toolbar button {
    padding: 0.35rem 0.5rem;
    font-size: 0.75rem;
  }

  .mode {
    font-size: 0.7rem;
    padding: 0.2rem 0.5rem;
  }

  .status-bar {
    flex-wrap: wrap;
    gap: 0.75rem;
  }
}

@media (max-width: 480px) {
  .toolbar {
    justify-content: center;
  }

  .tool-group {
    border-right: none;
    padding-right: 0;
  }

  .mode {
    width: 100%;
    text-align: center;
    margin-left: 0;
    margin-top: 0.25rem;
  }
}
</style>
