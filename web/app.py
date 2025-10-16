from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return "Hello, world!", 200

@app.errorhandler(404)
def error_404(error):
    return render_template("404.html"), 404

@app.errorhandler(403)
def error_403(error):
    return render_template("403.html"), 403

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
