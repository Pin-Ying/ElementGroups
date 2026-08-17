// 隱形浮水印的瀏覽器端實作（issue #25）。後端 app/watermark.py 的 JS 版，
// 一個檔對一個檔：套用（embed）與還原（reveal）都在這裡，常數只有一份。
//
// 兩件事刻意與後端保持一致，不然同一個簽名在兩邊會印出不同的圖樣：
//
// 1. **參數**：圖樣單元 192px、先畫在 TILE/BLOCK 的小格子上再放大 8 倍、
//    強度 3、同一組 RGB 位移、輸出 JPEG q90。
// 2. **簽名只能用英數**。後端要靠伺服器上的字型檔把文字畫成圖樣，而 Render 的
//    python:3.11-slim 一個字型都沒有（/usr/share/fonts 是空的），所以後端的
//    文字模式本來就只支援英數；瀏覽器雖然有中文字型，這裡仍然照同一條規則擋
//    下來，兩邊的行為才會一樣。中文簽名走後台的「上傳圖片」模式。
//
// 為什麼整組運算放在瀏覽器端而不是打後端：
//
// - 訪客要檢查的圖不必上傳，也就不必信任我們會不會留著它。
// - 後端在免費方案只有一個 worker（issue #28），陌生人上傳的大圖一張就能把
//   整站卡住。這裡的運算是 O(像素數) 的幾次掃描，交給瀏覽器剛好。
//
// 這裡只負責「顯示」，不做「判定」。自動判定要拿圖樣去比對所有位移與縮放，
// 而任意比例縮放過的圖對不上模板就會誤判成沒有——與其給出會說謊的是非題，
// 不如把還原圖攤開來讓人自己看。

// ── 共用參數（與後端 app/watermark.py 對齊）────────────────────────────

export const TILE = 192          // 圖樣單元邊長，同後端 DEFAULT_TILE
export const BLOCK = 8           // 先畫小格再放大的倍率，紋路才壓得住 JPEG
export const STRENGTH = 3        // 色度位移量，同後端 DEFAULT_STRENGTH
export const MIN_EDGE = 64       // 太小的圖不套，同後端
export const MAX_TEXT = 16       // 簽名長度上限，同後端 normalize()
export const JPEG_QUALITY = 0.9  // 同後端 encode_data_url

export const DEFAULT_WINDOW = TILE / 4  // 高通窗半徑，同後端 REVEAL_WINDOW
export const DEFAULT_GAIN = 24          // 顯影強度，同後端 REVEAL_GAIN
export const MIN_GAIN = 8
export const MAX_GAIN = 64

// 超過這個像素數就先等比縮小再算。四千萬像素的手機原圖會讓行動裝置直接分頁
// 崩掉，而縮小只是讓紋路變細，簽名照樣看得見。
export const MAX_PIXELS = 12e6

// 可列印的 ASCII。和後端同一條線：後端沒有字型畫得出這個範圍以外的字
const ASCII_ONLY = /^[\x20-\x7E]+$/

// ΔCb = +p、ΔCr = −p 換算成 RGB 的位移量。直接加在 RGB 上，等價於「只動色度、
// 不動亮度」：ΔY = 0.299·(−1.402) + 0.587·(+0.370) + 0.114·(+1.772) ≈ 0
const RGB_DELTA = [-1.402, 0.714136 - 0.344136, 1.772]

// ── 圖樣 ──────────────────────────────────────────────────────────────

/**
 * 把文字畫成 TILE×TILE、零均值、值域 [-1, 1] 的圖樣。
 *
 * 先畫在 TILE/BLOCK 的小格子上再放大，最細的紋路也有 8 像素寬——JPEG 的
 * 4:2:0 色度次取樣會把細線條吃掉，圖樣必須夠粗、夠低頻。
 *
 * @param {string} text 英數簽名，最多 MAX_TEXT 個字
 * @returns {Float32Array} 長度 TILE*TILE
 */
export function textMask(text) {
  const signature = (text || '').trim().slice(0, MAX_TEXT)
  if (!signature) throw new Error('請先打上你的簽名')
  if (!ASCII_ONLY.test(signature)) {
    throw new Error('簽名只能用英數字。這和站方自己的浮水印是同一條規則——'
      + '伺服器上沒有中文字型，畫不出中文的圖樣')
  }

  const small = Math.max(8, Math.round(TILE / BLOCK))
  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = small
  const ctx = canvas.getContext('2d', { willReadFrequently: true })
  ctx.fillStyle = '#000'
  ctx.fillRect(0, 0, small, small)
  ctx.fillStyle = '#fff'
  ctx.textBaseline = 'alphabetic'

  // 挑一個塞得進格子的字級
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

// ── 套用 ──────────────────────────────────────────────────────────────

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

// ── 還原 ──────────────────────────────────────────────────────────────

/** 一維移動平均，用滑動窗累加，邊界取邊界值（等同後端 np.pad(mode="edge")）。 */
function boxBlur1d(src, out, length, count, stride, radius) {
  const width = 2 * radius + 1
  for (let line = 0; line < count; line++) {
    const base = stride === 1 ? line * length : line
    const at = i => src[base + Math.min(length - 1, Math.max(0, i)) * stride]
    let sum = 0
    for (let k = -radius; k <= radius; k++) sum += at(k)
    out[base] = sum / width
    for (let i = 1; i < length; i++) {
      sum += at(i + radius) - at(i - radius - 1)
      out[base + i * stride] = sum / width
    }
  }
}

/**
 * 算出色度殘差：正常的畫面內容會被減掉，只留下浮水印那個頻段。
 *
 * 訊號取 (Cb − Cr) / 2——嵌入時 Cb 加、Cr 減同一個圖樣，相減就把兩邊的訊號
 * 併成一整份。
 *
 * @param {ImageData} imageData
 * @param {number} [radius] 高通窗半徑
 * @returns {Float32Array} 與 imageData 同尺寸，一個像素一個值
 */
export function chromaResidual(imageData, radius = DEFAULT_WINDOW) {
  const { width, height, data } = imageData
  const count = width * height
  const signal = new Float32Array(count)

  // (Cb − Cr) / 2 直接由 RGB 展開，省掉一次色彩空間轉換：
  // Cb − Cr = −0.668736·R + 0.087424·G + 0.581312·B（兩邊的 +128 相減掉了）
  for (let i = 0, p = 0; i < count; i++, p += 4) {
    signal[i] = (-0.334368 * data[p] + 0.043712 * data[p + 1] + 0.290656 * data[p + 2])
  }

  // 低頻用移動平均這種「位置無關」的做法算。用縮小再放大會在平滑漸層上留下
  // 以取樣格為週期的漣漪，那個週期一旦和圖樣對上，乾淨的圖也會浮出假紋路。
  const blurred = new Float32Array(count)
  const scratch = new Float32Array(count)
  boxBlur1d(signal, scratch, width, height, 1, radius)
  boxBlur1d(scratch, blurred, height, width, width, radius)

  const residual = new Float32Array(count)
  for (let i = 0; i < count; i++) residual[i] = signal[i] - blurred[i]
  return residual
}

/** 把殘差畫成灰階圖：128 為中間值，乘上 gain 讓它從看不見變成看得見。 */
export function residualToImageData(residual, width, height, gain = DEFAULT_GAIN) {
  const out = new ImageData(width, height)
  const pixels = out.data
  for (let i = 0, p = 0; i < residual.length; i++, p += 4) {
    let value = 128 + residual[i] * gain
    value = value < 0 ? 0 : value > 255 ? 255 : value
    pixels[p] = pixels[p + 1] = pixels[p + 2] = value
    pixels[p + 3] = 255
  }
  return out
}

// ── 讀檔 ──────────────────────────────────────────────────────────────

/**
 * 讀檔案並取出像素。太大的圖先等比縮小。
 *
 * @param {File|Blob} file
 * @returns {Promise<{imageData: ImageData, width: number, height: number, scaled: boolean}>}
 */
export async function imageDataFrom(file) {
  const url = URL.createObjectURL(file)
  try {
    const img = await new Promise((resolve, reject) => {
      const el = new Image()
      el.onload = () => resolve(el)
      el.onerror = () => reject(new Error('這個檔案不是瀏覽器能讀的圖片格式'))
      el.src = url
    })

    const source = img.naturalWidth * img.naturalHeight
    const ratio = source > MAX_PIXELS ? Math.sqrt(MAX_PIXELS / source) : 1
    const width = Math.max(1, Math.round(img.naturalWidth * ratio))
    const height = Math.max(1, Math.round(img.naturalHeight * ratio))

    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const ctx = canvas.getContext('2d', { willReadFrequently: true })
    ctx.drawImage(img, 0, 0, width, height)
    return { imageData: ctx.getImageData(0, 0, width, height), width, height, scaled: ratio < 1 }
  } finally {
    URL.revokeObjectURL(url)
  }
}
