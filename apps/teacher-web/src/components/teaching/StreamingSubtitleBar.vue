<template>
  <div class="subtitle-bar" :class="status">
    <div class="content">
      <span class="icon" v-if="status === 'listening'">🎙️</span>
      <span class="icon" v-else-if="status === 'processing'">⋯</span>
      <span class="icon" v-else>🤖</span>
      <p class="text">{{ text || placeholder }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  status: {
    type: String,
    default: 'listening' // listening | processing | speaking
  },
  text: {
    type: String,
    default: ''
  }
});

const placeholder = computed(() => {
  if (props.status === 'listening') return '請開始講解你的解題思路…';
  if (props.status === 'processing') return 'AI 正在分析你的說明…';
  return 'AI 回饋將在此顯示…';
});
</script>

<style scoped>
.subtitle-bar {
  position: absolute;
  left: 50%;
  bottom: 1.5rem;
  transform: translateX(-50%);
  min-width: 60%;
  max-width: 900px;
  border-radius: 999px;
  padding: 0.75rem 1.25rem;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.9);
}

.subtitle-bar.listening {
  background: rgba(15, 23, 42, 0.95);
}

.subtitle-bar.processing {
  background: rgba(15, 23, 42, 0.95);
}

.subtitle-bar.speaking {
  background: #1e3a8a;
}

.content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: #e5e7eb;
}

.icon {
  font-size: 1.25rem;
}

.text {
  margin: 0;
  font-size: 1.1rem;
}
</style>


