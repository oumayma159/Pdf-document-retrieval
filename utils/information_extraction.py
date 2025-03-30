import PyPDF2

import fitz
import os
from PIL import Image
from io import BytesIO

import pdfplumber

# PyPDF2 
def extract_text_from_pdf(file_path,page_num):
    extracted_text = ''    
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        pages = len(reader.pages)
        if page_num is not None :
            page = reader.pages[page_num]
            text = page.extract_text().strip()
            if text:
                extracted_text += text 
    return extracted_text

#  fitz (PyMuPDF)
# def extract_images_from_pdf(file_path,page_num):
#     extracted_images = []   
#     with fitz.open(file_path) as file:
#         if page_num is not None:
#             page = file.load_page(page_num)  
#             image_list = page.get_images(full=True)
#             if image_list:
#                 for img in image_list:
#                     xref = img[0]
#                     base_image = file.extract_image(xref)
#                     image_bytes = base_image["image"]
#                     pil_image = Image.open(BytesIO(image_bytes))
#                     extracted_images.append(pil_image)   
#     return extracted_images
def extract_images_from_pdf(file_path, page_num, output_dir="extracted_images"):
    extracted_images = []
    os.makedirs(output_dir, exist_ok=True) 
    with fitz.open(file_path) as file:
        if page_num is not None:
            page = file.load_page(page_num)
            image_list = page.get_images(full=True)        
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = file.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                image_filename = f"page_{page_num+1}_img_{img_index}.{image_ext}"
                image_path = os.path.join(output_dir, image_filename)
                with open(image_path, "wb") as img_file:
                    img_file.write(image_bytes)               
                extracted_images.append({
                    "path": image_path,
                    "width": base_image["width"],
                    "height": base_image["height"],
                    "xref": xref
                }) 
    return extracted_images

# pdfplumber
def extract_tables_from_pdf(file_path,page_num):
    extracted_tables = []   
    with pdfplumber.open(file_path) as pdf:
        if page_num is not None:
            page = pdf.pages[page_num]
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    if table:
                        extracted_tables.append(table)  
    return extracted_tables


def extract_all(file_path):
    all_pages = {
            'total_pages_treated': 0,
            'data_per_page': [],
            'total_text_extracted': 0,
            'total_images_extracted': 0,
            'total_tables_extracted': 0
        }    
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_data = {
                'page_number': i+1,
                'text': extract_text_from_pdf(file_path,page_num=i),
                'images': extract_images_from_pdf(file_path,page_num=i),
                'tables': extract_tables_from_pdf(file_path,page_num=i),
                'verification': None
            }
            all_pages['total_pages_treated'] += 1
            all_pages['total_text_extracted'] += len(page_data['text'])
            all_pages['total_images_extracted'] += len(page_data['images'])
            all_pages['total_tables_extracted'] += len(page_data['tables'])
            all_pages['data_per_page'].append(page_data)
               
    return all_pages
