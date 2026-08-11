import base64
import datetime
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
from app.gallery import normalize_gallery
from app.pages import normalize_pages, serialize_page, normalize_slug, PAGES_NODE
from app.molecules import normalize_molecules, serialize_molecule, normalize_slug as molecule_slug, MOLECULES_NODE
from app.page_meta import PAGE_META_NODE, META_KEYS, normalize_meta
from app.particles import normalize_particles, serialize_particle, normalize_slug as particle_slug, PARTICLES_NODE
from app import pubchem
from app.groups import GROUPS_NODE, GROUP_KEYS, normalize_group, normalize_groups, serialize_group, group_key_for, has_content as group_has_content
from app.layers import normalize_layers, serialize_layers, normalize_motion, resolve_orbit_particle, LAYERS_NODE, ORBIT_PARTICLE_NODE, MOTION_NODE, MOTIONS
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


@admin_bp.route("/admin/page-suggest", methods=["POST"])
@login_required
def page_suggest():
    """頁面內容的 AI 協助（issue #19）。與故事共用每日額度。"""
    if not ai.is_enabled():
        return jsonify({"result": "failure", "message": "AI 功能未啟用"}), 400

    data = request.get_json() or {}
    topic = (data.get("topic") or "").strip()
    if not topic:
        return jsonify({"result": "failure", "message": "請先描述頁面主題"}), 400

    try:
        text, used, limit = ai.generate_page(
            topic,
            draft=(data.get("draft") or "").strip(),
            direction=(data.get("direction") or "").strip(),
        )
        return jsonify({"result": "success", "suggestion": text, "used": used, "limit": limit})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 502


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

    # 勾選帶入主族形象時，後端自己查該元素所屬族的設定（issue #16）
    group_info = ""
    if data.get("include_group"):
        key = group_key_for(element.get("AtomicNumber"))
        if key:
            group = normalize_group(key, show_fdb(f"{GROUPS_NODE}/{key}"))
            if group_has_content(group):
                pieces = [f"所屬族：{key}"]
                if group["name"]:
                    pieces.append(f"形象名稱：{group['name']}")
                if group["description"]:
                    pieces.append(f"共同特色：{group['description']}")
                group_info = "\n".join(pieces)

    try:
        text, used, limit = ai.generate_story(
            element,
            draft=(data.get("draft") or "").strip(),
            direction=(data.get("direction") or "").strip(),
            reference=(data.get("reference") or "").strip(),
            group_info=group_info,
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


@admin_bp.route("/admin/orbit-particle", methods=["GET", "POST"])
@login_required
def orbit_particle():
    """全站繞行粒子。

    候選來自「基本粒子」（`_particles`），所以要新增電子以外的粒子是到
    那邊加一筆，不需要在這裡再維護一套圖。
    """
    if request.method == "GET":
        try:
            particles = normalize_particles(show_fdb(PARTICLES_NODE), include_drafts=True)
            current = resolve_orbit_particle(particles, show_fdb(ORBIT_PARTICLE_NODE))
            return jsonify({
                # 沒有形象圖的粒子當不了繞行粒子，先濾掉
                "particles": [
                    {"slug": p["slug"], "name": p["name"], "img_data": p["img_data"]}
                    for p in particles if p["img_data"]
                ],
                "current": current["slug"] if current else "",
            })
        except Exception as e:
            return jsonify({"result": "failure", "message": str(e)}), 500

    try:
        slug = ((request.get_json() or {}).get("slug") or "").strip()
        fdb.child(ORBIT_PARTICLE_NODE).set(slug)
        return jsonify({"result": "success", "message": "繞行粒子已儲存", "slug": slug})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/electron-motion", methods=["GET", "POST"])
@login_required
def electron_motion():
    """全站電子運動方式。三種模式是整體視覺風格，統一設定不逐個元素指定。"""
    if request.method == "GET":
        try:
            return jsonify({
                "motion": normalize_motion(show_fdb(MOTION_NODE)),
                "options": list(MOTIONS),
            })
        except Exception as e:
            return jsonify({"result": "failure", "message": str(e)}), 500

    try:
        motion = normalize_motion((request.get_json() or {}).get("motion"))
        fdb.child(MOTION_NODE).set(motion)
        return jsonify({"result": "success", "message": "電子運動方式已儲存", "motion": motion})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/elements/<symbol>/layers", methods=["GET", "POST"])
@login_required
def manage_layers(symbol):
    if request.method == "GET":
        try:
            return jsonify(normalize_layers(show_fdb(f"{LAYERS_NODE}/{symbol}")))
        except Exception as e:
            return jsonify({"result": "failure", "message": str(e)}), 500

    try:
        record = serialize_layers(request.get_json() or {})
        if not record:
            return jsonify({"result": "failure", "message": "沒有要更新的欄位"}), 400
        # 用 update：只送了原子核時不該把手寫名那層清掉
        fdb.child(LAYERS_NODE).child(symbol).update(record)
        return jsonify({"result": "success", "message": "圖層已儲存"})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/element-groups", methods=["GET"])
@login_required
def list_element_groups():
    try:
        return jsonify({"groups": normalize_groups(show_fdb(GROUPS_NODE))})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/element-groups/<key>", methods=["POST"])
@login_required
def update_element_group(key):
    if key not in GROUP_KEYS:
        return jsonify({"result": "failure", "message": f"沒有 {key} 這個族"}), 400

    try:
        record = serialize_group(request.get_json() or {})
        if record is None:
            return jsonify({"result": "failure", "message": "無效的資料"}), 400
        record["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        fdb.child(GROUPS_NODE).child(key).set(record)
        return jsonify({"result": "success", "message": "主族形象已儲存"})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/page-meta/<key>", methods=["POST"])
@login_required
def update_page_meta(key):
    """儲存單一內建頁面的文案覆寫；欄位值為空字串表示還原成內建預設。"""
    if key not in META_KEYS:
        return jsonify({"result": "failure", "message": f"沒有 {key} 這個頁面"}), 400
    try:
        record = normalize_meta(request.get_json() or {})
        fdb.child(PAGE_META_NODE).child(key).set(record)
        return jsonify({"result": "success", "message": "文案已儲存"})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/particles", methods=["GET", "POST"])
@login_required
def manage_particles():
    if request.method == "GET":
        try:
            return jsonify({"particles": normalize_particles(show_fdb(PARTICLES_NODE),
                                                             include_drafts=True)})
        except Exception as e:
            return jsonify({"result": "failure", "message": str(e)}), 500

    try:
        payload = request.get_json() or {}
        slug, record = serialize_particle(payload)
        if not slug:
            return jsonify({"result": "failure", "message": record}), 400

        original = particle_slug(payload.get("original_slug") or "")
        if original and original != slug:
            fdb.child(PARTICLES_NODE).child(original).delete()

        record["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        fdb.child(PARTICLES_NODE).child(slug).set(record)
        return jsonify({"result": "success", "message": "粒子已儲存", "slug": slug})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/particles/<slug>", methods=["DELETE"])
@login_required
def delete_particle(slug):
    safe = particle_slug(slug)
    if not safe:
        return jsonify({"result": "failure", "message": "無效的代稱"}), 400
    try:
        fdb.child(PARTICLES_NODE).child(safe).delete()
        return jsonify({"result": "success", "message": "粒子已刪除"})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/molecules/lookup", methods=["GET"])
@login_required
def lookup_molecule():
    """到 PubChem 查分子。查不到回空陣列，前端據此切換到手動填寫。"""
    try:
        name = (request.args.get("name") or "").strip()
        formula = (request.args.get("formula") or "").strip()
        if not name and not formula:
            return jsonify({"result": "failure", "message": "請提供名稱或分子式"}), 400

        results = pubchem.lookup_by_name(name) if name else pubchem.lookup_by_formula(formula)
        return jsonify({"results": results, "found": len(results) > 0})
    except Exception as e:
        return jsonify({"result": "failure", "message": f"查詢失敗：{e}"}), 502


@admin_bp.route("/admin/molecules", methods=["GET", "POST"])
@login_required
def manage_molecules():
    if request.method == "GET":
        try:
            return jsonify({"molecules": normalize_molecules(show_fdb(MOLECULES_NODE),
                                                             include_drafts=True)})
        except Exception as e:
            return jsonify({"result": "failure", "message": str(e)}), 500

    try:
        payload = request.get_json() or {}
        slug, record = serialize_molecule(payload)
        if not slug:
            return jsonify({"result": "failure", "message": record}), 400

        # 改過 slug 時刪掉舊的那筆，避免留下孤兒
        original = molecule_slug(payload.get("original_slug") or "")
        if original and original != slug:
            fdb.child(MOLECULES_NODE).child(original).delete()

        record["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        fdb.child(MOLECULES_NODE).child(slug).set(record)
        return jsonify({"result": "success", "message": "分子已儲存", "slug": slug})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/molecules/<slug>", methods=["DELETE"])
@login_required
def delete_molecule(slug):
    try:
        safe = molecule_slug(slug)
        if not safe:
            return jsonify({"result": "failure", "message": "無效的網址代稱"}), 400
        fdb.child(MOLECULES_NODE).child(safe).delete()
        return jsonify({"result": "success", "message": "分子已刪除"})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/pages", methods=["GET", "POST"])
@login_required
def manage_pages():
    if request.method == "GET":
        try:
            return jsonify({"pages": normalize_pages(show_fdb(PAGES_NODE), include_drafts=True)})
        except Exception as e:
            return jsonify({"result": "failure", "message": str(e)}), 500

    # POST：新增或更新單一頁面
    try:
        payload = request.get_json() or {}
        slug, record = serialize_page(payload)
        if not slug:
            return jsonify({"result": "failure", "message": record}), 400

        # 改過 slug 時要把舊的那筆刪掉，否則會留下孤兒頁面
        original = normalize_slug(payload.get("original_slug"))
        if original and original != slug:
            fdb.child(PAGES_NODE).child(original).delete()

        record["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        fdb.child(PAGES_NODE).child(slug).set(record)
        return jsonify({"result": "success", "message": "頁面已儲存", "slug": slug})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/pages/<slug>", methods=["DELETE"])
@login_required
def delete_page(slug):
    try:
        safe = normalize_slug(slug)
        if not safe:
            return jsonify({"result": "failure", "message": "無效的網址代稱"}), 400
        fdb.child(PAGES_NODE).child(safe).delete()
        return jsonify({"result": "success", "message": "頁面已刪除"})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


SITE_SETTINGS_FIELDS = ("title", "subtitle", "description", "frame_style", "layer_bg", "electron_size")
# 每個元素最多幾張「其他樣貌」。圖片以 base64 存進 Realtime DB，
# 不設上限的話很容易把免費方案的額度吃掉。
GALLERY_MAX = 6


@admin_bp.route("/admin/elements/<symbol>/gallery", methods=["GET", "POST"])
@login_required
def manage_gallery(symbol):
    if request.method == "GET":
        try:
            return jsonify({"images": normalize_gallery(show_fdb(f"_gallery/{symbol}"))})
        except Exception as e:
            return jsonify({"result": "failure", "message": str(e)}), 500

    # POST：整批覆寫，前端送完整清單（含排序結果）
    try:
        data = request.get_json() or {}
        images = data.get("images")
        if not isinstance(images, list):
            images = []
        if len(images) > GALLERY_MAX:
            return jsonify({
                "result": "failure",
                "message": f"最多只能放 {GALLERY_MAX} 張，目前有 {len(images)} 張"
            }), 400

        cleaned = []
        for item in images:
            if not isinstance(item, dict):
                continue
            img_data = (item.get("img_data") or "").strip()
            if not img_data:
                continue
            cleaned.append({
                "img_data": img_data,
                "caption": (item.get("caption") or "").strip(),
            })

        fdb.child("_gallery").child(symbol).set(cleaned)
        return jsonify({"result": "success", "message": "Gallery updated!", "count": len(cleaned)})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/site-settings", methods=["GET", "POST"])
@login_required
def manage_site_settings():
    if request.method == "GET":
        try:
            data = show_fdb("_site_settings") or {}
            result = {f: data.get(f, "") for f in SITE_SETTINGS_FIELDS}
            result["frame_style"] = data.get("frame_style") or "classic"
            # 分層圖是去背 PNG，需要一個底色才看得清楚；預設白色
            result["layer_bg"] = data.get("layer_bg") or "#ffffff"
            result["electron_size"] = data.get("electron_size") or 24
            result["bg_image"] = data.get("bg_image", "")
            result["frame_image"] = data.get("frame_image", "")
            return jsonify(result)
        except Exception as e:
            return jsonify({"result": "failure", "message": str(e)}), 500

    # POST：文字欄位走 JSON，背景圖走 multipart
    try:
        existing = show_fdb("_site_settings") or {}
        payload = dict(existing)

        if request.content_type and request.content_type.startswith("multipart/"):
            for f in SITE_SETTINGS_FIELDS:
                if f in request.form:
                    payload[f] = (request.form.get(f) or "").strip()

            for field, clear_flag in (("bg_image", "clear_bg_image"), ("frame_image", "clear_frame_image")):
                image = request.files.get(field)
                if image and image.filename:
                    # 外框圖需要透明背景，一律存 PNG；背景圖沿用 JPEG
                    mime = "image/png" if field == "frame_image" else "image/jpeg"
                    payload[field] = (
                        f"data:{mime};base64,"
                        + base64.b64encode(image.read()).decode("utf-8")
                    )
                elif request.form.get(clear_flag) == "1":
                    payload[field] = ""
        else:
            data = request.get_json() or {}
            for f in SITE_SETTINGS_FIELDS:
                if f in data:
                    payload[f] = (data.get(f) or "").strip()
            if data.get("clear_bg_image"):
                payload["bg_image"] = ""

        upload_fdb("_site_settings", payload)
        return jsonify({"result": "success", "message": "Site settings updated!"})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/creator-links", methods=["GET", "POST"])
@login_required
def manage_creator_links():
    if request.method == "GET":
        try:
            data = show_fdb("_creator_links")
            return jsonify(normalize_creator_links(data))
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
            # 未發布的草稿；前台不會讀到，只有後台編輯時會帶出來
            draftDatas = {
                data: fbDatas[data].get("draft", "")
                for data in symbols if fbDatas[data].get("draft")
            }
            # Storage 關閉時圖片只存在 img_data(base64)，兩者任一有值就算已上傳
            hasImage = {
                data: bool(fbDatas[data].get("img") or fbDatas[data].get("img_data"))
                for data in symbols
            }
            elements_data = get_periodic_table()
            elements = [e["Symbol"] for e in elements_data]
            # 圖層設定要依電子組態算出最外層電子數
            configurations = {
                e["Symbol"]: e.get("ElectronConfiguration", "") for e in elements_data
            }
            return jsonify(
                {
                    "elements": elements,
                    "imageDatas": imageDatas,
                    "storyDatas": storyDatas,
                    "draftDatas": draftDatas,
                    "hasImage": hasImage,
                    "configurations": configurations,
                }
            )
        except Exception as e:
            return jsonify({"result": "failure", "message": str(e)}), 500

    # POST
    try:
        symbol = request.form.get("symbol")
        story = request.form.get("stroy")  # kept original field name for compat
        image = request.files.get("image")
        # 草稿：內容存起來但不對外顯示，前台仍看到上一次發布的版本
        is_draft = request.form.get("draft") == "1"
        # 首頁「最近更新」用；UTC ISO 8601
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        has_story = bool((story or "").strip())

        if is_draft:
            # 只寫進 draft 欄位，不動 description 與圖片
            fdb.child(symbol).update({"draft": story, "draft_updated_at": now})
            return jsonify({"result": "success", "message": "草稿已儲存"})

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

            fdb.child(symbol).update({
                "img": img,
                "img_data": img_data,
                "description": story,
                "updated_at": now,
                # 已正式發布，草稿不再需要
                "draft": "",
                "draft_updated_at": "",
            })
            update_completion(symbol, {"story": has_story, "image": True, "updated_at": now})
        else:
            # 沒有選新圖片時完全不碰 img / img_data。
            # 原本的做法是先把整個 DB 讀回來取出舊圖再整筆覆寫，只要那次
            # 讀取出問題，既有圖片就會被空字串蓋掉。
            fdb.child(symbol).update({
                "description": story, "updated_at": now,
                "draft": "", "draft_updated_at": ""
            })
            update_completion(symbol, {"story": has_story, "updated_at": now})

        return jsonify({"result": "success", "message": "Finish!"})

    except Exception as e:
        print(e)
        return jsonify({"result": "failure", "message": str(e)}), 500
