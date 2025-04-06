import fitz
import pytesseract
from PIL import Image
from io import BytesIO


# PyMuPDF library fitz is twice as fast as pdf2image and more efficient
def pdf_to_images(pdf_page, dpi=300):
    zoom_x = dpi / 72.0
    zoom_y = dpi / 72.0
    mat = fitz.Matrix(zoom_x, zoom_y)
    pix = pdf_page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("ppm")
    pil_img = Image.open(BytesIO(img_bytes))

    return pil_img


def extract_text_ocr(image):
    custom_config = r"--oem 3 --psm 6"
    ocr_text = pytesseract.image_to_string(image, lang="eng+fra", config=custom_config)
    return {"type": "text", "lines": [ocr_text.strip()]}


def extract_tables_ocr(image):
    ocr_data = pytesseract.image_to_data(
        image, output_type=pytesseract.Output.DICT, config="--oem 3 --psm 6 -l eng+fra"
    )

    rows = {}

    for i in range(len(ocr_data["text"])):
        if int(ocr_data["conf"][i]) > 60:
            text = ocr_data["text"][i].strip()

            if not text:
                continue

            y = ocr_data["top"][i]
            x = ocr_data["left"][i]

            matched = False

            for row_y in rows:
                if abs(y - row_y) < 10:
                    rows[row_y].append((x, text))
                    matched = True

                    break

            if not matched:
                rows[y] = [(x, text)]

    tables = []
    table_data = []

    rows_y = sorted(rows.keys())

    for i in range(len(rows_y)):
        row_y = rows_y[i]
        row_data = sorted(rows[row_y], key=lambda x: x[0])

        if not table_data:
            table_data.append([cell[1] for cell in row_data])

        last_row_data = table_data[-1]
        last_row_y = rows_y[i - 1]

        if (len(row_data) == len(last_row_data)) and ((row_y - last_row_y < 20)):
            continue

        tables.append({"type": "table", "rows": table_data})
        table_data = []

    if table_data:
        tables.append({"type": "table", "rows": table_data})

    return tables


def ocr_fallback(file_path, pages_to_verify):
    try:
        ocr_results = {}

        with fitz.open(file_path) as pdf:
            for page_num in pages_to_verify:
                page = pdf.load_page(page_num)
                pil_img = pdf_to_images(page, dpi=300)

                text = extract_text_ocr(pil_img)
                tables = extract_tables_ocr(pil_img)

                result = [
                    text,
                    *tables,
                ]

                ocr_results[page_num] = result

                pil_img.close()

        return ocr_results
    except Exception:
        print(f"OCR failed for page {page_num}")

        return {}


def apply_ocr_fallback(file_path, extracted_data, pages_to_verify):
    ocr_results = ocr_fallback(file_path, pages_to_verify)

    for page_num, ocr_data in ocr_results.items():
        page_data = extracted_data["pages"][page_num]
        page_data["contents"].append({"type": "ocr", "contents": ocr_data})

        extracted_data["total_text_extracted"] += len(ocr_data[0]["lines"][0])

    return extracted_data
