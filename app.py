from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
import os
from utils import load_malaria_model, predict_image

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load the trained model
model = load_malaria_model()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return "No image file uploaded.", 400

    file = request.files['image']
    if file.filename == '':
        return "No file selected.", 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    result = predict_image(filepath, model)

    return render_template('index.html', prediction=result, image_url=filepath)

if __name__ == '__main__':
    app.run(debug=True)

