import tensorflow as tf
import numpy as np
import json
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

def load_malaria_model():
    """
    Loads the trained malaria detection model and its training metrics.

    Returns:
        tuple: (model, metrics_dict)
    """
    model = load_model('model/malaria_model.h5')

    # Load training metrics
    metrics_path = 'model/metrics.json'
    metrics = {}
    try:
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
    except FileNotFoundError:
        print("⚠️ Metrics file not found. Skipping metrics load.")

    return model, metrics

def predict_image(img_path, model):
    """
    Preprocesses an image and makes a prediction using the given model and class mapping.

    Args:
        img_path (str): Path to the image.
        model (keras.Model): Trained model for prediction.

    Returns:
        str: Predicted class label ("Parasitized" or "Uninfected")
    """
    # Load and preprocess image
    img = image.load_img(img_path, target_size=(64, 64))
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    # Make prediction
    prediction = model.predict(img_array)[0][0]

    # Load class indices mapping
    with open('model/class_indices.json', 'r') as f:
        class_indices = json.load(f)

    # Reverse the mapping to get index-to-class
    index_to_class = {v: k for k, v in class_indices.items()}

    # Use threshold to determine predicted class index
    predicted_index = 1 if prediction > 0.5 else 0

    return index_to_class[predicted_index]

