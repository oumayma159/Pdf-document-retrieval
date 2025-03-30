import fitz  
import pytesseract
from PIL import Image
from io import BytesIO
import os



# PyMuPDF library fitz is twice as fast as pdf2image and more efficient 
def pdf_to_images(pdf_page, dpi=300):
    zoom_x = dpi / 72.0
    zoom_y = dpi / 72.0
    mat = fitz.Matrix(zoom_x, zoom_y)
    pix = pdf_page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("ppm")
    pil_img = Image.open(BytesIO(img_bytes))
    return pil_img

def apply_ocr(image):
    custom_config = r'--oem 3 --psm 6'
    ocr_text = pytesseract.image_to_string(image, lang='eng+fra', config=custom_config)
    return ocr_text.strip()

def extract_tables_ocr(image):
    ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, config='--oem 3 --psm 6 -l eng+fra')      
    rows = {}
    for i in range(len(ocr_data["text"])):
        if int(ocr_data["conf"][i]) > 60:
            text = ocr_data["text"][i].strip()
            if text:
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
    for y in sorted(rows.keys()):
        row = sorted(rows[y], key=lambda x: x[0])
        table_data.append([text for (x, text) in row])
    
    if len(table_data) >= 2:
        tables.append(table_data)    
    return tables


def extract_images(page, output_dir="extracted_images"):
    extracted_images = []
    os.makedirs(output_dir, exist_ok=True)   
    image_list = page.get_images(full=True)        
    for img_index, img in enumerate(image_list):
        xref = img[0]
        base_image = page.parent.extract_image(xref)  
        image_bytes = base_image["image"]
        image_ext = base_image["ext"]
        image_filename = f"page_{page.number + 1}_img_{img_index}.{image_ext}"
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


def ocr_fallback(file_path, pages_to_ocr,output_dir="extracted_images"):
    ocr_results = {}  
    try:
        with fitz.open(file_path) as pdf:
            for page_num in pages_to_ocr:
                page = pdf.load_page(page_num - 1)  
                pil_img = pdf_to_images(page, dpi=300)
                # text
                ocr_text = apply_ocr(pil_img)
                # images
                images = extract_images(page, output_dir)
                # tables
                tables = extract_tables_ocr(pil_img)
                result = {
                    "page_number": page_num,
                    "text": ocr_text,
                    "tables": tables,
                    "images": images
                }                
                ocr_results[page_num] = result
                del pil_img
        return ocr_results                                  
    except Exception as e:
        print(f"OCR failed for page {page_num}")
        return None
    
    

def apply_ocr_fallback(file_path, extracted_data, verification_results, output_dir="extracted_images"): 
    if not verification_results.get('needs_ocr'):
        return extracted_data

    pages_to_ocr = sorted(set(verification_results['needs_ocr']))
    ocr_results = ocr_fallback(file_path, pages_to_ocr, output_dir)
    # Update extracted data
    if ocr_results:
        for page_num, ocr_data in ocr_results.items():
            for page_data in extracted_data['data_per_page']:
                if page_data['page_number'] == page_num:
                    # Replace text with OCR result      
                    page_data['text'] = ocr_data['text']
                    page_data['images'] = ocr_data['images']
                    page_data['tables'] = ocr_data['tables']
                    page_data['verification'] = 'ocr_corrected'
                    
                    original_length = len(page_data['text'])
                    extracted_data['total_text_extracted'] += (len(ocr_data['text']) - original_length)     
    return extracted_data


