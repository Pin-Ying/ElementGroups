<template>
  <div class="spinner-overlay">
    <div class="spinner-wrap">
      <div class="spinner"></div>
      <transition name="hint-fade">
        <div v-if="stage >= 1" class="spinner-hint">
          <p class="hint-title">{{ stage >= 2 ? 'Still waking up…' : 'Waking up the server…' }}</p>
          <p class="hint-sub">
            {{ stage >= 2
              ? 'Render free-tier servers sleep after inactivity. Hang tight!'
              : 'The backend is cold-starting. This usually takes under 30 seconds.' }}
          </p>
          <div class="hint-dots">
            <span></span><span></span><span></span>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return { stage: 0, timers: [] }
  },
  mounted() {
    this.timers.push(setTimeout(() => { this.stage = 1 }, 10000))
    this.timers.push(setTimeout(() => { this.stage = 2 }, 22000))
  },
  beforeUnmount() {
    this.timers.forEach(clearTimeout)
  }
}
</script>

<style scoped>
.spinner-overlay {
  position: fixed;
  inset: 0;
  background: rgba(3, 1, 10, 0.72);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.spinner-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 28px;
}

.spinner {
  width: 56px;
  height: 56px;
  border: 4px solid rgba(100, 0, 180, 0.25);
  border-top-color: #e4fbff;
  border-right-color: rgba(100, 184, 255, 0.7);
  border-radius: 50%;
  animation: spin 0.85s linear infinite;
  box-shadow: 0 0 18px rgba(228, 251, 255, 0.2);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Hint card */
.spinner-hint {
  text-align: center;
  max-width: 280px;
  background: rgba(20, 10, 35, 0.85);
  border: 1px solid rgba(228, 251, 255, 0.15);
  border-radius: 10px;
  padding: 18px 22px 14px;
  backdrop-filter: blur(8px);
}

.hint-title {
  font-size: 14px;
  font-weight: 600;
  color: #e4fbff;
  margin: 0 0 6px;
  letter-spacing: 0.02em;
}

.hint-sub {
  font-size: 12px;
  color: rgba(228, 251, 255, 0.5);
  margin: 0 0 12px;
  line-height: 1.55;
}

/* Animated dots */
.hint-dots {
  display: flex;
  justify-content: center;
  gap: 6px;
}

.hint-dots span {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: rgba(228, 251, 255, 0.4);
  animation: dot-pulse 1.4s ease-in-out infinite;
}

.hint-dots span:nth-child(2) { animation-delay: 0.2s; }
.hint-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes dot-pulse {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.85); }
  40%           { opacity: 1;   transform: scale(1.15); }
}

/* Transition */
.hint-fade-enter-active { transition: opacity 0.5s ease, transform 0.5s ease; }
.hint-fade-enter-from   { opacity: 0; transform: translateY(8px); }
</style>
