<template>
  <div class="particles">
    <LoadingSpinner v-if="loading" />

    <p class="title">基本粒子</p>
    <p class="subtitle">組成元素的更小單位，每種粒子都有自己的形象。</p>

    <div v-if="!loading && !particles.length" class="no-results">
      還沒有建立任何粒子
    </div>

    <section v-for="p in particles" :key="p.slug" class="particle-card">
      <div v-if="p.img_data" class="particle-figure">
        <img :src="p.img_data" :alt="p.name" />
      </div>

      <div class="particle-info">
        <h2 class="particle-name">
          {{ p.name }}
          <span v-if="!p.published" class="draft-tag">草稿</span>
        </h2>
        <p v-if="p.title" class="particle-title">{{ p.title }}</p>
        <p v-if="p.description" class="particle-desc">{{ p.description }}</p>
      </div>
    </section>
  </div>
</template>

<script>
import { getParticles } from '../api'
import LoadingSpinner from '../components/LoadingSpinner.vue'

export default {
  components: { LoadingSpinner },
  data() {
    return { particles: [], loading: false }
  },
  async created() {
    this.loading = true
    try {
      const res = await getParticles()
      this.particles = res.data.particles || []
    } catch (e) {
      console.error('Failed to load particles:', e)
    } finally {
      this.loading = false
    }
  }
}
</script>

<style scoped>
.particles {
  max-width: 860px;
  margin: 0 auto;
  padding: 20px 18px 40px;
}

.subtitle {
  font-size: 14px;
  color: rgba(228, 251, 255, 0.55);
  margin: -6px 0 24px;
}

.particle-card {
  display: flex;
  gap: 26px;
  align-items: center;
  text-align: left;
  padding: 24px 26px;
  border: 1px solid rgba(228, 251, 255, 0.14);
  border-radius: 12px;
  background: rgba(20, 5, 35, 0.5);
  margin-bottom: 16px;
}

/* 左右交錯，看起來比較像圖鑑跨頁 */
.particle-card:nth-child(even) {
  flex-direction: row-reverse;
}

.particle-figure {
  flex: 0 0 180px;
}

.particle-figure img {
  width: 100%;
  aspect-ratio: 1 / 1;
  object-fit: contain;
}

.particle-info {
  flex: 1;
  min-width: 0;
}

.particle-name {
  font-size: 22px;
  font-weight: 700;
  color: #e4fbff;
  margin: 0 0 4px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.particle-title {
  font-size: 14px;
  color: rgba(200, 190, 255, 0.85);
  margin: 0 0 10px;
}

.particle-desc {
  font-size: 15px;
  line-height: 1.9;
  color: rgba(228, 251, 255, 0.78);
  margin: 0;
  white-space: pre-wrap;
}

.draft-tag {
  font-size: 11px;
  font-weight: 400;
  color: #ffc46b;
  border: 1px solid rgba(255, 196, 107, 0.4);
  border-radius: 999px;
  padding: 1px 8px;
}

@media (max-width: 620px) {
  .particle-card,
  .particle-card:nth-child(even) {
    flex-direction: column;
  }
  .particle-figure { flex-basis: auto; width: 150px; }
}
</style>
