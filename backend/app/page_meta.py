"""內建頁面的文案覆寫。

附加頁面（分子圖鑑、基本粒子⋯）的標題、副標與零碎文案原本寫死在前端，
部署後改不了（issue #20）。這裡提供 `_page_meta/{key}` 覆寫層：
只存被改過的欄位，前端沒讀到的欄位退回內建預設值，
所以部署更新預設文案不會影響已編輯的內容。

欄位定義（有哪些欄位、顯示名稱、預設值）放在前端 utils/pageMeta.js，
後端只負責通用的字串儲存，新頁面加欄位不用動後端。
"""

# 允許的頁面 key。新增附加頁面時在這裡補一個 key 即可
META_KEYS = ("molecules", "molecule", "particles", "watermark", "story", "footer")

PAGE_META_NODE = "_page_meta"

# 單一欄位長度上限：文案欄位不該拿來塞整篇文章（那是頁面管理的事）
MAX_FIELD_LENGTH = 2000


def normalize_meta(data):
    """整理單一頁面的覆寫欄位；只保留非空字串。"""
    if not isinstance(data, dict):
        return {}
    result = {}
    for field, value in data.items():
        if not isinstance(field, str) or not isinstance(value, str):
            continue
        value = value.strip()
        if value:
            result[field[:64]] = value[:MAX_FIELD_LENGTH]
    return result


def normalize_all(data):
    if not isinstance(data, dict):
        return {}
    return {key: normalize_meta(data.get(key)) for key in META_KEYS if data.get(key)}
