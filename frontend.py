from flask import Flask, render_template, request
import requests
import backend

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

"""@app.route('/', methods=['POST'])
def render_collage():
    print(request.get_json())
    return 'wawa'"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000)
