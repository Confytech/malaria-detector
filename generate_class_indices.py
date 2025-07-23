# generate_class_indices.py

from tensorflow.keras.preprocessing.image import ImageDataGenerator
import json
import os

# Ensure the model directory exists
os.makedirs("model", exist_ok=True)

# Create a data generator
datagen = ImageDataGenerator(rescale=1.0 / 255)

# Load training data from the correct path
train_generator = datagen.flow_from_directory(
    'cell_images_split/train',  # your actual training folder
    target_size=(64, 64),
    batch_size=32,
    class_mode='categorical'
)

# Save only the class indices as JSON
with open("model/class_indices.json", "w") as f:
    json.dump(train_generator.class_indices, f)

print("✅ Class indices saved to model/class_indices.json")

