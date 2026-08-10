// 主族形象用的族別定義。key 與後端 GROUP_KEYS、periodicTableGroups 的
// 分組標籤一致，這裡補上中文俗名讓後台與前台顯示比較好讀。
export const GROUP_INFO = [
  { key: '1A', label: '1A', name: '鹼金屬' },
  { key: '2A', label: '2A', name: '鹼土金屬' },
  { key: '3A', label: '3A', name: '硼族' },
  { key: '4A', label: '4A', name: '碳族' },
  { key: '5A', label: '5A', name: '氮族' },
  { key: '6A', label: '6A', name: '氧族' },
  { key: '7A', label: '7A', name: '鹵素' },
  { key: '8A', label: '8A', name: '惰性氣體' },
  { key: '1B', label: '1B', name: '銅族' },
  { key: '2B', label: '2B', name: '鋅族' },
  { key: '3B', label: '3B', name: '鈧族' },
  { key: '4B', label: '4B', name: '鈦族' },
  { key: '5B', label: '5B', name: '釩族' },
  { key: '6B', label: '6B', name: '鉻族' },
  { key: '7B', label: '7B', name: '錳族' },
  { key: '8B', label: '8B', name: '鐵族' },
  { key: '9B', label: '9B', name: '鈷族' },
  { key: '10B', label: '10B', name: '鎳族' },
  { key: 'Lanthanides', label: '鑭系', name: '' },
  { key: 'Actinides', label: '錒系', name: '' }
]

export function groupInfo(key) {
  return GROUP_INFO.find(g => g.key === key) || { key, label: key, name: '' }
}
