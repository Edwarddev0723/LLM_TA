<template>
  <div class="profile-edit-page">
    <header class="page-header">
      <div>
        <h1>教師管理中心</h1>
        <p>管理個人資訊和學生-家長配對</p>
      </div>
      <button class="back-btn" @click="goBack">← 返回</button>
    </header>

    <div class="tabs">
      <button 
        :class="['tab-btn', { active: activeTab === 'profile' }]"
        @click="activeTab = 'profile'"
      >
        個人資料
      </button>
      <button 
        :class="['tab-btn', { active: activeTab === 'pairing' }]"
        @click="activeTab = 'pairing'"
      >
        學生-家長配對
      </button>
    </div>

    <!-- 個人資料標籤 -->
    <div v-if="activeTab === 'profile'" class="profile-edit-card">
      <form @submit.prevent="saveProfile">
        <div class="form-section">
          <h3>基本資訊</h3>
          <div class="form-group">
            <label>姓名</label>
            <input 
              type="text" 
              v-model="editedProfile.name" 
              class="form-input"
              required
            />
          </div>
          <div class="form-group">
            <label>任教班級</label>
            <input 
              type="text" 
              v-model="editedProfile.class" 
              class="form-input"
              placeholder="例如：2年3班"
            />
          </div>
          <div class="form-group">
            <label>教師編號</label>
            <input 
              type="text" 
              v-model="editedProfile.id" 
              class="form-input"
              disabled
            />
            <small class="form-hint">教師編號無法修改</small>
          </div>
        </div>

        <div class="form-section">
          <h3>聯絡資訊</h3>
          <div class="form-group">
            <label>電子郵件</label>
            <input 
              type="email" 
              v-model="editedProfile.email" 
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label>電話</label>
            <input 
              type="tel" 
              v-model="editedProfile.phone" 
              class="form-input"
              placeholder="例如：0912-345-678"
            />
          </div>
        </div>

        <div class="form-actions">
          <button type="button" class="cancel-btn" @click="goBack">取消</button>
          <button type="submit" class="save-btn">儲存變更</button>
        </div>
      </form>
    </div>

    <!-- 學生-家長配對管理標籤 -->
    <div v-if="activeTab === 'pairing'" class="pairing-card">
      <div class="pairing-header">
        <h3>學生-家長配對管理</h3>
        <button class="add-btn" @click="showAddPairingForm = !showAddPairingForm">
          {{ showAddPairingForm ? '✕ 取消' : '+ 新增配對' }}
        </button>
      </div>

      <!-- 新增配對表單 -->
      <div v-if="showAddPairingForm" class="add-pairing-form">
        <div class="form-group">
          <label>選擇學生</label>
          <select v-model="newPairing.studentId" class="form-input">
            <option value="">-- 選擇學生 --</option>
            <option v-for="student in availableStudents" :key="student.id" :value="student.id">
              {{ student.name }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label>選擇家長</label>
          <select v-model="newPairing.parentId" class="form-input">
            <option value="">-- 選擇家長 --</option>
            <option v-for="parent in availableParents" :key="parent.id" :value="parent.id">
              {{ parent.name }}
            </option>
          </select>
        </div>
        <div class="form-actions">
          <button type="button" class="cancel-btn" @click="showAddPairingForm = false">取消</button>
          <button type="button" class="save-btn" @click="addPairing">確認配對</button>
        </div>
      </div>

      <!-- 配對列表 -->
      <table class="pairing-table">
        <thead>
          <tr>
            <th>學生姓名</th>
            <th>家長姓名</th>
            <th>家長關係</th>
            <th>家長聯繫</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="pairing in pairings" :key="pairing.id">
            <td class="student-name">{{ pairing.studentName }}</td>
            <td class="parent-name">{{ pairing.parentName }}</td>
            <td class="relationship">{{ pairing.relationship }}</td>
            <td class="contact">{{ pairing.parentEmail }}</td>
            <td class="actions">
              <button class="delete-btn" @click="removePairing(pairing.id)">刪除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="pairings.length === 0" class="empty-state">
        <p>還沒有配對記錄。點擊「新增配對」開始管理。</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useSessionStore } from '@/stores/session';

const router = useRouter();
const sessionStore = useSessionStore();

const activeTab = ref('profile');
const showAddPairingForm = ref(false);

const editedProfile = ref({
  name: '',
  class: '',
  id: '',
  email: '',
  phone: ''
});

// 假資料：可用的學生和家長
const allStudents = ref([
  { id: 1, name: '張小明' },
  { id: 2, name: '李小花' },
  { id: 3, name: '王大華' },
  { id: 4, name: '陳小華' }
]);

const allParents = ref([
  { id: 1, name: '張家長', email: 'parent1@example.com', relationship: '父親' },
  { id: 2, name: '李家長', email: 'parent2@example.com', relationship: '母親' },
  { id: 3, name: '王家長', email: 'parent3@example.com', relationship: '父親' },
  { id: 4, name: '陳家長', email: 'parent4@example.com', relationship: '母親' }
]);

// 已配對的記錄
const pairings = ref([
  {
    id: 1,
    studentId: 1,
    studentName: '張小明',
    parentId: 1,
    parentName: '張家長',
    relationship: '父親',
    parentEmail: 'parent1@example.com'
  }
]);

const newPairing = ref({
  studentId: '',
  parentId: ''
});

// 計算可用的學生（未配對過的）
const availableStudents = computed(() => {
  const pairedStudentIds = pairings.value.map(p => p.studentId);
  return allStudents.value.filter(s => !pairedStudentIds.includes(s.id));
});

// 計算可用的家長（未配對過的）
const availableParents = computed(() => {
  const pairedParentIds = pairings.value.map(p => p.parentId);
  return allParents.value.filter(p => !pairedParentIds.includes(p.id));
});

onMounted(() => {
  if (sessionStore.user) {
    editedProfile.value = { ...sessionStore.user };
  }
});

const saveProfile = async () => {
  try {
    const response = await fetch('/api/auth/me', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'user-id': sessionStore.user?.id?.toString() || ''
      },
      body: JSON.stringify(editedProfile.value)
    });

    if (response.ok) {
      const data = await response.json();
      sessionStore.setUser(data.user);
      alert('✅ 個人資料已更新！');
      goBack();
    } else {
      const error = await response.json();
      alert('❌ 更新失敗：' + (error.detail || error.error || '未知錯誤'));
    }
  } catch (error) {
    console.error('Save profile error:', error);
    alert('❌ 網路錯誤，請稍後再試');
  }
};

const addPairing = () => {
  if (!newPairing.value.studentId || !newPairing.value.parentId) {
    alert('⚠️ 請選擇學生和家長');
    return;
  }

  const student = allStudents.value.find(s => s.id === parseInt(newPairing.value.studentId));
  const parent = allParents.value.find(p => p.id === parseInt(newPairing.value.parentId));

  const pairing = {
    id: Math.max(...pairings.value.map(p => p.id), 0) + 1,
    studentId: parseInt(newPairing.value.studentId),
    studentName: student.name,
    parentId: parseInt(newPairing.value.parentId),
    parentName: parent.name,
    relationship: parent.relationship,
    parentEmail: parent.email
  };

  pairings.value.push(pairing);
  newPairing.value = { studentId: '', parentId: '' };
  showAddPairingForm.value = false;
  alert('✅ 配對成功！');
};

const removePairing = (pairingId) => {
  if (confirm('確定要刪除此配對嗎？')) {
    pairings.value = pairings.value.filter(p => p.id !== pairingId);
    alert('✅ 配對已刪除！');
  }
};

const goBack = () => {
  router.back();
};
</script>

<style scoped>
.profile-edit-page {
  padding: 2rem;
  background: #F8FAFC;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
  background: #FFFFFF;
  padding: 1.5rem;
  border-radius: 0.75rem;
  border: 2px solid #BFDBFE;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
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

.back-btn {
  padding: 0.5rem 1rem;
  background: #EFF6FF;
  color: #2563eb;
  border: 1px solid #BFDBFE;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #DBEAFE;
}

.profile-edit-card {
  background: #FFFFFF;
  border-radius: 0.75rem;
  padding: 2rem;
  border: 2px solid #BFDBFE;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
}

.form-section {
  margin-bottom: 2rem;
}

.form-section h3 {
  color: #1e3a8a;
  margin: 0 0 1rem 0;
  font-size: 1.2rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #EFF6FF;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #3b82f6;
  font-weight: 500;
  font-size: 0.9rem;
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #BFDBFE;
  border-radius: 0.5rem;
  background: #FFFFFF;
  color: #1e3a8a;
  font-size: 0.95rem;
  transition: border-color 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #2563eb;
}

.form-input:disabled {
  background: #F3F4F6;
  color: #6B7280;
  cursor: not-allowed;
}

.form-hint {
  display: block;
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: #6B7280;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #E5E7EB;
}

.cancel-btn,
.save-btn {
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  border: none;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 500;
  transition: all 0.2s;
}

.cancel-btn {
  background: #F3F4F6;
  color: #374151;
}

.cancel-btn:hover {
  background: #E5E7EB;
}

.save-btn {
  background: #2563eb;
  color: white;
}

.save-btn:hover {
  background: #1d4ed8;
}

/* 標籤樣式 */
.tabs {
  display: flex;
  gap: 0;
  margin-bottom: 1.5rem;
  background: #FFFFFF;
  border: 2px solid #BFDBFE;
  border-radius: 0.75rem;
  overflow: hidden;
}

.tab-btn {
  flex: 1;
  padding: 1rem;
  background: #F3F4F6;
  border: none;
  color: #6B7280;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border-right: 1px solid #BFDBFE;
}

.tab-btn:last-child {
  border-right: none;
}

.tab-btn:hover {
  background: #EFF6FF;
  color: #2563eb;
}

.tab-btn.active {
  background: #2563eb;
  color: white;
}

/* 配對卡片樣式 */
.pairing-card {
  background: #FFFFFF;
  border-radius: 0.75rem;
  padding: 2rem;
  border: 2px solid #BFDBFE;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
}

.pairing-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #EFF6FF;
}

.pairing-header h3 {
  color: #1e3a8a;
  margin: 0;
  font-size: 1.2rem;
}

.add-btn {
  padding: 0.5rem 1rem;
  background: #10B981;
  color: white;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s;
}

.add-btn:hover {
  background: #059669;
}

/* 新增配對表單 */
.add-pairing-form {
  background: #F0FDF4;
  border: 2px solid #DCFCE7;
  border-radius: 0.5rem;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.add-pairing-form .form-group {
  margin-bottom: 1rem;
}

/* 配對表格 */
.pairing-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1.5rem;
}

.pairing-table thead {
  background: #EFF6FF;
}

.pairing-table th {
  padding: 1rem;
  text-align: left;
  color: #1e3a8a;
  font-weight: 600;
  border: 1px solid #BFDBFE;
  font-size: 0.9rem;
}

.pairing-table td {
  padding: 0.75rem 1rem;
  border: 1px solid #BFDBFE;
  color: #374151;
  font-size: 0.9rem;
}

.pairing-table tbody tr:hover {
  background: #F8FAFC;
}

.pairing-table .student-name {
  font-weight: 600;
  color: #1e3a8a;
}

.pairing-table .parent-name {
  color: #2563eb;
}

.pairing-table .relationship {
  color: #6B7280;
}

.pairing-table .actions {
  text-align: center;
}

.delete-btn {
  padding: 0.4rem 0.8rem;
  background: #EF4444;
  color: white;
  border: none;
  border-radius: 0.4rem;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.delete-btn:hover {
  background: #DC2626;
}

/* 空狀態 */
.empty-state {
  text-align: center;
  padding: 2rem;
  color: #6B7280;
  background: #F9FAFB;
  border-radius: 0.5rem;
  border: 2px dashed #BFDBFE;
}

.empty-state p {
  margin: 0;
  font-size: 0.95rem;
}
</style>

