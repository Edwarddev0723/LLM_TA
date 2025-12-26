<template>
  <div class="login-page">
    <div class="login-card">
      <h1>AI 助教</h1>
      <p class="subtitle">{{ isLoginMode ? '請登入您的帳戶' : '建立新帳戶' }}</p>

      <!-- 模式切換 -->
      <div class="mode-toggle">
        <button
          :class="['mode-btn', { active: isLoginMode }]"
          @click="setMode(true)"
        >
          登入
        </button>
        <button
          :class="['mode-btn', { active: !isLoginMode }]"
          @click="setMode(false)"
        >
          註冊
        </button>
      </div>

      <!-- 登入表單 -->
      <form v-if="isLoginMode" @submit.prevent="handleLogin" class="auth-form">
        <div class="form-group">
          <label for="login-email">電子郵件</label>
          <input
            id="login-email"
            v-model="loginForm.email"
            type="email"
            required
            placeholder="輸入您的電子郵件"
          >
        </div>

        <div class="form-group">
          <label for="login-password">密碼</label>
          <input
            id="login-password"
            v-model="loginForm.password"
            type="password"
            required
            placeholder="輸入您的密碼"
          >
        </div>

        <button type="submit" class="submit-btn" :disabled="loading">
          {{ loading ? '登入中...' : '登入' }}
        </button>
      </form>

      <!-- 註冊表單 -->
      <form v-else @submit.prevent="handleRegister" class="auth-form">
        <div class="form-group">
          <label for="register-fullName">姓名</label>
          <input
            id="register-fullName"
            v-model="registerForm.fullName"
            type="text"
            required
            placeholder="輸入您的真實姓名"
          >
        </div>

        <div class="form-group">
          <label for="register-email">電子郵件</label>
          <input
            id="register-email"
            v-model="registerForm.email"
            type="email"
            required
            placeholder="輸入您的電子郵件"
          >
        </div>

        <div class="form-group">
          <label for="register-password">密碼</label>
          <input
            id="register-password"
            v-model="registerForm.password"
            type="password"
            required
            placeholder="設定密碼"
          >
        </div>

        <div class="form-group">
          <label for="register-role">角色</label>
          <select id="register-role" v-model="registerForm.role" required>
            <option value="">選擇角色</option>
            <option value="student">學生</option>
            <option value="teacher">老師</option>
            <option value="parent">家長</option>
          </select>
        </div>

        <div class="form-group" v-if="registerForm.role === 'teacher'">
          <label for="register-idDocument">教師證明文件</label>
          <input
            id="register-idDocument"
            type="file"
            ref="idDocumentInput"
            accept="image/*"
            required
            @change="handleFileSelect"
          >
          <small class="file-hint">請上傳證明文件，檔案大小限制 5MB</small>
        </div>

        <button type="submit" class="submit-btn" :disabled="loading">
          {{ loading ? '註冊中...' : '提交註冊申請' }}
        </button>
      </form>

      <!-- 錯誤訊息 -->
      <div v-if="error" class="error-message">
        {{ error }}
      </div>

      <!-- 成功訊息 -->
      <div v-if="success" class="success-message">
        {{ success }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useSessionStore } from '@/stores/session';

const router = useRouter();
const sessionStore = useSessionStore();

// 表單狀態
const isLoginMode = ref(true);
const loading = ref(false);
const error = ref('');
const success = ref('');

// 登入表單
const loginForm = reactive({
  email: '',
  password: ''
});

// 註冊表單
const registerForm = reactive({
  fullName: '',
  email: '',
  password: '',
  role: '',
  idDocument: null
});

// 文件輸入引用
const idDocumentInput = ref(null);

// 設定模式
const setMode = (loginMode) => {
  isLoginMode.value = loginMode;
  error.value = '';
  success.value = '';
};

// 處理登入
const handleLogin = async () => {
  loading.value = true;
  error.value = '';
  success.value = '';

  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(loginForm)
    });

    const data = await response.json();

    if (response.ok) {
      // 登入成功，先設置基本用戶資料
      sessionStore.setUser(data.user);
      sessionStore.setRole(data.user.role);

      // 獲取完整的用戶資訊
      try {
        const userResponse = await fetch('/api/auth/me', {
          headers: {
            'user-id': data.user.id.toString()
          }
        });

        if (userResponse.ok) {
          const userData = await userResponse.json();
          sessionStore.setUser(userData.user);
        }
      } catch (userError) {
        console.warn('Failed to fetch complete user data:', userError);
      }

      success.value = '登入成功！請選擇您的角色。';

      // 顯示角色選擇
      showRoleSelection(data.user);
    } else {
      error.value = data.detail || data.error || '登入失敗';
    }
  } catch (err) {
    error.value = '網路錯誤，請稍後再試';
  } finally {
    loading.value = false;
  }
};

// 處理註冊
const handleRegister = async () => {
  loading.value = true;
  error.value = '';
  success.value = '';

  try {
    // 創建 FormData 來處理文件上傳
    const formData = new FormData();
    formData.append('fullName', registerForm.fullName);
    formData.append('email', registerForm.email);
    formData.append('password', registerForm.password);
    formData.append('role', registerForm.role);
    if (registerForm.idDocument) {
      formData.append('idDocument', registerForm.idDocument);
    }

    const response = await fetch('/api/auth/register', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    if (response.ok) {
      success.value = registerForm.role === 'teacher'
        ? '註冊成功！請等待管理員審核您的教師證明文件。'
        : '註冊成功！您可以立即登入使用系統。';
      // 切換到登入模式
      setMode(true);
      // 清空註冊表單
      Object.keys(registerForm).forEach(key => {
        registerForm[key] = '';
      });
      // 清空文件輸入
      if (idDocumentInput.value) {
        idDocumentInput.value.value = '';
      }
    } else {
      error.value = data.detail || data.error || '註冊失敗';
    }
  } catch (err) {
    error.value = '網路錯誤，請稍後再試';
  } finally {
    loading.value = false;
  }
};

// 處理文件選擇
const handleFileSelect = (event) => {
  const file = event.target.files[0];
  if (file) {
    // 檢查檔案大小（5MB 限制）
    if (file.size > 5 * 1024 * 1024) {
      error.value = '檔案大小超過 5MB 限制';
      event.target.value = '';
      return;
    }
    registerForm.idDocument = file;
    error.value = ''; // 清空錯誤訊息
  }
};

// 顯示角色選擇（登入成功後）
const showRoleSelection = (user) => {
  // 導航到對應的儀表板
  if (user.role === 'student') {
    router.push({ name: 'student-dashboard' });
  } else if (user.role === 'teacher') {
    router.push({ name: 'teacher-overview' });
  } else if (user.role === 'parent') {
    router.push({ name: 'parent-overview' });
  } else if (user.role === 'admin') {
    router.push({ name: 'admin-dashboard' });
  }
};
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 50%, #BFDBFE 100%);
  padding: 2rem;
}

.login-card {
  background: #FFFFFF;
  border-radius: 1rem;
  padding: 3rem;
  box-shadow: 0 10px 30px rgba(37, 99, 235, 0.2);
  border: 2px solid #BFDBFE;
  max-width: 500px;
  width: 100%;
}

.login-card h1 {
  text-align: center;
  color: #1e3a8a;
  font-size: 2rem;
  margin: 0 0 0.5rem 0;
}

.subtitle {
  text-align: center;
  color: #3b82f6;
  margin: 0 0 2rem 0;
  font-size: 1rem;
}

/* 模式切換 */
.mode-toggle {
  display: flex;
  margin-bottom: 2rem;
  background: #F3F4F6;
  border-radius: 0.5rem;
  padding: 0.25rem;
}

.mode-btn {
  flex: 1;
  padding: 0.75rem;
  border: none;
  background: transparent;
  border-radius: 0.375rem;
  font-weight: 500;
  color: #6B7280;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-btn.active {
  background: #FFFFFF;
  color: #2563eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 表單樣式 */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  color: #374151;
  font-size: 0.9rem;
}

.form-group input,
.form-group select {
  padding: 0.75rem;
  border: 2px solid #E5E7EB;
  border-radius: 0.5rem;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.submit-btn {
  padding: 0.75rem;
  background: #2563eb;
  color: #FFFFFF;
  border: none;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.submit-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.submit-btn:disabled {
  background: #9CA3AF;
  cursor: not-allowed;
}

/* 訊息樣式 */
.error-message {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #FEF2F2;
  border: 1px solid #FECACA;
  border-radius: 0.5rem;
  color: #DC2626;
  font-size: 0.9rem;
}

.success-message {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #F0FDF4;
  border: 1px solid #BBF7D0;
  border-radius: 0.5rem;
  color: #16A34A;
  font-size: 0.9rem;
}
</style>

