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
from app.gallery import normalize_gallery, GALLERY_NODE
from app.pages import normalize_pages, serialize_page, normalize_slug, PAGES_NODE
from app.molecules import normalize_molecules, serialize_molecule, normalize_slug as molecule_slug, MOLECULES_NODE
from app.page_meta import PAGE_META_NODE, META_KEYS, normalize_meta
from app.particles import normalize_particles, serialize_particle, normalize_slug as particle_slug, PARTICLES_NODE
from app import pubchem
from app.groups import GROUPS_NODE, GROUP_KEYS, normalize_group, normalize_groups, serialize_group, group_key_for, has_content as group_has_content
from app.layers import normalize_layers, serialize_layers, normalize_electron_styles, normalize_motion, LAYERS_NODE, ELECTRON_STYLES_NODE, ELECTRON_DEFAULT_NODE, MOTION_NODE, MOTIONS
from app.firebase import show_fdb, upload_fdb, upload_file, periodic_table_exists, upload_periodic_table, get_periodic_table, get_image_bytes, get_element_by_symbol, fdb
from app.libraries import (normalize_libraries, serialize_library, bindable_definitions,
                           libraries_for, find_library, library_id_for, primary_image_data,
                           targets_from_node,
                           BINDABLE_TYPES, LIBRARIES_NODE, MAX_IMAGES)
from app import ai
from app import watermark

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


@admin_bp.route("/auth/google", methods=["POST"])
def login_google():
    data = request.get_json() or {}
    token, message = auth_module.login_with_google(data.get("idToken"))

    if token:
        return jsonify({"result": "success", "message": message, "token": token})
    return jsonify({"result": "failure", "message": message}), 401


@admin_bp.route("/auth/firebase-config", methods=["GET"])
def firebase_config():
    """前端初始化 Firebase SDK 需要的設定。

    公開端點，理由和 /api/ai/status 一樣：這些值依設計就不是機密（它們會
    出現在任何用 Firebase 的網站的前端程式碼裡），擋住 Firebase 的是安全
    規則與 ADMIN_ACCOUNTS，不是把 apiKey 藏起來。做成端點而不是 build 時
    注入，是因為後端已經有這些值了，站長不必再去 Render 的前端服務設一次
    VITE_ 變數——設定只有一處，換 Firebase 專案時也只改一個地方。

    沒啟用就只回 enabled: false，前端據此不顯示按鈕，也不會下載 SDK。
    """
    if not settings.GOOGLE_LOGIN_ENABLED:
        return jsonify({"enabled": False})

    return jsonify({
        "enabled": True,
        "config": {
            "apiKey": settings.FIREBASE_API_KEY,
            "authDomain": settings.FIREBASE_AUTH_DOMAIN,
            "projectId": settings.FIREBASE_PROJECT_ID,
            "appId": settings.FIREBASE_APP_ID,
            "messagingSenderId": settings.FIREBASE_MESSAGING_SENDER_ID,
        }
    })


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


@admin_bp.route("/admin/ai/suggest", methods=["POST"])
@login_required
def ai_suggest():
    """所有 AI 建議共用的端點。

    kind 決定用哪個提示模板（見 app/ai.py 的 SUGGEST_KINDS），context 是
    該用途需要的資料。新增用途不必再開一支端點。
    """
    data = request.get_json() or {}
    try:
        text, used, limit = ai.suggest(
            (data.get("kind") or "").strip(),
            context=data.get("context") or {},
            draft=(data.get("draft") or "").strip(),
            direction=(data.get("direction") or "").strip(),
        )
        return jsonify({"result": "success", "suggestion": text, "used": used, "limit": limit})
    except ValueError as e:
        # 輸入問題（不認得的 kind、缺主題、找不到元素）算 400
        return jsonify({"result": "failure", "message": str(e)}), 400
    except RuntimeError as e:
        # 未啟用或額度用盡
        return jsonify({"result": "failure", "message": str(e)}), 400
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
        img_data = watermark.mark_data_url(
            "data:image/jpeg;base64," + base64.b64encode(image_bytes).decode("utf-8"),
            origin_path="_default/img_data")
        # Storage 送的要是套過浮水印的那份，否則 /api/elements/…/img 會漏出乾淨的原圖
        image_bytes = base64.b64decode(img_data.split(",", 1)[1])

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


@admin_bp.route("/admin/electron-styles", methods=["GET", "POST"])
@login_required
def manage_electron_styles():
    """共用的電子樣式庫。同一種畫法可以套用到任何元素。"""
    if request.method == "GET":
        try:
            return jsonify({
                "styles": normalize_electron_styles(show_fdb(ELECTRON_STYLES_NODE)),
                "default_id": show_fdb(ELECTRON_DEFAULT_NODE) or ""
            })
        except Exception as e:
            return jsonify({"result": "failure", "message": str(e)}), 500

    try:
        data = request.get_json() or {}
        name = (data.get("name") or "").strip()
        img_data = (data.get("img_data") or "").strip()
        if not img_data:
            return jsonify({"result": "failure", "message": "請選擇圖片"}), 400

        style_id = (data.get("id") or "").strip()
        if not style_id:
            # 用時間戳當 id，避免與既有樣式衝突
            style_id = datetime.datetime.now(datetime.timezone.utc).strftime("s%Y%m%d%H%M%S%f")

        fdb.child(ELECTRON_STYLES_NODE).child(style_id).set(watermark.mark_payload({
            "name": name or style_id,
            "img_data": img_data,
        }, origin_path=f"{ELECTRON_STYLES_NODE}/{style_id}"))
        return jsonify({"result": "success", "message": "電子樣式已儲存", "id": style_id})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/electron-styles/default", methods=["POST"])
@login_required
def set_default_electron_style():
    """設定全站預設電子樣式；元素沒有各自指定時就用它。"""
    try:
        style_id = ((request.get_json() or {}).get("id") or "").strip()
        fdb.child(ELECTRON_DEFAULT_NODE).set(style_id)
        return jsonify({"result": "success", "message": "已設為預設電子" if style_id else "已取消預設"})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/electron-styles/<style_id>", methods=["DELETE"])
@login_required
def delete_electron_style(style_id):
    try:
        fdb.child(ELECTRON_STYLES_NODE).child(style_id).delete()
        # 刪掉的正好是預設時要一併清除，否則會指向不存在的樣式
        if (show_fdb(ELECTRON_DEFAULT_NODE) or "") == style_id:
            fdb.child(ELECTRON_DEFAULT_NODE).set("")
        return jsonify({"result": "success", "message": "電子樣式已刪除"})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/electron-styles/migrate", methods=["POST"])
@login_required
def migrate_electron_styles():
    """把 `_electron_styles` 搬進通用圖庫，成為綁在「基本粒子／電子」的一個庫。

    刻意保留原本的樣式 id 當作圖片 id：每個元素的 `_layers/{symbol}.electron_style`
    存的就是那些 id，保留下來搬遷前後才指得到同一張圖。

    舊節點不刪除——確認新的沒問題之前留著當退路，前台也是找不到圖庫才會退回去讀它。
    """
    try:
        styles = normalize_electron_styles(show_fdb(ELECTRON_STYLES_NODE))
        if not styles:
            return jsonify({"result": "failure", "message": "沒有可搬移的電子樣式"}), 400

        existing = libraries_for(normalize_libraries(show_fdb(LIBRARIES_NODE)), "particle", "electron")
        if existing:
            return jsonify({"result": "failure", "message": "電子的圖庫已經存在，請直接到「圖庫管理」編輯"}), 400

        images = {
            style["id"]: {"name": style["name"], "img_data": style["img_data"], "order": order}
            for order, style in enumerate(styles)
        }

        default_id = (show_fdb(ELECTRON_DEFAULT_NODE) or "").strip()
        library_id = "particle-electron"
        fdb.child(LIBRARIES_NODE).child(library_id).set({
            "name": "電子",
            "bind_type": "particle",
            "bind_id": "electron",
            "default_image": default_id if default_id in images else "",
            "images": images,
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        })
        return jsonify({
            "result": "success",
            "message": f"已搬移 {len(images)} 張到圖庫",
            "id": library_id,
        })
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/libraries/migrate/<bind_type>", methods=["POST"])
@login_required
def migrate_into_libraries(bind_type):
    """把某一類對象身上的單張 img_data 搬進通用圖庫，一個對象一個庫。

    是泛型的：接點註冊表已經知道節點在哪、識別碼與名稱怎麼取、圖存在哪個
    欄位，所以不必為每一類各寫一支。要讓新的類型也能搬，在 BINDABLE_TYPES
    補上 image_field 就好。

    對象已經有圖庫時是「併入」而不是新建——同一個對象的各種樣貌本來就該在
    同一個庫裡。圖片內容已存在時略過，重複執行安全。
    """
    cfg = BINDABLE_TYPES.get(bind_type)
    if not cfg:
        return jsonify({"result": "failure", "message": "不認得的綁定類型"}), 400
    if not cfg.get("image_field"):
        return jsonify({"result": "failure", "message": f"{cfg['label']}沒有可搬移的單張圖欄位"}), 400

    try:
        targets = targets_from_node(bind_type, show_fdb(cfg["node"]))
        libraries = normalize_libraries(show_fdb(LIBRARIES_NODE))

        created, merged, skipped = 0, 0, 0
        for target in targets:
            if not target["image"]:
                continue

            library = find_library(libraries, bind_type, target["id"])
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()

            if not library:
                fdb.child(LIBRARIES_NODE).child(library_id_for(bind_type, target["id"])).set({
                    "name": target["name"],
                    "bind_type": bind_type,
                    "bind_id": target["id"],
                    "default_image": "img-0",
                    "images": {"img-0": {"name": target["name"], "img_data": target["image"], "order": 0}},
                    "updated_at": now,
                })
                created += 1
                continue

            if any(i["img_data"] == target["image"] for i in library["images"]):
                skipped += 1
                continue

            order = len(library["images"])
            fdb.child(LIBRARIES_NODE).child(library["id"]).child("images").update({
                f"img-{bind_type}-{order}": {
                    "name": target["name"], "img_data": target["image"], "order": order,
                }
            })
            fdb.child(LIBRARIES_NODE).child(library["id"]).update({"updated_at": now})
            merged += 1

        if not (created or merged or skipped):
            return jsonify({"result": "failure", "message": f"沒有可搬移的{cfg['label']}圖片"}), 400

        parts = []
        if created:
            parts.append(f"新建 {created} 個圖庫")
        if merged:
            parts.append(f"併入既有圖庫 {merged} 張")
        if skipped:
            parts.append(f"{skipped} 張已存在，略過")
        return jsonify({"result": "success", "message": "、".join(parts)})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/gallery/migrate", methods=["POST"])
@login_required
def migrate_galleries():
    """把 `_gallery/{Symbol}` 全部搬進通用圖庫，一個元素一個庫。

    caption 對應圖庫的 name。舊節點不刪除，留著當退路；已經有圖庫的元素
    會略過，不覆蓋你在圖庫裡的編輯。
    """
    try:
        all_galleries = show_fdb("_gallery") or {}
        if not isinstance(all_galleries, dict) or not all_galleries:
            return jsonify({"result": "failure", "message": "沒有可搬移的其他樣貌"}), 400

        existing = {l["bind_id"] for l in libraries_for(
            normalize_libraries(show_fdb(LIBRARIES_NODE)), "element")}

        migrated, skipped = 0, 0
        for symbol, raw in all_galleries.items():
            images = normalize_gallery(raw)
            if not images:
                continue
            if symbol in existing:
                skipped += 1
                continue

            fdb.child(LIBRARIES_NODE).child(library_id_for("element", symbol)).set({
                "name": f"{symbol} 其他樣貌",
                "bind_type": "element",
                "bind_id": symbol,
                "default_image": "",
                "images": {
                    f"img-{order}": {
                        "name": item.get("caption") or f"樣貌 {order + 1}",
                        "img_data": item["img_data"],
                        "order": order,
                    }
                    for order, item in enumerate(images)
                },
                "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            })
            migrated += 1

        if not migrated and not skipped:
            return jsonify({"result": "failure", "message": "沒有可搬移的其他樣貌"}), 400

        msg = f"已搬移 {migrated} 個元素的其他樣貌"
        if skipped:
            msg += f"（{skipped} 個已有圖庫，略過）"
        return jsonify({"result": "success", "message": msg, "migrated": migrated})
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
        fdb.child(LAYERS_NODE).child(symbol).update(
            watermark.mark_payload(record, origin_path=f"{LAYERS_NODE}/{symbol}"))
        return jsonify({"result": "success", "message": "圖層已儲存"})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/element-groups", methods=["GET"])
@login_required
def list_element_groups():
    try:
        groups = normalize_groups(show_fdb(GROUPS_NODE))
        libraries = normalize_libraries(show_fdb(LIBRARIES_NODE))
        for group in groups:
            from_library = primary_image_data(libraries, "group", group["key"])
            if from_library:
                group["img_data"] = from_library
            group["has_library"] = bool(from_library)
        return jsonify({"groups": groups})
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
        fdb.child(GROUPS_NODE).child(key).set(
            watermark.mark_payload(record, origin_path=f"{GROUPS_NODE}/{key}"))
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


@admin_bp.route("/admin/libraries", methods=["GET", "POST"])
@login_required
def manage_libraries():
    """通用圖庫。GET 一併回傳接點定義，前端不必自己重複一份。"""
    if request.method == "GET":
        try:
            return jsonify({
                "libraries": normalize_libraries(show_fdb(LIBRARIES_NODE)),
                "bindable": bindable_definitions(),
                "max_images": MAX_IMAGES,
            })
        except Exception as e:
            return jsonify({"result": "failure", "message": str(e)}), 500

    try:
        library_id, record = serialize_library(request.get_json() or {})
        if not library_id:
            return jsonify({"result": "failure", "message": record}), 400
        fdb.child(LIBRARIES_NODE).child(library_id).set(
            watermark.mark_payload(record, origin_path=f"{LIBRARIES_NODE}/{library_id}"))
        return jsonify({"result": "success", "message": "圖庫已儲存", "id": library_id})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/libraries/<library_id>", methods=["DELETE"])
@login_required
def delete_library(library_id):
    try:
        fdb.child(LIBRARIES_NODE).child(library_id).delete()
        return jsonify({"result": "success", "message": "圖庫已刪除"})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/bindable/<bind_type>", methods=["GET"])
@login_required
def bindable_targets(bind_type):
    """某個接點類型底下可以綁的對象清單，給後台下拉用。

    對象散在不同節點、識別欄位也不一樣，統一在這裡依 BINDABLE_TYPES 的
    定義取出來，前端只認得 {id, name}。
    """
    cfg = BINDABLE_TYPES.get(bind_type)
    if not cfg:
        return jsonify({"result": "failure", "message": "不認得的綁定類型"}), 400
    if cfg["node"] is None:
        return jsonify({"targets": []})

    try:
        targets = targets_from_node(bind_type, show_fdb(cfg["node"]))
        return jsonify({"targets": [{"id": t["id"], "name": t["name"]} for t in targets]})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/particles", methods=["GET", "POST"])
@login_required
def manage_particles():
    if request.method == "GET":
        try:
            particles = normalize_particles(show_fdb(PARTICLES_NODE), include_drafts=True)
            libraries = normalize_libraries(show_fdb(LIBRARIES_NODE))
            for particle in particles:
                from_library = primary_image_data(libraries, "particle", particle["slug"])
                if from_library:
                    particle["img_data"] = from_library
                # 讓後台知道這顆粒子的形象圖是不是由圖庫接管了
                particle["has_library"] = bool(from_library)
            return jsonify({"particles": particles})
        except Exception as e:
            return jsonify({"result": "failure", "message": str(e)}), 500

    try:
        payload = request.get_json() or {}
        slug, record = serialize_particle(payload)
        # 形象圖已由圖庫接管時，保留原本存著的舊值當退路，不要被前端送來的
        # （來自圖庫的）圖覆蓋，否則兩邊會慢慢長成不同的東西
        if slug and find_library(normalize_libraries(show_fdb(LIBRARIES_NODE)), "particle", slug):
            existing = show_fdb(f"{PARTICLES_NODE}/{slug}")
            if isinstance(existing, dict):
                record["img_data"] = (existing.get("img_data") or "").strip()
        if not slug:
            return jsonify({"result": "failure", "message": record}), 400

        original = particle_slug(payload.get("original_slug") or "")
        if original and original != slug:
            fdb.child(PARTICLES_NODE).child(original).delete()

        record["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        fdb.child(PARTICLES_NODE).child(slug).set(
            watermark.mark_payload(record, origin_path=f"{PARTICLES_NODE}/{slug}"))
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
        fdb.child(MOLECULES_NODE).child(slug).set(
            watermark.mark_payload(record, origin_path=f"{MOLECULES_NODE}/{slug}"))
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
        fdb.child(PAGES_NODE).child(slug).set(
            watermark.mark_payload(record, origin_path=f"{PAGES_NODE}/{slug}"))
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
    library = find_library(normalize_libraries(show_fdb(LIBRARIES_NODE)), "element", symbol)

    if request.method == "GET":
        try:
            # 搬進圖庫的元素改讀圖庫，回傳形狀不變，後台介面不必知道換了地方
            if library:
                return jsonify({"images": [
                    {"img_data": i["img_data"], "caption": i["name"]} for i in library["images"]
                ]})
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

        images = watermark.mark_payload(images, origin_path=f"{GALLERY_NODE}/{symbol}")
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

        # 已經搬進圖庫的元素要寫回圖庫，否則存了卻不生效
        if library:
            # 同一張圖沿用原本的 id，避免每次儲存都換 id
            by_img = {i["img_data"]: i["id"] for i in library["images"]}
            images_map = {}
            for order, item in enumerate(cleaned):
                image_id = by_img.get(item["img_data"]) or f"img-{order}-{int(datetime.datetime.now().timestamp() * 1000)}"
                images_map[image_id] = {
                    "name": item["caption"],
                    "img_data": item["img_data"],
                    "order": order,
                }
            fdb.child(LIBRARIES_NODE).child(library["id"]).update({
                "images": images_map,
                "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            })
        else:
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

        upload_fdb("_site_settings", watermark.mark_payload(payload, origin_path="_site_settings"))
        return jsonify({"result": "success", "message": "Site settings updated!"})
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/watermark", methods=["GET", "POST"])
@login_required
def manage_watermark():
    """隱形浮水印的設定（issue #25）。開關、簽名文字或自訂圖樣、強度。"""
    if request.method == "GET":
        try:
            return jsonify(watermark.load_settings())
        except Exception as e:
            return jsonify({"result": "failure", "message": str(e)}), 500

    try:
        record = watermark.save_settings(request.get_json() or {})
        return jsonify({"result": "success", "message": "浮水印設定已儲存", "settings": record})
    except ValueError as e:
        # 圖樣做不出來（沒填文字、沒有中文字型、圖樣整片空白）
        return jsonify({"result": "failure", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/watermark/preview", methods=["POST"])
@login_required
def preview_watermark():
    """拿一張圖試套，回傳套用前後與還原圖，用來調強度。不會存任何東西。"""
    try:
        settings_used = watermark.normalize(request.get_json() or {})
        img_data = ((request.get_json() or {}).get("img_data") or "").strip()
        image = watermark.decode_data_url(img_data)
        if image is None:
            return jsonify({"result": "failure", "message": "請選一張圖片"}), 400

        marked = watermark.embed(image, settings_used)
        return jsonify({
            "result": "success",
            "marked": watermark.encode_data_url(marked, keep_alpha="A" in marked.getbands()),
            "recovered": watermark.reveal_data_url(marked),
        })
    except ValueError as e:
        return jsonify({"result": "failure", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/watermark/repaint", methods=["GET", "POST"])
@login_required
def repaint_watermark():
    """換過簽名（或改了強度、關掉開關）之後，從備份的原圖把站上的圖重印一次。

    不能拿已經套過的圖再套一次——那只會疊上去，所以一定要從原圖重來。

    GET 回傳待處理的位置清單，POST 一次處理一個位置。一次做完會撞上 gunicorn
    的 30 秒上限，而且只有一個 worker（issue #28），整站會在那段時間沒反應；
    交給前端一個一個叫，順便還能顯示進度。
    """
    return _run_watermark_job(watermark.repaint_targets, watermark.repaint)


@admin_bp.route("/admin/watermark/backfill", methods=["GET", "POST"])
@login_required
def backfill_watermark():
    """把資料庫裡「原本就在」的圖片補上浮水印，順便備份原圖。

    開啟浮水印只影響之後上傳的圖。補過之後這些圖才有原圖備份，往後改簽名
    才能自動重印。

    與重印同一套分批做法（見 `_run_watermark_job`）。
    """
    return _run_watermark_job(watermark.backfill_targets, watermark.backfill)


def _run_watermark_job(list_targets, run_one):
    """浮水印的批次作業：GET 拿位置清單，POST 做其中一個位置的一批。

    做不完會回 more=True，前端帶著 offset 再叫一次同一個位置。一次做完會撞上
    gunicorn 的 30 秒上限，而且只有一個 worker（issue #28），整站會在那段時間
    沒反應。
    """
    if request.method == "GET":
        try:
            return jsonify({"targets": list_targets()})
        except Exception as e:
            return jsonify({"result": "failure", "message": str(e)}), 500

    try:
        data = request.get_json() or {}
        path = (data.get("path") or "").strip()
        # 只認清單裡的位置。這個值會被拿去組資料庫路徑，不驗的話等於開放
        # 「指定任意節點寫入」
        if path not in list_targets():
            return jsonify({"result": "failure", "message": "不認得這個位置"}), 400
        try:
            offset = max(0, int(data.get("offset") or 0))
        except (TypeError, ValueError):
            offset = 0
        count, more = run_one(path, offset=offset)
        return jsonify({"result": "success", "path": path, "count": count, "more": more})
    except ValueError as e:
        return jsonify({"result": "failure", "message": str(e)}), 400
    except Exception as e:
        # 印出來，否則失敗的細節只留在瀏覽器那端，伺服器日誌上一片空白
        import traceback
        print(f"watermark job failed at {path!r} offset={offset}: {e}")
        traceback.print_exc()
        return jsonify({"result": "failure", "message": f"{type(e).__name__}: {e}"}), 500


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
            img_data = watermark.mark_data_url(
                "data:image/jpeg;base64," + base64.b64encode(image_bytes).decode("utf-8"),
                origin_path=f"{symbol}/img_data")
            # 同上：Storage 那份也要有浮水印
            image_bytes = base64.b64decode(img_data.split(",", 1)[1])

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
