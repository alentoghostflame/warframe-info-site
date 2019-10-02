from flask import Flask, render_template, redirect, url_for


website = Flask(__name__)


@website.route("/", strict_slashes=False)
def homepage():
    return render_template("homepage.html")


@website.route("/warframes", strict_slashes=False)
def warframe_list():
    return render_template("warframe_list.html")


@website.route("/<path:path>", strict_slashes=False)
def catch_all(path):
    print("User tried to go to /{}".format(path))
    return redirect(url_for("homepage"))
