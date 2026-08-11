// 內建頁面的預設內容（Markdown）。
//
// `/guide` 與 `/links` 原本是寫死的 Vue 元件，改為：資料庫有同名頁面就用
// 資料庫的內容，沒有則回退到這裡的預設值。這樣既有網址不會壞。
//
// 標題一律用英文當佔位字，中文由站長在後台自己填。
//
// 排版用的是 utils/markdown.js 的區塊語法（:::cards / :::note / :::links），
// 所以後台編輯時可以照樣排出卡片格線，不必寫 HTML。

export const BUILTIN_PAGES = {
  // 內容留空：預設的中文說明書由站長自己在後台撰寫，
  // 這裡不預先塞一份，免得和站長寫的版本混淆
  guide: {
    title: 'Element Guide',
    content: ''
  },

  links: {
    title: 'Connect',
    content: `追蹤創作者的社群帳號。

:::links
:::`
  }
}

export function builtinPage(slug) {
  return BUILTIN_PAGES[slug] || null
}
