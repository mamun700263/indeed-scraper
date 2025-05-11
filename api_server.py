from flask import Flask, request, jsonify

app = Flask(__name__)

# A route to receive the POST data
@app.route('/api/products/', methods=['POST'])
def receive_data():
    # Get the JSON data from the POST request
    data = request.get_json()
    print("Received data:", data)

    # You can now process this data (save to database, etc.)
    # For now, let's return it back as a response
    return jsonify(data), 201

if __name__ == "__main__":
    app.run(debug=True)
