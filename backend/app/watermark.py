"""隱形浮水印（issue #25）。

把簽名藏進色度（chroma），亮度一個位元都不動：轉到 YCbCr 之後只在 Cb 加、
Cr 減同一個圖樣，Y 完全不碰。正常觀看看不出來，把色度差放大就會浮出簽名。

兩個設計上的選擇，之後回來看才知道當初在擔心什麼：

1. **圖樣刻意做得很低頻**。先畫在 `tile // BLOCK` 的小格子上再放大 BLOCK 倍，
   最細的紋路也有好幾像素寬。JPEG 的 4:2:0 色度次取樣會把 2×2 的色度平均掉、
   DCT 量化又特別粗暴地對付色度高頻——細線條的圖樣壓一次就沒了。

2. **不做「是不是盜圖」的自動判定**，只把殘差放大成還原圖（`reveal`），由人自己
   看有沒有簽名。判定要拿圖樣去比對所有位移與縮放比例，而任意比例縮放過的圖對
   不上模板：實測縮到 0.75 驗得到，0.8 或 0.7 就掉到門檻的一半以下——離散地掃
   幾個比例會漏掉大部分真的盜圖，那種會說謊的是非題比沒有結論更糟。
   程式裡唯一保留的判定是 `already_marked`，用途只有擋掉重複套用。

模組本身不碰 Firebase，設定的讀寫才會 import——這樣本機沒有憑證也能直接試
`python scripts/try_watermark.py`。
"""

import base64
import io
import re

import numpy as np
from PIL import Image, ImageDraw, ImageFont

WATERMARK_NODE = "_watermark"

# 小於這個邊長的圖不套。電子、圖層那種疊上去的小素材套了也讀不出來，
# 卻要冒著在小圖上被看見的風險。
MIN_EDGE = 64

# 圖樣單元的邊長（px）與「先畫小再放大」的倍率。
# BLOCK 實測過 4／8／16：4 太細，JPEG 的色度量化壓一次就掉了七成；
# 16 讓一個 tile 只剩十幾格，圖樣本身糊掉。8 兩邊都過得去。
DEFAULT_TILE = 192
BLOCK = 8

# 強度：色度的位移量，換算成 RGB 最多差 5/255。3 是實測的甜蜜點——
# 2 在「縮一半再壓 q0.6」之後就驗不到了，4 以上在大片平塗的淺色底上開始看得出來
DEFAULT_STRENGTH = 3
MAX_STRENGTH = 6

# `already_marked` 的分數要多大才算「這張已經套過了」。實測剛套完的圖落在
# 1.0〜1.9，乾淨的圖在 0.1 以內，所以門檻取強度的 1/4，兩邊都留得下餘裕
DETECT_RATIO = 0.25
DETECT_FLOOR = 0.35

# 還原圖的參數。窗要比圖樣的紋路大、比畫面內容小，取預設 tile 的四分之一；
# 放大倍率是肉眼看得出圖樣的下限附近。前端 utils/watermarkReveal.js 用同一組值，
# 兩邊的還原圖才會長得一樣
REVEAL_WINDOW = DEFAULT_TILE // 4
REVEAL_GAIN = 24

# 中文字型不是每個環境都有；python:3.11-slim 裡一個都沒有。
# 找不到就在存設定時直接報錯，叫使用者改用圖片模式，不要默默畫出一堆豆腐。
CJK_FONT_PATHS = (
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
    "/System/Library/Fonts/PingFang.ttc",
)

DATA_URL_RE = re.compile(r"^data:image/([a-zA-Z0-9.+-]+);base64,(.+)$", re.S)


# ── 設定 ──────────────────────────────────────────────────────────────

def defaults():
    return {
        "enabled": False,
        "mode": "text",
        "text": "",
        "pattern": "",
        "strength": DEFAULT_STRENGTH,
        "tile": DEFAULT_TILE,
    }


def normalize(raw):
    """把 RTDB 或前端送來的設定收成固定形狀，缺的欄位補預設值。"""
    data = raw if isinstance(raw, dict) else {}
    result = defaults()
    result["enabled"] = bool(data.get("enabled"))
    result["mode"] = "image" if (data.get("mode") or "").strip() == "image" else "text"
    result["text"] = (data.get("text") or "").strip()[:16]
    pattern = (data.get("pattern") or "").strip()
    result["pattern"] = pattern if DATA_URL_RE.match(pattern) else ""

    try:
        strength = int(data.get("strength") or DEFAULT_STRENGTH)
    except (TypeError, ValueError):
        strength = DEFAULT_STRENGTH
    result["strength"] = max(1, min(MAX_STRENGTH, strength))

    try:
        tile = int(data.get("tile") or DEFAULT_TILE)
    except (TypeError, ValueError):
        tile = DEFAULT_TILE
    result["tile"] = max(64, min(512, tile))
    return result


def load_settings():
    from app.firebase import show_fdb
    return normalize(show_fdb(WATERMARK_NODE))


def save_settings(payload):
    """存設定。存之前先把圖樣做出來，做不出來就直接拒絕——
    不然要等到下次上傳圖片才發現浮水印其實是空的。"""
    from app.firebase import fdb

    record = normalize(payload)
    if record["enabled"]:
        tile_mask(record)  # 會在圖樣不成立時丟 ValueError
    fdb.child(WATERMARK_NODE).set(record)
    return record


# ── 圖樣 ──────────────────────────────────────────────────────────────

def _text_font(text, box):
    """挑一個塞得進 box 的字型。含非英數字元時需要 CJK 字型，沒有就報錯。"""
    if any(ord(ch) > 0x2E80 for ch in text):
        import os
        path = next((p for p in CJK_FONT_PATHS if os.path.exists(p)), None)
        if not path:
            raise ValueError("這個環境沒有中文字型，文字浮水印只能用英數字；中文簽名請改用「上傳圖片」模式")
        loader = lambda size: ImageFont.truetype(path, size)
    else:
        loader = lambda size: ImageFont.load_default(size=size)

    for size in range(box, 5, -1):
        font = loader(size)
        left, top, right, bottom = font.getbbox(text)
        if right - left <= box and bottom - top <= box:
            return font
    return loader(6)


def tile_mask(settings):
    """做出 tile×tile、零均值、值域 [-1, 1] 的圖樣。

    先畫在 tile // BLOCK 的小格子上再用最近鄰放大，紋路才夠粗、壓得住 JPEG。
    """
    tile = settings["tile"]
    small = max(8, tile // BLOCK)
    canvas = Image.new("L", (small, small), 0)

    if settings["mode"] == "image":
        pattern = decode_data_url(settings["pattern"])
        if pattern is None:
            raise ValueError("請先上傳浮水印圖樣")
        mark = pattern.convert("L").resize((small, small), Image.LANCZOS)
        arr = np.asarray(mark, dtype=np.float32)
        # 有 alpha 的去背 PNG 用透明度當形狀，否則用亮度二值化
        if "A" in pattern.getbands():
            alpha = np.asarray(pattern.getchannel("A").resize((small, small), Image.LANCZOS), dtype=np.float32)
            arr = alpha
        binary = (arr > (arr.min() + arr.max()) / 2).astype(np.float32)
        canvas = Image.fromarray((binary * 255).astype(np.uint8), "L")
    else:
        text = settings["text"]
        if not text:
            raise ValueError("請先填浮水印文字")
        draw = ImageDraw.Draw(canvas)
        font = _text_font(text, int(small * 0.9))
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        draw.text(((small - (right - left)) / 2 - left, (small - (bottom - top)) / 2 - top),
                  text, fill=255, font=font)

    mask = np.asarray(canvas, dtype=np.float32) / 255.0
    mask = np.kron(mask, np.ones((BLOCK, BLOCK), dtype=np.float32))[:tile, :tile]
    if mask.shape != (tile, tile):  # tile 不是 BLOCK 的整數倍時補齊
        padded = np.zeros((tile, tile), dtype=np.float32)
        padded[:mask.shape[0], :mask.shape[1]] = mask
        mask = padded

    mask -= mask.mean()  # 零均值：整張圖的平均色度不變，才不會出現色偏
    peak = np.abs(mask).max()
    if peak < 1e-6:
        raise ValueError("圖樣是整片空白或整片實心，做不出浮水印")
    return mask / peak


def _tiled(mask, height, width):
    reps = (height // mask.shape[0] + 1, width // mask.shape[1] + 1)
    return np.tile(mask, reps)[:height, :width]


# ── 套用與偵測 ────────────────────────────────────────────────────────

def decode_data_url(img_data):
    match = DATA_URL_RE.match((img_data or "").strip())
    if not match:
        return None
    try:
        return Image.open(io.BytesIO(base64.b64decode(match.group(2))))
    except Exception:
        return None


def encode_data_url(image, keep_alpha=False):
    buffer = io.BytesIO()
    if keep_alpha:
        image.save(buffer, format="PNG", optimize=True)
        mime = "image/png"
    else:
        # quality 90：色度量化再粗一點就會開始吃掉圖樣
        image.save(buffer, format="JPEG", quality=90)
        mime = "image/jpeg"
    return "data:" + mime + ";base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")


# ΔCb = +p、ΔCr = −p 換算成 RGB 的位移量。
# 直接在 RGB 上加這三個數，等價於「只動色度、不動亮度」：
# ΔY = 0.299·(−1.402) + 0.587·(+0.370) + 0.114·(+1.772) ≈ 0
#
# 為什麼不乾脆轉成 YCbCr 改完再轉回來——那樣一來一回的取整會讓「每一個」
# 像素的 Y 都差 1，量出來就不是「亮度完全不動」了。
RGB_DELTA = np.array([-1.402, 0.714136 - 0.344136, 1.772], dtype=np.float32)


def embed(image, settings, mask=None):
    """在單張 PIL 圖片上套浮水印，回傳新的 PIL 圖片（原圖不動）。"""
    mask = tile_mask(settings) if mask is None else mask
    alpha = image.getchannel("A") if "A" in image.getbands() else None
    rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    pattern = _tiled(mask, rgb.shape[0], rgb.shape[1]) * settings["strength"]

    if alpha is not None:
        # 透明的地方 RGB 是垃圾值（多半是 0），在那裡加位移只會被 clip 掉，
        # 白白損失訊號；偵測時也會把透明區域排除掉
        pattern = pattern * (np.asarray(alpha, dtype=np.float32) > 0)

    rgb += pattern[:, :, None] * RGB_DELTA[None, None, :]
    result = Image.fromarray(np.clip(rgb + 0.5, 0, 255).astype(np.uint8), "RGB")
    if alpha is not None:
        result.putalpha(alpha)
    return result


def _chroma(image):
    """(Cb − Cr) / 2。嵌入時 Cb 加、Cr 減，所以這個相減會把訊號還原成一整份。"""
    ycc = np.asarray(image.convert("YCbCr"), dtype=np.float32)
    return (ycc[:, :, 1] - ycc[:, :, 2]) / 2


def _box1d(signal, radius, axis):
    """一維移動平均，用前綴和算，O(n) 且不需要 scipy。"""
    width = 2 * radius + 1
    padding = [(0, 0), (0, 0)]
    padding[axis] = (radius, radius)
    padded = np.pad(signal, padding, mode="edge")
    head = list(padded.shape)
    head[axis] = 1
    cumulative = np.concatenate(
        [np.zeros(head, dtype=np.float32), np.cumsum(padded, axis=axis, dtype=np.float32)], axis=axis)
    length = signal.shape[axis]
    upper = np.take(cumulative, np.arange(width, width + length), axis=axis)
    lower = np.take(cumulative, np.arange(0, length), axis=axis)
    return (upper - lower) / width


def _highpass(signal, window):
    """減掉低頻，剩下的就是圖樣所在的頻段。

    `window` 要比圖樣的紋路大、比畫面內容小：實測 tile/4 最乾淨。

    低頻一定要用移動平均這種「位置無關」的做法算。原本圖省事用「縮小再放大」，
    結果在平滑漸層的圖上留下一圈以取樣格子為週期的漣漪——那個週期和圖樣一
    對上，乾淨的圖也會驗出高分（合成漸層測試圖假陽性 3.4，門檻才 0.5）。
    """
    return signal - _box1d(_box1d(signal, window, 0), window, 1)


def reveal(image, radius=REVEAL_WINDOW):
    """抽出色度殘差：正常的畫面內容被減掉，只留下浮水印所在的頻段。

    放大之後就是給人看的「還原圖」。前端 utils/watermarkReveal.js 是同一組
    運算的 JS 版本，前台的檢視頁在瀏覽器裡跑，不必把圖上傳。
    """
    return _highpass(_chroma(image), radius)


def reveal_data_url(image, gain=REVEAL_GAIN, radius=REVEAL_WINDOW):
    """還原圖，灰階 PNG。128 是中間值，殘差放大 gain 倍。"""
    preview = np.clip(128 + reveal(image, radius) * gain, 0, 255).astype(np.uint8)
    return encode_data_url(Image.fromarray(preview, "L"), keep_alpha=True)


def already_marked(image, settings, mask=None):
    """這張圖是不是已經套過現在這個浮水印了。

    只給 `mark_data_url` 用來擋掉重複套用：後台每次儲存都會把整批圖重送，
    沒有這道檢查的話同樣的位移會一次次疊上去，存幾次就看得見了。

    用 FFT 一次算完「圖樣對齊在任何位置」的相關值——圖樣是週期性的，所以
    只有一個 tile 內的位移是新的。分數取「最高的那個位移」減掉「所有位移的
    雜訊水準」：畫面本身的紋理會讓每個位移都有一點反應，真的套過才會在某一
    個位移上冒出尖峰。

    刻意只比對原尺寸。這裡要判斷的是「剛剛存進來的這張是不是我們自己套的」，
    那張圖不會被縮放過，掃描縮放比例只會多花時間又多一次誤判的機會——而誤判
    成「已經套過」的代價是這張圖從此漏掉浮水印。

    （被別人縮放、轉存過的圖要不要算本站的，改由前台的檢視頁把還原圖攤開來
    讓人自己看。自動判定得對上任意縮放比例，離散地掃幾個比例只會漏掉大部分
    情況：實測縮到 0.75 驗得到，0.8 或 0.7 就掉到門檻的一半以下。）
    """
    base = tile_mask(settings) if mask is None else mask
    size = base.shape[0]
    residual = _highpass(_chroma(image), max(8, size // 4))
    # 邊緣（人物輪廓、色塊交界）的色度落差是浮水印的十幾倍，不壓下來的話
    # 相關值整個被它們主導。夾在中位數的幾倍以內，訊號完全保得住
    limit = 3.0 * max(0.5, float(np.median(np.abs(residual))))
    residual = np.clip(residual, -limit, limit)

    height, width = residual.shape
    pattern = _tiled(base, height, width)
    if "A" in image.getbands():
        opaque = (np.asarray(image.getchannel("A"), dtype=np.float32) > 0).astype(np.float32)
        residual = residual * opaque
        pattern = pattern * opaque

    energy = float((pattern * pattern).sum())
    if energy <= 0:
        return False

    correlation = np.fft.irfft2(
        np.fft.rfft2(residual) * np.conj(np.fft.rfft2(pattern)), s=(height, width)
    )[:min(size, height), :min(size, width)] / energy
    score = float(correlation.max()) - float(np.percentile(np.abs(correlation), 90))
    return score >= max(DETECT_FLOOR, settings["strength"] * DETECT_RATIO)


def mark_data_url(img_data, settings=None, mask=None):
    """套浮水印到一張 base64 圖片，回傳新的 data URL。

    刻意做成「出任何問題都原封不動回傳」——浮水印是加值功能，
    絕對不該讓後台存不了圖。
    """
    settings = load_settings() if settings is None else settings
    if not settings["enabled"]:
        return img_data

    image = decode_data_url(img_data)
    if image is None:
        return img_data
    if min(image.size) < MIN_EDGE:
        return img_data

    try:
        mask = tile_mask(settings) if mask is None else mask
        # 已經有浮水印的圖不要再套一次：同樣的圖樣疊兩次，位移就變兩倍，
        # 存個幾次之後就看得見了。後台每次儲存都會把整批圖重送，所以這條必要。
        if already_marked(image, settings, mask):
            return img_data
        keep_alpha = "A" in image.getbands()
        return encode_data_url(embed(image, settings, mask), keep_alpha)
    except Exception as e:  # noqa: BLE001 — 見上方 docstring
        print("watermark: 套用失敗，維持原圖", e)
        return img_data


def mark_payload(value, settings=None):
    """走過整包要寫進 RTDB 的資料，把每一個 base64 圖片欄位換成套過浮水印的版本。

    區塊編輯器的圖片藏在巢狀結構裡，逐個欄位處理會漏；這裡不管它長在哪，
    只認 `data:image/…;base64,` 開頭的字串。
    """
    settings = load_settings() if settings is None else settings
    if not settings["enabled"]:
        return value
    try:
        mask = tile_mask(settings)
    except ValueError as e:
        print("watermark: 設定不完整，略過", e)
        return value

    def walk(node):
        if isinstance(node, str):
            return mark_data_url(node, settings, mask) if node.startswith("data:image/") else node
        if isinstance(node, dict):
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v) for v in node]
        return node

    return walk(value)
