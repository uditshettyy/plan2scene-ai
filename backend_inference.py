import sys
from pathlib import Path

# Delegate to models/inference.py
models_dir = Path(__file__).resolve().parent / "models"
sys.path.insert(0, str(models_dir))

from inference import run_inference

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python backend_inference.py input_image output_json [conf]")
        sys.exit(1)

    image_path = sys.argv[1]
    output_path = sys.argv[2]
    conf = float(sys.argv[3]) if len(sys.argv) > 3 else 0.15

    run_inference(image_path, output_path, conf)