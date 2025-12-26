<template>
  <div class="profile-edit-page">
    <header class="page-header">
      <div>
        <h1>編輯個人資料</h1>
        <p>更新你的個人資訊</p>
      </div>
      <button class="back-btn" @click="goBack">← 返回</button>
    </header>

    <div class="profile-edit-card">
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
            <label>年級</label>
            <select v-model="editedProfile.grade" class="form-input">
              <option value="國中一年級">國中一年級</option>
              <option value="國中二年級">國中二年級</option>
              <option value="國中三年級">國中三年級</option>
            </select>
          </div>
          <div class="form-group">
            <label>班級</label>
            <input 
              type="text" 
              v-model="editedProfile.class" 
              class="form-input"
              placeholder="例如：2年3班"
            />
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useSessionStore } from '@/stores/session';

const router = useRouter();
const sessionStore = useSessionStore();

const editedProfile = ref({
  name: '',
  grade: '',
  class: '',
  email: '',
  phone: ''
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
</style>

