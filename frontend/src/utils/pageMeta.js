// 內建頁面文案的欄位定義與預設值（issue #20）。
// 後台依這份定義長出編輯欄位；前台讀不到覆寫值時退回這裡的 default，
// 所以部署更新預設文案不會蓋掉後台已編輯的內容。
//
// 標題類的預設值一律用英文，當作中性的佔位字。中文由站長在後台自己填，
// 這樣預設值與實際文案不會混在一起，也不會出現「有些預設是中文、有些
// 是英文」的不一致。
// 導覽位置的選項。放在這裡而不是 AdminView，是為了讓內建頁面的欄位定義
// 與自訂頁面的表單共用同一份，不要又變成兩個真相來源。
export const NAV_POSITIONS = [
  { key: 'sidebar', label: '左側導覽' },
  { key: 'footer', label: '頁尾' },
  { key: 'header', label: '頁首' },
  { key: 'none', label: '不顯示於導覽' }
]

// 純文案的內建頁面（沒有 Markdown 內容、不會進 _pages）也要能決定自己
// 放在哪個導覽位置，否則站長對這些頁面完全沒有主導權。
const NAV_FIELDS = [
  { name: 'nav_position', label: '導覽位置', type: 'select', options: NAV_POSITIONS, default: 'footer' },
  { name: 'nav_order', label: '導覽排序', type: 'number', default: '0' }
]

export const PAGE_META_DEFS = [
  {
    key: 'molecules',
    label: '分子圖鑑（/molecules）',
    fields: [
      { name: 'title', label: '頁面標題', default: 'Molecule Groups' },
      { name: 'subtitle', label: '副標題', default: '', multiline: true },
      { name: 'empty_text', label: '沒有任何分子時的文字', default: '還沒有建立任何分子' },
      { name: 'filter_note', label: '元素篩選說明（{element} 會代入元素符號）', default: '只顯示含有 {element} 的分子' },
      ...NAV_FIELDS
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
      { name: 'empty_text', label: '沒有任何粒子時的文字', default: '還沒有建立任何粒子' },
      ...NAV_FIELDS
    ]
  },
  {
    key: 'watermark',
    label: '浮水印檢視（/watermark）',
    fields: [
      { name: 'title', label: '頁面標題', default: 'Watermark Check' },
      {
        name: 'subtitle',
        label: '副標題',
        default: '這個站的作品都藏了一層看不見的簽名。把圖丟進來，色度差會被放大，簽名就會浮出來。',
        multiline: true
      },
      {
        name: 'hint',
        label: '操作說明',
        default: '也可以把圖直接拖進這個框，或按 Ctrl/⌘ + V 貼上。圖片不會上傳，全部在你自己的瀏覽器裡處理。',
        multiline: true
      },
      { name: 'original_label', label: '左邊那張圖的說明', default: '原圖' },
      { name: 'result_label', label: '右邊那張圖的說明', default: '放大色度差之後' },
      {
        name: 'result_hint',
        label: '結果下方的說明',
        default: '看到重複鋪滿整張的簽名，就是從這個站拿走的。壓過、縮過、裁過的圖會比較模糊，'
          + '調整放大倍率再看一次；整張都是雜訊看不出圖樣，那就不是這裡的圖。',
        multiline: true
      },
      // 這頁是給讀者主動查的工具，預設就放在左側選單
      { name: 'nav_position', label: '導覽位置', type: 'select', options: NAV_POSITIONS, default: 'sidebar' },
      { name: 'nav_order', label: '導覽排序', type: 'number', default: '0' }
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
