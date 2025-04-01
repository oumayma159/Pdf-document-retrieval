import fitz
import os
import pdfplumber


def extract_all(file_path, image_output_dir="extracted_images"):
    all_pages = {
        'total_pages_treated': 0,
        'data_per_page': [],
        'total_text_extracted': 0,
        'total_images_extracted': 0,
        'total_tables_extracted': 0
    }
    with pdfplumber.open(file_path) as pdf:
        total_pages = len(pdf.pages)
        for i in range(total_pages):
            ordered_content = extract_ordered_content(file_path, i, image_output_dir=image_output_dir)
            page_data = {
                'page_number': i + 1,
                'ordered_content': ordered_content,  
                'verification': None
            }
            num_tables = sum(1 for item in ordered_content if item["type"] == "table")
            num_images = sum(1 for item in ordered_content if item["type"] == "image")
            total_text_chars = sum(len(item["content"]) for item in ordered_content if item["type"] == "text")
            
            all_pages['total_pages_treated'] += 1
            all_pages['total_text_extracted'] += total_text_chars
            all_pages['total_images_extracted'] += num_images
            all_pages['total_tables_extracted'] += num_tables
            all_pages['data_per_page'].append(page_data)
    return all_pages


# top here designates position (y) of the element on the page
def extract_ordered_content(file_path, page_num, image_output_dir="extracted_images"):
    contents = []  
    with pdfplumber.open(file_path) as pdf:
        page = pdf.pages[page_num]
        # extract text (PyPDF2 can extract text too but isnt layout aware)
        lines = page.extract_text(layout=True).split("\n")
        for line in lines:
            print(line)
            bbox = page.search(line)
            print(bbox)
            if bbox:
                contents.append({
                    "type": "text",
                    "content": line,
                    "top": bbox[0]["top"],
                    "bottom": max(c["bottom"] for c in line_chars)
                })
        # tables (also pdfplumber)
        for table in page.find_tables():
            position = table.bbox[1]
            contents.append({
                "type": "table",
                "content": table.extract(),  
                "top": position
            })
        # 3. Get images (fitz)
        with fitz.open(file_path) as doc:
            fitz_page = doc.load_page(page_num)
            image_list = fitz_page.get_images(full=True)  
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_ext = base_image["ext"]
                image_bytes = base_image["image"]
                image_filename = f"page_{page_num+1}_img_{img_index}.{image_ext}"
                image_path = os.path.join(image_output_dir, image_filename)
                os.makedirs(image_output_dir, exist_ok=True)
                with open(image_path, "wb") as img_file:
                    img_file.write(image_bytes)
                contents.append({
                    "type": "image",
                    "content": image_path,
                    "top": img[3] 
                })
    contents = sorted(contents, key=lambda x: x["top"])
    return contents
