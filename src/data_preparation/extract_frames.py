import cv2
import sys
import argparse
from pathlib import Path
from tqdm import tqdm

def extract_frames_from_videos(
    video_dir: Path, 
    output_dir: Path, 
    frame_stride: int
):
    output_dir.mkdir(parents=True, exist_ok=True)
    
    video_extensions = ['.mov']
    video_files = [p for p in video_dir.glob('*') if p.suffix.lower() in video_extensions]

    if not video_files:
        return

    for video_path in tqdm(video_files, desc="Extracting frames", unit="video"):
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            continue

        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_stride == 0:
                output_filename = output_dir / f"{video_path.stem}_frame_{frame_count:05d}.jpg"
                cv2.imwrite(str(output_filename), frame)

            frame_count += 1
        
        cap.release()

if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--video-dir", 
        type=Path, 
        default=PROJECT_ROOT / "data/raw"
    )
    parser.add_argument(
        "--output-dir", 
        type=Path, 
        default=PROJECT_ROOT / "data/extracted_frames"
    )
    parser.add_argument(
        "--stride", 
        type=int, 
        default=60
    )
    
    args = parser.parse_args()
    
    extract_frames_from_videos(
        video_dir=args.video_dir,
        output_dir=args.output_dir,
        frame_stride=args.stride
    )