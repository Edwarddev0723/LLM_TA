<template>
  <div class="teaching-suggestions">
    <h1>LLM 教學建議</h1>
    <div class="suggestions-list">
      <div
        v-for="suggestion in suggestions"
        :key="suggestion.id"
        class="suggestion-card"
      >
        <div class="suggestion-header">
          <h3>{{ suggestion.title }}</h3>
          <span class="priority" :class="`priority-${suggestion.priority}`">
            {{ suggestion.priority === 'high' ? '高' : '中' }}
          </span>
        </div>
        <p class="suggestion-content">{{ suggestion.content }}</p>
        <div class="suggestion-meta">
          <span>針對: {{ suggestion.target }}</span>
          <span>生成時間: {{ suggestion.date }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';

export default {
  name: 'TeachingSuggestions',
  setup() {
    const suggestions = ref([
      {
        id: 1,
        title: '加強因式分解概念教學',
        content:
          '根據錯題分析，班級中有 65% 的學生在因式分解單元出現困難。建議使用視覺化工具輔助教學，並提供更多練習題。',
        priority: 'high',
        target: '全班',
        date: '2025-12-03'
      },
      {
        id: 2,
        title: '個別輔導建議 - 李小花',
        content:
          '該學生在口語表達方面需要加強，WPM 較低且停頓比例高。建議多鼓勵口述解題，並給予正向回饋。',
        priority: 'medium',
        target: '李小花',
        date: '2025-12-02'
      },
      {
        id: 3,
        title: '調整教學節奏',
        content:
          '觀察到學生在 45 分鐘後專注度明顯下降。建議將課程分為兩個 30 分鐘區塊，中間加入短暫休息。',
        priority: 'medium',
        target: '全班',
        date: '2025-12-01'
      }
    ]);

    return {
      suggestions
    };
  }
};
</script>

<style scoped>
.teaching-suggestions {
  background: white;
  border-radius: 8px;
  padding: 2rem;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin-top: 1.5rem;
}

.suggestion-card {
  background: #f9fafb;
  border-radius: 8px;
  padding: 1.5rem;
  border-left: 4px solid #2563eb;
}

.suggestion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.suggestion-header h3 {
  margin: 0;
  color: #1e3a8a;
}

.priority {
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 600;
}

.priority-high {
  background: #fee2e2;
  color: #991b1b;
}

.priority-medium {
  background: #fef3c7;
  color: #92400e;
}

.suggestion-content {
  color: #374151;
  line-height: 1.6;
  margin-bottom: 1rem;
}

.suggestion-meta {
  display: flex;
  gap: 1.5rem;
  font-size: 0.85rem;
  color: #666;
}
</style>

