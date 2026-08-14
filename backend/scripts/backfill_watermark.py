"""把浮水印補到「已經存在」的圖片上（issue #25）。

開啟浮水印之後，只有新上傳的圖會被套用；資料庫裡原本就有的圖不會自動變。
這支腳本掃過所有存圖片的節點，對還沒有浮水印的圖套一次再寫回去。

用法（在 backend/ 底下）：

    python scripts/backfill_watermark.py                 # 預覽，不寫入
    python scripts/backfill_watermark.py --apply         # 真的寫入
    python scripts/backfill_watermark.py --node _libraries --apply
    python scripts/backfill_watermark.py --list          # 只列出會掃哪些節點

寫入是「一張圖一個路徑」地寫，不是整包覆寫——中途失敗不會把整個節點弄壞，
也不會把別人同時間改的東西蓋掉。

節點是一個一個讀的。`_libraries` 一個節點就有好幾 MB（issue #30），
全部一起讀下來會直接吃掉記憶體。
"""

import argparse
import os
import sys
import types

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

# 同 try_ai.py：先塞一個空的 app 套件，避免 app/__init__.py 連鎖 import
_pkg = types.ModuleType("app")
_pkg.__path__ = [os.path.join(_ROOT, "app")]
sys.modules.setdefault("app", _pkg)

from app import watermark  # noqa: E402

# 會存圖片的節點。元素代表圖散在根節點底下（每個元素符號一個），
# 所以用 None 代表「根節點的元素們」，另外處理。
NODES = (
    None,               # 各元素的代表圖 {symbol}/img_data
    "_default",
    "_libraries",
    "_gallery",
    "_particles",
    "_molecules",
    "_element_groups",
    "_electron_styles",
    "_layers",
    "_pages",
    "_site_settings",
)


def collect(node, prefix=()):
    """走過一個節點，回傳所有 base64 圖片的 (路徑, 內容)。"""
    found = []
    if isinstance(node, str):
        if node.startswith("data:image/"):
            found.append((prefix, node))
    elif isinstance(node, dict):
        for key, value in node.items():
            found.extend(collect(value, prefix + (str(key),)))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.extend(collect(value, prefix + (str(index),)))
    return found


def process(root, settings, apply_changes):
    """處理單一節點，回傳 (掃到幾張, 改了幾張)。"""
    from app.firebase import fdb, show_fdb

    if root is None:
        data = show_fdb() or {}
        # 只留元素節點：periodic_table 是資料、底線開頭的是設定用節點
        data = {k: v for k, v in data.items()
                if k != "periodic_table" and not k.startswith("_") and isinstance(v, dict)}
        base = ()
        label = "（元素代表圖）"
    else:
        data = show_fdb(root)
        base = (root,)
        label = root

    images = collect(data, base)
    if not images:
        print(f"  {label}：沒有圖片")
        return 0, 0

    changed = 0
    for path, img_data in images:
        marked = watermark.mark_data_url(img_data, settings)
        if marked == img_data:
            continue
        changed += 1
        location = "/".join(path)
        size = (len(marked) - len(img_data)) // 1024
        print(f"    {'寫入' if apply_changes else '待補'} {location}（{size:+d}KB）")
        if apply_changes:
            reference = fdb
            for part in path:
                reference = reference.child(part)
            reference.set(marked)

    print(f"  {label}：{len(images)} 張，其中 {changed} 張要補")
    return len(images), changed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="真的寫入；不加就只是預覽")
    parser.add_argument("--node", help="只處理這一個節點（例如 _libraries）")
    parser.add_argument("--list", action="store_true", help="列出會掃哪些節點就結束")
    args = parser.parse_args()

    if args.list:
        for node in NODES:
            print(node or "（根節點下的元素）")
        return 0

    settings = watermark.load_settings()
    if not settings["enabled"]:
        print("浮水印目前是關閉的。先到後台「浮水印」把它打開並設定好簽名，再跑這支腳本。")
        return 1

    print(f"設定：{settings['mode']} 模式、強度 {settings['strength']}、圖樣單元 {settings['tile']}px")
    print("預覽模式，不會寫入（要寫入請加 --apply）\n" if not args.apply else "寫入模式\n")

    targets = NODES if not args.node else tuple(
        n for n in NODES if (n or "") == args.node)
    if not targets:
        print(f"不認得的節點：{args.node}（--list 可以看清單）")
        return 1

    total = fixed = 0
    for node in targets:
        seen, changed = process(node, settings, args.apply)
        total += seen
        fixed += changed

    print(f"\n合計 {total} 張圖，{fixed} 張{'已補上' if args.apply else '需要補'}浮水印")
    if fixed and not args.apply:
        print("確認沒問題後再加 --apply 跑一次")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
