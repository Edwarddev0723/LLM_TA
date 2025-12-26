<template>
  <main class="role-page">
    <section class="hero">
      <h1>AI 助教 (AI Tutor)</h1>
      <p>選擇您的角色以進入專屬體驗。</p>
    </section>
    <section class="roles">
      <button class="role-card student" @click="enter('student')">
        <span class="icon">🎧</span>
        <h2>學生 Student</h2>
        <p>進入沉浸式講題與做題模式。</p>
      </button>
      <button class="role-card teacher" @click="enter('teacher')">
        <span class="icon">📊</span>
        <h2>老師 Teacher</h2>
        <p>查看班級掌握度與 AI 教學建議。</p>
      </button>
      <button class="role-card parent" @click="enter('parent')">
        <span class="icon">👨‍👩‍👧</span>
        <h2>家長 Parent</h2>
        <p>追蹤長期口說與專注習慣趨勢。</p>
      </button>
      <button class="role-card admin" @click="enter('admin')">
        <span class="icon">⚙️</span>
        <h2>管理員 Admin</h2>
        <p>管理班級、審核用戶及系統設定。</p>
      </button>
    </section>
  </main>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { useSessionStore } from '@/stores/session';

const router = useRouter();
const session = useSessionStore();

const enter = (role) => {
  // 設置假用戶資料
  const userData = {
    student: {
      name: '張小明',
      id: 'student-001',
      grade: '國中二年級',
      class: '2年3班'
    },
    teacher: {
      name: '王老師',
      id: 'teacher-001',
      class: '2年3班'
    },
    parent: {
      name: '張家長',
      id: 'parent-001',
      studentName: '張小明'
    },
    admin: {
      name: '系統管理員',
      id: 'admin-001',
      email: 'admin@school.edu'
    }
  };
  
  session.setRole(role);
  session.setUser(userData[role]);
  
  if (role === 'student') router.push({ name: 'student-dashboard' });
  else if (role === 'teacher') router.push({ name: 'teacher-overview' });
  else if (role === 'parent') router.push({ name: 'parent-overview' });
  else if (role === 'admin') router.push({ name: 'admin-dashboard' });
};
</script>

<style scoped>
.role-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 50%, #BFDBFE 100%);
  color: #1e3a8a;
}

.hero {
  text-align: center;
  margin-bottom: 2rem;
}

.hero h1 {
  font-size: 2.25rem;
  margin-bottom: 0.5rem;
  color: #1e3a8a;
  font-weight: 700;
}

.hero p {
  color: #3b82f6;
  font-size: 1.1rem;
}

.roles {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.5rem;
  width: 100%;
  max-width: 960px;
}

.role-card {
  border-radius: 1rem;
  padding: 1.5rem;
  border: 2px solid #BFDBFE;
  background: #FFFFFF;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.5rem;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease,
    border-color 0.15s ease, background 0.15s ease;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
}

.role-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(37, 99, 235, 0.2);
  border-color: #2563eb;
  background: #EFF6FF;
}

.icon {
  font-size: 1.75rem;
}

.role-card h2 {
  font-size: 1.25rem;
  margin: 0;
  color: #1e3a8a;
  font-weight: 600;
}

.role-card p {
  margin: 0;
  font-size: 0.95rem;
  color: #3b82f6;
}

.role-card.admin {
  border-color: #A78BFA;
  background: #F5F3FF;
}

.role-card.admin:hover {
  border-color: #8b5cf6;
  background: #EDE9FE;
}

.role-card.admin h2,
.role-card.admin p {
  color: #6d28d9;
}

.role-card.admin:hover p {
  color: #8b5cf6;
}
</style>


