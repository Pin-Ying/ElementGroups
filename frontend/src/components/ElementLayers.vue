<template>
  <!-- 三層都齊備時才用分層呈現，否則交給呼叫端顯示原本的靜態圖 -->
  <div class="layers" :class="'layers--' + motion" :style="{ background: bgColor, ...layerVars }">
    <img class="layer layer--nucleus" :src="nucleus" alt="" />

    <div v-if="electronImg && count && motion !== 'free'" class="electrons">
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

  <!-- 自由飄動不受圖框限制，整頁都是電子的活動範圍，所以掛到 body 上 -->
  <Teleport v-if="motion === 'free' && electronImg && count" to="body">
    <div class="free-field" aria-hidden="true">
      <span
        v-for="(e, i) in wanderers"
        :key="i"
        class="free-electron"
        :style="e.style"
      >
        <img :src="electronImg" alt="" />
      </span>
    </div>
  </Teleport>
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

// 繞行模式的軌道層。電子分配到不同層，半徑、傾角與遠近對比都不同，
// 看起來才像在各自的圖層上繞，而不是擠在同一個圈上。
const ORBIT_LAYERS = [
  { radius: 26, depth: 0.34, tilt: -18, speed: 1.18 },
  { radius: 35, depth: 0.5, tilt: 12, speed: 1 },
  { radius: 44, depth: 0.66, tilt: -7, speed: 0.86 }
]

// 依元素符號產生穩定的偏移量。用雜湊而不是亂數，重新整理不會跳動，
// 但不同元素的軌道配置看起來各有差異。
function symbolSeed(symbol) {
  let h = 0
  for (const ch of String(symbol || '')) h = (h * 31 + ch.charCodeAt(0)) % 997
  return h
}

// 由種子長出的可重現偽亂數序列，讓自由飄動的路徑每顆都不同，
// 但同一個元素每次進來都一樣，不會每次重整就換位置。
function seededRandom(seed) {
  let s = (seed % 2147483647) + 1
  return () => {
    s = (s * 16807) % 2147483647
    return (s - 1) / 2147483646
  }
}

export default {
  props: {
    nucleus: { type: String, required: true },
    nameImg: { type: String, default: '' },
    electronImg: { type: String, default: '' },
    // 最外層電子數，決定要放幾顆
    count: { type: Number, default: 0 },
    // orbit：分層繞著原子核／free：在整個網頁飄／static：均勻排開不動
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
    electronCount() {
      return Math.max(0, Math.min(this.count, 8))
    },
    orbits() {
      const n = this.electronCount
      const offset = symbolSeed(this.seed)

      return Array.from({ length: n }, (_, i) => {
        // 該顆電子所屬的軌域；沒有資料時退回 s（球對稱）
        const type = this.orbitals[i]?.type || 's'
        const shape = ORBITAL_SHAPES[type] || ORBITAL_SHAPES.s
        // 同一軌域內第幾顆，用來挑選該軌域的不同方向
        const k = this.orbitals.slice(0, i).filter(o => o.type === type).length

        // 靜止模式是「排開」，角度平均分散就好，不需要軌域的幾何變化
        if (this.motion === 'static') {
          return {
            orbitalType: type,
            style: {
              '--angle': `${(360 / n) * i + (offset % 37)}deg`,
              '--radius': orbitRadius(38 + (offset % 4), this.electronSize)
            }
          }
        }

        // 繞行：把電子分配到不同軌道層，層與層之間半徑與遠近對比都拉開
        const layer = ORBIT_LAYERS[i % ORBIT_LAYERS.length]

        // 起始角度平均分散，再加上依元素而異的偏移
        const angle = (360 / n) * i + (offset % 37) + (i % 2 ? 14 : -9)
        const radiusPct = layer.radius + shape.radius + (offset % 5)

        // p 軌域壓得很扁看起來就像沿軸來回，s 軌域接近正圓
        const flatten = shape.flatten[k % shape.flatten.length]

        // 同軌域的不同方向錯開（p 的三個方向、d 的四葉），再加上該層的整體傾斜
        const tilt = shape.tilts[k % shape.tilts.length] + layer.tilt + (offset % 23) - 11

        const duration = (6.5 + (i % 3) * 2.2) / (shape.speed * layer.speed)

        return {
          orbitalType: type,
          style: {
            '--angle': `${angle}deg`,
            '--delay': `${-(i * duration) / n}s`,
            '--radius': orbitRadius(radiusPct, this.electronSize),
            '--flatten': flatten,
            '--tilt': `${tilt}deg`,
            '--duration': `${duration}s`,
            // 繞到原子核後方時縮到 depth 倍，轉回前方時放大，做出前後景深
            '--depth': layer.depth
          }
        }
      })
    },
    // 自由飄動：每顆電子在整個視窗裡沿自己的路徑漫遊
    wanderers() {
      if (this.motion !== 'free') return []

      const rand = seededRandom(symbolSeed(this.seed) + 13)

      return Array.from({ length: this.electronCount }, (_, i) => {
        // 四個停留點連成一圈，繞完回到起點，路徑就不會有跳接
        const waypoints = {}
        for (let w = 0; w < 4; w++) {
          waypoints[`--x${w}`] = `${Math.round(rand() * 88 + 6)}vw`
          waypoints[`--y${w}`] = `${Math.round(rand() * 84 + 8)}vh`
        }

        return {
          style: {
            ...waypoints,
            '--size': `${(4.5 + rand() * 3).toFixed(1)}vmin`,
            // 慢一點才像飄，太快會變成滿版亂竄
            '--duration': `${Math.round(38 + rand() * 34)}s`,
            '--spin': `${Math.round(14 + rand() * 16)}s`,
            '--delay': `${-Math.round(rand() * 30)}s`,
            '--fade': (0.55 + rand() * 0.35).toFixed(2)
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

/* 這一層刻意不設 z-index：留成 auto 才不會自成堆疊環境，
   底下每顆電子的 z-index 才能各自跟原子核比前後 */
.electrons {
  position: absolute;
  inset: 0;
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

/* ── 繞行：分層繞著原子核，且有前後景深 ── */
.layers--orbit .electron {
  animation:
    orbit var(--duration, 8s) linear infinite,
    orbit-depth var(--duration, 8s) linear infinite;
  animation-delay: var(--delay, 0s), var(--delay, 0s);
}

/* 內層負責遠近縮放，跟外層的位移分開，兩個 transform 才不會互相蓋掉 */
.layers--orbit .electron img {
  animation: orbit-scale var(--duration, 8s) ease-in-out infinite;
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

/* 前半圈在原子核後面，後半圈轉到前面。z-index 是整數，會直接跳階不會漸變 */
@keyframes orbit-depth {
  0%, 49.9% { z-index: 0; }
  50%, 100% { z-index: 2; }
}

@keyframes orbit-scale {
  0%, 100% { transform: scale(var(--depth, 0.5)); }
  50%      { transform: scale(1); }
}

/* ── 靜止排開：等角度均分，彼此距離最遠，完全不動 ── */
.layers--static .electron {
  z-index: 2;
  transform: rotate(var(--angle)) translateX(var(--radius, 225%)) rotate(calc(-1 * var(--angle)));
}

@media (prefers-reduced-motion: reduce) {
  .electron,
  .electron img { animation: none !important; }
  .layers--orbit .electron {
    z-index: 2;
    transform:
      rotate(var(--tilt, 0deg)) scaleY(var(--flatten, 1))
      rotate(var(--angle)) translateX(var(--radius, 225%))
      rotate(calc(-1 * var(--angle))) scaleY(calc(1 / var(--flatten, 1))) rotate(calc(-1 * var(--tilt, 0deg)));
  }
}
</style>

<style>
/* Teleport 到 body 的內容不在元件範圍內，樣式不能加 scoped */
.free-field {
  position: fixed;
  inset: 0;
  z-index: 5;
  pointer-events: none;
  overflow: hidden;
}

/* 用 absolute 而不是 fixed：fixed 不會被 .free-field 的 overflow 裁切，
   萬一路徑算到邊界外就會撐出捲軸 */
.free-electron {
  position: absolute;
  top: 0;
  left: 0;
  width: var(--size, 6vmin);
  height: var(--size, 6vmin);
  margin: calc(var(--size, 6vmin) / -2) 0 0 calc(var(--size, 6vmin) / -2);
  opacity: var(--fade, 0.8);
  animation: wander var(--duration, 45s) ease-in-out infinite;
  animation-delay: var(--delay, 0s);
  will-change: transform;
}

.free-electron img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border: none;
  border-radius: 0;
  display: block;
  animation: wander-spin var(--spin, 20s) linear infinite;
}

/* 四個停留點繞一圈回到起點，路徑才接得起來 */
@keyframes wander {
  0%   { transform: translate(var(--x0), var(--y0)); }
  25%  { transform: translate(var(--x1), var(--y1)); }
  50%  { transform: translate(var(--x2), var(--y2)); }
  75%  { transform: translate(var(--x3), var(--y3)); }
  100% { transform: translate(var(--x0), var(--y0)); }
}

@keyframes wander-spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

@media (prefers-reduced-motion: reduce) {
  .free-electron,
  .free-electron img { animation: none !important; }
  .free-electron { transform: translate(var(--x0), var(--y0)); }
}
</style>
