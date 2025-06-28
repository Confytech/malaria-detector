import os
import shutil
import random

def split_data(source_dir, dest_train, dest_test, split_ratio=0.8):
    files = os.listdir(source_dir)
    random.shuffle(files)
    split = int(len(files) * split_ratio)
    
    for i, file in enumerate(files):
        src = os.path.join(source_dir, file)
        if os.path.isfile(src):
            dst_folder = dest_train if i < split else dest_test
            os.makedirs(dst_folder, exist_ok=True)
            shutil.copy(src, os.path.join(dst_folder, file))

base_dir = 'cell_images'
split_base = 'cell_images_split'

split_data(
    os.path.join(base_dir, 'Parasitized'),
    os.path.join(split_base, 'train/Parasitized'),
    os.path.join(split_base, 'test/Parasitized')
)

split_data(
    os.path.join(base_dir, 'Uninfected'),
    os.path.join(split_base, 'train/Uninfected'),
    os.path.join(split_base, 'test/Uninfected')
)

print("✅ Dataset successfully split into train and test folders.")

