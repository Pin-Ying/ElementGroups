// 擋掉前台圖片的右鍵與拖曳（issue #25）。
//
// 說清楚它擋得住什麼、擋不住什麼，之後才不會誤以為圖片是安全的：
//
// 擋得住：右鍵另存、把圖直接拖到桌面、手機長按跳出的儲存選單。也就是
//        「順手存一張」那一類——實際上大部分的取用就是這一類。
// 擋不住：F12 的 Network／Elements、直接打 /api/elements/{Symbol}/img 這個
//        公開網址、截圖、關掉 JavaScript。圖片要顯示在螢幕上，位元組就已經
//        在對方的電腦裡了，這是原理上的事，任何前端手段都改不了。
//
// 所以這只是第一道門檻，真正的防線是隱形浮水印——拿走也看得出是誰的。
//
// 後台與浮水印檢視頁不擋：站長自己要能存圖，而檢視頁上的圖是訪客自己上傳的，
// 擋他自己的圖沒有道理。

const ALLOW_PREFIXES = ['/admin', '/watermark']

function allowed(path) {
  return ALLOW_PREFIXES.some(prefix => path.startsWith(prefix))
}

/**
 * @param {import('vue-router').Router} router 用來判斷目前在哪一頁
 */
export function installImageGuard(router) {
  const shouldBlock = event => {
    const target = event.target
    if (!(target instanceof HTMLImageElement)) return false
    return !allowed(router.currentRoute.value.path)
  }

  // 捕捉階段就攔下來，元件自己的 handler 不會有機會把選單叫出來
  document.addEventListener('contextmenu', event => {
    if (shouldBlock(event)) event.preventDefault()
  }, true)

  document.addEventListener('dragstart', event => {
    if (shouldBlock(event)) event.preventDefault()
  }, true)

  // 手機長按跳出的儲存選單不是 contextmenu 事件，只能靠 CSS 的
  // -webkit-touch-callout 關掉，所以要依頁面掛上／拿掉這個 class
  const sync = path => {
    document.documentElement.classList.toggle('guard-images', !allowed(path))
  }
  sync(router.currentRoute.value.path)
  router.afterEach(to => sync(to.path))
}
