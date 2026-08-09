import io
import json

from flask import Blueprint, jsonify, make_response, request, send_file
from flask_login import current_user

from app import ai
from app.config import settings

from app.elements import get_atomicOrbital, get_characteristic, get_abMax
from app.links import normalize_creator_links
from app.completion import get_completion
from app.gallery import normalize_gallery
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
        query = show_fdb(symbol)
        if query:
            story = query.get("description")
            img_data = query.get("img_data")

        return jsonify(
            {
                "el_info": el_info,
                "f_el": {"Symbol": f_el["Symbol"], "CPKHexColor": f_el["CPKHexColor"]},
                "b_el": {"Symbol": b_el["Symbol"], "CPKHexColor": b_el["CPKHexColor"]},
                "story": story,
                "img_data": img_data,
            }
        )

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
            "frame_image": data.get("frame_image", ""),
        })
    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500


@public_bp.route("/elements/<symbol>/gallery", methods=["GET"])
def get_element_gallery(symbol):
    """元素的「其他樣貌」圖庫，與代表圖分開存放。"""
    try:
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
