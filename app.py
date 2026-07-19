from flask import Flask, request, jsonify, send_from_directory
import os
import re
import json
import random
import string
from datetime import datetime


app = Flask(__name__)

RECIPES_FILE = "data/recipes.json"
GAMES_FILE = "data/jeopardy.json"


def load_json(path):
    if not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    os.makedirs("data", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_recipes():
    return load_json(RECIPES_FILE).get("recipes", [])


def save_recipes(recipes):
    save_json(RECIPES_FILE, {"recipes": recipes})


def load_games():
    return load_json(GAMES_FILE).get("games", [])


def save_games(games):
    save_json(GAMES_FILE, {"games": games})


def gen_code(length=6):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))


ALLOWED_EXT = {".html", ".css", ".js", ".json", ".py", ".md", ".txt"}


@app.route("/")
def home():
    return send_from_directory(".", "index.html")


@app.route("/<path:file>")
def files(file):
    return send_from_directory(".", file)


@app.get("/api/recipes")
def all_recipes():
    recipes = load_recipes()
    return jsonify([{"id": r["id"], "title": r["title"], "tags": r.get("tags", "")} for r in recipes])


@app.get("/api/recipes/<int:id>")
def one_recipe(id):
    recipes = load_recipes()
    for r in recipes:
        if r["id"] == id:
            return jsonify(r)
    return jsonify({"error": "not found"}), 404


@app.post("/api/recipes")
def create():
    data = request.json
    recipes = load_recipes()
    new_id = max((r["id"] for r in recipes), default=0) + 1
    recipe = {
        "id": new_id,
        "title": data.get("title", ""),
        "tags": data.get("tags", ""),
        "servings": data.get("servings", 0),
        "ingredients": data.get("ingredients", ""),
        "instructions": data.get("instructions", ""),
        "nutrition": data.get("nutrition", ""),
    }
    recipes.append(recipe)
    save_recipes(recipes)
    return jsonify({"id": new_id})


@app.put("/api/recipes/<int:id>")
def update(id):
    data = request.json
    recipes = load_recipes()
    for r in recipes:
        if r["id"] == id:
            r["title"] = data["title"]
            r["tags"] = data["tags"]
            r["servings"] = data["servings"]
            r["ingredients"] = data["ingredients"]
            r["instructions"] = data["instructions"]
            r["nutrition"] = data["nutrition"]
            save_recipes(recipes)
            return jsonify({"ok": True})
    return jsonify({"error": "not found"}), 404


@app.delete("/api/recipes/<int:id>")
def delete(id):
    recipes = load_recipes()
    recipes = [r for r in recipes if r["id"] != id]
    save_recipes(recipes)
    return jsonify({"ok": True})


@app.get("/api/games")
def list_games():
    games = load_games()
    return jsonify([{
        "game_code": g["game_code"],
        "name": g["name"],
        "created_at": g.get("created_at", ""),
    } for g in games])


@app.post("/api/games/create")
def create_game():
    data = request.json
    name = (data.get("name") or "").strip()
    password = (data.get("password") or "").strip()
    custom_code = (data.get("game_code") or "").strip()
    if not name:
        return jsonify({"error": "Game name is required"}), 400
    if not password:
        password = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    if not re.match(r'^[A-Za-z0-9]+$', password):
        return jsonify({"error": "Password must be alphanumeric only (letters and numbers)"}), 400

    games = load_games()
    if custom_code:
        code = custom_code.upper().replace(" ", "")
        if any(g["game_code"].upper() == code for g in games):
            return jsonify({"error": "Game code already exists"}), 400
    else:
        code = gen_code()
        while any(g["game_code"] == code for g in games):
            code = gen_code()

    games.append({
        "game_code": code,
        "name": name,
        "password": password,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "categories": [],
        "cards": [],
        "team_count": 3,
        "values": [100, 200, 300, 400, 500],
    })
    save_games(games)
    return jsonify({"game_code": code, "name": name, "password": password})


@app.post("/api/games/validate")
def validate_game():
    data = request.json
    code = (data.get("game_code") or "").strip().upper()
    password = (data.get("password") or "").strip()
    games = load_games()
    for g in games:
        if g["game_code"].upper() == code.upper() and g["password"] == password:
            return jsonify({"ok": True, "game_code": g["game_code"], "name": g["name"]})
    return jsonify({"error": "Invalid game code or password"}), 401


@app.get("/api/games/<code>/data")
def get_game_data(code):
    password = request.args.get("password", "").strip()
    games = load_games()
    for g in games:
        if g["game_code"].upper() == code.upper() and g["password"] == password:
            return jsonify({
                "name": g["name"],
                "categories": g.get("categories", []),
                "cards": g.get("cards", []),
                "teamCount": g.get("team_count", 3),
                "values": g.get("values", [100, 200, 300, 400, 500]),
            })
    return jsonify({"error": "Unauthorized"}), 401


@app.post("/api/games/<code>/data")
def save_game_data(code):
    data = request.json
    password = data.pop("password", "").strip()
    games = load_games()
    for g in games:
        if g["game_code"].upper() == code.upper() and g["password"] == password:
            g["categories"] = data.get("categories", [])
            g["cards"] = data.get("cards", [])
            g["team_count"] = data.get("teamCount", 3)
            g["values"] = data.get("values", [100, 200, 300, 400, 500])
            save_games(games)
            return jsonify({"ok": True})
    return jsonify({"error": "Unauthorized"}), 401


@app.delete("/api/games/<code>")
def delete_game(code):
    games = load_games()
    games = [g for g in games if g["game_code"].upper() != code.upper()]
    save_games(games)
    return jsonify({"ok": True})


@app.get("/admin")
def admin_page():
    return send_from_directory(".", "admin.html")


@app.get("/code")
def code_admin_page():
    return send_from_directory(".", "code-admin.html")


@app.get("/api/admin/files")
def list_files():
    files = []
    for f in os.listdir("."):
        if os.path.isfile(f) and os.path.splitext(f)[1] in ALLOWED_EXT:
            files.append(f)
    return jsonify(files)


@app.get("/api/admin/file/<path:filename>")
def read_file(filename):
    ext = os.path.splitext(filename)[1]
    if ext not in ALLOWED_EXT:
        return jsonify({"error": "not allowed"}), 403
    if not os.path.isfile(filename):
        return jsonify({"error": "not found"}), 404
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()
    return jsonify({"filename": filename, "content": content})


@app.post("/api/admin/file/<path:filename>")
def save_file(filename):
    ext = os.path.splitext(filename)[1]
    if ext not in ALLOWED_EXT:
        return jsonify({"error": "not allowed"}), 403
    data = request.json
    content = data.get("content", "")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
