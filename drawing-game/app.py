from flask import Flask, render_template
from extensions.socketio import socketio
from blueprints.packs.Routes import packs_bp
import os

app = Flask(__name__)
socketio.init_app(app)
app.register_blueprint(packs_bp, url_prefix="/api")

# Import socketIO events after loading app
import game.events

@app.route("/")
def index():
    return render_template("index.html"), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
