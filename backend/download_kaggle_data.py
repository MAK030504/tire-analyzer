import kagglehub
import shutil
import os
from pathlib import Path

def prepare_dataset():
    print("Downloading Kaggle dataset...")
    # This downloads the dataset to an internal kagglehub cache and returns the path
    dataset_path = kagglehub.dataset_download("jehanbhathena/tire-texture-image-recognition")
    print(f"Downloaded to: {dataset_path}")
    
    source_dir = Path(dataset_path)
    # The dataset has subfolders 'Tire Textures/training_data' and 'Tire Textures/testing_data'
    # We'll just combine them all into our pure 'data/Cracked' and 'data/Normal' 
    # since train_classifier.py already does its own random train/val split.
    
    target_dir = Path("data")
    if target_dir.exists():
        print("Cleaning up old 'data' directory...")
        shutil.rmtree(target_dir)
        
    target_cracked = target_dir / "Cracked"
    target_normal = target_dir / "Normal"
    
    target_cracked.mkdir(parents=True, exist_ok=True)
    target_normal.mkdir(parents=True, exist_ok=True)
    
    # Define mapping from possible kaggle folder names to our target folders
    mapping = {
        "cracked": target_cracked,
        "normal": target_normal,
    }
    
    print("Copying and organizing files...")
    count = 0
    
    # Walk through all directories in the dataset
    for root, _, files in os.walk(source_dir):
        root_path = Path(root)
        # Check if the current folder belongs to a class we care about
        folder_name = root_path.name.lower()
        
        target = mapping.get(folder_name)
        if target:
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    src_file = root_path / file
                    # Prefix filename with part of its path to avoid name collisions between train/test
                    dst_file = target / f"{root_path.parent.name}_{file}"
                    shutil.copy2(src_file, dst_file)
                    count += 1
                    
    print(f"\nDone! Copied {count} images.")
    print(f"Cracked: {len(list(target_cracked.glob('*')))} images")
    print(f"Normal: {len(list(target_normal.glob('*')))} images")

if __name__ == "__main__":
    prepare_dataset()
