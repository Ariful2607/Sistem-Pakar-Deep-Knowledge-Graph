from flask import Flask
from flask import Flask, request, render_template

app = Flask(__name__)

@app.route("/")
# def home():
#     return "bisa"
def index_page():
    return render_template("index.html")