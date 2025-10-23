from flask import Flask, request, jsonify
from flask_cors import CORS
from sklearn.linear_model import LinearRegression
import numpy as np

app = Flask(__name__)
CORS(app)

# Global model (will be trained dynamically)
model = None

@app.route('/train', methods=['POST'])
def train():
    global model
    data = request.get_json()

    # Get training data from request
    X = np.array(data['X']).reshape(-1, 1)
    y = np.array(data['y'])

    # Train the model
    model = LinearRegression().fit(X, y)

    return jsonify({'message': 'Model trained successfully!'})

@app.route('/predict', methods=['POST'])
def predict():
    global model
    if model is None:
        return jsonify({'error': 'Model not trained yet!'}), 400

    data = request.get_json()
    hours = float(data['hours'])
    prediction = model.predict(np.array([[hours]]))
    return jsonify({'predicted_marks': round(prediction[0], 2)})

if __name__ == '__main__':
    app.run(debug=True)
