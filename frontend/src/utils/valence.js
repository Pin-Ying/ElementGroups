// 從電子組態算出最外層電子數。
//
// 用途：元素頁的電子圖層要放幾顆電子，依這個數字決定。
//
// 作法是取電子組態中主量子數最大的那一層，把該層各軌域的電子數加總。
// 例如：
//   H  → 1s1              → n=1 → 1
//   O  → [He]2s2 2p4      → n=2 → 2 + 4 = 6
//   Fe → [Ar]4s2 3d6      → n=4 → 2（3d 屬於 n=3，不算最外層）
//
// 注意這是「最外層電子數」而非嚴格定義的價電子數：過渡金屬的 d 軌域
// 電子也會參與成鍵，但對這裡的視覺呈現來說，取最外殼層就夠了。

export const MAX_ELECTRONS = 8

export function outerElectronCount(configuration) {
  if (!configuration) return 0

  // 去掉 [Ar] 這類內層簡寫與 (predicted) 註記
  const cleaned = String(configuration)
    .replace(/\[[A-Za-z]+\]/g, ' ')
    .replace(/\(predicted\)/gi, ' ')

  // 逐個抓「主量子數 + 軌域字母 + 電子數」，例如 4s2、3d6、2p4
  const orbitals = [...cleaned.matchAll(/(\d+)\s*([spdf])\s*(\d+)/gi)]
  if (!orbitals.length) return 0

  let maxShell = 0
  for (const [, shell] of orbitals) {
    maxShell = Math.max(maxShell, Number(shell))
  }

  let count = 0
  for (const [, shell, , electrons] of orbitals) {
    if (Number(shell) === maxShell) count += Number(electrons)
  }

  return Math.min(count, MAX_ELECTRONS)
}
