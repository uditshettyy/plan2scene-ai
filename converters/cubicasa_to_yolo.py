import os
from pathlib import Path

from PIL import Image
from bs4 import BeautifulSoup
from multiprocessing import Pool, Lock

import re
from svg.path import parse_path

print_lock = Lock()

possible_fixed_furniture_lut = {}
possible_fixed_furniture_count = 0

# building elements
building_element_names = ['Door']

# fixed furniture classes
interested_classes = []

classes_lut = {}
class_count = 0

find_new_annotations = False


def write(file, content):
    with open(file, 'w') as outfile:
        outfile.write(content)


def bounding_box(xs, ys):
    x_min = min(xs)
    x_max = max(xs)
    y_min = min(ys)
    y_max = max(ys)

    w = x_max - x_min
    h = y_max - y_min

    return x_min + (w / 2), y_min + (h / 2), w, h


def get_first_png(path):
    pngs = list(path.glob('*scaled.png'))
    return pngs[0]


def add_class(name):
    global class_count
    classes_lut[name] = class_count
    class_count += 1


def add_candidate(name):
    if name not in possible_fixed_furniture_lut:
        global possible_fixed_furniture_count
        possible_fixed_furniture_lut[name] = possible_fixed_furniture_count
        possible_fixed_furniture_count += 1


def is_interested(name):
    return name in classes_lut


def get_class_id(name):
    return classes_lut[name]


def convert_polygon_string(text):
    xs = []
    ys = []

    for p in text.split(" "):
        if p == "":
            continue

        e = p.split(",")

        if len(e) != 2:
            continue

        xs.append(float(e[0]))
        ys.append(float(e[1]))

    return xs, ys


def fix_inner_polygon_coordinates(points_txt):
    elements = [e for e in points_txt.split(" ") if e != ""]
    output = ""
    for i, e in enumerate(elements):
        output += e

        if i % 2 == 0 or i == 0:
            output += ","

        if i % 2 != 0:
            output += " "
    return output


def arc_to_xys(path):
    segments = path._segments

    xs = []
    ys = []

    for segment in segments:
        xs.append(segment.start.real)
        xs.append(segment.end.real)

        ys.append(segment.start.imag)
        ys.append(segment.end.imag)

    return xs, ys


def resolve_d(d):
    # clean arc path
    cleaned_d = re.sub('[^0-9,\.\-\s]', '', d)
    arcx, arcy = convert_polygon_string(cleaned_d)

    x = arcx[0]
    y = arcy[0]

    # make global coordinates
    for i in range(1, len(arcx)):
        arcx[i] = x + arcx[i]
        arcy[i] = y + arcy[i]

    return arcx, arcy


def post_process(index, img_width, img_height, cx, cy, w, h):
    return "%s %s %s %s %s" % (index, cx / img_width, cy / img_height, w / img_width, h / img_height)


def is_image_size_valid(img_width, img_height, svg_width, svg_height):
    # error margin in 1/100 percent
    error_margin = 0.2

    if error_margin < abs(img_width / svg_width - 1.0):
        return False

    if error_margin < abs(img_height / svg_height - 1.0):
        return False

    return True


def create_annotation(svg):
    with print_lock:
        print("processing %s..." % svg)

    data_path = Path(svg).parent
    annotations = []
    class_candidates = []
    could_not_parse_counter = 0

    # get image width
    img_path = get_first_png(data_path)

    im = Image.open(img_path)
    img_width = im.size[0]
    img_height = im.size[1]

    # read svg
    with open(svg, "r") as file:
        xml_content = file.read()

    soup = BeautifulSoup(xml_content, features="xml")
    svg_tag = soup.select("svg")[0]
    svg_width = float(svg_tag["width"])
    svg_height = float(svg_tag["height"])

    # if not is_image_size_valid(img_width, img_height, svg_width, svg_height):
    #    return img_path, class_candidates, could_not_parse_counter, "size invalid"

    # find all building elements
    building_elements = []
    for name in building_element_names:
        elements = soup.find_all(id=name)
        for element in elements:
            building_elements.append((name, element))

    for name, element in building_elements:
        id = classes_lut[name]

        polygon = element.findChildren("polygon", recursive=False)[0]
        xs, ys = convert_polygon_string(polygon["points"])
        cx, cy, w, h = bounding_box(xs, ys)

        # door fix
        if name == "Door":
            paths = element.findChildren("path", recursive=True)
            for path in paths:
                d = path["d"]
                arc = parse_path(d)
                arcx, arcy = arc_to_xys(arc)

                nxs = xs + arcx
                nys = ys + arcy

                cx, cy, w, h = bounding_box(nxs, nys)
                annotations.append(post_process(id, img_width, img_height, cx, cy, w, h))
        else:
            annotations.append(post_process(id, img_width, img_height, cx, cy, w, h))

    # find all fixed furniture
    class_elements = [element for element in soup.find_all(class_=True)]
    fixed_furniture_element = [ff for ff in class_elements if "FixedFurniture" in ff["class"].split(" ")]

    # choose the last class name as furniture descriptor (most specific)
    class_names = [e["class"].split(" ")[-1] for e in fixed_furniture_element]

    # convert element to yolo annotation
    for i, name in enumerate(class_names):
        if not is_interested(name):
            class_candidates.append(name)
            continue

        if find_new_annotations:
            continue

        id = get_class_id(name)
        element = fixed_furniture_element[i]

        # read coordinates
        #  matrix(1,0,0,1,487.399,608.3636)
        transform_matrix_elements = [float(e) for e
                                     in element["transform"].replace("matrix(", "").replace(")", "").split(",")]

        # fix bug if fixedfurniture set
        if element.parent.attrs['class'] == 'FixedFurnitureSet':
            parent = element.parent
            transform_matrix_elements = [float(e) for e
                                         in parent["transform"].replace("matrix(", "").replace(")", "").split(",")]

        x = transform_matrix_elements[4]
        y = transform_matrix_elements[5]

        inner_polygon = False
        boundary_elements = element.findChildren("g", {"class": "BoundaryPolygon"}, recursive=False)
        if len(boundary_elements) == 0:
            boundary_elements = element.findChildren("g", {"class": "InnerPolygon"}, recursive=False)
            inner_polygon = True

        if len(boundary_elements) == 0:
            # if no boundary polygon was found
            could_not_parse_counter += 1
            continue

        boundary_element = boundary_elements[0]
        polygons = boundary_element.findChildren("polygon", recursive=False)

        if len(polygons) == 0:
            # not using a polygon for boundary info but a rect
            # todo: implement extended caluclation of boundary

            could_not_parse_counter += 1
            continue

        polygon = polygons[0]
        points_txt = polygon["points"]

        # fix inner polygon different structure of values
        if inner_polygon and "," not in points_txt:
            points_txt = fix_inner_polygon_coordinates(points_txt)

        xs, ys = convert_polygon_string(points_txt)
        width = float(max(xs))
        height = float(max(ys))

        cx, cy, w, h = bounding_box([x, x + width], [y, y + height])

        # translate by matrix
        if transform_matrix_elements[2] < 0.0:
            cx += transform_matrix_elements[2] * w

        if transform_matrix_elements[1] < 0.0:
            cy += transform_matrix_elements[1] * h

        annotations.append(post_process(id, img_width, img_height, cx, cy, w, h))

    # store annotation in txt file besides scaled png
    txt_name = os.path.join(data_path, img_path.stem + ".txt")
    write(txt_name, "\n".join(annotations))

    # find out of bounds annotation
    if len(annotations) > 0 \
            and True in [float(e) > 1.0 for e in " ".join(annotations).split(" ")] \
            and not is_image_size_valid(img_width, img_height, svg_width, svg_height):
        return img_path, class_candidates, could_not_parse_counter, "over one position"

    return img_path, class_candidates, could_not_parse_counter, None


def store_names(filename, class_lut):
    pairs = class_lut.items()
    pairs = sorted(pairs, key=lambda x: x[1])
    write(filename, "\n".join(map(lambda x: x[0], pairs)))


def main():
    print("converting CubiCasa5k svgs into yolo annotations...")

    svgs = sorted(list(Path('data').glob('**/*.svg')))

    pool = Pool()
    results = pool.map(create_annotation, svgs)
    pool.close()
    pool.join()

    annotated_image_files = [result[0] for result in results]
    candidates_list = [result[1] for result in results]
    candidates = [item for sublist in candidates_list for item in sublist]
    could_not_parse_counter = sum([result[2] for result in results])

    for name in sorted(candidates):
        add_candidate(name)

    store_names("possible.names", possible_fixed_furniture_lut)
    store_names("obj.names", classes_lut)

    write("list.txt", "\n".join([str(e) for e in annotated_image_files]))

    print("processed %s files!" % len(svgs))
    print("could not parse: %s" % could_not_parse_counter)

    failed_imgs = [e for e in results if e[3] is not None]

    if len(failed_imgs) > 0:
        print("Errors (%s): " % len(failed_imgs))
        for result in [e for e in results if e[3] is not None]:
            img_name = result[0]
            message = result[3]

            # print("%s: %s" % (img_name, message))
            print(img_name)


# add classes
for cls in sorted([item for sublist in [building_element_names, interested_classes] for item in sublist]):
    add_class(cls)

if __name__ == "__main__":
    main()
