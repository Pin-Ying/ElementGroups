import base64
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app import auth as auth_module
from app.config import settings
from app.elements import element_info
from app.links import normalize_creator_links, serialize_creator_links
from app.completion import update_completion, rebuild_completion
from app.firebase import show_fdb, upload_fdb, upload_file, periodic_table_exists, upload_periodic_table, get_periodic_table, get_image_bytes, get_element_by_symbol, fdb
from app import ai

admin_bp = Blueprint("admin", __name__, url_prefix="/api")


@admin_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"result": "failure", "message": "Missing request body"}), 400

    email = data.get("email")
    password = data.get("password")
    token, message = auth_module.login(email, password)

    if token:
        return jsonify({"result": "success", "message": message, "token": token})
    return jsonify({"result": "failure", "message": message}), 401


@admin_bp.route("/auth/logout", methods=["POST"])
def logout():
    auth_header = request.headers.get('Authorization', '')
    token = auth_header[7:] if auth_header.startswith('Bearer ') else None
    auth_module.logout(token)
    return jsonify({"result": "success", "message": "Logged out successfully"})


@admin_bp.route("/auth/status", methods=["GET"])
def auth_status():
    return jsonify({"loggedIn": current_user.is_authenticated})


@admin_bp.route("/admin/create-db", methods=["POST"])
@login_required
def create_db():
    return jsonify({"result": "success", "message": "Firestore 無需建立資料表"})


@admin_bp.route("/admin/update-db", methods=["POST"])
@login_required
def update_db():
    try:
        if periodic_table_exists():
            return jsonify({"result": "success", "message": "資料已存在，略過更新"})
        data = element_info()
        if data is None:
            return jsonify({"result": "failure", "message": "無法取得元素資料"}), 500
        upload_periodic_table(data.to_dict(orient='records'))
        return jsonify({"result": "success", "message": "update-db finish!"})
    except Exception as e:
        print("update-db error!", e)
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/backfill-img-data", methods=["POST"])
@login_required
def backfill_img_data():
    try:
        fbDatas = show_fdb()
        if not fbDatas:
            return jsonify({"result": "success", "message": "No story data found", "updated": 0})

        pending = [
            symbol for symbol, data in fbDatas.items()
            if symbol != "periodic_table" and not data.get("img_data") and data.get("img")
        ]

        def process_one(symbol):
            img_bytes, _ = get_image_bytes(symbol)
            if img_bytes is None:
                return False
            img_data = "data:image/jpeg;base64," + base64.b64encode(img_bytes).decode("utf-8")
            fdb.child(symbol).update({"img_data": img_data})
            return True

        updated = 0
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(process_one, symbol): symbol for symbol in pending}
            for future in as_completed(futures):
                if future.result():
                    updated += 1

        return jsonify({
            "result": "success",
            "message": f"完成！新增 {updated} 筆",
            "updated": updated
        })
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/ai/status", methods=["GET"])
@login_required
def ai_status():
    """前端據此決定要不要顯示 AI 協助介面。"""
    if not ai.is_enabled():
        return jsonify({"enabled": False})
    used, limit = ai.get_usage()
    return jsonify({
        "enabled": True,
        "provider": settings.AI_PROVIDER,
        "model": settings.AI_MODEL,
        "used": used,
        "limit": limit,
    })


@admin_bp.route("/admin/story-suggest", methods=["POST"])
@login_required
def story_suggest():
    if not ai.is_enabled():
        return jsonify({"result": "failure", "message": "AI 功能未啟用"}), 400

    data = request.get_json() or {}
    symbol = (data.get("symbol") or "").strip()
    if not symbol:
        return jsonify({"result": "failure", "message": "缺少 symbol"}), 400

    element = get_element_by_symbol(symbol)
    if not element:
        return jsonify({"result": "failure", "message": f"找不到元素 {symbol}"}), 404

    try:
        text, used, limit = ai.generate_story(
            element,
            draft=(data.get("draft") or "").strip(),
            direction=(data.get("direction") or "").strip(),
            reference=(data.get("reference") or "").strip(),
        )
        return jsonify({"result": "success", "suggestion": text, "used": used, "limit": limit})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 502


@admin_bp.route("/admin/rebuild-completion", methods=["POST"])
@login_required
def rebuild_completion_summary():
    """重新掃描所有元素，重建首頁用的完成度摘要。
    正常情況下寫入故事/圖片時已自動同步，這裡是資料被外部改動後的補救。"""
    try:
        completion = rebuild_completion()
        return jsonify({
            "result": "success",
            "message": f"完成！已重建 {len(completion)} 筆",
            "count": len(completion)
        })
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/default-img", methods=["GET", "POST"])
@login_required
def manage_default_image():
    if request.method == "GET":
        try:
            data = show_fdb("_default")
            img_data = data.get("img_data", "") if data else ""
            return jsonify({"img_data": img_data})
        except Exception as e:
            return jsonify({"result": "failure", "message": str(e)}), 500

    # POST
    try:
        image = request.files.get("image")
        if not image or not image.filename:
            return jsonify({"result": "failure", "message": "No image provided"}), 400

        image_bytes = image.read()
        img_data = "data:image/jpeg;base64," + base64.b64encode(image_bytes).decode("utf-8")

        img = ""
        if settings.FIREBASE_STORAGE_ENABLED:
            filename = "static/img/_default.JPG"
            temp = tempfile.NamedTemporaryFile(delete=False)
            temp.write(image_bytes)
            temp.close()
            img = upload_file(temp.name, filename)
            os.remove(temp.name)

        upload_fdb("_default", {"img": img, "img_data": img_data})
        return jsonify({"result": "success", "message": "Default image updated!"})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/creator-links", methods=["GET", "POST"])
@login_required
def manage_creator_links():
    if request.method == "GET":
        try:
            data = show_fdb("_creator_links")
            return jsonify({"links": normalize_creator_links(data)})
        except Exception as e:
            return jsonify({"result": "failure", "message": str(e)}), 500

    # POST
    try:
        payload = serialize_creator_links(request.get_json() or {})
        # upload_fdb 是整個覆寫，admin 刪掉的連結與舊格式欄位都會一併消失
        upload_fdb("_creator_links", payload)
        return jsonify({"result": "success", "message": "Creator links updated!"})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/story", methods=["POST", "GET"])
@login_required
def update_story():
    if request.method == "GET":
        try:
            fbDatas = show_fdb()
            if not fbDatas:
                fbDatas = {}
            # 排除 periodic_table 與 _default / _creator_links 等設定用 node
            symbols = [d for d in fbDatas if d != "periodic_table" and not d.startswith("_")]
            imageDatas = {data: fbDatas[data].get("img", "") for data in symbols}
            storyDatas = {data: fbDatas[data].get("description", "") for data in symbols}
            # Storage 關閉時圖片只存在 img_data(base64)，兩者任一有值就算已上傳
            hasImage = {
                data: bool(fbDatas[data].get("img") or fbDatas[data].get("img_data"))
                for data in symbols
            }
            elements_data = get_periodic_table()
            elements = [e["Symbol"] for e in elements_data]
            return jsonify(
                {
                    "elements": elements,
                    "imageDatas": imageDatas,
                    "storyDatas": storyDatas,
                    "hasImage": hasImage,
                }
            )
        except Exception as e:
            return jsonify({"result": "failure", "message": str(e)}), 500

    # POST
    try:
        symbol = request.form.get("symbol")
        story = request.form.get("stroy")  # kept original field name for compat
        image = request.files.get("image")

        fbDatas = show_fdb()
        if not fbDatas:
            fbDatas = {}
        imageDatas = {data: fbDatas[data].get("img", "") for data in fbDatas if data != "periodic_table"}

        if image and image.filename:
            image_bytes = image.read()
            img_data = "data:image/jpeg;base64," + base64.b64encode(image_bytes).decode("utf-8")

            img = ""
            if settings.FIREBASE_STORAGE_ENABLED:
                filename = f"static/img/{symbol}.JPG"
                temp = tempfile.NamedTemporaryFile(delete=False)
                temp.write(image_bytes)
                temp.close()
                img = upload_file(temp.name, filename)
                os.remove(temp.name)
        else:
            img = imageDatas.get(symbol, "")
            img_data = fbDatas.get(symbol, {}).get("img_data", "")

        record = {"img": img, "img_data": img_data, "description": story}
        upload_fdb(symbol, record)
        update_completion(symbol, record)
        return jsonify({"result": "success", "message": "Finish!"})

    except Exception as e:
        print(e)
        return jsonify({"result": "failure", "message": str(e)}), 500
