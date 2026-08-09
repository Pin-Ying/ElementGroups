<template>
  <a
    class="social"
    :class="[`social--${size}`, { 'social--avatar': link.avatar }]"
    :style="{ '--brand': brandColor }"
    :href="link.url"
    target="_blank"
    rel="noopener noreferrer"
    :title="link.label"
  >
    <span
      v-if="link.avatar"
      class="social-avatar"
      :class="`social-avatar--${shape}`"
    >
      <img :src="link.avatar" :alt="link.label" />
    </span>
    <span class="social-label">{{ link.label }}</span>
  </a>
</template>

<script>
import { platformInfo } from '../utils/socialPlatforms'

export default {
  props: {
    link: { type: Object, required: true },
    // circle | square
    shape: { type: String, default: 'circle' },
    // sm 用於頁尾，md 用於 /links 頁
    size: { type: String, default: 'sm' }
  },
  computed: {
    brandColor() {
      // 後台填了自訂色就用它，否則沿用平台預設色
      return this.link.color || platformInfo(this.link.platform).color
    }
  }
}
</script>

<style scoped>
.social {
  --brand: #64b8e8;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  text-decoration: none;
  color: rgba(228, 251, 255, 0.85);
  border: 1px solid color-mix(in srgb, var(--brand) 45%, transparent);
  background: color-mix(in srgb, var(--brand) 10%, transparent);
  border-radius: 999px;
  transition: background 0.18s, border-color 0.18s, color 0.18s, transform 0.18s;
}

.social:hover {
  color: #fff;
  border-color: var(--brand);
  background: color-mix(in srgb, var(--brand) 26%, transparent);
  transform: translateY(-1px);
}

.social--sm {
  padding: 5px 16px;
  font-size: 13px;
}

.social--md {
  padding: 8px 20px;
  font-size: 14px;
}

/* 有頭像時左側留給頭像，padding 收窄 */
.social--avatar.social--sm { padding: 3px 14px 3px 3px; }
.social--avatar.social--md { padding: 4px 20px 4px 4px; }

.social-avatar {
  display: block;
  overflow: hidden;
  flex-shrink: 0;
  border: 1px solid color-mix(in srgb, var(--brand) 60%, transparent);
}

.social--sm .social-avatar { width: 26px; height: 26px; }
.social--md .social-avatar { width: 34px; height: 34px; }

.social-avatar--circle { border-radius: 50%; }
.social-avatar--square { border-radius: 6px; }

.social-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  border: none;
  border-radius: 0;
}
</style>
