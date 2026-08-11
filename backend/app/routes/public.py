import io
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Blueprint, jsonify, make_response, request, send_file
from flask_login import current_user

from app import ai
from app.config import settings

from app.elements import get_atomicOrbital, get_characteristic, get_abMax
from app.links import normalize_creator_links
from app.completion import get_completion
from app.gallery import normalize_gallery
from app.pages import normalize_page, normalize_pages, PAGES_NODE
from app.molecules import normalize_molecule, normalize_molecules, MOLECULES_NODE
from app.particles import normalize_particles, PARTICLES_NODE
from app.page_meta import PAGE_META_NODE, normalize_all
from app.groups import GROUPS_NODE, GROUP_KEYS, normalize_group, normalize_groups, has_content
from app.layers import normalize_layers, normalize_electron_styles, normalize_motion, resolve_electron_style, LAYERS_NODE, ELECTRON_STYLES_NODE, ELECTRON_DEFAULT_NODE, MOTION_NODE
from app.libraries import normalize_libraries, libraries_for, find_library, resolve_image, primary_image_data, LIBRARIES_NODE
from app.stats import get_all_views, record_view
from app.firebase import show_fdb, get_periodic_table, get_element_by_symbol, get_element_by_atomic_number, get_image_bytes

public_bp = Blueprint("public", __name__, url_prefix="/api")


def _element_summary(e):
    """首頁各種檢視共用的欄位。詳細清單模式會用到原子量與常溫狀態。"""
    return {
        "AtomicNumber": e["AtomicNumber"],
        "Symbol": e["Symbol"],
        "Name": e.get("Name", ""),
        "CPKHexColor": e["CPKHexColor"],
        "AtomicMass": e.get("AtomicMass", ""),
        "StandardState": e.get("StandardState", ""),
    }


@public_bp.route("/elements", methods=["GET"])
def get_elements():
    try:
        elements_data = get_periodic_table()
        elements = [_element_summary(e) for e in elements_data]
        groups = get_characteristic()
    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500

    return jsonify({"elements": elements, "groups": groups})


@public_bp.route("/groups", methods=["POST"])
def get_groups():
    body = request.get_json()
    group_type = body.get("groupType")

    elements_data = get_periodic_table()
    elements = [_element_summary(e) for e in elements_data]

    try:
        if group_type == "cp":
            groups = get_characteristic()
        elif group_type == "vs":
            groups = get_atomicOrbital()
        else:
            return jsonify({"result": "failure", "exception": "Invalid groupType"}), 400

        # Build grouped data structure for frontend
        grouped = {}
        for group_name in set(groups.values()):
            grouped[group_name] = [
                elt for elt in elements if groups.get(elt["Symbol"]) == group_name
            ]

        return jsonify({"elements": elements, "groups": groups, "grouped": grouped})

    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500


@public_bp.route("/elements/<symbol>", methods=["GET"])
def get_element_detail(symbol):
    try:
        el_info = get_element_by_symbol(symbol)

        if not el_info:
            return jsonify({"result": "failure", "exception": "Element not found"}), 404

        el_AN = int(el_info["AtomicNumber"])

        # Previous element
        if el_AN != 1:
            f_el = get_element_by_atomic_number(el_AN - 1) or el_info
        else:
            f_el = el_info

        # Next element
        if el_AN != 118:
            b_el = get_element_by_atomic_number(el_AN + 1) or el_info
        else:
            b_el = el_info

        # Firebase story data
        story = None
        img_data = None
        draft = ""
        query = show_fdb(symbol)
        if query:
            story = query.get("description")
            img_data = query.get("img_data")
            # 草稿只給登入者，前台一律看已發布的版本
            if current_user.is_authenticated:
                draft = query.get("draft") or ""

        return jsonify(
            {
                "el_info": el_info,
                "f_el": {"Symbol": f_el["Symbol"], "CPKHexColor": f_el["CPKHexColor"]},
                "b_el": {"Symbol": b_el["Symbol"], "CPKHexColor": b_el["CPKHexColor"]},
                "story": story,
                "img_data": img_data,
                "draft": draft,
            }
        )

    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500


@public_bp.route("/elements/seo", methods=["GET"])
def get_elements_seo():
    """預渲染用：118 個元素的基本資料與故事開頭，一次拿完。

    前端 build 時要為每個元素產生一份含自己 title/description 的靜態 HTML
    （見 vite-plugin-prerender.js）。走 `/elements/<symbol>` 得打 118 次，
    這裡改成一支端點回傳全部。

    兩個效能上的要點，少一個都會讓這支端點超過 gunicorn 的 30 秒上限：

    1. 只讀 `{symbol}/description` 而不是整個元素節點——整個節點含 base64
       的 img_data，118 個加起來是好幾 MB
    2. 並行讀取。Firebase 每次往返約 0.2~0.3 秒，118 次循序就是 30 秒起跳，
       正好卡在 worker timeout。沿用 admin.py backfill 的 ThreadPoolExecutor
    """
    EXCERPT_LEN = 200

    def excerpt_for(symbol):
        # 只取 description 這個子節點，不要整包元素資料
        raw = show_fdb(f"{symbol}/description")
        if not isinstance(raw, str):
            return ""
        # 存的可能是字面的反斜線 n，換回真正的換行再壓成單行
        story = " ".join(raw.replace("\\n", "\n").split())
        return story[:EXCERPT_LEN] + "…" if len(story) > EXCERPT_LEN else story

    try:
        elements = [el for el in get_periodic_table() if el.get("Symbol")]

        excerpts = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(excerpt_for, el["Symbol"]): el["Symbol"] for el in elements}
            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    excerpts[symbol] = future.result()
                except Exception:
                    # 單一元素讀不到不該讓整支端點失敗，沒有故事就用資料式描述
                    excerpts[symbol] = ""

        return jsonify({"elements": [{
            "Symbol": el["Symbol"],
            "Name": el.get("Name", ""),
            "AtomicNumber": el.get("AtomicNumber"),
            "AtomicMass": el.get("AtomicMass", ""),
            "GroupBlock": el.get("GroupBlock", ""),
            "StandardState": el.get("StandardState", ""),
            "excerpt": excerpts.get(el["Symbol"], ""),
        } for el in elements]})
    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500


def _element_cards(symbols):
    """把 symbol 清單轉成首頁卡片需要的最小欄位。"""
    cards = []
    for symbol in symbols:
        el = get_element_by_symbol(symbol)
        if not el:
            continue
        cards.append({
            "Symbol": el.get("Symbol"),
            "Name": el.get("Name", ""),
            "AtomicNumber": el.get("AtomicNumber"),
            "CPKHexColor": el.get("CPKHexColor", ""),
        })
    return cards


@public_bp.route("/elements/recent", methods=["GET"])
def get_recent_elements():
    """最近更新過故事/圖片的元素。"""
    try:
        limit = min(int(request.args.get("limit", 8)), 20)
        completion = get_completion() or {}
        dated = [
            (symbol, entry.get("updated_at"))
            for symbol, entry in completion.items()
            if isinstance(entry, dict) and entry.get("updated_at")
        ]
        dated.sort(key=lambda item: item[1], reverse=True)
        symbols = [symbol for symbol, _ in dated[:limit]]

        updated_map = dict(dated)
        cards = _element_cards(symbols)
        for card in cards:
            card["updated_at"] = updated_map.get(card["Symbol"], "")
        return jsonify({"elements": cards})
    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500


@public_bp.route("/elements/popular", methods=["GET"])
def get_popular_elements():
    """依點閱次數排序的熱門元素。"""
    try:
        limit = min(int(request.args.get("limit", 8)), 20)
        views = get_all_views()
        ranked = sorted(views.items(), key=lambda item: item[1], reverse=True)[:limit]

        cards = _element_cards([symbol for symbol, _ in ranked])
        view_map = dict(ranked)
        for card in cards:
            card["views"] = view_map.get(card["Symbol"], 0)
        return jsonify({"elements": cards})
    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500


@public_bp.route("/elements/<symbol>/view", methods=["POST"])
def record_element_view(symbol):
    """元素頁載入時累加點閱。失敗不影響前台，回 200 即可。"""
    try:
        if not get_element_by_symbol(symbol):
            return jsonify({"result": "failure", "exception": "Element not found"}), 404
        views = record_view(symbol)
        return jsonify({"result": "success", "views": views})
    except Exception as e:
        print(f"Failed to record view for {symbol}: {e}")
        return jsonify({"result": "failure", "exception": str(e)}), 500


@public_bp.route("/ai/status", methods=["GET"])
def ai_status():
    """AI 協助是否可用。

    刻意不加登入保護，方便部署後直接確認環境變數有沒有生效；
    回應只有「有沒有啟用」與模型名稱，用量統計仍需登入才會回傳。
    """
    if not ai.is_enabled():
        return jsonify({"enabled": False})

    result = {
        "enabled": True,
        "provider": settings.AI_PROVIDER,
        "model": settings.AI_MODEL,
    }
    if current_user.is_authenticated:
        used, limit = ai.get_usage()
        result.update({"used": used, "limit": limit})
    return jsonify(result)


@public_bp.route("/elements/<symbol>/layers", methods=["GET"])
def get_element_layers(symbol):
    """元素的圖層設定，連同選用的電子樣式圖一起回傳，前端才不用再打一次。

    電子的圖優先讀通用圖庫（綁在「基本粒子／電子」的那個庫）；還沒搬進
    圖庫時退回舊的 `_electron_styles`。兩條路都用同一組 id，所以每個元素
    原本指定的樣式在搬遷前後都指得到。
    """
    try:
        layers = normalize_layers(show_fdb(f"{LAYERS_NODE}/{symbol}"))
        picked = (layers.get("electron_style") or "").strip()
        electron_img = ""
        style_id = ""

        library = next(iter(libraries_for(
            normalize_libraries(show_fdb(LIBRARIES_NODE)), "particle", "electron")), None)

        if library:
            image = resolve_image(library, picked)
            if image:
                style_id = image["id"]
                electron_img = image["img_data"]
        else:
            # 舊路徑：元素沒有各自指定時退回全站預設
            style_id = resolve_electron_style(layers, show_fdb(ELECTRON_DEFAULT_NODE))
            if style_id:
                style = show_fdb(f"{ELECTRON_STYLES_NODE}/{style_id}")
                if isinstance(style, dict):
                    electron_img = (style.get("img_data") or "").strip()
        return jsonify({
            **layers,
            # 運動方式是全站統一的，不看元素自己的設定
            "motion": normalize_motion(show_fdb(MOTION_NODE)),
            "electron_style": style_id,
            "electron_img": electron_img,
        })
    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500


@public_bp.route("/element-groups", methods=["GET"])
def get_element_groups():
    """所有已設定形象的族。"""
    try:
        libraries = normalize_libraries(show_fdb(LIBRARIES_NODE))
        groups = normalize_groups(show_fdb(GROUPS_NODE))
        for group in groups:
            from_library = primary_image_data(libraries, "group", group["key"])
            if from_library:
                group["img_data"] = from_library
        groups = [g for g in groups if has_content(g)]
        return jsonify({"groups": groups})
    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500


@public_bp.route("/element-groups/<key>", methods=["GET"])
def get_element_group(key):
    """單一族的形象，元素頁用族別對照後來拿。"""
    if key not in GROUP_KEYS:
        return jsonify({"result": "failure", "message": "not found"}), 404
    try:
        group = normalize_group(key, show_fdb(f"{GROUPS_NODE}/{key}"))
        from_library = primary_image_data(
            normalize_libraries(show_fdb(LIBRARIES_NODE)), "group", key)
        if from_library:
            group["img_data"] = from_library
        return jsonify(group)
    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500


@public_bp.route("/page-meta", methods=["GET"])
def get_page_meta():
    """全部內建頁面的文案覆寫，一次回傳（資料量小、頁面共用）。"""
    try:
        return jsonify({"meta": normalize_all(show_fdb(PAGE_META_NODE))})
    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500


@public_bp.route("/particles", methods=["GET"])
def get_particles():
    """基本粒子形象清單。登入後一併回傳未發布的。"""
    try:
        particles = normalize_particles(show_fdb(PARTICLES_NODE),
                                        include_drafts=current_user.is_authenticated)
        # 搬進圖庫的粒子改用圖庫的預設圖當形象圖；沒搬的沿用自己的 img_data
        libraries = normalize_libraries(show_fdb(LIBRARIES_NODE))
        for particle in particles:
            from_library = primary_image_data(libraries, "particle", particle["slug"])
            if from_library:
                particle["img_data"] = from_library
        return jsonify({"particles": particles})
    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500


@public_bp.route("/molecules", methods=["GET"])
def get_molecules():
    """分子清單。登入後一併回傳未發布的。"""
    try:
        items = normalize_molecules(show_fdb(MOLECULES_NODE),
                                    include_drafts=current_user.is_authenticated)
        element = (request.args.get("element") or "").strip()
        if element:
            items = [m for m in items if element in (m.get("elements") or [])]
        limit = request.args.get("limit")
        total = len(items)
        if limit:
            items = items[:max(0, int(limit))]
        # 清單不需要故事與圖片，省下傳輸量
        slim = [{k: m[k] for k in ("slug", "name", "formula", "elements", "published", "updated_at")}
                for m in items]
        return jsonify({"molecules": slim, "total": total})
    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500


@public_bp.route("/molecules/<slug>", methods=["GET"])
def get_molecule(slug):
    try:
        molecule = normalize_molecule(slug, show_fdb(f"{MOLECULES_NODE}/{slug}"))
        if molecule:
            from_library = primary_image_data(
                normalize_libraries(show_fdb(LIBRARIES_NODE)), "molecule", slug)
            if from_library:
                molecule["img_data"] = from_library
        if not molecule:
            return jsonify({"result": "failure", "exception": "Molecule not found"}), 404
        if not molecule["published"] and not current_user.is_authenticated:
            return jsonify({"result": "failure", "exception": "Molecule not found"}), 404
        return jsonify(molecule)
    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500


@public_bp.route("/pages", methods=["GET"])
def get_pages():
    """已發布頁面的清單，供導覽列使用。登入後一併回傳草稿。"""
    try:
        include_drafts = current_user.is_authenticated
        pages = normalize_pages(show_fdb(PAGES_NODE), include_drafts=include_drafts)
        # 導覽只需要標題與位置，內容另外抓，避免清單塞一堆 Markdown
        return jsonify({"pages": [
            {k: p[k] for k in ("slug", "title", "nav_position", "nav_order", "published")}
            for p in pages
        ]})
    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500


@public_bp.route("/pages/<slug>", methods=["GET"])
def get_page(slug):
    try:
        page = normalize_page(slug, show_fdb(f"{PAGES_NODE}/{slug}"))
        if not page:
            return jsonify({"result": "failure", "exception": "Page not found"}), 404
        # 草稿只有登入後看得到
        if not page["published"] and not current_user.is_authenticated:
            return jsonify({"result": "failure", "exception": "Page not found"}), 404
        return jsonify(page)
    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500


@public_bp.route("/site-settings", methods=["GET"])
def get_site_settings():
    """網站標題／副標題／SEO 描述與首頁背景圖，供前端動態套用。"""
    try:
        data = show_fdb("_site_settings") or {}
        return jsonify({
            "title": data.get("title", ""),
            "subtitle": data.get("subtitle", ""),
            "description": data.get("description", ""),
            "bg_image": data.get("bg_image", ""),
            # 元素代表圖的圖鑑外框：內建款式，或自訂的框圖（優先）
            "frame_style": data.get("frame_style", "classic"),
            "layer_bg": data.get("layer_bg") or "#ffffff",
            # 電子在畫面上的大小（佔容器寬度的百分比）
            "electron_size": data.get("electron_size") or 24,
            "frame_image": data.get("frame_image", ""),
        })
    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500


@public_bp.route("/elements/<symbol>/gallery", methods=["GET"])
def get_element_gallery(symbol):
    """元素的「其他樣貌」圖庫，與代表圖分開存放。"""
    try:
        # 搬進圖庫的元素改讀圖庫；沒搬的照舊。圖庫的 name 對應舊的 caption，
        # 回傳形狀維持不變，前端不必知道資料換了地方
        library = find_library(
            normalize_libraries(show_fdb(LIBRARIES_NODE)), "element", symbol)
        if library:
            return jsonify({"images": [
                {"img_data": i["img_data"], "caption": i["name"]} for i in library["images"]
            ]})
        return jsonify({"images": normalize_gallery(show_fdb(f"_gallery/{symbol}"))})
    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500


@public_bp.route("/elements/completion", methods=["GET"])
def get_elements_completion():
    """首頁用：哪些元素已經有故事/圖片。"""
    try:
        return jsonify({"completion": get_completion() or {}})
    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500


@public_bp.route("/creator-links", methods=["GET"])
def get_creator_links():
    try:
        data = show_fdb("_creator_links")
        return jsonify(normalize_creator_links(data))
    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500


@public_bp.route("/elements/default-img", methods=["GET"])
def get_default_image():
    try:
        img_bytes, content_type = get_image_bytes("_default")
        if img_bytes is None:
            return "", 404
        response = make_response(send_file(io.BytesIO(img_bytes), mimetype=content_type))
        response.headers["Cache-Control"] = "public, max-age=86400"
        return response
    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500


@public_bp.route("/elements/<symbol>/img", methods=["GET"])
def get_element_image(symbol):
    try:
        img_bytes, content_type = get_image_bytes(symbol)
        if img_bytes is None:
            return "", 404
        response = make_response(send_file(io.BytesIO(img_bytes), mimetype=content_type))
        response.headers["Cache-Control"] = "public, max-age=86400"
        return response
    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500


@public_bp.route("/elements/<symbol>/ability", methods=["GET"])
def get_element_ability(symbol):
    try:
        el_info = get_element_by_symbol(symbol)

        if not el_info:
            return jsonify({"result": "failure", "exception": "Element not found"}), 404

        abMax = get_abMax()
        el_info["abMax"] = abMax
        return json.dumps(el_info, ensure_ascii=False)

    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500
