from flask import Flask, render_template


website = Flask(__name__)


@website.route("/")
@website.route("/index")
def index():
    return render_template("base.html")
