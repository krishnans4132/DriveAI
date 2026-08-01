from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({"status": "running", "message": "DriveAlert AI Backend is online"})

@app.route('/api/analyze_frame', methods=['POST'])
def analyze_frame():
    # Mock endpoint for frame analysis
    # In a real app, this would receive a frame, run it through the fatigue detection model,
    # and return the EAR (Eye Aspect Ratio), PERCLOS, and fatigue state.
    return jsonify({
        "fatigue_detected": False,
        "ear": 0.32,
        "perclos": 0.05
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
