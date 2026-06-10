import os
import cloudinary
import cloudinary.uploader
from bson import ObjectId
from pymongo import MongoClient
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret-key-for-dev")

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True
)

mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(mongo_uri)
db = client["ai_gallery"]
collection = db["artworks"]


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    try:
        count = collection.count_documents({})
        return f"Documents Found: {count}"

    except Exception as e:
        return f"MongoDB Error: {e}"


@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/upload")
        return "Wrong Password", 401

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/upload", methods=["GET", "POST"])
def upload_page():
    if not session.get("admin"):
        return redirect("/admin")

    if request.method == "POST":
        if "file" not in request.files:
            return "No File Selected", 400

        file = request.files["file"]
        prompt = request.form.get("prompt", "")

        if file.filename == "":
            return "No File Selected", 400

        if not allowed_file(file.filename):
            return "Invalid File Type", 400

        try:
            result = cloudinary.uploader.upload(file, folder="ai-gallery")
            image_url = result.get("secure_url")
            public_id = result.get("public_id")

            collection.insert_one({
                "image_url": image_url,
                "public_id": public_id,
                "prompt": prompt
            })
            return render_template("success.html")

        except Exception as e:
            return f"Upload Error: {str(e)}", 500

    return render_template("upload.html")


@app.route("/delete/<art_id>")
def delete_art(art_id):
    if not session.get("admin"):
        return redirect("/admin")

    try:
        item = collection.find_one({"_id": ObjectId(art_id)})
        if item:
            public_id = item.get("public_id")
            if public_id:
                try:
                    cloudinary.uploader.destroy(public_id)
                except Exception:
                    pass

            collection.delete_one({"_id": ObjectId(art_id)})

    except Exception:
        pass

    return redirect("/")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
