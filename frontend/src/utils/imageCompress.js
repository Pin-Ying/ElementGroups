// 上傳前的圖片壓縮。
//
// 圖片會以 base64 存進 Realtime DB（base64 本身就比原檔大約 33%），
// Spark 免費方案有 1GB 上限，因此在送出前先等比縮小並重新編碼，
// 避免一張手機原圖就吃掉可觀的額度。

export const MAX_UPLOAD_BYTES = 5 * 1024 * 1024  // 超過這個大小直接擋下
export const MAX_EDGE = 1200                     // 長邊上限（px）
export const JPEG_QUALITY = 0.85

export function formatBytes(bytes) {
  if (!bytes) return '0 KB'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(0) + ' KB'
  return (bytes / 1024 / 1024).toFixed(2) + ' MB'
}

function loadImage(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const img = new Image()
    img.onload = () => {
      URL.revokeObjectURL(url)
      resolve(img)
    }
    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('圖片讀取失敗'))
    }
    img.src = url
  })
}

/**
 * 找出圖片中「不透明內容」的邊界。
 * 完全不透明的圖片會回傳整張圖的範圍。
 */
function contentBounds(ctx, width, height, alphaThreshold = 8) {
  const { data } = ctx.getImageData(0, 0, width, height)
  let top = height, left = width, right = -1, bottom = -1

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      if (data[(y * width + x) * 4 + 3] > alphaThreshold) {
        if (x < left) left = x
        if (x > right) right = x
        if (y < top) top = y
        if (y > bottom) bottom = y
      }
    }
  }

  if (right < 0) return null  // 整張透明
  return { left, top, width: right - left + 1, height: bottom - top + 1 }
}

/**
 * 把素材正規化成內容置中的正方形 PNG。
 *
 * 用於電子這類要疊在其他圖上的小圖：使用者提供的 PNG 常常帶著大片透明
 * 邊距、或根本不是正方形，只做等比縮放的話疊上去會偏小或偏移。這裡先
 * 裁掉透明邊距，再等比置中放進正方形畫布。
 *
 * @param {File} file
 * @param {object} [options]
 * @param {number} [options.size] 輸出邊長
 * @param {number} [options.padding] 四周留白佔邊長的比例
 */
export async function normalizeSprite(file, options = {}) {
  const { size = 240, padding = 0.04 } = options

  if (!file.type.startsWith('image/')) throw new Error('請選擇圖片檔')
  if (file.size > MAX_UPLOAD_BYTES) {
    throw new Error(`圖片 ${formatBytes(file.size)} 超過 ${formatBytes(MAX_UPLOAD_BYTES)} 上限`)
  }

  const img = await loadImage(file)

  // 先原尺寸畫一次以取得內容範圍
  const probe = document.createElement('canvas')
  probe.width = img.width
  probe.height = img.height
  const probeCtx = probe.getContext('2d', { willReadFrequently: true })
  probeCtx.drawImage(img, 0, 0)

  const bounds = contentBounds(probeCtx, img.width, img.height)
  if (!bounds) throw new Error('圖片內容是全透明的，請確認檔案')

  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const ctx = canvas.getContext('2d')

  // 等比縮放內容，讓長邊填滿扣掉留白後的空間
  const inner = size * (1 - padding * 2)
  const scale = Math.min(inner / bounds.width, inner / bounds.height)
  const drawW = bounds.width * scale
  const drawH = bounds.height * scale

  ctx.drawImage(
    img,
    bounds.left, bounds.top, bounds.width, bounds.height,
    (size - drawW) / 2, (size - drawH) / 2, drawW, drawH
  )

  const blob = await new Promise((resolve, reject) => {
    canvas.toBlob(b => (b ? resolve(b) : reject(new Error('圖片處理失敗'))), 'image/png')
  })

  return {
    blob,
    originalSize: file.size,
    compressedSize: blob.size,
    width: size,
    height: size,
    // 原圖有多少比例是透明邊距，供介面說明實際做了什麼
    trimmed: bounds.width !== img.width || bounds.height !== img.height,
    sourceSize: `${img.width}×${img.height}`,
    contentSize: `${bounds.width}×${bounds.height}`
  }
}

/**
 * 壓縮圖片檔。
 *
 * @param {File} file 使用者選的檔案
 * @param {object} [options]
 * @param {boolean} [options.keepTransparency] 保留透明背景。圖層與電子樣式
 *        這類要疊在其他圖上的素材必須開啟，否則 JPEG 會把透明區域填成黑色。
 * @param {number} [options.maxEdge] 長邊上限，預設 MAX_EDGE。PNG 壓不掉多少，
 *        需要透明的素材建議給小一點。
 * @returns {Promise<{blob: Blob, originalSize: number, compressedSize: number,
 *                    width: number, height: number, resized: boolean}>}
 * @throws {Error} 檔案過大或不是圖片時
 */
export async function compressImage(file, options = {}) {
  const { keepTransparency = false, maxEdge = MAX_EDGE } = options

  if (!file.type.startsWith('image/')) {
    throw new Error('請選擇圖片檔')
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    throw new Error(`圖片 ${formatBytes(file.size)} 超過 ${formatBytes(MAX_UPLOAD_BYTES)} 上限，請先縮小或改用其他圖片`)
  }

  const img = await loadImage(file)
  const scale = Math.min(1, maxEdge / Math.max(img.width, img.height))
  const width = Math.round(img.width * scale)
  const height = Math.round(img.height * scale)

  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d')
  ctx.drawImage(img, 0, 0, width, height)

  // PNG 才有 alpha 通道；toBlob 對 PNG 會忽略 quality 參數
  const type = keepTransparency ? 'image/png' : 'image/jpeg'
  const blob = await new Promise((resolve, reject) => {
    canvas.toBlob(
      b => (b ? resolve(b) : reject(new Error('圖片壓縮失敗'))),
      type,
      keepTransparency ? undefined : JPEG_QUALITY
    )
  })

  return {
    blob,
    originalSize: file.size,
    compressedSize: blob.size,
    width,
    height,
    resized: scale < 1
  }
}
