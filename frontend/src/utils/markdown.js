// 小型 Markdown 渲染器。
//
// 刻意不引入 marked / markdown-it：那些函式庫會產生任意 HTML，需要再搭一層
// DOMPurify 才安全。這裡只支援固定的語法子集，所有使用者輸入一律先 escape，
// 輸出的標籤全部由本檔產生，沒有讓原始 HTML 通過的路徑。
//
// 除了一般 Markdown，另外支援「區塊」語法，讓後台不必寫 HTML 也能排出
// 卡片格線這類版面：
//
//   :::cards
//   ### 標題 | 附註
//   說明文字
//
//   ### 另一張卡
//   說明文字
//   :::
//
//   :::links     ← 插入目前設定的社群連結
//   :::
//
//   :::note
//   提示區塊
//   :::

export const BLOCK_TYPES = ['cards', 'links', 'note']

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

// 只允許 http/https/mailto，擋掉 javascript: 這類 URL
function safeUrl(url) {
  const trimmed = String(url).trim()
  if (/^(https?:|mailto:)/i.test(trimmed)) return escapeHtml(trimmed)
  if (trimmed.startsWith('/') || trimmed.startsWith('#')) return escapeHtml(trimmed)
  return '#'
}

// 行內語法：粗體、斜體、行內程式碼、連結
function inline(text) {
  let out = escapeHtml(text)
  out = out.replace(/`([^`]+)`/g, '<code>$1</code>')
  out = out.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  out = out.replace(/(^|[^*])\*([^*]+)\*/g, '$1<em>$2</em>')
  out = out.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, url) => {
    const href = safeUrl(url)
    const external = /^https?:/i.test(href)
    const attrs = external ? ' target="_blank" rel="noopener noreferrer"' : ''
    return `<a href="${href}"${attrs}>${label}</a>`
  })
  return out
}

// :::cards 內部：每個 ### 開一張卡，標題可用 | 分隔附註
function renderCards(body) {
  const cards = []
  let current = null

  for (const line of body.split('\n')) {
    const heading = line.match(/^###\s+(.+)$/)
    if (heading) {
      if (current) cards.push(current)
      const [title, ...rest] = heading[1].split('|')
      current = { title: title.trim(), note: rest.join('|').trim(), lines: [] }
    } else if (current) {
      current.lines.push(line)
    }
  }
  if (current) cards.push(current)
  if (!cards.length) return ''

  const items = cards.map(c => {
    const note = c.note ? `<span class="md-card-note">${inline(c.note)}</span>` : ''
    const body = c.lines.join('\n').trim()
    return `<div class="md-card">
      <div class="md-card-head"><span class="md-card-title">${inline(c.title)}</span>${note}</div>
      ${body ? `<p class="md-card-body">${inline(body).replace(/\n/g, '<br>')}</p>` : ''}
    </div>`
  }).join('')

  return `<div class="md-cards">${items}</div>`
}

/**
 * 把 Markdown 轉成 HTML。
 *
 * @param {string} source
 * @returns {{html: string, blocks: string[]}} blocks 是內容用到的動態區塊
 *          （例如 links），由呼叫端決定怎麼渲染
 */
export function renderMarkdown(source) {
  if (!source) return { html: '', blocks: [] }

  const lines = String(source).replace(/\r\n/g, '\n').split('\n')
  const out = []
  const blocks = []
  let listType = null
  let paragraph = []

  const flushParagraph = () => {
    if (paragraph.length) {
      out.push(`<p>${inline(paragraph.join('\n')).replace(/\n/g, '<br>')}</p>`)
      paragraph = []
    }
  }
  const closeList = () => {
    if (listType) {
      out.push(listType === 'ul' ? '</ul>' : '</ol>')
      listType = null
    }
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]

    // 區塊：:::type ... :::
    const blockStart = line.match(/^:::(\w+)\s*$/)
    if (blockStart) {
      flushParagraph()
      closeList()
      const type = blockStart[1]
      const body = []
      i++
      while (i < lines.length && !/^:::\s*$/.test(lines[i])) {
        body.push(lines[i])
        i++
      }
      if (type === 'cards') {
        out.push(renderCards(body.join('\n')))
      } else if (type === 'note') {
        out.push(`<div class="md-note">${inline(body.join('\n')).replace(/\n/g, '<br>')}</div>`)
      } else if (BLOCK_TYPES.includes(type)) {
        // 需要即時資料的區塊交給呼叫端，這裡只留一個插槽
        blocks.push(type)
        out.push(`<div data-block="${escapeHtml(type)}"></div>`)
      }
      continue
    }

    if (!line.trim()) {
      flushParagraph()
      closeList()
      continue
    }

    const heading = line.match(/^(#{1,4})\s+(.+)$/)
    if (heading) {
      flushParagraph()
      closeList()
      const level = heading[1].length + 1  // # → h2，頁面標題已經是 h1
      out.push(`<h${level}>${inline(heading[2])}</h${level}>`)
      continue
    }

    if (/^---+\s*$/.test(line)) {
      flushParagraph()
      closeList()
      out.push('<hr>')
      continue
    }

    const ul = line.match(/^[-*]\s+(.+)$/)
    if (ul) {
      flushParagraph()
      if (listType !== 'ul') { closeList(); out.push('<ul>'); listType = 'ul' }
      out.push(`<li>${inline(ul[1])}</li>`)
      continue
    }

    const ol = line.match(/^\d+\.\s+(.+)$/)
    if (ol) {
      flushParagraph()
      if (listType !== 'ol') { closeList(); out.push('<ol>'); listType = 'ol' }
      out.push(`<li>${inline(ol[1])}</li>`)
      continue
    }

    paragraph.push(line)
  }

  flushParagraph()
  closeList()

  return { html: out.join('\n'), blocks }
}
