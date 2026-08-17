// 把圖片的色度差放大，讓隱形浮水印浮出來（issue #25）。
//
// 用的是後端 app/watermark.py 的同一組運算：訊號取 (Cb − Cr) / 2（嵌入時
// Cb 加、Cr 減同一個圖樣，相減就把兩邊的訊號併成一整份），減掉移動平均當
// 高通留下圖樣所在的頻段，再放大成灰階。
//
// 刻意放在瀏覽器端算，不走後端：
//
// 1. 使用者要檢查的圖不必上傳，也就不必信任我們會不會留著它。
// 2. 後端在免費方案只有一個 worker（issue #28），陌生人上傳的大圖一張就
//    能把整站卡住。這裡的運算是 O(像素數) 的幾次掃描，交給瀏覽器剛好。
//
// 這裡只負責「顯示」，不做「判定」。自動判定要拿圖樣去比對所有可能的位移與
// 縮放，而任意比例縮放過的圖對不上模板就會誤判成沒有——與其給出會說謊的
// 是非題，不如把還原圖攤開來讓人自己看。

export const DEFAULT_WINDOW = 48   // 高通窗半徑。後端預設圖樣單元 192px 的四分之一
export const DEFAULT_GAIN = 24     // 放大倍率。與後端還原圖的預設值相同
export const MIN_GAIN = 8
export const MAX_GAIN = 64

// 超過這個像素數就先等比縮小再算。四千萬像素的手機原圖會讓行動裝置直接分頁崩掉，
// 而縮小只是讓紋路變細，簽名照樣看得見。
export const MAX_PIXELS = 12e6

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

/** 把殘差畫成灰階圖：128 為中間值，放大 gain 倍。 */
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
