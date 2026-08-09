// 分子式的結構化表示與序列化。
//
// 結構仿照運算式樹：每個節點是「元素」或「群組」，都可以帶數量，
// 群組可以再巢狀，於是 Ca(OH)2、Fe2(SO4)3 這類都表示得出來。
//
//   [
//     { type: 'element', symbol: 'Ca', count: 1 },
//     { type: 'group', count: 2, children: [
//         { type: 'element', symbol: 'O', count: 1 },
//         { type: 'element', symbol: 'H', count: 1 }
//     ]}
//   ]
//
// 序列化後為 "Ca(OH)2"，可直接拿去 PubChem 以分子式查詢。

const SUBSCRIPTS = ['₀', '₁', '₂', '₃', '₄', '₅', '₆', '₇', '₈', '₉']

export function elementNode(symbol) {
  return { type: 'element', symbol, count: 1 }
}

export function groupNode(children = []) {
  return { type: 'group', count: 1, children }
}

/** 序列化成標準分子式，例如 Ca(OH)2。數量為 1 時省略。 */
export function toFormula(nodes) {
  if (!Array.isArray(nodes)) return ''
  return nodes.map(node => {
    if (node.type === 'element') {
      return node.symbol + (node.count > 1 ? node.count : '')
    }
    if (node.type === 'group') {
      const inner = toFormula(node.children)
      if (!inner) return ''
      // 只有一個元素又沒有倍數時不needs括號
      const needsParens = node.count > 1 || node.children.length > 1
      return needsParens
        ? `(${inner})${node.count > 1 ? node.count : ''}`
        : inner
    }
    return ''
  }).join('')
}

/** 顯示用：數字轉成下標，例如 H₂O。 */
export function toDisplay(nodes) {
  return toFormula(nodes).replace(/\d/g, d => SUBSCRIPTS[Number(d)])
}

/** 統計各元素的總原子數，群組的倍數會乘進去。 */
export function elementCounts(nodes, multiplier = 1, acc = {}) {
  if (!Array.isArray(nodes)) return acc
  for (const node of nodes) {
    const n = (node.count || 1) * multiplier
    if (node.type === 'element') {
      acc[node.symbol] = (acc[node.symbol] || 0) + n
    } else if (node.type === 'group') {
      elementCounts(node.children, n, acc)
    }
  }
  return acc
}

/** 用到的元素符號，供分子與元素頁互相連結。 */
export function usedElements(nodes) {
  return Object.keys(elementCounts(nodes))
}

/**
 * 把分子式字串解析回節點結構，例如從 PubChem 查回來的 "C6H12O6"。
 * 只處理元素、數量與一層以上的括號；解析不出來時回傳空陣列。
 */
export function parseFormula(text) {
  const source = String(text || '').trim()
  if (!source) return []

  let i = 0

  function parseSequence(stopAtParen) {
    const nodes = []
    while (i < source.length) {
      const ch = source[i]

      if (ch === '(' || ch === '[') {
        i++
        const children = parseSequence(true)
        const count = readNumber()
        nodes.push({ type: 'group', count: count || 1, children })
        continue
      }

      if (ch === ')' || ch === ']') {
        if (stopAtParen) { i++; return nodes }
        i++
        continue
      }

      const symbol = readSymbol()
      if (!symbol) { i++; continue }
      nodes.push({ type: 'element', symbol, count: readNumber() || 1 })
    }
    return nodes
  }

  function readSymbol() {
    if (!/[A-Z]/.test(source[i] || '')) return ''
    let symbol = source[i++]
    while (i < source.length && /[a-z]/.test(source[i])) symbol += source[i++]
    return symbol
  }

  function readNumber() {
    let digits = ''
    while (i < source.length && /\d/.test(source[i])) digits += source[i++]
    return digits ? Number(digits) : 0
  }

  return parseSequence(false)
}
