import random
import shutil
from pathlib import Path
from tqdm import tqdm

def split_annotated_dataset(
    images_source: Path,
    labels_source: Path,
    output_dir: Path,
    split_ratios=(0.7, 0.2, 0.1)
):
    label_files = list(labels_source.glob("*.txt"))
        
    random.shuffle(label_files)
    
    total = len(label_files)
    train_end = int(total * split_ratios[0])
    val_end = train_end + int(total * split_ratios[1])
    
    splits = {
        "train": label_files[:train_end],
        "val": label_files[train_end:val_end],
        "test": label_files[val_end:]
    }
    
    for split_name, files in splits.items():
        img_dir = output_dir / "images" / split_name
        lbl_dir = output_dir / "labels" / split_name
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)
        
        for label_path in tqdm(files, desc=f"Processing '{split_name}' split", unit="file"):
            image_path = images_source / f"{label_path.stem}.jpg"
            if image_path.exists():
                shutil.copy(image_path, img_dir)
                shutil.copy(label_path, lbl_dir)

if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    
    IMAGES_DIR = PROJECT_ROOT / "data/extracted_frames"
    LABELS_DIR = PROJECT_ROOT / "data/extracted_frames_labels"
    PROCESSED_DIR = PROJECT_ROOT / "data/processed"
    
    split_annotated_dataset(IMAGES_DIR, LABELS_DIR, PROCESSED_DIR)