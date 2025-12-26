<template>
  <div class="teacher-import-questions">
    <div class="header-section">
      <h1>匯入題目</h1>
      <p class="subtitle">上傳題目檔案，支援 Excel 或 CSV 格式</p>
    </div>

    <!-- 上傳區域 -->
    <div class="upload-section">
      <div class="upload-box" @click="triggerFileInput" @dragover.prevent="isDragging = true" @dragleave="isDragging = false" @drop.prevent="handleFileDrop" :class="{ dragging: isDragging }">
        <div class="upload-icon">📤</div>
        <h3>拖拽檔案到此或點擊選擇</h3>
        <p>支援 .xlsx, .xls, .csv 檔案，最大 5MB</p>
        <input
          ref="fileInput"
          type="file"
          @change="handleFileSelect"
          accept=".xlsx,.xls,.csv"
          style="display: none"
        />
      </div>
    </div>

    <!-- 預覽區域 -->
    <div v-if="previewData.length > 0" class="preview-section">
      <div class="preview-header">
        <h2>預覽</h2>
        <div class="file-info">
          <span class="file-name">{{ selectedFileName }}</span>
          <span class="file-size">{{ (selectedFile?.size / 1024).toFixed(2) }} KB</span>
        </div>
      </div>

      <div class="form-section">
        <div class="form-group">
          <label for="subject">選擇科目 *</label>
          <select id="subject" v-model="importConfig.subjectId" required>
            <option value="">請選擇科目</option>
            <option v-for="subject in subjects" :key="subject.id" :value="subject.id">
              {{ subject.subject_name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label for="unit">選擇單元 *</label>
          <select id="unit" v-model="importConfig.unitId" required :disabled="!importConfig.subjectId">
            <option value="">請先選擇科目</option>
            <option v-for="unit in availableUnits" :key="unit.id" :value="unit.id">
              {{ unit.unit_name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label for="difficulty">預設難度</label>
          <select id="difficulty" v-model="importConfig.difficulty">
            <option value="easy">簡單</option>
            <option value="medium">中等</option>
            <option value="hard">困難</option>
          </select>
        </div>
      </div>

      <div class="preview-table">
        <table>
          <thead>
            <tr>
              <th>題目</th>
              <th>答案</th>
              <th>解析</th>
              <th>難度</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in previewData.slice(0, 10)" :key="index">
              <td>
                <div class="cell-content">
                  {{ row.question_text?.substring(0, 50) || '-' }}...
                </div>
              </td>
              <td>
                <div class="cell-content">
                  {{ row.answer_text?.substring(0, 30) || '-' }}...
                </div>
              </td>
              <td>
                <div class="cell-content">
                  {{ row.solution_text?.substring(0, 30) || '-' }}...
                </div>
              </td>
              <td>
                <span :class="['difficulty-badge', row.difficulty || importConfig.difficulty]">
                  {{ getDifficultyLabel(row.difficulty || importConfig.difficulty) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="previewData.length > 10" class="preview-footer">
          <p>顯示前 10 條，共 {{ previewData.length }} 條題目</p>
        </div>
      </div>

      <div class="action-section">
        <button class="btn-secondary" @click="resetImport">
          清除
        </button>
        <button
          class="btn-primary"
          @click="importQuestions"
          :disabled="!importConfig.subjectId || !importConfig.unitId || isImporting"
        >
          {{ isImporting ? '匯入中...' : `匯入 ${previewData.length} 條題目` }}
        </button>
      </div>
    </div>

    <!-- 說明區域 -->
    <div v-else class="instructions-section">
      <h2>匯入說明</h2>
      <div class="instruction-grid">
        <div class="instruction-card">
          <div class="card-icon">📋</div>
          <h3>檔案格式</h3>
          <p>支援 Excel (.xlsx, .xls) 或 CSV 格式</p>
        </div>
        <div class="instruction-card">
          <div class="card-icon">🔤</div>
          <h3>必填欄位</h3>
          <p>question_text（題目）、answer_text（答案）</p>
        </div>
        <div class="instruction-card">
          <div class="card-icon">📊</div>
          <h3>選填欄位</h3>
          <p>solution_text（解析）、difficulty（難度）</p>
        </div>
        <div class="instruction-card">
          <div class="card-icon">⚙️</div>
          <h3>難度選項</h3>
          <p>easy（簡單）、medium（中等）、hard（困難）</p>
        </div>
      </div>

      <div class="template-section">
        <h3>下載模板</h3>
        <p>使用以下模板可確保匯入成功</p>
        <button class="btn-secondary" @click="downloadTemplate">
          📥 下載 Excel 模板
        </button>
      </div>
    </div>

    <!-- 成功提示 -->
    <div v-if="importSuccess" class="success-notification">
      <div class="success-content">
        <span class="success-icon">✅</span>
        <div>
          <h3>匯入成功</h3>
          <p>成功匯入 {{ importedCount }} 條題目</p>
        </div>
        <button class="close-btn" @click="importSuccess = false">✕</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useSessionStore } from '@/stores/session';

const sessionStore = useSessionStore();
const fileInput = ref(null);
const selectedFile = ref(null);
const selectedFileName = ref('');
const isDragging = ref(false);
const previewData = ref([]);
const isImporting = ref(false);
const importSuccess = ref(false);
const importedCount = ref(0);

const subjects = ref([]);
const units = ref([]);

const importConfig = ref({
  subjectId: '',
  unitId: '',
  difficulty: 'medium'
});

const availableUnits = computed(() => {
  if (!importConfig.value.subjectId) return [];
  return units.value.filter(u => u.subject_id === parseInt(importConfig.value.subjectId));
});

const getDifficultyLabel = (difficulty) => {
  const labels = {
    easy: '簡單',
    medium: '中等',
    hard: '困難'
  };
  return labels[difficulty] || difficulty;
};

const triggerFileInput = () => {
  fileInput.value?.click();
};

const handleFileSelect = (event) => {
  const file = event.target.files?.[0];
  if (file) {
    processFile(file);
  }
};

const handleFileDrop = (event) => {
  isDragging.value = false;
  const file = event.dataTransfer?.files?.[0];
  if (file) {
    processFile(file);
  }
};

const processFile = async (file) => {
  if (file.size > 5 * 1024 * 1024) {
    alert('檔案大小不能超過 5MB');
    return;
  }

  selectedFile.value = file;
  selectedFileName.value = file.name;

  // 模擬檔案解析
  // 實際應用中應該在後端進行檔案解析
  const text = await file.text();
  parseFileContent(text, file.name);
};

const parseFileContent = (content, filename) => {
  const lines = content.split('\n');
  const data = [];

  // 簡單的 CSV 解析
  for (let i = 1; i < lines.length; i++) {
    if (!lines[i].trim()) continue;

    const parts = lines[i].split(',');
    if (parts.length >= 2) {
      data.push({
        question_text: parts[0]?.trim() || '',
        answer_text: parts[1]?.trim() || '',
        solution_text: parts[2]?.trim() || '',
        difficulty: parts[3]?.trim() || 'medium'
      });
    }
  }

  previewData.value = data;
  if (data.length === 0) {
    alert('檔案中沒有找到有效的題目資料');
  }
};

const resetImport = () => {
  selectedFile.value = null;
  selectedFileName.value = '';
  previewData.value = [];
  importConfig.value = {
    subjectId: '',
    unitId: '',
    difficulty: 'medium'
  };
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};

const importQuestions = async () => {
  if (!importConfig.value.subjectId || !importConfig.value.unitId) {
    alert('請選擇科目和單元');
    return;
  }

  if (previewData.value.length === 0) {
    alert('沒有題目可匯入');
    return;
  }

  isImporting.value = true;
  try {
    const response = await fetch('/api/teacher/questions/import', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'user-id': sessionStore.user.id
      },
      body: JSON.stringify({
        unit_id: parseInt(importConfig.value.unitId),
        difficulty: importConfig.value.difficulty,
        questions: previewData.value
      })
    });

    if (response.ok) {
      const data = await response.json();
      importedCount.value = data.imported_count || previewData.value.length;
      importSuccess.value = true;
      setTimeout(() => {
        resetImport();
        importSuccess.value = false;
      }, 3000);
    } else {
      const error = await response.json();
      alert('匯入失敗：' + (error.detail || error.error || '未知錯誤'));
    }
  } catch (error) {
    console.error('Error importing questions:', error);
    alert('匯入失敗');
  } finally {
    isImporting.value = false;
  }
};

const downloadTemplate = () => {
  const template = 'question_text,answer_text,solution_text,difficulty\n' +
    '例題1：計算 2+2,4,2+2=4,easy\n' +
    '例題2：計算 10×10,100,10×10=100,medium\n';

  const blob = new Blob([template], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = '題目匯入模板.csv';
  a.click();
  window.URL.revokeObjectURL(url);
};

const fetchSubjectsAndUnits = async () => {
  try {
    const response = await fetch('/api/subjects', {
      headers: {
        'user-id': sessionStore.user.id
      }
    });

    if (response.ok) {
      const data = await response.json();
      subjects.value = data.subjects || [];

      // 獲取所有單元
      const unitsResponse = await fetch('/api/units', {
        headers: {
          'user-id': sessionStore.user.id
        }
      });

      if (unitsResponse.ok) {
        const unitsData = await unitsResponse.json();
        units.value = unitsData.units || [];
      }
    }
  } catch (error) {
    console.error('Error fetching subjects and units:', error);
  }
};

onMounted(() => {
  fetchSubjectsAndUnits();
});
</script>

<style scoped>
.teacher-import-questions {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}

.header-section {
  text-align: center;
  margin-bottom: 40px;
}

.header-section h1 {
  font-size: 28px;
  color: #333;
  margin: 0 0 10px 0;
}

.subtitle {
  color: #666;
  font-size: 16px;
  margin: 0;
}

/* 上傳區域 */
.upload-section {
  margin-bottom: 30px;
}

.upload-box {
  border: 2px dashed #667eea;
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #f9f9ff;
}

.upload-box:hover {
  border-color: #764ba2;
  background: #f5f3ff;
}

.upload-box.dragging {
  border-color: #764ba2;
  background: #eae3ff;
  transform: scale(1.02);
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 10px;
}

.upload-box h3 {
  font-size: 18px;
  color: #333;
  margin: 10px 0 5px 0;
}

.upload-box p {
  color: #999;
  font-size: 14px;
  margin: 0;
}

/* 預覽區域 */
.preview-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e0e0e0;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #f0f0f0;
}

.preview-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.file-info {
  display: flex;
  gap: 15px;
  font-size: 14px;
  color: #666;
}

.file-name {
  background: #f0f0f0;
  padding: 4px 12px;
  border-radius: 4px;
  font-weight: 600;
}

.file-size {
  color: #999;
}

/* 表單區域 */
.form-section {
  margin-bottom: 25px;
  padding: 15px;
  background: #f9f9f9;
  border-radius: 8px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.form-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.3s ease;
}

.form-group select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-group select:disabled {
  background: #f0f0f0;
  cursor: not-allowed;
  opacity: 0.6;
}

/* 預覽表 */
.preview-table {
  margin-bottom: 20px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e0e0e0;
}

.preview-table table {
  width: 100%;
  border-collapse: collapse;
}

.preview-table thead {
  background: #f5f5f5;
}

.preview-table th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #ddd;
  font-size: 13px;
}

.preview-table td {
  padding: 12px;
  border-bottom: 1px solid #eee;
  color: #666;
  font-size: 13px;
}

.preview-table tbody tr:hover {
  background: #f9f9f9;
}

.cell-content {
  max-width: 300px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.difficulty-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  width: fit-content;
}

.difficulty-badge.easy {
  background: #d4edda;
  color: #155724;
}

.difficulty-badge.medium {
  background: #fff3cd;
  color: #856404;
}

.difficulty-badge.hard {
  background: #f8d7da;
  color: #721c24;
}

.preview-footer {
  text-align: center;
  padding: 10px;
  background: #f9f9f9;
  color: #999;
  font-size: 12px;
  border-top: 1px solid #eee;
}

/* 操作區域 */
.action-section {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: 25px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f0f0f0;
  color: #333;
  border: 1px solid #ddd;
  padding: 10px 24px;
  border-radius: 25px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: #e8e8e8;
  border-color: #999;
}

/* 說明區域 */
.instructions-section {
  margin-top: 40px;
}

.instructions-section h2 {
  font-size: 22px;
  color: #333;
  margin-bottom: 20px;
}

.instruction-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.instruction-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e0e0e0;
  text-align: center;
  transition: all 0.3s ease;
}

.instruction-card:hover {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
}

.card-icon {
  font-size: 36px;
  margin-bottom: 10px;
}

.instruction-card h3 {
  font-size: 16px;
  color: #333;
  margin: 10px 0 5px 0;
}

.instruction-card p {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.template-section {
  background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
  border-radius: 12px;
  padding: 25px;
  text-align: center;
}

.template-section h3 {
  font-size: 18px;
  color: #333;
  margin: 0 0 10px 0;
}

.template-section p {
  color: #666;
  margin: 0 0 15px 0;
}

/* 成功通知 */
.success-notification {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: white;
  border-left: 4px solid #28a745;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  animation: slideInUp 0.3s ease;
  z-index: 1000;
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.success-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.success-icon {
  font-size: 24px;
}

.success-content h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  color: #28a745;
}

.success-content p {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #999;
  padding: 0;
  transition: color 0.3s ease;
}

.close-btn:hover {
  color: #333;
}

@media (max-width: 768px) {
  .teacher-import-questions {
    padding: 15px;
  }

  .upload-box {
    padding: 30px 15px;
  }

  .instruction-grid {
    grid-template-columns: 1fr;
  }

  .action-section {
    flex-direction: column;
  }

  .action-section button {
    width: 100%;
  }

  .success-notification {
    right: 10px;
    left: 10px;
    bottom: 10px;
  }
}
</style>
