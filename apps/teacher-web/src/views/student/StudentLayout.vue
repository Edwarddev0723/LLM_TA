<template>
  <div class="student-shell">
    <aside v-if="!isTeachingImmersive" class="sidebar">
      <div class="logo-section">
        <div class="logo">AI 助教</div>
        <div class="user-badge" v-if="currentUser" @click="go('student-profile-edit')">
          <div class="user-avatar">👤</div>
          <div class="user-details">
            <div class="user-name">{{ currentUser.name }}</div>
            <div class="user-class">{{ currentUser.class }}</div>
          </div>
          <button class="edit-profile-btn" @click.stop="go('student-profile-edit')" title="編輯個人資料">
            ✏️
          </button>
        </div>
      </div>
      <nav>
        <button 
          @click="go('student-dashboard')" 
          :class="{ active: route.name === 'student-dashboard' }"
        >
          🏠 首頁
        </button>
        <button 
          @click="go('student-practice')"
          :class="{ active: route.name === 'student-practice' }"
        >
          ✍️ 做題模式
        </button>
        <button 
          @click="go('student-teaching')"
          :class="{ active: route.name === 'student-teaching' }"
        >
          🗣️ 講題模式
        </button>
        <button 
          @click="go('student-mistakes')"
          :class="{ active: route.name === 'student-mistakes' }"
        >
          ❌ 錯題診所
        </button>
        <button 
          @click="go('student-profile')"
          :class="{ active: route.name === 'student-profile' }"
        >
          🏆 個人檔案
        </button>
      </nav>
      <div class="sidebar-footer">
        <button class="logout-btn-sidebar" @click="handleLogout">
          🚪 登出
        </button>
      </div>
    </aside>
    <main class="content" :class="{ immersive: isTeachingImmersive }">
      <router-view :key="$route.fullPath" />
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useSessionStore } from '@/stores/session';

const route = useRoute();
const router = useRouter();
const sessionStore = useSessionStore();

const currentUser = ref({
  name: '張小明',
  class: '2年3班',
  grade: '國中二年級'
});

onMounted(async () => {
  if (sessionStore.user && sessionStore.user.id) {
    currentUser.value = sessionStore.user;
  } else {
    console.warn('No valid user session found, redirecting to login');
    router.push({ name: 'login' });
    return;
  }
  try {
    const response = await fetch('/api/auth/me', {
      headers: {
        'user-id': sessionStore.user.id
      }
    });

    if (response.ok) {
      const data = await response.json();
      sessionStore.setUser(data.user);
      currentUser.value = data.user;
    } else {
      console.warn('Session validation failed, redirecting to login');
      sessionStore.reset();
      router.push({ name: 'login' });
    }
  } catch (error) {
    console.error('Failed to validate session:', error);
    sessionStore.reset();
    router.push({ name: 'login' });
  }
});

const go = (name) => router.push({ name });

const isTeachingImmersive = computed(() => {
  return route.name === 'student-teaching';
});

const handleLogout = () => {
  sessionStore.reset();
  router.push({ name: 'login' });
};
</script>

<style scoped>
.student-shell {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 240px;
  background: #FFFFFF;
  border-right: 2px solid #BFDBFE;
  padding: 1.5rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  box-shadow: 2px 0 8px rgba(37, 99, 235, 0.05);
  justify-content: space-between;
}

.logo-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.logo {
  font-weight: 700;
  font-size: 1.25rem;
  color: #1e3a8a;
}

.user-badge {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #EFF6FF;
  border-radius: 0.5rem;
  border: 1px solid #BFDBFE;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.user-badge:hover {
  background: #DBEAFE;
  border-color: #2563eb;
}

.edit-profile-btn {
  margin-left: auto;
  background: transparent;
  border: none;
  font-size: 0.9rem;
  cursor: pointer;
  padding: 0.25rem;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.user-badge:hover .edit-profile-btn {
  opacity: 1;
}

.user-avatar {
  font-size: 1.5rem;
  width: 2.5rem;
  height: 2.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #DBEAFE;
  border-radius: 50%;
}

.user-details {
  flex: 1;
}

.user-name {
  font-weight: 600;
  color: #1e3a8a;
  font-size: 0.9rem;
}

.user-class {
  font-size: 0.75rem;
  color: #6B7280;
  margin-top: 0.25rem;
}

nav {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

nav button {
  border-radius: 0.5rem;
  border: none;
  padding: 0.6rem 0.9rem;
  background: transparent;
  color: #3b82f6;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
  font-size: 0.95rem;
}

nav button:hover {
  background: #EFF6FF;
  color: #1e3a8a;
}

nav button.active {
  background: #DBEAFE;
  color: #1e3a8a;
  font-weight: 600;
}

.sidebar-footer {
  margin-top: auto;
  padding-top: 1rem;
  border-top: 1px solid #E5E7EB;
}

.logout-btn-sidebar {
  width: 100%;
  padding: 0.6rem 0.9rem;
  background: #FEE2E2;
  color: #DC2626;
  border: 1px solid #FECACA;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s;
  text-align: left;
}

.logout-btn-sidebar:hover {
  background: #FECACA;
  color: #991B1B;
}

.content {
  flex: 1;
  background: #F8FAFC;
}

.content.immersive {
  width: 100%;
}
</style>


