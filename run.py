from flask import render_template
from app import create_app

app = create_app()

@app.get("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5001)  # or 5000 if free