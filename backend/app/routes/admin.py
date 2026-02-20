import os
import tempfile

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app import auth as auth_module
from app.elements import element_info
from app.firebase import show_fdb, upload_fdb, upload_file
from app.models import ElementGroups, alchemy_db, sess
from sqlalchemy import text

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


@admin_bp.route("/admin/create-db", methods=["POST"])
@login_required
def create_db():
    try:
        alchemy_db.create_all()
        return jsonify({"result": "success", "message": "create_db finish!"})
    except Exception as e:
        print("create_db error!", e)
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/update-db", methods=["POST"])
@login_required
def update_db():
    try:
        data = element_info()
        data.to_sql(
            "PeriodicTable", index=False, con=alchemy_db.engine, if_exists="replace"
        )
        return jsonify({"result": "success", "message": "update-db finish!"})
    except Exception as e:
        print("update-db error!", e)
        return jsonify({"result": "failure", "message": str(e)}), 500


@admin_bp.route("/admin/story", methods=["POST", "GET"])
@login_required
def update_story():
    if request.method == "GET":
        try:
            fbDatas = show_fdb()
            if not fbDatas:
                fbDatas = {}
            imageDatas = {data: fbDatas[data]["img"] for data in fbDatas}
            storyDatas = {data: fbDatas[data]["description"] for data in fbDatas}
            symbols = sess.execute(text("SELECT Symbol FROM PeriodicTable;")).fetchall()
            elements = [sym[0] for sym in symbols]
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
        imageDatas = {data: fbDatas[data]["img"] for data in fbDatas}

        if image and image.filename:
            filename = f"static/img/{symbol}.JPG"
            temp = tempfile.NamedTemporaryFile(delete=False)
            image.save(temp.name)
            img = upload_file(temp.name, filename)
            temp.close()
            os.remove(temp.name)
        else:
            img = imageDatas.get(symbol, "")

        ElementGroups.updateData(symbol=symbol, img=img, description=story)
        upload_fdb(symbol, {"img": img, "description": story})
        return jsonify({"result": "success", "message": "Finish!"})

    except Exception as e:
        print(e)
        return jsonify({"result": "failure", "message": str(e)}), 500
