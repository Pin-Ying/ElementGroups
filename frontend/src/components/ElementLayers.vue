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
        :class="'orbit-path--' + e.orbitalType"
        :style="e.pathStyle"
      ></i>

      <span
        v-for="(e, i) in orbits"
        :key="i"
        class="electron"
        :class="'electron--' + e.orbitalType"
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

// 各軌域的運動形態。
//
// 這裡不是精確的量子力學模型，而是取軌域最容易辨認的幾何特徵：
//   s 軌域球對稱     → 接近正圓，方向隨意
//   p 軌域是啞鈴形   → 壓得很扁，看起來像沿著某個軸來回，且分三個方向
//   d 軌域四葉       → 中等扁率，方向更分散
//   f 軌域更複雜     → 扁率與方向都再拉開
const ORBITAL_SHAPES = {
  s: { flatten: [0.92, 0.82, 0.88], tilts: [0, 55, 110], radius: 0, speed: 1 },
  p: { flatten: [0.16, 0.22, 0.19], tilts: [0, 60, 120], radius: 5, speed: 0.82 },
  d: { flatten: [0.45, 0.38, 0.52, 0.42], tilts: [20, 70, 115, 160], radius: 9, speed: 0.7 },
  f: { flatten: [0.3, 0.6, 0.24, 0.5], tilts: [15, 65, 100, 145], radius: 12, speed: 0.62 }
}

// 依元素符號產生穩定的偏移量。用雜湊而不是亂數，重新整理不會跳動，
// 但不同元素的軌道配置看起來各有差異。
function symbolSeed(symbol) {
  let h = 0
  for (const ch of String(symbol || '')) h = (h * 31 + ch.charCodeAt(0)) % 997
  return h
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
    // 每顆電子所屬的軌域，例如 [{type:'s'},{type:'s'},{type:'p'}...]
    orbitals: { type: Array, default: () => [] },
    // 用來產生穩定的軌道偏移，讓不同元素看起來不一樣
    seed: { type: String, default: '' },
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
      const offset = symbolSeed(this.seed)

      return Array.from({ length: n }, (_, i) => {
        // 該顆電子所屬的軌域；沒有資料時退回 s（球對稱）
        const type = this.orbitals[i]?.type || 's'
        const shape = ORBITAL_SHAPES[type] || ORBITAL_SHAPES.s
        // 同一軌域內第幾顆，用來挑選該軌域的不同方向
        const k = this.orbitals.slice(0, i).filter(o => o.type === type).length

        // 起始角度平均分散，再加上依元素而異的偏移
        const angle = (360 / n) * i + (offset % 37) + (i % 2 ? 14 : -9)

        const radiusPct = (this.motion === 'free' ? 30 + (i % 4) * 6 : 32 + (i % 3) * 5)
          + shape.radius
          + (offset % 5)

        // p 軌域壓得很扁看起來就像沿軸來回，s 軌域接近正圓
        const flatten = this.motion === 'static'
          ? 1
          : shape.flatten[k % shape.flatten.length]

        // 同軌域的不同方向錯開（p 的三個方向、d 的四葉）
        const tilt = shape.tilts[k % shape.tilts.length] + (offset % 23) - 11

        const duration = ((this.motion === 'free' ? 7 + (i % 4) * 2.5 : 6.5 + (i % 3) * 2.2)
          / shape.speed)

        // 軌道線的尺寸用容器百分比，與電子的 translateX 換算基準不同
        const pathSize = radiusPct * 2

        return {
          orbitalType: type,
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

/* 軌道線（僅繞行模式）：讓「各自有軌道」這件事看得出來。
   依軌域上色，s／p／d 的差別才看得出來 */
.orbit-path--s { border-color: rgba(0, 0, 0, 0.13); }
.orbit-path--p { border-color: rgba(43, 108, 176, 0.22); }
.orbit-path--d { border-color: rgba(160, 60, 200, 0.2); }
.orbit-path--f { border-color: rgba(200, 120, 40, 0.2); }

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
