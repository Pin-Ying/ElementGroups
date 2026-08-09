<template>
  <!-- 三層都齊備時才用分層呈現，否則交給呼叫端顯示原本的靜態圖 -->
  <div class="layers" :class="'layers--' + motion">
    <img class="layer layer--nucleus" :src="nucleus" alt="" />

    <div v-if="electronImg && count" class="electrons">
      <span
        v-for="(e, i) in orbits"
        :key="i"
        class="electron"
        :style="e.style"
      >
        <img :src="electronImg" alt="" />
      </span>
    </div>

    <img v-if="nameImg" class="layer layer--name" :src="nameImg" alt="" />
  </div>
</template>

<script>
export default {
  props: {
    nucleus: { type: String, required: true },
    nameImg: { type: String, default: '' },
    electronImg: { type: String, default: '' },
    // 最外層電子數，決定要放幾顆
    count: { type: Number, default: 0 },
    // orbit：繞著原子核轉／free：在整個範圍內飄／static：固定不動
    motion: { type: String, default: 'orbit' }
  },
  computed: {
    orbits() {
      const n = Math.max(0, Math.min(this.count, 8))
      return Array.from({ length: n }, (_, i) => {
        const angle = (360 / n) * i
        // 每顆錯開起始角度與時間，才不會整排同步移動
        const delay = -(i * (this.motion === 'free' ? 1.7 : 8 / n))
        return {
          style: {
            '--angle': `${angle}deg`,
            '--delay': `${delay}s`,
            // free 模式各自用不同的軌跡半徑與速度，看起來比較自然
            '--radius': this.motion === 'free' ? `${34 + (i % 3) * 9}%` : '38%',
            '--duration': this.motion === 'free' ? `${7 + (i % 4) * 2.5}s` : '8s'
          }
        }
      })
    }
  }
}
</script>

<style scoped>
.layers {
  position: relative;
  width: 100%;
  aspect-ratio: 1 / 1;
}

.layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  border: none;
  border-radius: 0;
  margin: 0;
}

.layer--nucleus { z-index: 1; }
/* 手寫元素名壓在最上層，不會被電子蓋住 */
.layer--name { z-index: 3; pointer-events: none; }

.electrons {
  position: absolute;
  inset: 0;
  z-index: 2;
  pointer-events: none;
}

.electron {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 16%;
  height: 16%;
  margin: -8% 0 0 -8%;
  transform-origin: center;
}

.electron img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border: none;
  border-radius: 0;
  display: block;
}

/* ── 繞行：沿固定半徑的圓周轉 ── */
.layers--orbit .electron {
  animation: orbit var(--duration, 8s) linear infinite;
  animation-delay: var(--delay, 0s);
}

@keyframes orbit {
  from { transform: rotate(var(--angle)) translateX(var(--radius, 38%)) rotate(calc(-1 * var(--angle))); }
  to   { transform: rotate(calc(var(--angle) + 360deg)) translateX(var(--radius, 38%)) rotate(calc(-1 * var(--angle) - 360deg)); }
}

/* ── 自由飄動：繞行之外再疊一層上下浮動 ── */
.layers--free .electron {
  animation:
    orbit var(--duration, 9s) linear infinite,
    drift calc(var(--duration, 9s) / 2) ease-in-out infinite alternate;
  animation-delay: var(--delay, 0s), var(--delay, 0s);
}

@keyframes drift {
  from { margin-top: -11%; }
  to   { margin-top: -5%; }
}

/* ── 靜止：只按角度排開，不動 ── */
.layers--static .electron {
  transform: rotate(var(--angle)) translateX(var(--radius, 38%)) rotate(calc(-1 * var(--angle)));
}

@media (prefers-reduced-motion: reduce) {
  .electron { animation: none !important; }
  .layers--orbit .electron,
  .layers--free .electron {
    transform: rotate(var(--angle)) translateX(var(--radius, 38%)) rotate(calc(-1 * var(--angle)));
  }
}
</style>
