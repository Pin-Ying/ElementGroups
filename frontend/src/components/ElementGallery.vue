<template>
  <section v-if="images.length" class="gallery">
    <h2 class="gallery-title">其他樣貌</h2>
    <div class="gallery-grid">
      <figure
        v-for="(img, i) in images"
        :key="i"
        class="gallery-item"
        :style="{ borderColor: '#' + color }"
        @click="open(i)"
      >
        <img :src="img.img_data" :alt="img.caption || ''" loading="lazy" />
        <figcaption v-if="img.caption">{{ img.caption }}</figcaption>
      </figure>
    </div>

    <!-- 放大檢視 -->
    <div v-if="viewerIndex !== null" class="viewer" @click.self="close">
      <button class="viewer-close" type="button" @click="close">✕</button>
      <button v-if="images.length > 1" class="viewer-nav viewer-nav--prev" type="button" @click.stop="step(-1)">‹</button>

      <figure class="viewer-figure">
        <img :src="images[viewerIndex].img_data" :alt="images[viewerIndex].caption || ''" />
        <figcaption v-if="images[viewerIndex].caption">{{ images[viewerIndex].caption }}</figcaption>
      </figure>

      <button v-if="images.length > 1" class="viewer-nav viewer-nav--next" type="button" @click.stop="step(1)">›</button>
    </div>
  </section>
</template>

<script>
export default {
  props: {
    images: { type: Array, default: () => [] },
    color: { type: String, default: '64b8e8' }
  },
  data() {
    return { viewerIndex: null }
  },
  methods: {
    open(i) {
      this.viewerIndex = i
      window.addEventListener('keydown', this.onKey)
    },
    close() {
      this.viewerIndex = null
      window.removeEventListener('keydown', this.onKey)
    },
    step(delta) {
      const n = this.images.length
      this.viewerIndex = (this.viewerIndex + delta + n) % n
    },
    onKey(e) {
      if (e.key === 'Escape') this.close()
      else if (e.key === 'ArrowLeft') this.step(-1)
      else if (e.key === 'ArrowRight') this.step(1)
    }
  },
  beforeUnmount() {
    window.removeEventListener('keydown', this.onKey)
  }
}
</script>

<style scoped>
.gallery {
  margin: 26px auto 0;
  width: 100%;
}

.gallery-title {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.14em;
  color: rgba(228, 251, 255, 0.5);
  text-align: left;
  margin: 0 0 12px;
  padding-bottom: 7px;
  border-bottom: 1px solid rgba(228, 251, 255, 0.12);
}

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
}

.gallery-item {
  margin: 0;
  border: 1px solid;
  border-radius: 8px;
  overflow: hidden;
  cursor: zoom-in;
  background: rgba(20, 5, 35, 0.5);
  transition: transform 0.15s, box-shadow 0.15s;
}

.gallery-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.45);
}

.gallery-item img {
  display: block;
  width: 100%;
  aspect-ratio: 1 / 1;
  object-fit: cover;
  border: none;
  border-radius: 0;
}

.gallery-item figcaption {
  padding: 7px 10px;
  font-size: 12px;
  line-height: 1.5;
  color: rgba(228, 251, 255, 0.75);
  text-align: left;
}

/* ── 放大檢視 ── */
.viewer {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0, 0, 0, 0.88);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 24px;
}

.viewer-figure {
  margin: 0;
  max-width: min(880px, 90vw);
  max-height: 86vh;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.viewer-figure img {
  max-width: 100%;
  max-height: 76vh;
  width: auto;
  object-fit: contain;
  border: 1px solid rgba(228, 251, 255, 0.25);
  border-radius: 6px;
}

.viewer-figure figcaption {
  text-align: center;
  font-size: 14px;
  color: rgba(228, 251, 255, 0.85);
}

.viewer-close {
  position: absolute;
  top: 16px;
  right: 20px;
  width: 34px;
  height: 34px;
  border: 1px solid rgba(228, 251, 255, 0.25);
  border-radius: 50%;
  background: rgba(20, 10, 30, 0.8);
  color: rgba(228, 251, 255, 0.8);
  font-size: 15px;
  cursor: pointer;
}

.viewer-close:hover { color: #fff; border-color: rgba(228, 251, 255, 0.6); }

.viewer-nav {
  flex-shrink: 0;
  width: 40px;
  height: 60px;
  border: 1px solid rgba(228, 251, 255, 0.2);
  border-radius: 8px;
  background: rgba(20, 10, 30, 0.7);
  color: rgba(228, 251, 255, 0.7);
  font-size: 26px;
  line-height: 1;
  cursor: pointer;
}

.viewer-nav:hover { color: #fff; background: rgba(60, 40, 75, 0.9); }

@media (max-width: 600px) {
  .viewer { padding: 12px; gap: 4px; }
  .viewer-nav { width: 30px; height: 48px; font-size: 20px; }
}
</style>
