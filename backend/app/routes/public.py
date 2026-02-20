import json

from flask import Blueprint, jsonify, request
from sqlalchemy import text

from app.elements import get_atomicOrbital, get_characteristic, get_abMax
from app.firebase import show_fdb
from app.models import sess

public_bp = Blueprint("public", __name__, url_prefix="/api")


@public_bp.route("/elements", methods=["GET"])
def get_elements():
    try:
        columns = ["AtomicNumber", "Symbol", "CPKHexColor"]
        datas = sess.execute(
            text(f'SELECT {",".join(columns)} FROM PeriodicTable')
        ).fetchall()
        elements = [dict(zip(columns, data)) for data in datas]
    except Exception:
        elements = []

    groups = get_characteristic()
    return jsonify({"elements": elements, "groups": groups})


@public_bp.route("/groups", methods=["POST"])
def get_groups():
    body = request.get_json()
    group_type = body.get("groupType")

    columns = ["AtomicNumber", "Symbol", "CPKHexColor"]
    datas = sess.execute(
        text(f'SELECT {",".join(columns)} FROM PeriodicTable')
    ).fetchall()
    elements = [dict(zip(columns, data)) for data in datas]

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
        sql_str = "SELECT name FROM PRAGMA_TABLE_INFO('PeriodicTable');"
        columns = sess.execute(text(sql_str)).fetchall()
        columns = [col[0] for col in columns]

        info = sess.execute(
            text("SELECT * FROM PeriodicTable WHERE Symbol=:symbol"),
            {"symbol": symbol},
        ).fetchone()

        if not info:
            return jsonify({"result": "failure", "exception": "Element not found"}), 404

        el_info = dict(zip(columns, info))
        el_AN = int(el_info["AtomicNumber"])

        # Previous element
        if el_AN != 1:
            f_info = sess.execute(
                text("SELECT * FROM PeriodicTable WHERE AtomicNumber=:an"),
                {"an": el_AN - 1},
            ).fetchone()
            f_el = dict(zip(columns, f_info)) if f_info else el_info
        else:
            f_el = el_info

        # Next element
        if el_AN != 118:
            b_info = sess.execute(
                text("SELECT * FROM PeriodicTable WHERE AtomicNumber=:an"),
                {"an": el_AN + 1},
            ).fetchone()
            b_el = dict(zip(columns, b_info)) if b_info else el_info
        else:
            b_el = el_info

        # Firebase story data
        story = None
        img_src = None
        alt_image = "https://firebasestorage.googleapis.com/v0/b/elementgroups-168e4.appspot.com/o/static%2Fimg%2FElectron.JPG?alt=media&token=134d2620-9424-4b60-ae8e-1854a5e76988"
        query = show_fdb(symbol)
        if query:
            story = query.get("description")
            img_src = query.get("img")

        return jsonify(
            {
                "el_info": el_info,
                "f_el": {"Symbol": f_el["Symbol"], "CPKHexColor": f_el["CPKHexColor"]},
                "b_el": {"Symbol": b_el["Symbol"], "CPKHexColor": b_el["CPKHexColor"]},
                "story": story,
                "img_src": img_src,
                "alt_image": alt_image,
            }
        )

    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500


@public_bp.route("/elements/<symbol>/ability", methods=["GET"])
def get_element_ability(symbol):
    try:
        sql_str = "SELECT name FROM PRAGMA_TABLE_INFO('PeriodicTable');"
        columns = sess.execute(text(sql_str)).fetchall()
        columns = [col[0] for col in columns]

        info = sess.execute(
            text("SELECT * FROM PeriodicTable WHERE Symbol=:symbol"),
            {"symbol": symbol},
        ).fetchone()

        if not info:
            return jsonify({"result": "failure", "exception": "Element not found"}), 404

        el_info = dict(zip(columns, info))
        abMax = get_abMax()
        el_info["abMax"] = abMax
        return json.dumps(el_info, ensure_ascii=False)

    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500
