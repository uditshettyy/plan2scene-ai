import subprocess

steps = [
    ("YOLO Inference", "python models/inference.py"),
    ("Geometry Extraction", "python vectorization/geometry.py"),
    ("Extract Walls", "python vectorization/extract_walls.py"),
    ("Extract Rooms", "python vectorization/extract_rooms.py"),
    ("Optimize Walls", "python vectorization/optimize_walls.py"),
    ("Export 3D Model", "python reconstruction/exporter.py"),
]

print("=" * 60)
print("Plan2Scene AI")
print("=" * 60)

for name, command in steps:
    print(f"\n{name}...")
    result = subprocess.run(command, shell=True)

    if result.returncode != 0:
        print(f"\n❌ Failed at: {name}")
        exit()

print("\n✅ Pipeline Completed Successfully!")
print("📦 3D Model saved at: outputs/models/house.obj")