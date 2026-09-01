// 分子分類的規則測試。
//
// 這些案例在功能開發時就跑過一遍，只是當時寫在暫存檔裡、驗完就丟了。
// 收進 repo 的理由是分類規則會再被動到：之後若要細分官能基、或調整
// 類金屬的歸屬，這裡會立刻告訴你有沒有破壞既有判定。
//
// 選這個模組當第一批測試，因為它是純函式——輸入元素陣列、輸出分類字串，
// 不碰 API、不碰 DOM、不需要 Firebase 憑證。專案裡多數邏輯還沒有這個
// 性質，這也是它值得當範例的原因。

import { describe, it, expect } from 'vitest'
import {
  autoCategory,
  moleculeCategory,
  metallicity,
  groupByCategory,
  CATEGORY_ELEMENTAL,
  CATEGORY_METAL,
  CATEGORY_METALLOID,
  CATEGORY_NONMETAL
} from './moleculeCategory'

describe('metallicity', () => {
  it('依週期表 GroupBlock 判定三態', () => {
    expect(metallicity('Na')).toBe('metal')
    expect(metallicity('Fe')).toBe('metal')
    expect(metallicity('O')).toBe('nonmetal')
    expect(metallicity('C')).toBe('nonmetal')
    expect(metallicity('Si')).toBe('metalloid')
  })

  // 這幾個的判定與部分教科書不同，是刻意對齊站上的週期表資料。
  // 若哪天改成教科書版本，這裡會失敗——那就是提醒去更新 context.md
  it('PubChem 的判定與教科書不同之處', () => {
    expect(metallicity('Po')).toBe('metalloid')  // 常被歸金屬
    expect(metallicity('At')).toBe('nonmetal')   // 常被視為類金屬
    expect(metallicity('Og')).toBe('nonmetal')   // 人造超重元素，按族歸惰性氣體
    expect(metallicity('Ts')).toBe('nonmetal')   // 同上，按族歸鹵素
  })

  it('不是元素符號就回空字串', () => {
    expect(metallicity('Xx')).toBe('')
    expect(metallicity('')).toBe('')
  })
})

describe('autoCategory', () => {
  it('單一元素構成的是單質', () => {
    expect(autoCategory(['N'])).toBe(CATEGORY_ELEMENTAL)
    expect(autoCategory(['Fe'])).toBe(CATEGORY_ELEMENTAL)
  })

  it('全非金屬構成的是共價化合物', () => {
    expect(autoCategory(['H', 'O'])).toBe(CATEGORY_NONMETAL)
    expect(autoCategory(['C', 'H'])).toBe(CATEGORY_NONMETAL)
    expect(autoCategory(['C', 'O'])).toBe(CATEGORY_NONMETAL)      // CO₂：含碳但不含金屬
    expect(autoCategory(['H', 'S', 'O'])).toBe(CATEGORY_NONMETAL) // H₂SO₄
  })

  it('含金屬就歸含金屬化合物', () => {
    expect(autoCategory(['Na', 'Cl'])).toBe(CATEGORY_METAL)
    expect(autoCategory(['Fe', 'O'])).toBe(CATEGORY_METAL)
    expect(autoCategory(['Ca', 'C', 'O'])).toBe(CATEGORY_METAL)   // CaCO₃
  })

  // 判定順序的關鍵案例：金屬的性質在化合物裡是主導的那個
  it('同時含金屬與類金屬時，金屬優先', () => {
    expect(autoCategory(['Na', 'Si', 'O'])).toBe(CATEGORY_METAL)  // Na₂SiO₃
  })

  it('含類金屬但不含金屬', () => {
    expect(autoCategory(['Si', 'O'])).toBe(CATEGORY_METALLOID)
    expect(autoCategory(['As', 'H'])).toBe(CATEGORY_METALLOID)
    expect(autoCategory(['B', 'H'])).toBe(CATEGORY_METALLOID)
  })

  // 認不出來時回空字串，呼叫端當「未分類」處理，不要硬塞一類
  it('認不出任何元素就回空字串', () => {
    expect(autoCategory([])).toBe('')
    expect(autoCategory(['Xx'])).toBe('')
    expect(autoCategory(['Zz', 'Qq'])).toBe('')
    expect(autoCategory(undefined)).toBe('')
  })

  it('夾雜無效符號時，只看認得出來的那些', () => {
    expect(autoCategory(['Na', 'Xx'])).toBe(CATEGORY_ELEMENTAL)   // 只剩 Na 一種
    expect(autoCategory(['Na', 'Cl', 'Xx'])).toBe(CATEGORY_METAL)
  })
})

describe('moleculeCategory', () => {
  it('後台手填的分類優先於自動判斷', () => {
    expect(moleculeCategory({ elements: ['H', 'O'], category: '溶劑' })).toBe('溶劑')
  })

  it('沒填才自動判斷', () => {
    expect(moleculeCategory({ elements: ['H', 'O'], category: '' })).toBe(CATEGORY_NONMETAL)
    expect(moleculeCategory({ elements: ['H', 'O'] })).toBe(CATEGORY_NONMETAL)
  })

  it('只有空白的 category 視同沒填', () => {
    expect(moleculeCategory({ elements: ['Na', 'Cl'], category: '   ' })).toBe(CATEGORY_METAL)
  })
})

describe('groupByCategory', () => {
  // 用的是 production 上的實際資料（含使用者自己新增的 NaCl）
  const live = [
    { slug: 'sodium-chloride', formula: 'ClNa', elements: ['Cl', 'Na'] },
    { slug: 'molecular-nitrogen', formula: 'N2', elements: ['N'] },
    { slug: 'molecular-hydrogen', formula: 'H2', elements: ['H'] },
    { slug: 'molecular-oxygen', formula: 'O2', elements: ['O'] },
    { slug: 'oxidane', formula: 'H2O', elements: ['H', 'O'] }
  ]

  it('分組順序照 MOLECULE_CATEGORIES', () => {
    const groups = groupByCategory(live)
    expect(groups.map(g => g.category)).toEqual([
      CATEGORY_ELEMENTAL, CATEGORY_METAL, CATEGORY_NONMETAL
    ])
    expect(groups.map(g => g.molecules.length)).toEqual([3, 1, 1])
  })

  it('自訂分類排在已知分類之後，「其他」墊底', () => {
    const groups = groupByCategory([
      { slug: 'a', elements: ['N'] },
      { slug: 'b', elements: ['H', 'O'], category: '溶劑' },
      { slug: 'c', elements: [] }
    ])
    expect(groups.map(g => g.category)).toEqual([CATEGORY_ELEMENTAL, '溶劑', '其他'])
  })

  it('認不出分類的分子收進「其他」，不會憑空消失', () => {
    const groups = groupByCategory([{ slug: 'x', elements: ['Zz'] }])
    expect(groups).toHaveLength(1)
    expect(groups[0].category).toBe('其他')
    expect(groups[0].molecules).toHaveLength(1)
  })

  it('空清單回空陣列', () => {
    expect(groupByCategory([])).toEqual([])
    expect(groupByCategory(undefined)).toEqual([])
  })
})
