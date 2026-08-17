// 浮水印的批次作業（issue #25）。
//
// 兩個用途共用這一份：「套用到既有的所有圖片」（backfill）與「用新設定重印」
// （repaint）。後台的浮水印分頁與維護工具都會叫它，邏輯只有一份。
//
// 為什麼要分批：一次做完會超過後端 gunicorn 的 30 秒上限，而且只有一個
// worker（issue #28），整站會在那段時間沒反應。所以先問有哪些位置，一個位置
// 一次請求；一個位置的圖太多時後端回 more=true，帶著 offset 再叫一次同一個
// 位置。

import { getRepaintTargets, repaintWatermark, getBackfillTargets, backfillWatermark } from '../api'

export const JOBS = {
  backfill: { label: '套用', list: getBackfillTargets, run: backfillWatermark },
  repaint: { label: '重印', list: getRepaintTargets, run: repaintWatermark }
}

/**
 * 跑一個批次作業。
 *
 * @param {'backfill'|'repaint'} kind
 * @param {(progress: {label: string, total: number, done: number, images: number, failed: number}) => void} [onProgress]
 * @returns {Promise<{label: string, images: number, failed: number, text: string}>}
 */
export async function runWatermarkJob(kind, onProgress = () => {}) {
  const { label, list, run } = JOBS[kind]
  const progress = { label, total: 0, done: 0, images: 0, failed: 0 }
  onProgress(progress)

  const { data } = await list()
  const targets = data.targets || []
  progress.total = targets.length
  onProgress(progress)

  for (const path of targets) {
    try {
      let offset = 0
      let more = true
      while (more) {
        const { data: one } = await run(path, offset)
        offset += one.count || 0
        progress.images += one.count || 0
        // count 為 0 時一定要停，否則後端只要一直回 more 就會轉不完
        more = !!one.more && one.count > 0
        onProgress(progress)
      }
    } catch (e) {
      // 單一位置失敗不該中斷整批：其餘照樣做，最後一次報告
      console.error(`${label}失敗:`, path, e)
      progress.failed++
    }
    progress.done++
    onProgress(progress)
  }

  const text = `${label}完成，共 ${progress.images} 張`
    + (progress.failed ? `，有 ${progress.failed} 個位置失敗（見主控台）` : '')
  return { label, images: progress.images, failed: progress.failed, text }
}
