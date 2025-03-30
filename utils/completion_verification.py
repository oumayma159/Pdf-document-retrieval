import fitz  
import pdfplumber
import difflib
import camelot
import pandas as pd


# for completeness verification = we will check if all pages are processed / if the text is complete / 
# if images are missing / if tables are missing / if OCR is needed


def verify_completeness(file_path, extracted_data):   
    verification_results = {
        'missing_pages': [],
        'pages_with_missing_text': [],
        'pages_with_missing_images': [],
        'pages_with_missing_tables': [],
        'needs_ocr': [],
    }

    with fitz.open(file_path) as fitz_pdf, pdfplumber.open(file_path) as plumber_pdf:    
        total_pages = len(fitz_pdf)
        if extracted_data['total_pages_treated'] != total_pages:
            verification_results['missing_pages'] = list(
                set(range(1, total_pages+1)) - 
                set([p['page_number'] for p in extracted_data['data_per_page']])
            )
            
        for page_data in extracted_data['data_per_page']:
            page_num = page_data['page_number']

            fitz_page = fitz_pdf.load_page(page_num - 1)  
            plumber_page = plumber_pdf.pages[page_num - 1]
            # text verification (we will use fitz and pdfplumber as reference)
            extracted_text = page_data['text']
            fitz_text = fitz_page.get_text("text").strip()
            plumber_text = plumber_page.extract_text().strip()   
            extracted_vs_fitz = difflib.SequenceMatcher(None, extracted_text, fitz_text).ratio()
            extracted_vs_plumber = difflib.SequenceMatcher(None, extracted_text, plumber_text).ratio()
            if extracted_vs_fitz < 0.8 or extracted_vs_plumber < 0.8:
                verification_results['pages_with_missing_text'].append(page_num)
                if (len(extracted_text) < len(fitz_text) * 0.5 or 
                    min(extracted_vs_fitz, extracted_vs_plumber) < 0.6 or
                    (len(page_data['images']) > 0 and len(extracted_text) < 100)):
                    verification_results['needs_ocr'].append(page_num)
                    
            # image verification (we will use pdfplumber as reference)
            plumber_images = len(plumber_page.images) if hasattr(plumber_page, 'images') else 0
            extracted_images = len(page_data['images'])    
            if plumber_images > extracted_images:
                verification_results['pages_with_missing_images'].append(page_num)
                verification_results['needs_ocr'].append(page_num)
                
            # for tables (we will use camelot as reference)
            original_tables = page_data['tables']
            camelot_lattice = camelot.read_pdf(file_path, pages=str(page_num), flavor='lattice')
            camelot_stream = camelot.read_pdf(file_path, pages=str(page_num), flavor='stream')
            camelot_tables = camelot_lattice if len(camelot_lattice) >= len(camelot_stream) else camelot_stream
            # print(len(camelot_tables))
            if (len(original_tables) < len(camelot_tables)):
                verification_results['pages_with_missing_tables'].append(page_num)
                verification_results['needs_ocr'].append(page_num)
            elif len(original_tables) == len(camelot_tables) and len(original_tables) > 0:
                for orig_tbl, cam_tbl in zip(original_tables, camelot_tables):
                    orig_df = pd.DataFrame(orig_tbl).fillna('')
                    cam_df = cam_tbl.df.fillna('')
                    matches = 0
                    for r in range(min(len(orig_df), len(cam_df))):
                        for c in range(min(len(orig_df.columns), len(cam_df.columns))):
                            if str(orig_df.iloc[r,c]).strip() == str(cam_df.iloc[r,c]).strip():
                                matches += 1
                    total_cells = min(len(orig_df), len(cam_df)) * min(len(orig_df.columns), len(cam_df.columns))
                    similarity = matches / total_cells if total_cells > 0 else 0
                    if similarity < 0.7:
                        verification_results['needs_ocr'].append(page_num)
                        
    return verification_results