#! python3

from flask import (
    Flask,
    request,
    redirect,
    render_template,
)
import binascii
import os

# それぞれのメモはtextファイルとして保存される
# ファイル名のフォーマットは以下の通り
# hexlify(title) + ".txt"

app = Flask(__name__)
MEMO_DIR = "/tmp/files/"


# メモの一覧の表示
@app.route("/", methods=["GET"])
def route_index():
    files = [
        f
        for f in os.listdir(MEMO_DIR)
        if os.path.isfile(os.path.join(MEMO_DIR, f))  # noqa: E501
    ]
    memos = [
        {
            "title": binascii.unhexlify(
                f.split(".")[0]
            ).decode(),  # remove extention(.txt)
            "key": f,
        }
        for f in files
    ]

    return render_template("index.html", memos=memos)


# メモの追加画面の表示
@app.route("/add", methods=["GET"])
def route_add_index():
    return render_template("add.html")


# メモの追加
@app.route("/add", methods=["POST"])
def route_add_do():
    title = request.form.get("title")
    body = request.form.get("body")

    if title is None or title == "":
        return "title must be specified"

    filename = binascii.hexlify(title.encode()).decode() + ".txt"
    open(os.path.join(MEMO_DIR, filename), "w+").write(body)

    return redirect("/")


# メモの内容表示
@app.route("/memo", methods=["GET"])
def route_memo():
    key = request.args.get("key")
    filepath = MEMO_DIR + key

    if os.path.exists(filepath) is False:
        return "file not found"
    if os.path.isfile(filepath) is False:
        return "not a file"

    try:
        memo_title = binascii.unhexlify(
            key.split(".")[0]
        ).decode()  # remove file extension
    except BaseException:
        memo_title = ""
    memo_body = open(filepath, "r").read()

    return render_template("memo.html", title=memo_title, body=memo_body)


def init():
    app.config["FLAG"] = os.environ.get("FLAG")
    if os.path.exists(MEMO_DIR) is False:
        os.mkdir(MEMO_DIR)


init()
app.run(host="0.0.0.0", port=5001, debug=False)
