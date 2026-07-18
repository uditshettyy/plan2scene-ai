import cv2
import os
import numpy as np


INPUT = "outputs/geometry/wall_mask.png"

OUTPUT = "outputs/reconstruction/aligned_wall_mask.png"


TARGET_WIDTH = 4200
TARGET_HEIGHT = 2481


def main():

    mask = cv2.imread(
        INPUT,
        cv2.IMREAD_GRAYSCALE
    )


    if mask is None:
        raise FileNotFoundError(INPUT)


    print("Original:")
    print(mask.shape)


    resized = cv2.resize(
        mask,
        (TARGET_WIDTH, TARGET_HEIGHT),
        interpolation=cv2.INTER_NEAREST
    )


    # force binary

    resized = np.where(
        resized > 127,
        255,
        0
    ).astype(np.uint8)


    os.makedirs(
        os.path.dirname(OUTPUT),
        exist_ok=True
    )


    cv2.imwrite(
        OUTPUT,
        resized
    )


    print("Saved:")
    print(OUTPUT)

    print("New shape:")
    print(resized.shape)

    print(
        "White pixels:",
        np.sum(resized==255)
    )


if __name__=="__main__":
    main()