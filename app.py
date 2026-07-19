from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
import re
import json


app = Flask(__name__)

DB = "data/recipes.db"



def db():

    os.makedirs("data", exist_ok=True)

    con = sqlite3.connect(DB)

    con.row_factory = sqlite3.Row

    return con





def init():

    con=db()

    con.execute("""
    CREATE TABLE IF NOT EXISTS recipes(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        title TEXT NOT NULL,

        tags TEXT,

        servings INTEGER,

        ingredients TEXT,

        instructions TEXT,

        nutrition TEXT

    )
    """)

    con.commit()
    con.close()






@app.route("/")
def home():

    return send_from_directory(
        ".",
        "index.html"
    )





@app.route("/<path:file>")
def files(file):

    return send_from_directory(
        ".",
        file
    )







@app.get("/api/recipes")
def all_recipes():

    con = db()

    rows = con.execute(
        "SELECT id, title, tags FROM recipes"
    ).fetchall()

    con.close()

    return jsonify(
        [dict(x) for x in rows]
    )






@app.get("/api/recipes/<int:id>")
def one_recipe(id):

    con=db()

    row = con.execute(
    "SELECT * FROM recipes WHERE id=?",
    (id,)
    ).fetchone()

    con.close()


    return jsonify(dict(row))








@app.post("/api/recipes")
def create():


    data=request.json


    con=db()


    cur = con.execute(
    """
    INSERT INTO recipes
    (title,tags,servings,ingredients,instructions,nutrition)

    VALUES (?,?,?,?,?,?)
    """,

    (
    data.get("title"),
    data.get("tags",""),
    data.get("servings",0),
    data.get("ingredients",""),
    data.get("instructions",""),
    data.get("nutrition","")
    ))

    con.commit()


    new_id = cur.lastrowid


    con.close()


    return jsonify({
        "id":new_id
    })







@app.put("/api/recipes/<int:id>")
def update(id):

    d=request.json


    con=db()


    con.execute(
    """
    UPDATE recipes SET

    title=?,
    tags=?,
    servings=?,
    ingredients=?,
    instructions=?,
    nutrition=?

    WHERE id=?

    """,

    (
    d["title"],
    d["tags"],
    d["servings"],
    d["ingredients"],
    d["instructions"],
    d["nutrition"],
    id
    ))


    con.commit()
    con.close()


    return jsonify({"ok":True})








@app.delete("/api/recipes/<int:id>")
def delete(id):

    con=db()

    con.execute(
    "DELETE FROM recipes WHERE id=?",
    (id,)
    )

    con.commit()

    con.close()


    return jsonify({"ok":True})







ALLOWED_EXT = {".html", ".css", ".js", ".json", ".py", ".md", ".txt"}

JEOPARDY_DATA = "Jeopardy/game-data.js"


@app.get("/api/jeopardy/data")
def get_jeopardy_data():
    with open(JEOPARDY_DATA, "r", encoding="utf-8") as f:
        content = f.read()

    team_match = re.search(r"const TEAM_COUNT\s*=\s*(\d+)", content)
    team_count = int(team_match.group(1)) if team_match else 3

    val_match = re.search(r"const VALUES\s*=\s*\[([^\]]+)\]", content)
    values = [int(x.strip()) for x in val_match.group(1).split(",")] if val_match else [100,200,300,400,500]

    cat_match = re.search(r"categories:\s*\[(.*?)\]", content, re.DOTALL)
    categories = re.findall(r'"([^"]+)"', cat_match.group(1)) if cat_match else []

    cards = []
    card_pattern = re.compile(
        r'\{\s*category:\s*"([^"]+)"\s*,\s*value:\s*(\d+)\s*,\s*question:\s*"((?:[^"\\]|\\.)*)"\s*,\s*answer:\s*"((?:[^"\\]|\\.)*)"\s*\}'
    )
    for m in card_pattern.finditer(content):
        cards.append({
            "category": m.group(1),
            "value": int(m.group(2)),
            "question": m.group(3).encode().decode('unicode_escape'),
            "answer": m.group(4).encode().decode('unicode_escape'),
        })

    return jsonify({
        "teamCount": team_count,
        "values": values,
        "categories": categories,
        "cards": cards,
    })


@app.post("/api/jeopardy/data")
def save_jeopardy_data():
    data = request.json
    team_count = data.get("teamCount", 3)
    values = data.get("values", [100,200,300,400,500])
    categories = data.get("categories", [])
    cards = data.get("cards", [])

    js = '// ====================================================\n'
    js += '//  GAME CONFIGURATION\n'
    js += '//  Edit this file to customize your Jeopardy board.\n'
    js += '// ====================================================\n\n'
    js += f'const TEAM_COUNT = {team_count};\n\n'
    js += f'const VALUES = [{", ".join(str(v) for v in values)}];\n\n'
    js += 'const GAME_DATA = {\n'
    js += '  categories: [\n'
    for c in categories:
        js += f'    "{c}",\n'
    js += '  ],\n\n'
    js += '  cards: [\n'
    for card in cards:
        q = card["question"].replace('\\', '\\\\').replace('"', '\\"')
        a = card["answer"].replace('\\', '\\\\').replace('"', '\\"')
        js += f'    {{ category: "{card["category"]}", value: {card["value"]}, question: "{q}", answer: "{a}" }},\n'
    js += '  ],\n};\n'

    with open(JEOPARDY_DATA, "w", encoding="utf-8") as f:
        f.write(js)
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


init()


if __name__=="__main__":

    app.run(
    host="0.0.0.0",
    port=5000
    )