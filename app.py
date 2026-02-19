# sdsu-bioinformatics club website

from flask import Flask, render_template
import json
from datetime import datetime
import os

def create_app():
    app = Flask(__name__)

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/members")
    def about():
        return render_template("members.html")

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
