<template>
  <div class="spinner-overlay">
    <div class="spinner"></div>
  </div>
</template>

<style scoped>
.spinner-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.spinner {
  width: 56px;
  height: 56px;
  border: 5px solid rgba(228, 251, 255, 0.2);
  border-top-color: #e4fbff;
  border-radius: 50%;
  animation: spin 0.75s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
