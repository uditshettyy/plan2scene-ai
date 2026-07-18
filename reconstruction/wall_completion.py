import cv2
import numpy as np
import os


INPUT_PATH = "outputs/reconstruction/aligned_wall_mask.png"

OUTPUT_PATH = "outputs/reconstruction/completed_wall_mask.png"


# Maximum gap to close
MAX_GAP = 35



def find_endpoints(mask):

    """
    Detect possible wall endpoints
    """

    skeleton = cv2.ximgproc.thinning(mask)

    endpoints = []


    h,w = skeleton.shape


    for y in range(1,h-1):

        for x in range(1,w-1):

            if skeleton[y,x] == 255:

                area = skeleton[
                    y-1:y+2,
                    x-1:x+2
                ]

                count = np.sum(area==255)


                if count == 2:
                    endpoints.append(
                        (x,y)
                    )


    return endpoints



def connect_points(mask, endpoints):

    repaired = mask.copy()


    for i,p1 in enumerate(endpoints):

        for p2 in endpoints[i+1:]:


            dist = np.linalg.norm(
                np.array(p1)-np.array(p2)
            )


            if dist < MAX_GAP:


                cv2.line(
                    repaired,
                    p1,
                    p2,
                    255,
                    3
                )


    return repaired



def main():

    mask=cv2.imread(
        INPUT_PATH,
        0
    )


    if mask is None:
        raise FileNotFoundError(INPUT_PATH)



    print("Loaded wall mask")


    endpoints=find_endpoints(
        mask
    )


    print(
        "Endpoints detected:",
        len(endpoints)
    )


    repaired=connect_points(
        mask,
        endpoints
    )


    # small closing operation

    kernel=cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (3,3)
    )


    repaired=cv2.morphologyEx(
        repaired,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=2
    )


    os.makedirs(
        os.path.dirname(OUTPUT_PATH),
        exist_ok=True
    )


    cv2.imwrite(
        OUTPUT_PATH,
        repaired
    )


    print(
        "Saved:",
        OUTPUT_PATH
    )



if __name__=="__main__":
    main()