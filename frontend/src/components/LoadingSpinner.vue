<template>
  <div class="spinner-overlay">
    <div class="spinner"></div>
  </div>
</template>

<style scoped>
.spinner-overlay {
  position: fixed;
  inset: 0;
  background: rgba(3, 1, 10, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
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
</style>
