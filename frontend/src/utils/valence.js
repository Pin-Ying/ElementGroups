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

/**
 * 取出最外層各軌域的電子分布。
 *
 * 例如 O 的 [He]2s2 2p4 → [{ type: 's', count: 2 }, { type: 'p', count: 4 }]
 *
 * 用途：電子的運動路徑依所在軌域而不同——s 軌域是球對稱，p 軌域是沿著
 * 某個軸的啞鈴形，d 軌域更複雜。有了分布就能讓畫面呈現這件事，而不是
 * 全部電子繞同一種圓形軌道。
 */
export function outerOrbitals(configuration) {
  if (!configuration) return []

  const cleaned = String(configuration)
    .replace(/\[[A-Za-z]+\]/g, ' ')
    .replace(/\(predicted\)/gi, ' ')

  const orbitals = [...cleaned.matchAll(/(\d+)\s*([spdf])\s*(\d+)/gi)]
  if (!orbitals.length) return []

  const maxShell = Math.max(...orbitals.map(([, shell]) => Number(shell)))

  const order = { s: 0, p: 1, d: 2, f: 3 }
  return orbitals
    .filter(([, shell]) => Number(shell) === maxShell)
    .map(([, , type, electrons]) => ({
      type: type.toLowerCase(),
      count: Number(electrons)
    }))
    .sort((a, b) => order[a.type] - order[b.type])
}

/**
 * 把電子逐顆展開並標上所屬軌域，總數上限與 outerElectronCount 一致。
 * @returns {{type: string, indexInType: number}[]}
 */
export function outerElectronOrbitals(configuration) {
  const orbitals = outerOrbitals(configuration)
  const result = []
  for (const { type, count } of orbitals) {
    for (let i = 0; i < count && result.length < MAX_ELECTRONS; i++) {
      result.push({ type, indexInType: i })
    }
  }
  return result
}

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
