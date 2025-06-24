import argparse
from pathlib import Path
from ultralytics import YOLO

def run_prediction(weights_path: Path, source: Path, confidence_threshold: float):
    model = YOLO(weights_path)
    
    model.predict(
        source=str(source),
        save=True,
        imgsz=640,
        conf=confidence_threshold
    )

if __name__ == '__main__':
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--weights', 
        type=Path, 
        default=PROJECT_ROOT / "runs/detect/yolov11m_food_exp_hpo/weights/best.pt"
    )
    parser.add_argument(
        '--source', 
        type=Path, 
        default=PROJECT_ROOT / "data/processed/images/test"
    )
    parser.add_argument(
        '--conf', 
        type=float,
        default=0.5
    )
    
    args = parser.parse_args()
    
    run_prediction(
        weights_path=args.weights, 
        source=args.source,
        confidence_threshold=args.conf
    )