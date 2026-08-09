// Admin 可選的社群平台。key 會存進 DB，label/color 只用於顯示。
// 想支援新平台時在這裡加一筆即可，前後端都不用改。
export const PLATFORMS = [
  { key: 'instagram', label: 'Instagram', color: '#E1306C', placeholder: 'https://instagram.com/帳號' },
  { key: 'threads', label: 'Threads', color: '#f0f0f0', placeholder: 'https://threads.com/@帳號' },
  { key: 'facebook', label: 'Facebook', color: '#1877F2', placeholder: 'https://facebook.com/頁面' },
  { key: 'x', label: 'X', color: '#f0f0f0', placeholder: 'https://x.com/帳號' },
  { key: 'youtube', label: 'YouTube', color: '#FF0000', placeholder: 'https://youtube.com/@頻道' },
  { key: 'tiktok', label: 'TikTok', color: '#25F4EE', placeholder: 'https://tiktok.com/@帳號' },
  { key: 'line', label: 'LINE', color: '#06C755', placeholder: 'https://line.me/ti/p/~帳號' },
  { key: 'discord', label: 'Discord', color: '#5865F2', placeholder: 'https://discord.gg/邀請碼' },
  { key: 'github', label: 'GitHub', color: '#c9d1d9', placeholder: 'https://github.com/帳號' },
  { key: 'email', label: 'Email', color: '#9d8cff', placeholder: 'mailto:someone@example.com' },
  { key: 'website', label: '網站', color: '#64b8e8', placeholder: 'https://example.com' }
]

const PLATFORM_MAP = Object.fromEntries(PLATFORMS.map(p => [p.key, p]))

export function platformInfo(key) {
  return PLATFORM_MAP[key] || { key, label: key, color: '#64b8e8', placeholder: 'https://' }
}
