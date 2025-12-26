<template>
  <div class="teacher-class-management">
    <div class="header-section">
      <h1>班級管理</h1>
      <button class="btn-primary" @click="showCreateClassModal = true">
        ➕ 建立新班級
      </button>
    </div>

    <!-- 建立班級模態框 -->
    <div v-if="showCreateClassModal" class="modal-overlay" @click="closeCreateClassModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>建立新班級</h2>
          <button class="close-btn" @click="closeCreateClassModal">✕</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="createClass">
            <div class="form-group">
              <label for="class-name">班級名稱 *</label>
              <input
                id="class-name"
                v-model="newClass.name"
                type="text"
                placeholder="例如：2年3班"
                required
              />
            </div>
            <div class="form-group">
              <label for="class-desc">班級描述</label>
              <textarea
                id="class-desc"
                v-model="newClass.description"
                placeholder="班級簡介（可選）"
                rows="3"
              ></textarea>
            </div>
            <div class="form-group">
              <label for="subject">科目 *</label>
              <select id="subject" v-model="newClass.subject" required>
                <option value="">選擇科目</option>
                <option value="數學">數學</option>
                <option value="英文">英文</option>
                <option value="國文">國文</option>
                <option value="自然">自然</option>
                <option value="社會">社會</option>
              </select>
            </div>
            <div class="form-actions">
              <button type="button" class="btn-secondary" @click="closeCreateClassModal">
                取消
              </button>
              <button type="submit" class="btn-primary" :disabled="isCreatingClass">
                {{ isCreatingClass ? '建立中...' : '建立班級' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- 班級列表 -->
    <div class="classes-section">
      <h2>我的班級</h2>
      <div v-if="classes.length === 0" class="empty-state">
        <p>還沒有班級，點擊「建立新班級」開始</p>
      </div>
      <div v-else class="classes-grid">
        <div v-for="classItem in classes" :key="classItem.id" class="class-card">
          <div class="class-header">
            <h3>{{ classItem.class_name }}</h3>
            <div class="class-actions">
              <button
                class="icon-btn"
                @click="editClass(classItem)"
                title="編輯"
              >
                ✏️
              </button>
              <button
                class="icon-btn danger"
                @click="deleteClass(classItem.id)"
                title="刪除"
              >
                🗑️
              </button>
            </div>
          </div>
          <p class="class-description">{{ classItem.description || '無描述' }}</p>
          <div class="class-stats">
            <div class="stat">
              <span class="stat-label">學生數</span>
              <span class="stat-value">{{ classItem.studentCount || 0 }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">建立於</span>
              <span class="stat-value">{{ formatDate(classItem.created_at) }}</span>
            </div>
          </div>
          <div class="class-actions-bottom">
            <button
              class="btn-secondary"
              @click="viewClassStudents(classItem.id)"
            >
              查看學生 ({{ classItem.studentCount || 0 }})
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 班級學生列表模態框 -->
    <div v-if="showStudentsModal" class="modal-overlay" @click="closeStudentsModal">
      <div class="modal-content large" @click.stop>
        <div class="modal-header">
          <h2>{{ selectedClassName }} - 學生列表</h2>
          <button class="close-btn" @click="closeStudentsModal">✕</button>
        </div>
        <div class="modal-body">
          <div v-if="classStudents.length === 0" class="empty-state">
            <p>此班級還沒有學生</p>
          </div>
          <table v-else class="students-table">
            <thead>
              <tr>
                <th>學號</th>
                <th>姓名</th>
                <th>信箱</th>
                <th>加入日期</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="student in classStudents" :key="student.id">
                <td>{{ student.id }}</td>
                <td>{{ student.full_name }}</td>
                <td>{{ student.email }}</td>
                <td>{{ formatDate(student.joined_at) }}</td>
                <td>
                  <button
                    class="btn-small danger"
                    @click="removeStudentFromClass(student.id)"
                  >
                    移除
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useSessionStore } from '@/stores/session';

const sessionStore = useSessionStore();
const classes = ref([]);
const classStudents = ref([]);
const showCreateClassModal = ref(false);
const showStudentsModal = ref(false);
const isCreatingClass = ref(false);
const selectedClassId = ref(null);
const selectedClassName = ref('');

const newClass = ref({
  name: '',
  description: '',
  subject: ''
});

const formatDate = (date) => {
  if (!date) return '-';
  return new Date(date).toLocaleDateString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
};

const fetchClasses = async () => {
  try {
    const response = await fetch(`/api/teacher/classes`, {
      headers: {
        'user-id': sessionStore.user.id
      }
    });

    if (response.ok) {
      const data = await response.json();
      classes.value = data.classes || [];
    } else {
      console.error('Failed to fetch classes');
    }
  } catch (error) {
    console.error('Error fetching classes:', error);
  }
};

const createClass = async () => {
  if (!newClass.value.name || !newClass.value.subject) {
    alert('請填寫必填欄位');
    return;
  }

  isCreatingClass.value = true;
  try {
    const response = await fetch('/api/teacher/classes', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'user-id': sessionStore.user.id
      },
      body: JSON.stringify({
        class_name: newClass.value.name,
        description: newClass.value.description,
        subject: newClass.value.subject
      })
    });

    if (response.ok) {
      alert('班級建立成功');
      newClass.value = { name: '', description: '', subject: '' };
      showCreateClassModal.value = false;
      await fetchClasses();
    } else {
      const error = await response.json();
      alert('建立班級失敗：' + (error.detail || error.error || '未知錯誤'));
    }
  } catch (error) {
    console.error('Error creating class:', error);
    alert('建立班級失敗');
  } finally {
    isCreatingClass.value = false;
  }
};

const deleteClass = async (classId) => {
  if (!confirm('確定要刪除此班級嗎？')) {
    return;
  }

  try {
    const response = await fetch(`/api/teacher/classes/${classId}`, {
      method: 'DELETE',
      headers: {
        'user-id': sessionStore.user.id
      }
    });

    if (response.ok) {
      alert('班級刪除成功');
      await fetchClasses();
    } else {
      alert('刪除班級失敗');
    }
  } catch (error) {
    console.error('Error deleting class:', error);
    alert('刪除班級失敗');
  }
};

const viewClassStudents = async (classId) => {
  selectedClassId.value = classId;
  const classItem = classes.value.find(c => c.id === classId);
  selectedClassName.value = classItem?.class_name || '';
  showStudentsModal.value = true;

  try {
    const response = await fetch(
      `/api/teacher/classes/${classId}/students`,
      {
        headers: {
          'user-id': sessionStore.user.id
        }
      }
    );

    if (response.ok) {
      const data = await response.json();
      classStudents.value = data.students || [];
    } else {
      console.error('Failed to fetch class students');
    }
  } catch (error) {
    console.error('Error fetching class students:', error);
  }
};

const removeStudentFromClass = async (studentId) => {
  if (!confirm('確定要將此學生移除班級嗎？')) {
    return;
  }

  try {
    const response = await fetch(
      `/api/teacher/classes/${selectedClassId.value}/students/${studentId}`,
      {
        method: 'DELETE',
        headers: {
          'user-id': sessionStore.user.id
        }
      }
    );

    if (response.ok) {
      alert('學生已移除');
      classStudents.value = classStudents.value.filter(s => s.id !== studentId);
    } else {
      alert('移除學生失敗');
    }
  } catch (error) {
    console.error('Error removing student:', error);
    alert('移除學生失敗');
  }
};

const editClass = (classItem) => {
  // 預留編輯功能
  alert(`編輯班級功能預留：${classItem.class_name}`);
};

const closeCreateClassModal = () => {
  showCreateClassModal.value = false;
  newClass.value = { name: '', description: '', subject: '' };
};

const closeStudentsModal = () => {
  showStudentsModal.value = false;
  selectedClassId.value = null;
  classStudents.value = [];
};

onMounted(async () => {
  await fetchClasses();
});
</script>

<style scoped>
.teacher-class-management {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #e0e0e0;
}

.header-section h1 {
  font-size: 28px;
  color: #333;
  margin: 0;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 10px 20px;
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
  padding: 8px 16px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: #e8e8e8;
  border-color: #999;
}

.btn-small {
  padding: 6px 12px;
  font-size: 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-small.danger {
  background: #ff6b6b;
  color: white;
}

.btn-small.danger:hover {
  background: #ff5252;
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

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  animation: slideIn 0.3s ease;
}

.modal-content.large {
  max-width: 800px;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
  transition: color 0.3s ease;
}

.close-btn:hover {
  color: #333;
}

.modal-body {
  padding: 20px;
  max-height: 70vh;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.3s ease;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

/* 班級列表 */
.classes-section {
  margin-top: 40px;
}

.classes-section h2 {
  font-size: 22px;
  color: #333;
  margin-bottom: 20px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: #f9f9f9;
  border-radius: 12px;
  border: 2px dashed #ddd;
}

.empty-state p {
  color: #999;
  font-size: 16px;
  margin: 0;
}

.classes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.class-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e0e0e0;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.class-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  border-color: #667eea;
}

.class-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.class-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
  flex: 1;
}

.class-actions {
  display: flex;
  gap: 5px;
}

.icon-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  transition: all 0.3s ease;
  padding: 4px 8px;
}

.icon-btn:hover {
  transform: scale(1.2);
}

.icon-btn.danger:hover {
  color: #ff6b6b;
}

.class-description {
  color: #666;
  font-size: 14px;
  margin: 10px 0;
  line-height: 1.4;
}

.class-stats {
  display: flex;
  gap: 15px;
  margin: 15px 0;
  padding: 10px 0;
  border-top: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: #999;
  font-weight: 600;
}

.stat-value {
  font-size: 16px;
  color: #333;
  font-weight: 700;
}

.class-actions-bottom {
  margin-top: 15px;
}

.class-actions-bottom .btn-secondary {
  width: 100%;
  padding: 10px;
}

/* 學生表 */
.students-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}

.students-table thead {
  background: #f5f5f5;
}

.students-table th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #ddd;
  font-size: 14px;
}

.students-table td {
  padding: 12px;
  border-bottom: 1px solid #eee;
  color: #666;
  font-size: 14px;
}

.students-table tbody tr:hover {
  background: #f9f9f9;
}

/* 響應式設計 */
@media (max-width: 768px) {
  .header-section {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }

  .classes-grid {
    grid-template-columns: 1fr;
  }

  .modal-content {
    max-width: calc(100% - 20px);
  }

  .students-table {
    font-size: 12px;
  }

  .students-table th,
  .students-table td {
    padding: 8px;
  }
}
</style>
