<template>
  <!-- 三層都齊備時才用分層呈現，否則交給呼叫端顯示原本的靜態圖 -->
  <div class="layers" :class="'layers--' + motion" :style="{ background: bgColor, ...layerVars }">
    <img class="layer layer--nucleus" :src="nucleus" alt="" />

    <div v-if="electronImg && count" class="electrons">
      <!-- 每顆電子的軌道線，讓不同的傾角與扁率看得出來 -->
      <i
        v-for="(e, i) in orbits"
        :key="'path' + i"
        class="orbit-path"
        :style="e.pathStyle"
      ></i>

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
// translateX 的百分比是相對元素「自身」寬度，所以要把「距離容器中心多少
// 百分比」換算成電子自身的倍數，否則電子會全部擠在中心。
function orbitRadius(containerPct, electronPct) {
  return `${(containerPct / electronPct) * 100}%`
}

export default {
  props: {
    nucleus: { type: String, required: true },
    nameImg: { type: String, default: '' },
    electronImg: { type: String, default: '' },
    // 最外層電子數，決定要放幾顆
    count: { type: Number, default: 0 },
    // orbit：繞著原子核轉／free：在整個範圍內飄／static：固定不動
    motion: { type: String, default: 'orbit' },
    // 電子寬度佔容器的百分比，可在後台調整
    size: { type: Number, default: 24 },
    // 三層都是去背 PNG，需要底色才看得清楚
    bgColor: { type: String, default: '#ffffff' }
  },
  computed: {
    // 電子多的時候略為縮小，避免彼此重疊
    electronSize() {
      const base = Math.min(Math.max(this.size || 24, 6), 45)
      return this.count >= 7 ? base * 0.78 : this.count >= 5 ? base * 0.88 : base
    },
    layerVars() {
      return { '--electron-size': this.electronSize + '%' }
    },
    orbits() {
      const n = Math.max(0, Math.min(this.count, 8))
      return Array.from({ length: n }, (_, i) => {
        // 起始角度平均分散，再加一點偏移讓它不會排得太整齊
        const angle = (360 / n) * i + (i % 2 ? 14 : -9)

        // 每顆給不同的軌道半徑、傾角與速度。用固定的錯開量而不是亂數，
        // 這樣重新整理不會跳動，但看起來仍像各自繞著自己的軌道跑。
        const radiusPct = this.motion === 'free'
          ? 30 + (i % 4) * 6
          : 32 + (i % 3) * 5

        // 橢圓：垂直方向壓扁一些，並讓整個軌道面傾斜
        const flatten = this.motion === 'static' ? 1 : 0.62 + (i % 3) * 0.14
        const tilt = (i * 37) % 180 - 90

        const duration = this.motion === 'free'
          ? 7 + (i % 4) * 2.5
          : 6.5 + (i % 3) * 2.2

        // 軌道線的尺寸用容器百分比，與電子的 translateX 換算基準不同
        const pathSize = radiusPct * 2

        return {
          pathStyle: {
            width: `${pathSize}%`,
            height: `${pathSize}%`,
            '--flatten': flatten,
            '--tilt': `${tilt}deg`
          },
          style: {
            '--angle': `${angle}deg`,
            '--delay': `${-(i * duration) / n}s`,
            '--radius': orbitRadius(radiusPct, this.electronSize),
            '--flatten': flatten,
            '--tilt': `${tilt}deg`,
            '--duration': `${duration}s`
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
  border-radius: 4px;
  overflow: hidden;
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
  /* 尺寸由 script 的 electronSize 換算後透過 CSS 變數帶入 */
  width: var(--electron-size, 24%);
  height: var(--electron-size, 24%);
  margin: calc(var(--electron-size, 24%) / -2) 0 0 calc(var(--electron-size, 24%) / -2);
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

/* 先把整個軌道面傾斜，再壓扁成橢圓，最後才旋轉；
   每顆電子的傾角與扁率不同，看起來就不會像同心圓的齒輪 */
@keyframes orbit {
  from {
    transform:
      rotate(var(--tilt, 0deg)) scaleY(var(--flatten, 1))
      rotate(var(--angle)) translateX(var(--radius, 225%))
      rotate(calc(-1 * var(--angle))) scaleY(calc(1 / var(--flatten, 1))) rotate(calc(-1 * var(--tilt, 0deg)));
  }
  to {
    transform:
      rotate(var(--tilt, 0deg)) scaleY(var(--flatten, 1))
      rotate(calc(var(--angle) + 360deg)) translateX(var(--radius, 225%))
      rotate(calc(-1 * var(--angle) - 360deg)) scaleY(calc(1 / var(--flatten, 1))) rotate(calc(-1 * var(--tilt, 0deg)));
  }
}

/* ── 自由飄動：繞行之外再疊一層上下浮動 ── */
.layers--free .electron {
  animation:
    orbit var(--duration, 9s) linear infinite,
    drift calc(var(--duration, 9s) / 2) ease-in-out infinite alternate;
  animation-delay: var(--delay, 0s), var(--delay, 0s);
}

@keyframes drift {
  from { margin-top: calc(var(--electron-size, 24%) / -2 - 3%); }
  to   { margin-top: calc(var(--electron-size, 24%) / -2 + 3%); }
}

/* ── 靜止：只按角度排開，不動 ── */
.layers--static .electron {
  transform: rotate(var(--angle)) translateX(var(--radius, 225%)) rotate(calc(-1 * var(--angle)));
}

/* 軌道線（僅繞行模式）：讓「各自有軌道」這件事看得出來 */
.layers--orbit .orbit-path,
.layers--free .orbit-path {
  position: absolute;
  top: 50%;
  left: 50%;
  border: 1px dashed rgba(0, 0, 0, 0.12);
  border-radius: 50%;
  pointer-events: none;
  transform: translate(-50%, -50%) rotate(var(--tilt, 0deg)) scaleY(var(--flatten, 1));
}

@media (prefers-reduced-motion: reduce) {
  .electron { animation: none !important; }
  .layers--orbit .electron,
  .layers--free .electron {
    transform:
      rotate(var(--tilt, 0deg)) scaleY(var(--flatten, 1))
      rotate(var(--angle)) translateX(var(--radius, 225%))
      rotate(calc(-1 * var(--angle))) scaleY(calc(1 / var(--flatten, 1))) rotate(calc(-1 * var(--tilt, 0deg)));
  }
  .orbit-path { display: none; }
}
</style>
