// 內建頁面文案的欄位定義與預設值（issue #20）。
// 後台依這份定義長出編輯欄位；前台讀不到覆寫值時退回這裡的 default，
// 所以部署更新預設文案不會蓋掉後台已編輯的內容。
//
// 標題類的預設值一律用英文，當作中性的佔位字。中文由站長在後台自己填，
// 這樣預設值與實際文案不會混在一起，也不會出現「有些預設是中文、有些
// 是英文」的不一致。
export const PAGE_META_DEFS = [
  {
    key: 'molecules',
    label: '分子圖鑑（/molecules）',
    fields: [
      { name: 'title', label: '頁面標題', default: 'Molecule Groups' },
      { name: 'subtitle', label: '副標題', default: '', multiline: true },
      { name: 'empty_text', label: '沒有任何分子時的文字', default: '還沒有建立任何分子' },
      { name: 'filter_note', label: '元素篩選說明（{element} 會代入元素符號）', default: '只顯示含有 {element} 的分子' }
    ]
  },
  {
    key: 'molecule',
    label: '分子頁（/molecule/…）',
    fields: [
      { name: 'elements_label', label: '「組成元素」區塊標題', default: 'Composition' },
      { name: 'back_label', label: '返回連結文字', default: '← Molecule Groups' },
      { name: 'not_found', label: '找不到分子時的文字', default: '找不到這個分子' }
    ]
  },
  {
    key: 'particles',
    label: '基本粒子（/particles）',
    fields: [
      { name: 'title', label: '頁面標題', default: 'Elementary Particles' },
      { name: 'subtitle', label: '副標題', default: '組成元素的更小單位，每種粒子都有自己的形象。', multiline: true },
      { name: 'empty_text', label: '沒有任何粒子時的文字', default: '還沒有建立任何粒子' }
    ]
  },
  {
    key: 'story',
    label: '元素頁區塊標題',
    fields: [
      { name: 'groups_title', label: '主族形象區塊', default: 'Group Archetype' },
      { name: 'molecules_title', label: '相關分子區塊', default: 'Related Molecules' },
      { name: 'gallery_title', label: '其他樣貌區塊', default: 'Other Forms' }
    ]
  },
  {
    key: 'footer',
    label: '頁尾',
    fields: [
      { name: 'source_label', label: '資料來源連結文字', default: 'Data from PubChem' }
    ]
  }
]

export function metaDef(key) {
  return PAGE_META_DEFS.find(d => d.key === key)
}

export function fieldDefault(key, field) {
  return metaDef(key)?.fields.find(f => f.name === field)?.default ?? ''
}
