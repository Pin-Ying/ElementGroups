// 分子分類：依組成元素的金屬性決定。
//
// 為什麼用金屬性而不是有機／無機：有機無機的邊界是慣例問題——CO₂ 含碳但
// 習慣歸無機，碳酸鹽也是——要靠人工維護一張例外表才會準。金屬性則是查表
// 就有答案，118 個元素每個都確定，沒有爭議案例。
//
// 化學上這條軸也站得住腳：含金屬＋非金屬基本上就是離子化合物，全非金屬則
// 是共價（分子）化合物。已知的例外是有機金屬化合物（二茂鐵、四乙基鉛），
// 它們含金屬卻是共價鍵，這裡會被歸進「含金屬化合物」。以這個站的分子量級
// 不太會遇到，真的收錄了就在後台手動填 category 覆寫。
//
// 資料來源：週期表 GroupBlock 欄位（POST /api/groups 的 groups），也就是
// PubChem 給的分類，與站上元素頁看到的一致。這份對照不會變，所以照
// data/elementSymbols.js 的做法寫成靜態表，前台分類不必多打一次 API。
//
// 要注意 PubChem 的判定和部分教科書不同，這裡以站上資料為準：
//   Po（釙）歸類金屬，不少教科書歸金屬
//   At（砈）歸鹵素，常被視為類金屬
//   Ts、Og 是人造超重元素，實際性質未知，PubChem 按族歸為鹵素與惰性氣體

import { ELEMENT_SYMBOLS } from '../data/elementSymbols'

export const CATEGORY_ELEMENTAL = '單質'
export const CATEGORY_METAL = '含金屬化合物'
export const CATEGORY_METALLOID = '含類金屬'
export const CATEGORY_NONMETAL = '非金屬化合物'

// 前台分組與後台下拉的顯示順序：單質打頭，其餘照金屬性由強到弱
export const MOLECULE_CATEGORIES = [
  CATEGORY_ELEMENTAL,
  CATEGORY_METAL,
  CATEGORY_METALLOID,
  CATEGORY_NONMETAL
]

// 每一類的說明，前台篩選列的 title 與後台提示共用
export const CATEGORY_HINTS = {
  [CATEGORY_ELEMENTAL]: '只由一種元素構成，例如 O₂、Fe',
  [CATEGORY_METAL]: '組成裡含金屬元素，多半是離子化合物，例如 NaCl',
  [CATEGORY_METALLOID]: '含類金屬但不含金屬，例如 SiO₂',
  [CATEGORY_NONMETAL]: '完全由非金屬構成的共價化合物，例如 H₂O、CH₄'
}

// 只列非金屬與類金屬（27 個），其餘有效元素一律是金屬。
// 這樣寫不只是短，對未來新增的超重元素預設也是對的——它們幾乎都是金屬。
const NONMETALS = new Set([
  'H', 'He', 'C', 'N', 'O', 'F', 'Ne', 'P', 'S', 'Cl', 'Ar',
  'Se', 'Br', 'Kr', 'I', 'Xe', 'At', 'Rn', 'Ts', 'Og'
])

const METALLOIDS = new Set(['B', 'Si', 'Ge', 'As', 'Sb', 'Te', 'Po'])

// 分子式解析可能吐出不存在的符號（打錯字、或把 Co 鈷讀成 C+O），
// 那種東西不該影響分類，先用這份清單濾掉
const VALID = new Set(ELEMENT_SYMBOLS.map(e => e.Symbol))

/** 單一元素的金屬性：'metal' / 'metalloid' / 'nonmetal'，不是元素則回傳 ''。 */
export function metallicity(symbol) {
  if (!VALID.has(symbol)) return ''
  if (NONMETALS.has(symbol)) return 'nonmetal'
  if (METALLOIDS.has(symbol)) return 'metalloid'
  return 'metal'
}

/**
 * 從組成元素推斷分類。判定順序有意義：
 * 先看是不是單質，再由金屬性最強的元素決定——Na₂SiO₃ 同時含金屬與類金屬，
 * 歸「含金屬化合物」，因為金屬的性質在化合物裡是主導的那個。
 *
 * 認不出任何元素時回傳空字串，呼叫端當成「未分類」處理，不要硬塞一類。
 */
export function autoCategory(elements) {
  const known = (elements || []).filter(s => VALID.has(s))
  if (!known.length) return ''
  if (known.length === 1) return CATEGORY_ELEMENTAL

  const kinds = new Set(known.map(metallicity))
  if (kinds.has('metal')) return CATEGORY_METAL
  if (kinds.has('metalloid')) return CATEGORY_METALLOID
  return CATEGORY_NONMETAL
}

/**
 * 分子實際要顯示的分類。後台手動填的 category 永遠優先，
 * 沒填才用組成推斷——這樣既不必回填既有資料，也留著覆寫的餘地。
 */
export function moleculeCategory(molecule) {
  const manual = (molecule?.category || '').trim()
  if (manual) return manual
  return autoCategory(molecule?.elements)
}

/**
 * 把分子分組，回傳 [{ category, molecules }]。
 * 已知分類照 MOLECULE_CATEGORIES 排序，後台自訂的分類接在後面，
 * 完全認不出來的收在最後的「其他」，不會憑空消失。
 */
export function groupByCategory(molecules) {
  const buckets = new Map()
  for (const m of molecules || []) {
    const key = moleculeCategory(m) || '其他'
    if (!buckets.has(key)) buckets.set(key, [])
    buckets.get(key).push(m)
  }

  const rank = key => {
    const i = MOLECULE_CATEGORIES.indexOf(key)
    if (i >= 0) return i
    return key === '其他' ? 999 : 500
  }

  return [...buckets.entries()]
    .map(([category, items]) => ({ category, molecules: items }))
    .sort((a, b) => rank(a.category) - rank(b.category) ||
                    a.category.localeCompare(b.category, 'zh-Hant'))
}
