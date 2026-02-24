import base64
import os
import tempfile

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app import auth as auth_module
from app.elements import element_info
from app.firebase import show_fdb, upload_fdb, upload_file, periodic_table_exists, upload_periodic_table, get_periodic_table, get_image_bytes, fdb

admin_bp = Blueprint("admin", __name__, url_prefix="/api")


@admin_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"result": "failure", "message": "Missing request body"}), 400

    email = data.get("email")
    password = data.get("password")
    result = auth_module.login(email, password)

    if result == "Login successful":
        return jsonify({"result": "success", "message": result})
    return jsonify({"result": "failure", "message": result}), 401


@admin_bp.route("/auth/logout", methods=["POST"])
def logout():
    auth_module.logout()
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

        updated = 0
        skipped = 0
        for symbol, data in fbDatas.items():
            if symbol == "periodic_table":
                continue
            if data.get("img_data"):
                skipped += 1
                continue
            if not data.get("img"):
                continue

            img_bytes, _ = get_image_bytes(symbol)
            if img_bytes is None:
                continue

            img_data = "data:image/jpeg;base64," + base64.b64encode(img_bytes).decode("utf-8")
            fdb.child(symbol).update({"img_data": img_data})
            updated += 1

        return jsonify({
            "result": "success",
            "message": f"完成！新增 {updated} 筆，{skipped} 筆已有資料略過",
            "updated": updated
        })
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
            imageDatas = {data: fbDatas[data].get("img", "") for data in fbDatas if data != "periodic_table"}
            storyDatas = {data: fbDatas[data].get("description", "") for data in fbDatas if data != "periodic_table"}
            elements_data = get_periodic_table()
            elements = [e["Symbol"] for e in elements_data]
            return jsonify(
                {
                    "elements": elements,
                    "imageDatas": imageDatas,
                    "storyDatas": storyDatas,
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
            filename = f"static/img/{symbol}.JPG"
            temp = tempfile.NamedTemporaryFile(delete=False)
            image.save(temp.name)
            img = upload_file(temp.name, filename)
            with open(temp.name, "rb") as f:
                img_data = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("utf-8")
            temp.close()
            os.remove(temp.name)
        else:
            img = imageDatas.get(symbol, "")
            img_data = fbDatas.get(symbol, {}).get("img_data", "")

        upload_fdb(symbol, {"img": img, "img_data": img_data, "description": story})
        return jsonify({"result": "success", "message": "Finish!"})

    except Exception as e:
        print(e)
        return jsonify({"result": "failure", "message": str(e)}), 500
