"""在本機直接試浮水印，不需要 Firebase 憑證。

用法：
    python scripts/try_watermark.py                     # 用合成測試圖
    python scripts/try_watermark.py 某張圖.jpg           # 用自己的圖
    python scripts/try_watermark.py 圖.jpg --text EG --strength 2

會把對照圖寫到 /tmp：乾淨的圖、套完的圖，以及兩張還原圖（原尺寸與
縮 50% 再壓 quality 0.6 之後）——簽名讀不讀得出來就看還原圖。
順便檢查「重複套用」擋得住，以及亮度真的沒動。
"""

import argparse
import base64
import io
import os
import sys
import types

from PIL import Image, ImageDraw

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

# 同 try_ai.py：塞一個空的 app 套件，避免 app/__init__.py 一路 import 到
# firebase。watermark 的核心本來就不碰資料庫，設定的讀寫才會 import。
_pkg = types.ModuleType("app")
_pkg.__path__ = [os.path.join(_ROOT, "app")]
sys.modules.setdefault("app", _pkg)

from app import watermark  # noqa: E402


def sample_image(size=(640, 480)):
    """合成一張有漸層、有平坦色塊、也有飽和色塊的測試圖。"""
    width, height = size
    image = Image.new("RGB", size)
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            pixels[x, y] = (
                int(60 + 160 * x / width),
                int(40 + 120 * y / height),
                int(200 - 120 * x / width),
            )
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, width, height // 5], fill=(210, 210, 205))
    draw.ellipse([width * 0.55, height * 0.45, width * 0.9, height * 0.9], fill=(60, 140, 90))
    return image


def to_data_url(image, quality=85):
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="JPEG", quality=quality)
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")


def report(label, image, settings):
    """印出「這張是不是已經套過了」。這個判定只用來擋重複套用，不是給人
    判斷盜圖的——後者看還原圖，見下面存出來的對照圖。"""
    marked = watermark.already_marked(image, settings)
    print(f"  {label:<24} {'已套過' if marked else '沒套過'}")
    return marked


def save(data_url, path):
    match = watermark.DATA_URL_RE.match(data_url)
    with open(path, "wb") as f:
        f.write(base64.b64decode(match.group(2)))
    print(f"  → {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image", nargs="?", help="要試的圖片檔；不給就用合成測試圖")
    parser.add_argument("--text", default="EG", help="文字模式的簽名")
    parser.add_argument("--pattern", help="圖片模式：拿來當圖樣的檔案")
    parser.add_argument("--strength", type=int, default=watermark.DEFAULT_STRENGTH)
    parser.add_argument("--out", default="/tmp", help="對照圖輸出目錄")
    args = parser.parse_args()

    settings = watermark.normalize({
        "enabled": True,
        "mode": "image" if args.pattern else "text",
        "text": args.text,
        "pattern": to_data_url(Image.open(args.pattern)) if args.pattern else "",
        "strength": args.strength,
    })

    original = Image.open(args.image).convert("RGB") if args.image else sample_image()
    clean_url = to_data_url(original)

    print(f"\n設定：{settings['mode']} 模式，強度 {settings['strength']}，"
          f"圖樣單元 {settings['tile']}px，圖片 {original.size[0]}×{original.size[1]}")

    marked_url = watermark.mark_data_url(clean_url, settings)
    if marked_url == clean_url:
        print("\n⚠️ 沒有套上浮水印（圖太小或圖樣有問題）")
        return 1

    marked = watermark.decode_data_url(marked_url)
    shrunk = marked.resize((marked.width // 2, marked.height // 2), Image.LANCZOS)
    shrunk = watermark.decode_data_url(to_data_url(shrunk, quality=60))

    print("\n重複套用檢查（後台每次儲存都會重送整批圖，靠這個擋掉疊加）：")
    report("乾淨的圖（該是沒套過）", watermark.decode_data_url(clean_url), settings)
    report("套完的圖（該是已套過）", marked, settings)

    print("\n亮度檢查：")
    import numpy as np
    before = np.asarray(Image.open(io.BytesIO(base64.b64decode(
        watermark.DATA_URL_RE.match(clean_url).group(2)))).convert("YCbCr"), dtype=float)
    after = np.asarray(marked.convert("YCbCr"), dtype=float)
    print(f"  Y 通道最大差 {np.abs(before[:, :, 0] - after[:, :, 0]).max():.1f}、"
          f"平均差 {np.abs(before[:, :, 0] - after[:, :, 0]).mean():.3f}")

    print("\n對照圖：")
    save(clean_url, os.path.join(args.out, "wm-clean.jpg"))
    save(marked_url, os.path.join(args.out, "wm-marked.jpg"))
    # 還原圖：簽名讀不讀得出來看這兩張。前台的檢視頁在瀏覽器裡做同一件事
    save(watermark.reveal_data_url(marked), os.path.join(args.out, "wm-recovered.png"))
    save(watermark.reveal_data_url(shrunk), os.path.join(args.out, "wm-recovered-shrunk.png"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
