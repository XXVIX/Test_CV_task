import argparse
from pathlib import Path
from ultralytics import YOLO

def run_validation(weights_path: Path, data_config_path: Path):
    model = YOLO(weights_path)
    
    metrics = model.val(
        data=str(data_config_path),
        split='test',
        imgsz=640,
        batch=8
    )
    
    return metrics

if __name__ == '__main__':
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--weights', 
        type=Path, 
        default=PROJECT_ROOT / "runs/detect/yolov11m_food_exp_hpo/weights/best.pt"
    )
    parser.add_argument(
        '--data', 
        type=Path, 
        default=PROJECT_ROOT / "data/processed/dataset.yaml"
    )
    
    args = parser.parse_args()
    
    run_validation(
        weights_path=args.weights, 
        data_config_path=args.data
    )