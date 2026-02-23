import json

from flask import Blueprint, jsonify, request

from app.elements import get_atomicOrbital, get_characteristic, get_abMax
from app.firebase import show_fdb, get_periodic_table, get_element_by_symbol, get_element_by_atomic_number

public_bp = Blueprint("public", __name__, url_prefix="/api")


@public_bp.route("/elements", methods=["GET"])
def get_elements():
    try:
        elements_data = get_periodic_table()
        elements = [
            {"AtomicNumber": e["AtomicNumber"], "Symbol": e["Symbol"], "CPKHexColor": e["CPKHexColor"]}
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
        {"AtomicNumber": e["AtomicNumber"], "Symbol": e["Symbol"], "CPKHexColor": e["CPKHexColor"]}
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
        img_src = None
        img_data = None
        alt_image = "https://firebasestorage.googleapis.com/v0/b/elementgroups-168e4.appspot.com/o/static%2Fimg%2FElectron.JPG?alt=media&token=134d2620-9424-4b60-ae8e-1854a5e76988"
        query = show_fdb(symbol)
        if query:
            story = query.get("description")
            img_src = query.get("img")
            img_data = query.get("img_data")

        return jsonify(
            {
                "el_info": el_info,
                "f_el": {"Symbol": f_el["Symbol"], "CPKHexColor": f_el["CPKHexColor"]},
                "b_el": {"Symbol": b_el["Symbol"], "CPKHexColor": b_el["CPKHexColor"]},
                "story": story,
                "img_src": img_src,
                "img_data": img_data,
                "alt_image": alt_image,
            }
        )

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
