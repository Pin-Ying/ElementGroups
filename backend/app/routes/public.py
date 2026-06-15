import io
import json

from flask import Blueprint, jsonify, make_response, request, send_file

from app.elements import get_atomicOrbital, get_characteristic, get_abMax
from app.firebase import show_fdb, get_periodic_table, get_element_by_symbol, get_element_by_atomic_number, get_image_bytes

public_bp = Blueprint("public", __name__, url_prefix="/api")


@public_bp.route("/elements", methods=["GET"])
def get_elements():
    try:
        elements_data = get_periodic_table()
        elements = [
            {"AtomicNumber": e["AtomicNumber"], "Symbol": e["Symbol"], "Name": e.get("Name", ""), "CPKHexColor": e["CPKHexColor"]}
            for e in elements_data
        ]
        groups = get_characteristic()
    except Exception as e:
        return jsonify({"result": "failure", "exception": str(e)}), 500

    return jsonify({"elements": elements, "groups": groups})


@public_bp.route("/groups", methods=["POST"])
def get_groups():
    body = request.get_json()
    group_type = body.get("groupType")

    elements_data = get_periodic_table()
    elements = [
        {"AtomicNumber": e["AtomicNumber"], "Symbol": e["Symbol"], "Name": e.get("Name", ""), "CPKHexColor": e["CPKHexColor"]}
        for e in elements_data
    ]

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
