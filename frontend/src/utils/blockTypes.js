// 頁面區塊的類型定義（issue #20）。
//
// 這份是唯一的真相來源：後台的編輯欄位、前台的渲染，都從這裡長出來。
// 後端只做通用儲存（見 backend/app/pages.py 的 normalize_blocks），不認得
// 任何具體類型——每一種區塊的「欄位長什麼樣」與「畫出來長什麼樣」本來就是
// 同一份知識，拆到前後端兩邊只會變成又一個要同步的地方。
//
// 新增一種區塊：在下面補一筆定義，再到 PageBlocks.vue 補對應的渲染。
//
// 命名為 PAGE_BLOCKS 而非 BLOCK_TYPES：utils/markdown.js 已經有一個
// BLOCK_TYPES（指 ::: 區塊語法），同名會讓兩邊同時 import 時混淆。
//
// 類型是照這個站實際會用到的挑的，不是把參考專案那 16 種照搬——聯絡表單、
// 地圖嵌入、收費表格是服務業網站的需求，這裡用不到。

// 欄位型別：
//   text      單行
//   textarea  多行純文字
//   markdown  多行，會走 Markdown 渲染
//   select    下拉，需要 options
//   image     圖片（base64），可從圖庫挑或直接上傳
//   list      重複的子項目，需要 itemFields
export const PAGE_BLOCKS = [
  {
    key: 'heading',
    label: '標題',
    desc: '獨立標題，可選 H2／H3 層級，用來分隔章節',
    icon: 'H',
    fields: [
      { name: 'text', label: '標題文字', type: 'text', default: '' },
      {
        name: 'level',
        label: '層級',
        type: 'select',
        default: 'h2',
        options: [
          { value: 'h2', label: 'H2 大標題' },
          { value: 'h3', label: 'H3 小標題' }
        ]
      }
    ]
  },
  {
    key: 'text',
    label: '內文段落',
    desc: '一段文字，支援 Markdown 的粗體、連結、清單',
    icon: '¶',
    fields: [
      { name: 'body', label: '內文', type: 'markdown', default: '' }
    ]
  },
  {
    key: 'image',
    label: '圖片',
    desc: '單張圖片，可加說明文字',
    icon: '▣',
    fields: [
      { name: 'image', label: '圖片', type: 'image', default: '' },
      { name: 'caption', label: '說明文字', type: 'text', default: '' }
    ]
  },
  {
    key: 'gallery',
    label: '圖片集',
    desc: '多張圖片排成格線，適合放不同樣貌或作品集',
    icon: '▦',
    fields: [
      {
        name: 'images',
        label: '圖片',
        type: 'list',
        default: [],
        itemFields: [
          { name: 'image', label: '圖片', type: 'image', default: '' },
          { name: 'caption', label: '說明', type: 'text', default: '' }
        ]
      }
    ]
  },
  {
    key: 'cards',
    label: '卡片格線',
    desc: '每張卡片有標題、附註與說明，適合並列多個名詞解釋',
    icon: '⊞',
    fields: [
      {
        name: 'items',
        label: '卡片',
        type: 'list',
        default: [],
        itemFields: [
          { name: 'title', label: '標題', type: 'text', default: '' },
          { name: 'note', label: '附註（顯示在標題旁）', type: 'text', default: '' },
          { name: 'body', label: '說明', type: 'textarea', default: '' }
        ]
      }
    ]
  },
  {
    key: 'note',
    label: '提示區塊',
    desc: '框起來的一段提醒，用來強調注意事項',
    icon: '!',
    fields: [
      { name: 'body', label: '內容', type: 'markdown', default: '' }
    ]
  },
  {
    key: 'links',
    label: '社群連結',
    desc: '自動插入目前在「社群連結」設定的帳號，不必逐一維護',
    icon: '⚯',
    fields: []
  },
  {
    key: 'divider',
    label: '分隔線',
    desc: '一條橫線，用來斷開段落',
    icon: '—',
    fields: []
  },
  {
    key: 'markdown',
    label: '自訂 Markdown',
    desc: '直接寫 Markdown。舊頁面轉過來時會放進這一塊，也可以當作其他區塊做不到時的退路',
    icon: '</>',
    fields: [
      { name: 'body', label: 'Markdown', type: 'markdown', default: '' }
    ]
  }
]

export function blockType(key) {
  return PAGE_BLOCKS.find(b => b.key === key) || null
}

/** 依定義生出一個空白區塊，欄位都帶預設值。 */
export function emptyBlock(key) {
  const def = blockType(key)
  if (!def) return null

  const data = {}
  for (const field of def.fields) {
    // 陣列型別要複製，否則所有區塊會共用同一個陣列實例
    data[field.name] = Array.isArray(field.default) ? [] : field.default
  }
  return { type: key, data }
}

/** list 型別新增一個子項目時的空白值。 */
export function emptyItem(field) {
  const item = {}
  for (const sub of field.itemFields || []) item[sub.name] = sub.default
  return item
}

/**
 * 沒有區塊、只有舊 Markdown 內容的頁面，轉成單一個「自訂 Markdown」區塊。
 * 不在搬遷時改寫資料，而是讀取時即時轉——舊頁面不動，站長真的去編輯並
 * 存檔之後才會寫成區塊。
 */
export function blocksFrom(page) {
  if (page?.blocks?.length) return page.blocks
  const body = (page?.content || '').trim()
  return body ? [{ type: 'markdown', data: { body } }] : []
}
