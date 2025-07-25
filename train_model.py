# -*- coding: utf-8 -*-
import os
import json
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

# Set paths
train_dir = 'cell_images_split/train'
test_dir = 'cell_images_split/test'
batch_size = 32
image_size = (64, 64)

# Image data generators
train_datagen = ImageDataGenerator(rescale=1./255)
test_datagen = ImageDataGenerator(rescale=1./255)

train_generator = train_datagen.flow_from_directory(
    train_dir,
    target_size=image_size,
    batch_size=batch_size,
    class_mode='binary'
)

test_generator = test_datagen.flow_from_directory(
    test_dir,
    target_size=image_size,
    batch_size=batch_size,
    class_mode='binary'
)

# Build CNN model
model = Sequential([
    Conv2D(32, (3, 3), activation='relu', input_shape=(64, 64, 3)),
    MaxPooling2D(2, 2),
    Conv2D(64, (3, 3), activation='relu'),
    MaxPooling2D(2, 2),
    Conv2D(128, (3, 3), activation='relu'),
    MaxPooling2D(2, 2),
    Flatten(),
    Dense(128, activation='relu'),
    Dropout(0.5),
    Dense(1, activation='sigmoid')
])

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Train model
early_stop = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)

print("🚀 Training started...")
history = model.fit(
    train_generator,
    epochs=10,
    validation_data=test_generator,
    callbacks=[early_stop]
)

# Save the model
os.makedirs('model', exist_ok=True)
model.save('model/malaria_model.h5')
print("✅ Model trained and saved as model/malaria_model.h5")

# Save the class indices
with open("model/class_indices.json", "w") as f:
    json.dump(train_generator.class_indices, f)

print("🔤 Class indices saved to model/class_indices.json")

# Save final training metrics
metrics = {
    "train_accuracy": float(history.history['accuracy'][-1]),
    "train_loss": float(history.history['loss'][-1]),
    "val_accuracy": float(history.history['val_accuracy'][-1]),
    "val_loss": float(history.history['val_loss'][-1])
}

with open("model/metrics.json", "w") as f:
    json.dump(metrics, f)

print("📊 Training metrics saved to model/metrics.json")

