import os
import cloudinary
import cloudinary.uploader

from bson import ObjectId
from pymongo import MongoClient

from flask import (
Flask,
render_template,
request,
redirect,
session
)

app = Flask(name)
app.secret_key = os.environ.get(
"SECRET_KEY"
)

ADMIN_PASSWORD = os.environ.get(
"ADMIN_PASSWORD"
)
cloudinary.config(
cloud_name=os.environ.get(
"CLOUDINARY_CLOUD_NAME"
),
api_key=os.environ.get(
"CLOUDINARY_API_KEY"
),
api_secret=os.environ.get(
"CLOUDINARY_API_SECRET"
),
secure=True
)
client = MongoClient(
os.environ.get("MONGO_URI")
)

db = client["ai_gallery"]

collection = db["artworks"]
ALLOWED_EXTENSIONS = {
"png",
"jpg",
"jpeg",
"webp"
}

def allowed_file(filename):

return (
    "." in filename and
    filename.rsplit(
        ".", 1
    )[1].lower()
    in ALLOWED_EXTENSIONS
)
@app.route("/")
def index():

artworks = []

for item in collection.find():

    artworks.append({
        "index": str(
            item["_id"]
        ),
        "image_url":
            item.get(
                "image_url"
            ),
        "prompt":
            item.get(
                "prompt",
                ""
            )
    })

artworks.reverse()
return render_template(
    "index.html",
    artworks=artworks
)
@app.route(
"/admin",
methods=["GET", "POST"]
)
def admin_login():

if request.method == "POST":

    password = request.form.get(
        "password"
    )

    if (
        password ==
        ADMIN_PASSWORD
    ):

        session[
            "admin"
        ] = True

        return redirect(
            "/upload"
        )

    return (
        "Wrong Password"
    )

return render_template(
    "login.html"
)
@app.route("/logout")
def logout():

session.clear()

return redirect("/")

@app.route(
"/upload",
methods=["GET", "POST"]
)
def upload_page():

if not session.get(
    "admin"
):
    return redirect(
        "/admin"
    )

if request.method == "POST":

    if (
        "file"
        not in request.files
    ):
        return (
            "No File Selected"
        )

    file = request.files[
        "file"
    ]

    prompt = request.form.get(
        "prompt",
        ""
    )

    if (
        file.filename == ""
    ):
        return (
            "No File Selected"
        )

    if not allowed_file(
        file.filename
    ):
        return (
            "Invalid File Type"
        )

    try:

        result = (
            cloudinary
            .uploader
            .upload(
                file,
                folder=
                "ai-gallery"
            )
        )

        image_url = (
            result[
                "secure_url"
            ]
        )

        public_id = (
            result[
                "public_id"
            ]
        )

        collection.insert_one({

            "image_url":
                image_url,

            "public_id":
                public_id,

            "prompt":
                prompt

        })

        return render_template(
            "success.html"
        )

    except Exception as e:

        return (
            f"Upload Error: {e}"
        )

return render_template(
    "upload.html"
)


@app.route(
"/delete/<id>"
)
def delete_art(id):

if not session.get(
    "admin"
):
    return redirect(
        "/admin"
    )

try:

    item = (
        collection.find_one(
            {
                "_id":
                ObjectId(id)
            }
        )
    )

    if item:

        public_id = item.get(
            "public_id"
        )

        if public_id:

            try:

                cloudinary\
                .uploader\
                .destroy(
                    public_id
                )

            except:
                pass

        collection.delete_one(
            {
                "_id":
                ObjectId(id)
            }
        )

except:
    pass

return redirect("/")
if name == "main":

port = int(
    os.environ.get(
        "PORT",
        5000
    )
)

app.run(
    host="0.0.0.0",
    port=port,
    debug=True
)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@app.route("/")
def index():
    data = load_data()

    artworks = []

    for i, item in enumerate(data):
        artworks.append({
            "index": i,
            "image_url": item.get("image_url"),
            "prompt": item.get("prompt", "")
        })

    artworks = sorted(
        artworks,
        key=lambda x: x["index"],
        reverse=True
    )

    return render_template(
        "index.html",
        artworks=artworks
    )


@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password")

        if password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/upload")

        return "Wrong Password"

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
            return "No File Selected"

        file = request.files["file"]
        prompt = request.form.get("prompt", "")

        if file.filename == "":
            return "No File Selected"

        if not allowed_file(file.filename):
            return "Invalid File Type"

        try:
            result = cloudinary.uploader.upload(
                file,
                folder="ai-gallery"
            )

            image_url = result["secure_url"]
            public_id = result["public_id"]

            data = load_data()

            data.append({
                "image_url": image_url,
                "public_id": public_id,
                "prompt": prompt
            })

            save_data(data)

            return render_template("success.html")

        except Exception as e:
            return f"Upload Error: {e}"

    return render_template("upload.html")


@app.route("/delete/<int:index>")
def delete_art(index):
    if not session.get("admin"):
        return redirect("/admin")

    data = load_data()

    if 0 <= index < len(data):
        item = data[index]

        public_id = item.get("public_id")

        if public_id:
            try:
                cloudinary.uploader.destroy(public_id)
            except Exception:
                pass

        data.pop(index)
        save_data(data)

    return redirect("/")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )
