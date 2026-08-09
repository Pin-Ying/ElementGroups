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
