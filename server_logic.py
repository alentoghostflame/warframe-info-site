from flask import Flask, render_template, redirect, url_for


website = Flask(__name__)


@website.route("/", strict_slashes=False)
def homepage():
    return render_template("homepage.html")


@website.route("/<path:path>")
def catch_all(path):
    return redirect(url_for("homepage"))
