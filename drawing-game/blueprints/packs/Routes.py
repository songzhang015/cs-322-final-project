from flask import Blueprint, jsonify, request
from services.PackService import pack_service

packs_bp = Blueprint("packs", __name__)

@packs_bp.route("/packs", methods=["GET"])
def get_all_packs():
    """
    GET /api/packs
    Returns a list of all packs and their names + words.

    Response:
    {
        "success": True,
        "data": [
            {
                "name": "standard-pack",
                "words": ["lion", "frog", "hare", ...]
            }
            ...
        ]
    }
    """
    try:
        packs = pack_service.get_all_packs()
        return jsonify({"success": True, "data": packs}), 200
    except Exception:
        return jsonify({"success": False, "error": "Server error"}), 500

@packs_bp.route("/packs", methods=["POST"])
def create_pack():
    """
    POST /api/packs
    Creates a new pack via name and word list.

    Request:
    {
        "name": "new-pack",
        "words": ["lion", "tiger", "bear", ...]
    }

    Response:
    {
        "success": True,
        "message": "Pack new-pack successfully created."
    }
    """
    data = request.get_json()

    pack_name = data.get("name")
    words = data.get("words")

    if not pack_name:
        return jsonify({"success": False, "error": "Missing name"}), 400
    if words is None:
        return jsonify({"success": False, "error": "Missing words array"}), 400
    if not isinstance(words, list):
        return jsonify({"success": False, "error": "words must be a list"}), 400

    try:
        pack_service.create_pack(pack_name, words)

        return jsonify({
            "success": True,
            "message": f"Pack {pack_name} successfully created.",
        }), 201
    except FileExistsError as e:
        return jsonify({"success": False, "error": str(e)}), 409
    except Exception:
        return jsonify({"success": False, "error": "Server error"}), 500


@packs_bp.route("/packs/<pack_name>", methods=["GET"])
def get_pack(pack_name):
    """
    GET /api/packs/<pack_name>
    Returns a pack with list of words using the pack name

    Response:
    {
        "success": True,
        "data": {
            "name": "standard-pack",
            "words": ["lion", "frog", "hare", ...]
        }
    }
    """
    try:
        pack = pack_service.get_pack(pack_name)
        return jsonify({"success": True, "data": pack}), 200
    except LookupError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@packs_bp.route("/packs/<pack_name>", methods=["DELETE"])
def delete_pack(pack_name):
    """
    DELETE /api/packs/<pack_name>
    Deletes a pack from the DB by name.

    Response:
    {
        "success": True,
        "message": "Pack new-pack deleted."
    }
    """
    try:
        pack_service.delete_pack(pack_name)
        return jsonify({"success": True, "message": f"Pack {pack_name} deleted."}), 200
    except LookupError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception:
        return jsonify({"success": False, "error": "Server error"}), 500


@packs_bp.route("/packs/<pack_name>/words", methods=["POST"])
def add_word_to_pack(pack_name):
    """
    POST /packs/<pack_name>/words
    Inserts a new word to a specified pack

    Request:
    {
        "word": "dog"
    }

    Response:
    {
        "success": True,
        "message": "Word dog successfully added to test-pack."
    }
    """
    data = request.get_json()
    word = data.get("word")

    if not word:
        return jsonify({"error": "Missing word"}), 400

    try:
        pack_service.add_word(pack_name, word)
        return jsonify({
            "success": True,
            "message": f"Word {word} successfully added to {pack_name}.",
        }), 200
    except LookupError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception:
        return jsonify({"success": False, "error": "Server error"}), 500


@packs_bp.route("/packs/<pack_name>/words/<word>", methods=["DELETE"])
def delete_word_from_pack(pack_name, word):
    """
    DELETE /api/packs/<pack_name>/words/<word>
    Deletes a word from a specified pack.

    Response:
    {
        "success": True,
        "message": "Word dog removed from test-pack."
    }
    """
    try:
        pack_service.delete_word(pack_name, word)
        return jsonify({
            "success": True,
            "message": f"Word {word} removed from {pack_name}."
        }), 200
    except LookupError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception:
        return jsonify({"success": False, "error": "Server error"}), 500