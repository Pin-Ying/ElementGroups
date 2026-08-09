"""元素的「其他樣貌」圖庫。

比照昆蟲、鳥類圖鑑：代表圖只有一張（存在元素本體的 img_data），
其他型態、狀態的照片放在獨立的 `_gallery/{Symbol}` 節點。

刻意跟元素本體分開存：首頁與列表頁只需要代表圖，如果把整組圖片
塞進元素節點，那些頁面的查詢會連帶把所有圖片一起拉下來。
"""

GALLERY_NODE = "_gallery"


def normalize_gallery(data):
    """把原始資料轉成 [{img_data, caption}]。

    Realtime DB 對陣列的處理不一定會保持 list 型別（有空洞時會變成
    以索引為 key 的 dict），這裡統一處理。
    """
    if not data:
        return []

    if isinstance(data, dict):
        # 以數字字串為 key 的 dict，依 key 的數值排序還原順序
        try:
            items = [data[k] for k in sorted(data, key=lambda x: int(x))]
        except (ValueError, TypeError):
            items = list(data.values())
    elif isinstance(data, list):
        items = data
    else:
        return []

    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        img_data = (item.get("img_data") or "").strip()
        if not img_data:
            continue
        result.append({
            "img_data": img_data,
            "caption": (item.get("caption") or "").strip(),
        })
    return result
