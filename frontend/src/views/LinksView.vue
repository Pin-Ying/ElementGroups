<template>
  <div class="links-box">
    <p class="title">CONNECT</p>
    <div class="box">
      <p v-if="state.description" class="links-desc">{{ state.description }}</p>

      <div v-if="links.length" class="link-list">
        <SocialLink
          v-for="(link, i) in links"
          :key="link.platform + i"
          :link="link"
          :shape="state.avatar_shape"
          size="md"
        />
      </div>
      <p v-else class="placeholder-text">尚未設定任何連結</p>
    </div>
  </div>
</template>

<script>
import { creatorLinksState, ensureCreatorLinks } from '../store/creatorLinks'
import SocialLink from '../components/SocialLink.vue'

export default {
  components: { SocialLink },
  data() {
    return { state: creatorLinksState }
  },
  computed: {
    links() {
      return this.state.links
    }
  },
  created() {
    ensureCreatorLinks()
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

.links-desc {
  font-size: 14px;
  line-height: 1.85;
  color: rgba(228, 251, 255, 0.72);
  margin: 0 0 18px;
  white-space: pre-wrap;
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
</style>
