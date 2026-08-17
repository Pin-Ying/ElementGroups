// 在瀏覽器裡把簽名藏進圖片的色度（issue #25）。
//
// 後端 app/watermark.py 的 embed()／tile_mask() 的 JS 版，參數刻意保持一致
// （圖樣單元 192px、先畫小格再放大 8 倍、同一組 RGB 位移、輸出 JPEG q90），
// 所以這裡印出來的圖用後端的 reveal() 也讀得出來。
//
// 這是給訪客玩的：簽名是他自己打的，和站長設定的浮水印無關，圖與簽名都不會
// 離開他的瀏覽器。站長真正在用的簽名只存在後端，前端拿不到也不該拿到。
//
// 附帶一個後端做不到的事：瀏覽器有中文字型，所以這裡打中文可以，而 Render 的
// python:3.11-slim 一個中文字型都沒有（後端因此只能用英數或改上傳圖樣）。

export const TILE = 192          // 圖樣單元邊長，同後端 DEFAULT_TILE
export const BLOCK = 8           // 先畫在 TILE/BLOCK 的小格子上再放大，紋路才壓得住 JPEG
export const STRENGTH = 3        // 色度位移量，同後端 DEFAULT_STRENGTH
export const MIN_EDGE = 64       // 太小的圖不套，同後端
export const MAX_TEXT = 16       // 簽名長度上限，同後端 normalize()
export const JPEG_QUALITY = 0.9  // 同後端 encode_data_url，再低色度量化就開始吃圖樣

// ΔCb = +p、ΔCr = −p 換算成 RGB 的位移量。直接加在 RGB 上，等價於「只動色度、
// 不動亮度」：ΔY = 0.299·(−1.402) + 0.587·(+0.370) + 0.114·(+1.772) ≈ 0
const RGB_DELTA = [-1.402, 0.714136 - 0.344136, 1.772]

/**
 * 把文字畫成 TILE×TILE、零均值、值域 [-1, 1] 的圖樣。
 *
 * 先畫在 TILE/BLOCK 的小格子上再放大，最細的紋路也有 8 像素寬——JPEG 的 4:2:0
 * 色度次取樣會把細線條吃掉，圖樣必須夠粗、夠低頻。
 *
 * @param {string} text
 * @returns {Float32Array} 長度 TILE*TILE
 */
export function textMask(text) {
  const signature = (text || '').trim().slice(0, MAX_TEXT)
  if (!signature) throw new Error('請先打上你的簽名')

  const small = Math.max(8, Math.round(TILE / BLOCK))
  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = small
  const ctx = canvas.getContext('2d', { willReadFrequently: true })
  ctx.fillStyle = '#000'
  ctx.fillRect(0, 0, small, small)
  ctx.fillStyle = '#fff'
  ctx.textBaseline = 'alphabetic'

  // 挑一個塞得進格子的字級。字型串裡不指定中文字型，交給系統自己 fallback
  let size = Math.floor(small * 0.9)
  let metrics
  for (; size > 4; size--) {
    ctx.font = `700 ${size}px "Space Grotesk", system-ui, sans-serif`
    metrics = ctx.measureText(signature)
    const ascent = metrics.actualBoundingBoxAscent || size * 0.8
    const descent = metrics.actualBoundingBoxDescent || 0
    if (metrics.width <= small && ascent + descent <= small) break
  }
  const ascent = metrics.actualBoundingBoxAscent || size * 0.8
  const descent = metrics.actualBoundingBoxDescent || 0
  ctx.fillText(signature, (small - metrics.width) / 2, (small - (ascent + descent)) / 2 + ascent)

  // 放大 BLOCK 倍（最近鄰，等同後端的 np.kron）
  const pixels = ctx.getImageData(0, 0, small, small).data
  const mask = new Float32Array(TILE * TILE)
  let sum = 0
  for (let y = 0; y < TILE; y++) {
    const sourceRow = Math.min(small - 1, Math.floor(y / BLOCK)) * small
    for (let x = 0; x < TILE; x++) {
      const value = pixels[(sourceRow + Math.min(small - 1, Math.floor(x / BLOCK))) * 4] / 255
      mask[y * TILE + x] = value
      sum += value
    }
  }

  // 零均值：整張圖的平均色度不變，才不會整張偏色
  const mean = sum / mask.length
  let peak = 0
  for (let i = 0; i < mask.length; i++) {
    mask[i] -= mean
    const magnitude = Math.abs(mask[i])
    if (magnitude > peak) peak = magnitude
  }
  if (peak < 1e-6) throw new Error('這個簽名畫出來是整片空白，換幾個字試試')
  for (let i = 0; i < mask.length; i++) mask[i] /= peak
  return mask
}

/**
 * 把圖樣鋪滿整張圖，回傳新的一份（原本那份不動——呼叫端還要拿它顯示原圖、
 * 或換個簽名再印一次）。
 *
 * 透明的地方不動：那裡的 RGB 多半是垃圾值，加了位移只會被 clip 掉。
 */
export function embed(source, mask, strength = STRENGTH) {
  const imageData = new ImageData(
    new Uint8ClampedArray(source.data), source.width, source.height)
  const { width, height, data } = imageData
  for (let y = 0; y < height; y++) {
    const maskRow = (y % TILE) * TILE
    for (let x = 0; x < width; x++) {
      const p = (y * width + x) * 4
      if (data[p + 3] === 0) continue
      const amount = mask[maskRow + (x % TILE)] * strength
      for (let c = 0; c < 3; c++) {
        const value = Math.round(data[p + c] + amount * RGB_DELTA[c])
        data[p + c] = value < 0 ? 0 : value > 255 ? 255 : value
      }
    }
  }
  return imageData
}

/**
 * 套上簽名並重新編碼，回傳可以下載、也可以再丟回去看還原的 Blob。
 *
 * 有透明就走 PNG（JPEG 沒有 alpha，去背圖存成 JPEG 會多出一塊黑底），
 * 其餘走 JPEG q90，跟後端出貨的那份一樣。
 *
 * @returns {Promise<Blob>}
 */
export async function markImage(imageData, text, strength = STRENGTH) {
  if (Math.min(imageData.width, imageData.height) < MIN_EDGE) {
    throw new Error(`圖太小了（短邊要有 ${MIN_EDGE}px 以上），浮水印藏不進去`)
  }
  const marked = embed(imageData, textMask(text), strength)

  const canvas = document.createElement('canvas')
  canvas.width = marked.width
  canvas.height = marked.height
  canvas.getContext('2d').putImageData(marked, 0, 0)

  let transparent = false
  for (let p = 3; p < marked.data.length; p += 4) {
    if (marked.data[p] < 255) { transparent = true; break }
  }
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      blob => (blob ? resolve(blob) : reject(new Error('圖片轉檔失敗'))),
      transparent ? 'image/png' : 'image/jpeg',
      transparent ? undefined : JPEG_QUALITY
    )
  })
}
