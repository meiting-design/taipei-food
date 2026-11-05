
from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
import random

app = Flask(__name__)
app.json.ensure_ascii = False

# 設定 SQLite 資料庫
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///restaurants.db"

db = SQLAlchemy(app)

# 餐廳資料表
class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cuisine = db.Column(db.String(100), nullable=False)
    district = db.Column(db.String(30), nullable=False)
    note = db.Column(db.Text, nullable=False)


# 台北市行政區
districts = [
    "中正區", "大同區", "中山區", "松山區",
    "大安區", "萬華區", "信義區", "士林區",
    "北投區", "內湖區", "南港區", "文山區"
]


# 首頁
@app.route("/")
def index():

    selected_district = request.args.get("district", "")
    selected_cuisine = request.args.get("cuisine", "")

    query = Restaurant.query

    if selected_district:
        query = query.filter_by(district=selected_district)

    if selected_cuisine:
        query = query.filter_by(cuisine=selected_cuisine)

    restaurants = query.order_by(Restaurant.id.desc()).all()

    cuisines = [
        row[0] for row in
        db.session.query(Restaurant.cuisine).distinct().order_by(Restaurant.cuisine).all()
    ]

    grouped = {}

    for district in districts:
        matches = [r for r in restaurants if r.district == district]
        if matches:
            grouped[district] = matches

    return render_template(
        "index.html",
        grouped=grouped,
        districts=districts,
        cuisines=cuisines,
        selected_district=selected_district,
        selected_cuisine=selected_cuisine,
        total=len(restaurants)
    )


# 新增餐廳
@app.route("/add", methods=["GET", "POST"])
def add():

    if request.method == "POST":

        restaurant = Restaurant(
            name=request.form["name"].strip(),
            cuisine=request.form["cuisine"].strip(),
            district=request.form["district"],
            note=request.form["note"].strip()
        )

        if not restaurant.name or not restaurant.cuisine or not restaurant.note:
            return "請填寫所有欄位", 400

        db.session.add(restaurant)
        db.session.commit()

        return redirect(url_for("index"))

    return render_template("form.html", districts=districts, restaurant=None)


# 詳細資料
@app.route("/restaurant/<int:id>")
def detail(id):

    restaurant = db.get_or_404(Restaurant, id)

    return render_template("detail.html", restaurant=restaurant)


# 編輯餐廳
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    restaurant = db.get_or_404(Restaurant, id)

    if request.method == "POST":

        restaurant.name = request.form["name"].strip()
        restaurant.cuisine = request.form["cuisine"].strip()
        restaurant.district = request.form["district"]
        restaurant.note = request.form["note"].strip()

        if not restaurant.name or not restaurant.cuisine or not restaurant.note:
            return "請填寫所有欄位", 400

        db.session.commit()

        return redirect(url_for("detail", id=id))

    return render_template(
        "form.html",
        districts=districts,
        restaurant=restaurant
    )


# 刪除餐廳
@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):

    restaurant = db.get_or_404(Restaurant, id)

    db.session.delete(restaurant)
    db.session.commit()

    return redirect(url_for("index"))


# 隨機推薦
@app.route("/random")
def random_restaurant():

    district = request.args.get("district", "")
    cuisine = request.args.get("cuisine", "")

    query = Restaurant.query

    if district:
        query = query.filter_by(district=district)

    if cuisine:
        query = query.filter_by(cuisine=cuisine)

    restaurants = query.all()

    if not restaurants:
        return redirect(url_for("index"))

    restaurant = random.choice(restaurants)

    return redirect(url_for("detail", id=restaurant.id))


# 建立資料庫
with app.app_context():
    db.create_all()



# RESTful API：Create 新增餐廳
@app.route("/api/restaurants", methods=["POST"])
def api_create():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"error": "請提供 JSON 資料"}, 400

    required = ["name", "cuisine", "district", "note"]
    if any(not isinstance(data.get(k), str) or not data[k].strip()
           for k in required):
        return {"error": "請填寫所有欄位"}, 400

    restaurant = Restaurant(
        name=data["name"].strip(),
        cuisine=data["cuisine"].strip(),
        district=data["district"].strip(),
        note=data["note"].strip()
    )
    db.session.add(restaurant)
    db.session.commit()

    return {"message": "新增成功", "id": restaurant.id}, 201


# RESTful API：Read 讀取餐廳
@app.route("/api/restaurants", methods=["GET"])
def api_read():
    restaurants = Restaurant.query.all()

    return [
        {
            "id": r.id,
            "name": r.name,
            "cuisine": r.cuisine,
            "district": r.district,
            "note": r.note
        }
        for r in restaurants
    ]


# RESTful API：Update 更新餐廳
@app.route("/api/restaurants/<int:id>", methods=["PUT"])
def api_update(id):
    restaurant = db.get_or_404(Restaurant, id)
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"error": "請提供 JSON 資料"}, 400

    for field in ["name", "cuisine", "district", "note"]:
        if field in data:
            if not isinstance(data[field], str) or not data[field].strip():
                return {"error": "欄位不可為空"}, 400
            setattr(restaurant, field, data[field].strip())

    db.session.commit()
    return {"message": "更新成功"}


# RESTful API：Delete 刪除餐廳
@app.route("/api/restaurants/<int:id>", methods=["DELETE"])
def api_delete(id):
    restaurant = db.get_or_404(Restaurant, id)

    db.session.delete(restaurant)
    db.session.commit()

    return {"message": "刪除成功"}



if __name__ == "__main__":
    app.run(debug=True)


