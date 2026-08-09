// Admin 可選的社群平台。key 會存進 DB，label/color 只用於顯示。
// 想支援新平台時在這裡加一筆即可，前後端都不用改。
export const PLATFORMS = [
  { key: 'instagram', label: 'Instagram', color: '#E1306C' },
  { key: 'threads', label: 'Threads', color: '#f0f0f0' },
  { key: 'facebook', label: 'Facebook', color: '#1877F2' },
  { key: 'x', label: 'X', color: '#f0f0f0' },
  { key: 'youtube', label: 'YouTube', color: '#FF0000' },
  { key: 'tiktok', label: 'TikTok', color: '#25F4EE' },
  { key: 'line', label: 'LINE', color: '#06C755' },
  { key: 'discord', label: 'Discord', color: '#5865F2' },
  { key: 'github', label: 'GitHub', color: '#c9d1d9' },
  { key: 'email', label: 'Email', color: '#9d8cff' },
  { key: 'website', label: '網站', color: '#64b8e8' }
]

const PLATFORM_MAP = Object.fromEntries(PLATFORMS.map(p => [p.key, p]))

export function platformInfo(key) {
  return PLATFORM_MAP[key] || { key, label: key, color: '#64b8e8' }
}
