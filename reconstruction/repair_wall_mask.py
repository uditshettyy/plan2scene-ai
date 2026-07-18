import cv2
import os

INPUT_IMAGE = "outputs/geometry/wall_mask.png"
OUTPUT_IMAGE = "outputs/geometry/repaired_wall_mask.png"

img = cv2.imread(INPUT_IMAGE, cv2.IMREAD_GRAYSCALE)

# Larger kernel closes small wall gaps
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))

repaired = cv2.morphologyEx(
    img,
    cv2.MORPH_CLOSE,
    kernel,
    iterations=2
)

cv2.imwrite(OUTPUT_IMAGE, repaired)

print(f"Saved -> {OUTPUT_IMAGE}")