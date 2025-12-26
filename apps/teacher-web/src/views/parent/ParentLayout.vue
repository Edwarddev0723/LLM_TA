<template>
  <div class="parent-layout">
    <nav class="parent-nav">
      <div class="nav-header">
        <h2>家長儀表板</h2>
        <div class="user-badge" v-if="currentUser" @click="goToProfile">
          <div class="user-avatar">👤</div>
          <div class="user-details">
            <div class="user-name">{{ currentUser.name }}</div>
            <div class="user-student" v-if="currentUser.studentName">
              <span class="label">子女：</span>{{ currentUser.studentName }}
            </div>
          </div>
          <button class="edit-profile-btn" @click.stop="goToProfile" title="編輯個人資料">
            ✏️
          </button>
        </div>
      </div>
      <ul class="nav-menu">
        <li>
          <router-link to="/parent" class="nav-link">📊 總覽</router-link>
        </li>
      </ul>
      <div class="sidebar-footer">
        <button class="logout-btn-sidebar" @click="handleLogout">
          🚪 登出
        </button>
      </div>
    </nav>
    <main class="parent-content">
      <router-view :key="$route.fullPath" />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useSessionStore } from '@/stores/session';

const router = useRouter();
const sessionStore = useSessionStore();

const currentUser = ref({
  name: '張家長',
  id: 'parent-001',
  studentName: '張小明',
  email: 'parent@example.com',
  phone: '0912-345-679',
  relationship: '父親'
});

onMounted(async () => {
  if (sessionStore.user && sessionStore.user.id) {
    currentUser.value = { ...currentUser.value, ...sessionStore.user };
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
      currentUser.value = { ...currentUser.value, ...data.user };
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

const goToProfile = () => {
  router.push({ name: 'parent-profile-edit' });
};

const handleLogout = () => {
  sessionStore.reset();
  router.push({ name: 'login' });
};
</script>

<style scoped>
.parent-layout {
  display: flex;
  min-height: 100vh;
  background: #F8FAFC;
}

.parent-nav {
  width: 240px;
  background: #FFFFFF;
  border-right: 2px solid #BFDBFE;
  box-shadow: 2px 0 8px rgba(37, 99, 235, 0.05);
  padding: 2rem 1rem;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.nav-header {
  margin-bottom: 2rem;
}

.nav-header h2 {
  margin: 0 0 1rem 0;
  color: #1e3a8a;
  font-size: 1.2rem;
  font-weight: 700;
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
  margin-top: 1rem;
}

.user-badge:hover {
  background: #DBEAFE;
  border-color: #2563eb;
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

.user-student {
  font-size: 0.75rem;
  color: #6B7280;
  margin-top: 0.25rem;
}

.user-student .label {
  color: #3b82f6;
  font-weight: 500;
}

.edit-profile-btn {
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
}

.logout-btn-sidebar:hover {
  background: #FECACA;
  color: #991B1B;
}

.nav-menu {
  list-style: none;
  padding: 0;
  margin: 0;
}

.nav-menu li {
  margin-bottom: 0.5rem;
}

.nav-link {
  display: block;
  padding: 0.75rem 1rem;
  color: #3b82f6;
  text-decoration: none;
  border-radius: 0.5rem;
  transition: background 0.2s, color 0.2s;
  font-size: 0.95rem;
}

.nav-link:hover,
.nav-link.router-link-active {
  background: #EFF6FF;
  color: #1e3a8a;
  font-weight: 500;
}

.parent-content {
  flex: 1;
  padding: 2rem;
  background: #F8FAFC;
}
</style>

