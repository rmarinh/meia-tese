"""Minimal Flask API for testing TestForge.

Run with: python demo_app.py
"""

from flask import Flask, jsonify, request

app = Flask(__name__)

# In-memory data store
users_db: dict[int, dict] = {}
next_id = 1


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/users", methods=["GET"])
def list_users():
    return jsonify({"users": list(users_db.values()), "total": len(users_db)})


@app.route("/api/users", methods=["POST"])
def create_user():
    global next_id
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    if "name" not in data:
        return jsonify({"error": "Name is required"}), 400

    if "email" not in data:
        return jsonify({"error": "Email is required"}), 400

    # Check duplicate email
    for user in users_db.values():
        if user["email"] == data["email"]:
            return jsonify({"error": "Email already exists"}), 409

    user = {
        "id": next_id,
        "name": data["name"],
        "email": data["email"],
        "role": data.get("role", "user"),
    }
    users_db[next_id] = user
    next_id += 1

    return jsonify(user), 201


@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = users_db.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user)


@app.route("/api/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    user = users_db.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    if "name" in data:
        user["name"] = data["name"]
    if "email" in data:
        user["email"] = data["email"]
    if "role" in data:
        user["role"] = data["role"]

    return jsonify(user)


@app.route("/api/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = users_db.pop(user_id, None)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"message": "User deleted"}), 200


@app.route("/api/users/search", methods=["GET"])
def search_users():
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    results = [
        u for u in users_db.values()
        if query.lower() in u["name"].lower() or query.lower() in u["email"].lower()
    ]
    return jsonify({"users": results, "total": len(results)})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
