from flask import Flask


website = Flask(__name__)


@website.route("/")
@website.route("/index")
def index():
    return "Hello, World!"
