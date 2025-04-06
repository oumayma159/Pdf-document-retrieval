import fitz
import os
import pdfplumber
import math
import re


def extract_images(
    file_path, page_num, image_output_dir="extracted_images", results_dir="results"
):
    images = []

    with fitz.open(file_path) as pdf:
        page = pdf.load_page(page_num)
        images_list = page.get_images(full=True)

        for img_index, img in enumerate(images_list):
            xref = img[0]
            image_name = img[7]

            bbox = page.get_image_bbox(img)

            base_image = pdf.extract_image(xref)

            image_ext = base_image["ext"]
            image_bytes = base_image["image"]

            image_filename = f"page_{page_num+1}_img_{img_index}.{image_ext}"
            image_path = os.path.join(image_output_dir, image_filename)
            file_dir = os.path.join(results_dir, image_output_dir)
            file_path = os.path.join(file_dir, image_filename)
            os.makedirs(file_dir, exist_ok=True)

            with open(file_path, "wb") as img_file:
                img_file.write(image_bytes)

            images.append(
                {
                    "path": image_path,
                    "name": image_name,
                    "x0": bbox.x0,
                    "top": bbox.y0,
                    "x1": bbox.x1,
                    "bottom": bbox.y1,
                }
            )

    return images


def is_before(lhs, rhs):
    if lhs is None:
        return False

    if rhs is None:
        return True

    if lhs["top"] < rhs["top"] or lhs["x1"] < rhs["x0"]:
        return True

    return False


def is_part_of_paragraph(line, text):
    lines = text["lines"]

    if not lines:
        return True

    last_line = lines[-1]
    size = last_line["size"]

    if size is None:
        return False

    if not math.isclose(line["size"], size):
        return False

    if line["top"] > last_line["bottom"]:
        return line["top"] - last_line["bottom"] < 0.9 * size

    ends_with_punctuation = re.match("[?.!]$", last_line["text"]) is not None

    if ends_with_punctuation:
        return False

    if len(lines) < 2:
        return ends_with_punctuation

    before_last_line = lines[-2]

    line_width = line["x1"] - line["x0"]
    last_line_width = last_line["x1"] - last_line["x0"]
    before_last_line_width = before_last_line["x1"] - before_last_line["x0"]

    return (last_line_width >= 0.8 * before_last_line_width) and (
        line_width <= 1.2 * max(last_line_width, before_last_line_width)
    )


def sort_contents(tables, lines, images):
    contents = []
    i, j, k = (0, 0, 0)

    text = {"type": "text", "lines": []}

    while i < len(tables) or j < len(lines) or k < len(images):
        table = None
        line = None
        image = None

        first = None

        if i < len(tables):
            table = tables[i]

        if j < len(lines):
            line = lines[j]

        if k < len(images):
            image = images[k]

        if is_before(line, table):
            first = line
        else:
            first = table

        if not is_before(first, image):
            first = image

        if first == line:
            j += 1

            if not is_part_of_paragraph(line, text):
                contents.append(text)
                text = {"type": "text", "lines": []}

            text["lines"].append(line)

            continue

        if text["lines"]:
            contents.append(text)
            text = {"type": "text", "lines": []}

        if first == table:
            i += 1
            contents.append({"type": "table", **table})

            continue

        k += 1
        contents.append({"type": "image", **image})

    if text["lines"]:
        contents.append(text)

    return contents


def not_within(line, table):
    x0, top, x1, bottom = table.bbox

    return (
        line["x0"] > x1
        or line["x1"] < x0
        or line["top"] > bottom
        or line["bottom"] < top
    )


def extract_page_data(
    file_path, page_num, image_output_dir="extracted_images", results_dir="results"
):
    with pdfplumber.open(file_path) as pdf:
        page = pdf.pages[page_num].dedupe_chars()

        tables = page.find_tables()
        lines = [
            {**line, "size": next(iter(line["chars"]), {}).get("size")}
            for line in page.extract_text_lines(layout=True, use_text_flow=True)
            if all(not_within(line, table) for table in tables)
        ]

        tables = [
            {
                "rows": table.extract(),
                "x0": table.bbox[0],
                "top": table.bbox[1],
                "x1": table.bbox[2],
                "bottom": table.bbox[3],
            }
            for table in tables
        ]
        images = extract_images(file_path, page_num, image_output_dir, results_dir)

        return sort_contents(tables, lines, images)


def extract_all(file_path, image_output_dir="extracted_images", results_dir="results"):
    all_pages = {
        "total_pages_treated": 0,
        "pages": [],
        "total_text_extracted": 0,
        "total_images_extracted": 0,
        "total_tables_extracted": 0,
    }

    with pdfplumber.open(file_path) as pdf:
        total_pages = len(pdf.pages)

        for i in range(total_pages):
            page_contents = extract_page_data(
                file_path, i, image_output_dir, results_dir
            )

            page_data = {
                "page_number": i + 1,
                "contents": page_contents,
            }

            total_text_chars = sum(
                len(line["text"])
                for item in page_contents
                if item["type"] == "text"
                for line in item["lines"]
            )
            num_tables = sum(1 for item in page_contents if item["type"] == "table")
            num_images = sum(1 for item in page_contents if item["type"] == "image")

            all_pages["total_pages_treated"] += 1
            all_pages["total_text_extracted"] += total_text_chars
            all_pages["total_tables_extracted"] += num_tables
            all_pages["total_images_extracted"] += num_images

            all_pages["pages"].append(page_data)

    return all_pages
