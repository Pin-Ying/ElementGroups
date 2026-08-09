<template>
  <div class="links-box">
    <p class="title">CONNECT</p>
    <div class="box">
      <p class="desc">追蹤創作者的社群帳號</p>

      <div v-if="links.instagram || links.threads" class="link-list">
        <a
          v-if="links.instagram"
          class="button link-button"
          :href="links.instagram"
          target="_blank"
          rel="noopener noreferrer"
        >Instagram</a>
        <a
          v-if="links.threads"
          class="button link-button"
          :href="links.threads"
          target="_blank"
          rel="noopener noreferrer"
        >Threads</a>
      </div>
      <p v-else class="placeholder-text">尚未設定任何連結</p>
    </div>
  </div>
</template>

<script>
import { getCreatorLinks } from '../api'

export default {
  data() {
    return {
      links: { instagram: '', threads: '' }
    }
  },
  async created() {
    try {
      const res = await getCreatorLinks()
      this.links = { instagram: res.data.instagram || '', threads: res.data.threads || '' }
    } catch (e) {
      console.error('Failed to load creator links:', e)
    }
  }
}
</script>

<style scoped>
.links-box {
  text-align: center;
  padding: 20px;
  max-width: 720px;
  margin: 0 auto;
}

.box {
  background: rgba(20, 5, 35, 0.5);
  border: 1px solid rgba(228, 251, 255, 0.1);
  border-radius: 8px;
  padding: 24px 28px;
  margin-bottom: 20px;
  text-align: left;
}

.desc {
  font-size: 13px;
  opacity: 0.55;
  margin: 2px 0 14px;
  line-height: 1.5;
}

.placeholder-text {
  font-size: 13px;
  opacity: 0.4;
  margin: 8px 0;
}

.link-list {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.link-button {
  text-decoration: none;
}
</style>
