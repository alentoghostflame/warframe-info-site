from flask import Flask, render_template, redirect, url_for
from class_logic import ObjectStorage


website = Flask(__name__)
storage = ObjectStorage()
storage.load_all()


@website.route("/", strict_slashes=False)
def homepage():
    return render_template("homepage.html")


@website.route("/warframes/<path:path>", strict_slashes=False)
def warframes(path):
    print("Warframes: User tried to go to /warframes/{}".format(path))
    if path.lower in storage.warframe_list.names:
        return "lol hi there."
    else:
        return redirect(url_for("warframe_list"))


@website.route("/warframes", strict_slashes=False)
def warframe_list():
    return render_template("warframe_list.html", warframe_names=storage.warframe_list.names)


@website.route("/<path:path>", strict_slashes=False)
def catch_all(path):
    print("User tried to go to /{}".format(path))
    return redirect(url_for("homepage"))
