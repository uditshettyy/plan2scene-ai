import cv2
import json
import os
import numpy as np


# -----------------------------
# Paths
# -----------------------------

ROOMS_PATH = "outputs/geometry/rooms.json"
WALL_IMAGE_PATH = "outputs/reconstruction/wall_pixels.png"

OUTPUT_PATH = "outputs/reconstruction/room_polygons.json"
DEBUG_PATH = "outputs/reconstruction/debug_room_polygons.png"


# -----------------------------
# Parameters
# -----------------------------

# Controls polygon simplification
APPROX_FACTOR = 0.01


# -----------------------------
# Load files
# -----------------------------

def load_rooms(path):
    with open(path, "r") as f:
        return json.load(f)


def load_wall_image(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)

    if img is None:
        raise FileNotFoundError(
            f"Could not load wall image: {path}"
        )

    return img


# -----------------------------
# Extract polygon from room bbox
# -----------------------------

def extract_room_polygon(wall_mask, bbox):

    x1 = int(bbox["x1"])
    y1 = int(bbox["y1"])
    x2 = int(bbox["x2"])
    y2 = int(bbox["y2"])


    # Crop room area
    crop = wall_mask[y1:y2, x1:x2]


    if crop.size == 0:
        return None


    # ----------------------------------
    # Convert:
    #
    # White = walls
    # Black = empty space
    #
    # We need:
    #
    # White = room area
    # ----------------------------------

    inverted = cv2.bitwise_not(crop)


    # Remove small noise
    kernel = np.ones((5,5), np.uint8)

    clean = cv2.morphologyEx(
        inverted,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=2
    )


    # Find contours

    contours, _ = cv2.findContours(
        clean,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )


    if not contours:
        return None


    # Largest contour = room area

    contour = max(
        contours,
        key=cv2.contourArea
    )


    area = cv2.contourArea(contour)


    # Ignore tiny regions
    if area < 500:
        return None


    # Simplify contour

    epsilon = APPROX_FACTOR * cv2.arcLength(
        contour,
        True
    )


    approx = cv2.approxPolyDP(
        contour,
        epsilon,
        True
    )


    # Convert back to original image coordinates

    polygon = []

    for point in approx:
        px, py = point[0]

        polygon.append(
            [
                int(px + x1),
                int(py + y1)
            ]
        )


    return polygon



# -----------------------------
# Main
# -----------------------------

def main():

    rooms = load_rooms(ROOMS_PATH)

    wall_mask = load_wall_image(
        WALL_IMAGE_PATH
    )


    results = []


    debug = cv2.cvtColor(
        wall_mask,
        cv2.COLOR_GRAY2BGR
    )


    print(f"Rooms detected: {len(rooms)}")


    for idx, room in enumerate(rooms):

        polygon = extract_room_polygon(
            wall_mask,
            room["bbox"]
        )


        if polygon is None:
            print(
                f"Room {idx}: failed"
            )
            continue


        results.append(
            {
                "id": idx + 1,
                "confidence": room["confidence"],
                "polygon": polygon
            }
        )


        # Draw debug

        pts = np.array(
            polygon,
            np.int32
        )

        pts = pts.reshape(
            (-1,1,2)
        )

        cv2.polylines(
            debug,
            [pts],
            True,
            (0,255,0),
            3
        )


        cv2.putText(
            debug,
            str(idx+1),
            tuple(polygon[0]),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0,0,255),
            2
        )


    # Save JSON

    os.makedirs(
        os.path.dirname(OUTPUT_PATH),
        exist_ok=True
    )


    with open(
        OUTPUT_PATH,
        "w"
    ) as f:

        json.dump(
            results,
            f,
            indent=4
        )


    cv2.imwrite(
        DEBUG_PATH,
        debug
    )


    print("\nFinished")
    print(
        f"Extracted rooms: {len(results)}"
    )

    print(
        f"Saved: {OUTPUT_PATH}"
    )

    print(
        f"Debug: {DEBUG_PATH}"
    )


if __name__ == "__main__":
    main()