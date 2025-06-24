import yaml
from pathlib import Path
from ultralytics import YOLO

def download_file(url: str, destination: Path):
    if destination.exists():
        return

    import requests
    from tqdm import tqdm

    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024
    
    with open(destination, 'wb') as f, tqdm(
        total=total_size, unit='iB', unit_scale=True, desc=destination.name
    ) as pbar:
        for data in response.iter_content(block_size):
            f.write(data)
            pbar.update(len(data))

def train_hpo_model():
    project_root = Path(__file__).resolve().parents[2]
    
    model_name = 'yolov11m.pt'
    model_url = f'https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11m.pt'
    model_path = project_root / model_name
    
    download_file(model_url, model_path)

    processed_data_dir = project_root / "data/processed"
    
    dataset_config = {
        'path': str(processed_data_dir.resolve()),
        'train': 'images/train',
        'val': 'images/val',
        'test': 'images/test',
        'names': { 0: 'full_plate', 1: 'empty_plate', 2: 'cutlery', 3: 'glass' }
    }
    
    config_path = processed_data_dir / "dataset.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(dataset_config, f, default_flow_style=False)

    model = YOLO(model_path)

    results = model.train(
        data=str(config_path),
        epochs=100,
        imgsz=640,
        batch=8,
        name='yolov11m_food_exp_hpo',
        scale=0.6,
        translate=0.2
    )
    
    return results

if __name__ == '__main__':
    train_hpo_model()