from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api', methods=['POST'])
def render_collage():
    print(request.get_json())
    return jsonify({"status": "success", "message": "Got data!"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
