<template>
  <div class="profile-rewards-page">
    <header class="page-header">
      <div>
        <h1>個人檔案與獎勵</h1>
        <p>查看你的學習成就與統計資料</p>
      </div>
    </header>
    
    <div class="profile-rewards">
      <!-- 用戶資訊卡片 -->
      <div class="user-profile-card">
        <div class="user-avatar-large">👤</div>
        <div class="user-info">
          <h2>{{ userInfo.name }}</h2>
          <p>{{ userInfo.grade }} | {{ userInfo.class }}</p>
          <div class="user-level">
            <span class="level-badge">等級 {{ userInfo.level }}</span>
            <div class="level-progress">
              <div class="progress-bar" :style="{ width: `${userInfo.expProgress}%` }"></div>
            </div>
            <small>經驗值：{{ userInfo.exp }}/{{ userInfo.expToNext }}</small>
          </div>
        </div>
      </div>

      <!-- 學習成就 -->
      <div class="profile-section">
        <h2>學習成就</h2>
        <div class="achievements">
          <div 
            v-for="achievement in achievements" 
            :key="achievement.id" 
            class="achievement-card"
            :class="{ 'unlocked': achievement.unlocked }"
          >
            <div class="achievement-icon">{{ achievement.icon }}</div>
            <div class="achievement-info">
              <h3>{{ achievement.title }}</h3>
              <p>{{ achievement.description }}</p>
              <span class="achievement-date" v-if="achievement.unlocked">
                獲得日期：{{ achievement.unlockedDate }}
              </span>
            </div>
            <button 
              class="test-btn" 
              v-if="!achievement.unlocked"
              @click="testUnlockAchievement(achievement.id)"
            >
              測試解鎖
            </button>
          </div>
        </div>
      </div>

      <!-- 學習統計 -->
      <div class="stats-section">
        <h2>學習統計</h2>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-value">{{ stats.totalPractice }}</div>
            <div class="stat-label">總練習題數</div>
            <button class="test-btn-small" @click="testAddPractice">+10 題</button>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ stats.totalHours }}</div>
            <div class="stat-label">總學習時數</div>
            <button class="test-btn-small" @click="testAddHours">+1 小時</button>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ stats.streakDays }}</div>
            <div class="stat-label">連續學習天數</div>
            <button class="test-btn-small" @click="testAddStreak">+1 天</button>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ stats.totalMistakes }}</div>
            <div class="stat-label">累積錯題數</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ stats.avgCorrectRate }}%</div>
            <div class="stat-label">平均正確率</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ stats.totalSessions }}</div>
            <div class="stat-label">總練習次數</div>
          </div>
        </div>
      </div>

      <!-- 測試功能區 -->
      <div class="test-section">
        <h2>測試功能</h2>
        <div class="test-buttons">
          <button class="test-action-btn" @click="resetStats">重置統計</button>
          <button class="test-action-btn" @click="addRandomAchievement">隨機解鎖成就</button>
          <button class="test-action-btn" @click="simulateWeekProgress">模擬一週進度</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useSessionStore } from '@/stores/session';

const sessionStore = useSessionStore();

const userInfo = ref({
  name: '張小明',
  grade: '國中二年級',
  class: '2年3班',
  level: 5,
  exp: 1250,
  expToNext: 2000,
  expProgress: 62.5
});

const achievements = ref([
  {
    id: 1,
    icon: '🏆',
    title: '初學者',
    description: '完成第一次練習',
    unlocked: true,
    unlockedDate: '2025-11-15'
  },
  {
    id: 2,
    icon: '⭐',
    title: '持續學習',
    description: '連續學習 7 天',
    unlocked: true,
    unlockedDate: '2025-11-22'
  },
  {
    id: 3,
    icon: '🎯',
    title: '精準表達',
    description: 'WPM 達到 120',
    unlocked: true,
    unlockedDate: '2025-11-28'
  },
  {
    id: 4,
    icon: '🔥',
    title: '學習狂熱',
    description: '連續學習 30 天',
    unlocked: false,
    unlockedDate: null
  },
  {
    id: 5,
    icon: '💯',
    title: '完美表現',
    description: '單次練習正確率 100%',
    unlocked: false,
    unlockedDate: null
  },
  {
    id: 6,
    icon: '🚀',
    title: '快速解題',
    description: 'WPM 達到 150',
    unlocked: false,
    unlockedDate: null
  }
]);

const stats = ref({
  totalPractice: 156,
  totalHours: 42,
  streakDays: 12,
  totalMistakes: 38,
  avgCorrectRate: 76,
  totalSessions: 48
});

const testUnlockAchievement = (id) => {
  const achievement = achievements.value.find(a => a.id === id);
  if (achievement && !achievement.unlocked) {
    achievement.unlocked = true;
    achievement.unlockedDate = new Date().toISOString().split('T')[0];
    alert(`✅ 成就解鎖：${achievement.title}`);
  }
};

const testAddPractice = () => {
  stats.value.totalPractice += 10;
  userInfo.value.exp += 50;
  updateLevel();
  alert('✅ 已增加 10 題練習');
};

const testAddHours = () => {
  stats.value.totalHours += 1;
  userInfo.value.exp += 100;
  updateLevel();
  alert('✅ 已增加 1 小時學習時數');
};

const testAddStreak = () => {
  stats.value.streakDays += 1;
  userInfo.value.exp += 30;
  updateLevel();
  
  // 檢查是否解鎖成就
  if (stats.value.streakDays === 7) {
    const achievement = achievements.value.find(a => a.id === 2);
    if (achievement && !achievement.unlocked) {
      testUnlockAchievement(2);
    }
  }
  if (stats.value.streakDays === 30) {
    const achievement = achievements.value.find(a => a.id === 4);
    if (achievement && !achievement.unlocked) {
      testUnlockAchievement(4);
    }
  }
  
  alert('✅ 已增加 1 天連續學習');
};

const updateLevel = () => {
  if (userInfo.value.exp >= userInfo.value.expToNext) {
    userInfo.value.level += 1;
    userInfo.value.exp = userInfo.value.exp - userInfo.value.expToNext;
    userInfo.value.expToNext = userInfo.value.level * 400;
    alert(`🎉 升級了！現在是等級 ${userInfo.value.level}`);
  }
  userInfo.value.expProgress = (userInfo.value.exp / userInfo.value.expToNext) * 100;
};

const resetStats = () => {
  if (confirm('確定要重置所有統計資料嗎？')) {
    stats.value = {
      totalPractice: 0,
      totalHours: 0,
      streakDays: 0,
      totalMistakes: 0,
      avgCorrectRate: 0,
      totalSessions: 0
    };
    userInfo.value.level = 1;
    userInfo.value.exp = 0;
    userInfo.value.expToNext = 400;
    userInfo.value.expProgress = 0;
    alert('✅ 統計資料已重置');
  }
};

const addRandomAchievement = () => {
  const locked = achievements.value.filter(a => !a.unlocked);
  if (locked.length === 0) {
    alert('所有成就都已解鎖！');
    return;
  }
  const random = locked[Math.floor(Math.random() * locked.length)];
  testUnlockAchievement(random.id);
};

const simulateWeekProgress = () => {
  stats.value.totalPractice += 35;
  stats.value.totalHours += 7;
  stats.value.streakDays += 7;
  stats.value.totalSessions += 7;
  userInfo.value.exp += 500;
  updateLevel();
  alert('✅ 已模擬一週的學習進度');
};
</script>

<style scoped>
.profile-rewards-page {
  padding: 2rem;
  background: #F8FAFC;
  min-height: 100vh;
}

.page-header {
  background: #FFFFFF;
  padding: 1.5rem;
  border-radius: 0.75rem;
  border: 2px solid #BFDBFE;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
  margin-bottom: 1.5rem;
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

.profile-rewards {
  color: #1e3a8a;
}

.user-profile-card {
  background: #FFFFFF;
  border-radius: 0.75rem;
  padding: 2rem;
  border: 2px solid #BFDBFE;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
  display: flex;
  align-items: center;
  gap: 2rem;
  margin-bottom: 2rem;
}

.user-avatar-large {
  font-size: 4rem;
  width: 5rem;
  height: 5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #EFF6FF;
  border-radius: 50%;
  border: 3px solid #BFDBFE;
}

.user-info h2 {
  margin: 0 0 0.5rem 0;
  color: #1e3a8a;
  font-size: 1.5rem;
}

.user-info p {
  margin: 0 0 1rem 0;
  color: #6B7280;
}

.user-level {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.level-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  background: #DBEAFE;
  color: #1e40af;
  border-radius: 0.5rem;
  font-size: 0.85rem;
  font-weight: 600;
  width: fit-content;
}

.level-progress {
  width: 200px;
  height: 8px;
  background: #E5E7EB;
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #2563eb, #3b82f6);
  transition: width 0.3s;
}

.user-level small {
  color: #6B7280;
  font-size: 0.8rem;
}

.profile-section,
.stats-section {
  margin-bottom: 2rem;
}

.profile-section h2,
.stats-section h2 {
  color: #1e3a8a;
  margin-bottom: 0.75rem;
}

.achievements {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.achievement-card {
  background: #FFFFFF;
  border-radius: 0.75rem;
  padding: 1.5rem;
  border: 2px solid #BFDBFE;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: transform 0.2s, box-shadow 0.2s;
  position: relative;
}

.achievement-card.unlocked {
  border-color: #10B981;
  background: linear-gradient(135deg, #FFFFFF 0%, #F0FDF4 100%);
}

.achievement-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15);
}

.achievement-card:not(.unlocked) {
  opacity: 0.7;
}

.achievement-icon {
  font-size: 2.5rem;
}

.achievement-info h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  color: #1e3a8a;
}

.achievement-info {
  flex: 1;
}

.achievement-info p {
  margin: 0.25rem 0 0 0;
  color: #6B7280;
  font-size: 0.9rem;
}

.achievement-date {
  display: block;
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: #10B981;
}

.test-btn {
  padding: 0.4rem 0.8rem;
  background: #EFF6FF;
  color: #2563eb;
  border: 1px solid #BFDBFE;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s;
}

.test-btn:hover {
  background: #DBEAFE;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-top: 1rem;
}

.stat-card {
  background: #FFFFFF;
  border-radius: 0.75rem;
  padding: 1.5rem;
  text-align: center;
  border: 2px solid #BFDBFE;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
  position: relative;
}

.test-btn-small {
  margin-top: 0.75rem;
  padding: 0.3rem 0.6rem;
  background: #EFF6FF;
  color: #2563eb;
  border: 1px solid #BFDBFE;
  border-radius: 0.4rem;
  cursor: pointer;
  font-size: 0.75rem;
  transition: all 0.2s;
}

.test-btn-small:hover {
  background: #DBEAFE;
}

.test-section {
  margin-top: 2rem;
  background: #FFFFFF;
  border-radius: 0.75rem;
  padding: 1.5rem;
  border: 2px solid #BFDBFE;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
}

.test-section h2 {
  color: #1e3a8a;
  margin: 0 0 1rem 0;
}

.test-buttons {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.test-action-btn {
  padding: 0.6rem 1.2rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: background 0.2s;
}

.test-action-btn:hover {
  background: #1d4ed8;
}

.stat-value {
  font-size: 2.5rem;
  font-weight: bold;
  color: #2563eb;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: #6B7280;
  font-size: 0.9rem;
}
</style>

