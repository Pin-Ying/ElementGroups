<template>
  <teleport to="body">
    <div class="toast-container">
      <transition-group name="toast" tag="div">
        <div
          v-for="toast in toastState.toasts"
          :key="toast.id"
          class="toast"
          :class="`toast--${toast.type}`"
          @click="removeToast(toast.id)"
        >
          <span class="toast-icon">{{ icons[toast.type] }}</span>
          <span class="toast-msg">{{ toast.message }}</span>
          <button class="toast-close" @click.stop="removeToast(toast.id)">✕</button>
        </div>
      </transition-group>
    </div>
  </teleport>
</template>

<script>
import { toastState, removeToast } from '../store/toast'

export default {
  setup() {
    return {
      toastState,
      removeToast,
      icons: { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' }
    }
  }
}
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 8px;
  min-width: 260px;
  max-width: 380px;
  backdrop-filter: blur(12px);
  border: 1px solid;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  font-size: 14px;
  font-family: 'Space Grotesk', sans-serif;
  cursor: pointer;
  pointer-events: all;
}

.toast--success {
  background: rgba(16, 40, 20, 0.88);
  border-color: rgba(110, 231, 110, 0.45);
  color: #a3f0a3;
}
.toast--error {
  background: rgba(40, 12, 12, 0.88);
  border-color: rgba(255, 100, 100, 0.45);
  color: #ffaaaa;
}
.toast--warning {
  background: rgba(40, 32, 8, 0.88);
  border-color: rgba(255, 200, 60, 0.45);
  color: #ffe080;
}
.toast--info {
  background: rgba(8, 24, 44, 0.88);
  border-color: rgba(100, 200, 255, 0.35);
  color: #a0d8ff;
}

.toast-icon {
  font-size: 15px;
  flex-shrink: 0;
  width: 18px;
  text-align: center;
}

.toast-msg {
  flex: 1;
  line-height: 1.4;
  word-break: break-word;
}

.toast-close {
  background: none;
  border: none;
  color: inherit;
  opacity: 0.5;
  font-size: 13px;
  cursor: pointer;
  padding: 0;
  flex-shrink: 0;
  line-height: 1;
  transition: opacity 0.15s;
}
.toast-close:hover { opacity: 1; }

/* Animation */
.toast-enter-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.toast-leave-active {
  transition: all 0.2s ease-in;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(60px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(60px);
}

@media (max-width: 480px) {
  .toast-container {
    top: auto;
    bottom: 16px;
    right: 12px;
    left: 12px;
  }
  .toast {
    min-width: unset;
    max-width: unset;
    width: 100%;
  }
}
</style>
