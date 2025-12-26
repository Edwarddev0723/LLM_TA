<template>
  <div class="admin-shell">
    <aside class="admin-sidebar">
      <div class="logo-section">
        <div class="logo">⚙️ 系統管理</div>
      </div>
      <nav>
        <button 
          @click="currentTab = 'dashboard'" 
          :class="{ active: currentTab === 'dashboard' }"
        >
          📊 儀表板
        </button>
        <button 
          @click="currentTab = 'classes'" 
          :class="{ active: currentTab === 'classes' }"
        >
          🏫 班級管理
        </button>
        <button 
          @click="currentTab = 'approvals'" 
          :class="{ active: currentTab === 'approvals' }"
        >
          ✅ 審核申請
        </button>
        <button 
          @click="currentTab = 'users'" 
          :class="{ active: currentTab === 'users' }"
        >
          👥 用戶管理
        </button>
      </nav>
      <div class="sidebar-footer">
        <button class="logout-btn-sidebar" @click="handleLogout">
          🚪 登出
        </button>
      </div>
    </aside>

    <main class="admin-content">
      <!-- 儀表板 -->
      <section v-if="currentTab === 'dashboard'" class="tab-content">
        <h1>系統儀表板</h1>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-value">{{ classesStore.classes.length }}</div>
            <div class="stat-label">班級總數</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ classesStore.registeredUsers.length }}</div>
            <div class="stat-label">已註冊用戶</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ classesStore.pendingApprovals.length }}</div>
            <div class="stat-label">待審核申請</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ teacherCount }}</div>
            <div class="stat-label">教師總數</div>
          </div>
        </div>
      </section>

      <!-- 班級管理 -->
      <section v-if="currentTab === 'classes'" class="tab-content">
        <div class="section-header">
          <h1>班級管理</h1>
          <button class="add-btn" @click="showAddClassForm = !showAddClassForm">
            {{ showAddClassForm ? '✕' : '+ 新增班級' }}
          </button>
        </div>

        <div v-if="showAddClassForm" class="form-card">
          <h3>新增班級</h3>
          <div class="form-group">
            <label>班級名稱</label>
            <input 
              v-model="newClass.name" 
              type="text" 
              placeholder="例如：2年3班"
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label>選擇班級教師</label>
            <select v-model="newClass.teacherId" class="form-input">
              <option value="">-- 選擇教師 --</option>
              <option v-for="teacher in teacherList" :key="teacher.id" :value="teacher.id">
                {{ teacher.name }}
              </option>
            </select>
          </div>
          <div class="form-actions">
            <button class="cancel-btn" @click="showAddClassForm = false">取消</button>
            <button class="save-btn" @click="addNewClass">新增</button>
          </div>
        </div>

        <table class="data-table">
          <thead>
            <tr>
              <th>班級名稱</th>
              <th>班級教師</th>
              <th>教師數</th>
              <th>學生數</th>
              <th>家長數</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="cls in classesStore.classes" :key="cls.id">
              <td v-if="editingClassId !== cls.id"><strong>{{ cls.name }}</strong></td>
              <td v-else>
                <input 
                  v-model="editingClass.name" 
                  type="text" 
                  class="inline-input"
                  placeholder="班級名稱"
                />
              </td>
              <td v-if="editingClassId !== cls.id">{{ cls.teacherName || '待分配' }}</td>
              <td v-else>
                <select v-model="editingClass.teacherId" class="inline-input">
                  <option value="">-- 選擇教師 --</option>
                  <option v-for="teacher in teacherList" :key="teacher.id" :value="teacher.id">
                    {{ teacher.name }}
                  </option>
                </select>
              </td>
              <td>{{ getTeacherCountInClass(cls.id) }}</td>
              <td>{{ getStudentCountInClass(cls.id) }}</td>
              <td>{{ getParentCountInClass(cls.id) }}</td>
              <td>
                <template v-if="editingClassId !== cls.id">
                  <button class="edit-btn" @click="startEditClass(cls)">編輯</button>
                  <button class="delete-btn" @click="deleteClass(cls.id)">刪除</button>
                </template>
                <template v-else>
                  <button class="save-btn-small" @click="saveEditClass">儲存</button>
                  <button class="cancel-btn-small" @click="cancelEditClass">取消</button>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- 審核申請 -->
      <section v-if="currentTab === 'approvals'" class="tab-content">
        <h1>待審核申請</h1>
        <div class="approval-tabs">
          <button 
            v-for="role in ['student', 'teacher', 'parent']" 
            :key="role"
            @click="approvalRole = role"
            :class="{ active: approvalRole === role }"
            class="approval-tab"
          >
            {{ role === 'student' ? '👨‍🎓 學生' : role === 'teacher' ? '👨‍🏫 教師' : '👨‍👩‍👧 家長' }}
          </button>
        </div>

        <div class="approval-list">
          <div v-if="pendingApplications.length === 0" class="empty-state">
            <p>暫無待審核的 {{ approvalRole }} 申請</p>
          </div>
          <div v-for="application in pendingApplications" :key="application.id" class="approval-card">
            <div class="approval-info">
              <h4>{{ application.name }}</h4>
              <p>📧 {{ application.email }}</p>
              <p>🏫 申請班級：{{ application.className }}</p>
              <p v-if="application.studentName">👨‍🎓 關聯學生：{{ application.studentName }}</p>
              <p v-if="application.relationship">👥 關係：{{ application.relationship }}</p>
            </div>
            <div class="approval-actions">
              <button class="approve-btn" @click="approveApplication(application.id)">
                ✅ 批准
              </button>
              <button class="reject-btn" @click="rejectApplication(application.id)">
                ❌ 拒絕
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- 用戶管理 -->
      <section v-if="currentTab === 'users'" class="tab-content">
        <h1>用戶管理</h1>
        <div class="users-filter">
          <button 
            v-for="role in ['all', 'teacher', 'student', 'parent']" 
            :key="role"
            @click="userRole = role"
            :class="{ active: userRole === role }"
            class="filter-btn"
          >
            {{ role === 'all' ? '全部' : role === 'teacher' ? '教師' : role === 'student' ? '學生' : '家長' }}
          </button>
        </div>

        <table class="data-table">
          <thead>
            <tr>
              <th>姓名</th>
              <th>郵件</th>
              <th>身分</th>
              <th>班級</th>
              <th>狀態</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in filteredUsers" :key="user.id">
              <td><strong>{{ user.name }}</strong></td>
              <td>{{ user.email }}</td>
              <td>
                <span class="role-badge" :class="user.role">
                  {{ user.role === 'teacher' ? '教師' : user.role === 'student' ? '學生' : '家長' }}
                </span>
              </td>
              <td>{{ user.className || '-' }}</td>
              <td>
                <span class="status-badge" :class="user.status">{{ user.status === 'approved' ? '已批准' : '待審核' }}</span>
              </td>
              <td>
                <button class="edit-btn">編輯</button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useSessionStore } from '@/stores/session';
import { useClassAndRolesStore } from '@/stores/classAndRoles';

const router = useRouter();
const sessionStore = useSessionStore();
const classesStore = useClassAndRolesStore();

const currentTab = ref('dashboard');
const approvalRole = ref('student');
const userRole = ref('all');
const showAddClassForm = ref(false);

const newClass = ref({
  name: '',
  teacherId: ''
});

onMounted(() => {
  // 檢查是否是管理員
  if (sessionStore.role !== 'admin') {
    router.push({ name: 'login' });
  }
});

// 計算統計數據
const teacherCount = computed(() => {
  return classesStore.registeredUsers.filter(u => u.role === 'teacher').length;
});

const teacherList = computed(() => {
  return classesStore.registeredUsers.filter(u => u.role === 'teacher');
});

const pendingApplications = computed(() => {
  return classesStore.pendingApprovals.filter(a => a.role === approvalRole.value && a.status === 'pending');
});

const filteredUsers = computed(() => {
  if (userRole.value === 'all') {
    return classesStore.registeredUsers;
  }
  return classesStore.registeredUsers.filter(u => u.role === userRole.value);
});

const getStudentCountInClass = (classId) => {
  return classesStore.getStudentsByClass(classId).length;
};

const getParentCountInClass = (classId) => {
  return classesStore.getParentsByClass(classId).length;
};

const getTeacherCountInClass = (classId) => {
  const classInfo = classesStore.classes.find(c => c.id === classId);
  if (!classInfo || !classInfo.teacherId) return 0;
  return 1; // 每个班级只有一个老师
};

const editingClassId = ref(null);
const editingClass = ref({
  name: '',
  teacherId: ''
});

const startEditClass = (cls) => {
  editingClassId.value = cls.id;
  editingClass.value = {
    name: cls.name,
    teacherId: cls.teacherId || ''
  };
};

const cancelEditClass = () => {
  editingClassId.value = null;
  editingClass.value = { name: '', teacherId: '' };
};

const saveEditClass = () => {
  if (!editingClass.value.name) {
    alert('⚠️ 請輸入班級名稱');
    return;
  }

  const success = classesStore.updateClass(
    editingClassId.value,
    editingClass.value.name,
    editingClass.value.teacherId || null
  );

  if (success) {
    alert('✅ 班級更新成功！');
    cancelEditClass();
  } else {
    alert('❌ 更新失敗，請檢查輸入');
  }
};

const deleteClass = (classId) => {
  const classInfo = classesStore.classes.find(c => c.id === classId);
  if (!classInfo) return;

  const studentCount = getStudentCountInClass(classId);
  const parentCount = getParentCountInClass(classId);

  if (studentCount > 0 || parentCount > 0) {
    alert(`⚠️ 無法刪除：此班級還有 ${studentCount} 位學生和 ${parentCount} 位家長`);
    return;
  }

  if (confirm(`確定要刪除班級「${classInfo.name}」嗎？`)) {
    const success = classesStore.deleteClass(classId);
    if (success) {
      alert('✅ 班級已刪除！');
    } else {
      alert('❌ 刪除失敗');
    }
  }
};

const addNewClass = () => {
  if (!newClass.value.name) {
    alert('⚠️ 請輸入班級名稱');
    return;
  }
  
  classesStore.addClass(newClass.value.name, newClass.value.teacherId);
  alert('✅ 班級新增成功！');
  newClass.value = { name: '', teacherId: '' };
  showAddClassForm.value = false;
};

const approveApplication = (applicationId) => {
  classesStore.approveRegistration(applicationId, sessionStore.user?.id);
  alert('✅ 申請已批准！');
};

const rejectApplication = (applicationId) => {
  if (confirm('確定要拒絕此申請嗎？')) {
    classesStore.rejectRegistration(applicationId);
    alert('✅ 申請已拒絕！');
  }
};

const handleLogout = () => {
  sessionStore.reset();
  router.push({ name: 'login' });
};
</script>

<style scoped>
.admin-shell {
  display: flex;
  min-height: 100vh;
  background: #F8FAFC;
}

.admin-sidebar {
  width: 280px;
  background: #1e293b;
  color: white;
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
  left: 0;
  top: 0;
  overflow-y: auto;
}

.logo-section {
  padding: 1.5rem;
  border-bottom: 1px solid #334155;
}

.logo {
  font-size: 1.3rem;
  font-weight: 700;
  color: #fff;
}

.admin-sidebar nav {
  flex: 1;
  padding: 1rem 0;
}

.admin-sidebar button {
  width: 100%;
  padding: 0.75rem 1.5rem;
  border: none;
  background: transparent;
  color: #cbd5e1;
  text-align: left;
  cursor: pointer;
  font-size: 0.95rem;
  transition: all 0.2s;
}

.admin-sidebar button:hover {
  background: #334155;
  color: #fff;
}

.admin-sidebar button.active {
  background: #3b82f6;
  color: white;
  border-right: 4px solid #60a5fa;
}

.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid #334155;
}

.logout-btn-sidebar {
  width: 100%;
  padding: 0.75rem;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

.logout-btn-sidebar:hover {
  background: #dc2626;
}

.admin-content {
  margin-left: 280px;
  flex: 1;
  padding: 2rem;
}

.tab-content {
  background: white;
  border-radius: 0.75rem;
  border: 2px solid #e2e8f0;
  padding: 2rem;
}

.tab-content h1 {
  color: #1e3a8a;
  margin: 0 0 1.5rem 0;
  font-size: 1.75rem;
}

/* 統計卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.stat-card {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  padding: 1.5rem;
  border-radius: 0.75rem;
  text-align: center;
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: 0.95rem;
  opacity: 0.9;
}

/* 表單 */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.add-btn {
  padding: 0.5rem 1rem;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

.add-btn:hover {
  background: #059669;
}

.form-card {
  background: #f0fdf4;
  border: 2px solid #dcfce7;
  border-radius: 0.5rem;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.form-card h3 {
  color: #1e3a8a;
  margin: 0 0 1rem 0;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #374151;
  font-weight: 500;
  font-size: 0.9rem;
}

.form-input,
.form-select {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e5e7eb;
  border-radius: 0.5rem;
  font-size: 0.95rem;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1rem;
}

.cancel-btn,
.save-btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.cancel-btn {
  background: #e5e7eb;
  color: #374151;
}

.cancel-btn:hover {
  background: #d1d5db;
}

.save-btn {
  background: #3b82f6;
  color: white;
}

.save-btn:hover {
  background: #2563eb;
}

/* 表格 */
.data-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1.5rem;
}

.data-table thead {
  background: #f3f4f6;
}

.data-table th {
  padding: 1rem;
  text-align: left;
  color: #1e3a8a;
  font-weight: 600;
  border-bottom: 2px solid #e5e7eb;
}

.data-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.data-table tbody tr:hover {
  background: #f9fafb;
}

.edit-btn,
.delete-btn {
  padding: 0.4rem 0.8rem;
  margin-right: 0.5rem;
  border: none;
  border-radius: 0.4rem;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.edit-btn {
  background: #3b82f6;
  color: white;
}

.edit-btn:hover {
  background: #2563eb;
}

.delete-btn {
  background: #ef4444;
  color: white;
}

.delete-btn:hover {
  background: #dc2626;
}

.inline-input {
  width: 100%;
  padding: 0.4rem 0.6rem;
  border: 2px solid #e5e7eb;
  border-radius: 0.4rem;
  font-size: 0.9rem;
}

.inline-input:focus {
  outline: none;
  border-color: #3b82f6;
}

.save-btn-small,
.cancel-btn-small {
  padding: 0.3rem 0.6rem;
  margin-right: 0.5rem;
  border: none;
  border-radius: 0.4rem;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.save-btn-small {
  background: #10b981;
  color: white;
}

.save-btn-small:hover {
  background: #059669;
}

.cancel-btn-small {
  background: #e5e7eb;
  color: #374151;
}

.cancel-btn-small:hover {
  background: #d1d5db;
}

/* 審核標籤 */
.approval-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.approval-tab {
  padding: 0.5rem 1rem;
  background: #e5e7eb;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.approval-tab:hover {
  background: #d1d5db;
}

.approval-tab.active {
  background: #3b82f6;
  color: white;
}

.approval-list {
  display: grid;
  gap: 1rem;
}

.approval-card {
  background: #fff;
  border: 2px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.approval-info h4 {
  margin: 0 0 0.5rem 0;
  color: #1e3a8a;
}

.approval-info p {
  margin: 0.25rem 0;
  color: #6b7280;
  font-size: 0.9rem;
}

.approval-actions {
  display: flex;
  gap: 0.5rem;
}

.approve-btn,
.reject-btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.approve-btn {
  background: #10b981;
  color: white;
}

.approve-btn:hover {
  background: #059669;
}

.reject-btn {
  background: #ef4444;
  color: white;
}

.reject-btn:hover {
  background: #dc2626;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}

/* 狀態徽章 */
.role-badge,
.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.85rem;
  font-weight: 500;
}

.role-badge.teacher {
  background: #dbeafe;
  color: #1e40af;
}

.role-badge.student {
  background: #fef3c7;
  color: #92400e;
}

.role-badge.parent {
  background: #ddd6fe;
  color: #4c1d95;
}

.status-badge.approved {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.pending {
  background: #fed7aa;
  color: #92400e;
}

/* 用戶過濾 */
.users-filter {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.filter-btn {
  padding: 0.5rem 1rem;
  background: #e5e7eb;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-btn:hover {
  background: #d1d5db;
}

.filter-btn.active {
  background: #3b82f6;
  color: white;
}

@media (max-width: 768px) {
  .admin-sidebar {
    width: 200px;
  }

  .admin-content {
    margin-left: 200px;
    padding: 1rem;
  }

  .approval-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .approval-actions {
    width: 100%;
    margin-top: 1rem;
  }
}
</style>
