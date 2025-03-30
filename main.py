from utils.information_extraction import extract_all
from utils.completion_verification import verify_completeness
from utils.fallback import apply_ocr_fallback
from utils.markdown_conversion import convert_to_markdown, save_markdown


file_path = "C:/Users/dell/Desktop/TECH/ML-AI/LLMs/PDFdocumentRetrieval/data/pdf/multiple.pdf" 
output_dir = "C:/Users/dell/Desktop/TECH/ML-AI/LLMs/PDFdocumentRetrieval/results"
output_file = "result"  # primary result
output_file2 = "output2.md"  # Additional cleaning output


if __name__ == "__main__":
    # Extract content
    extracted_data = extract_all(file_path)
    print(extracted_data)
    print("Extraction completed. Data ready for verification.")
    
    verification = verify_completeness(file_path, extracted_data)
    print(verification)
    print("Verification completed. Data ready for reprocessing/conversion.")
    
    if verification['needs_ocr']:
        # Reprocess pages that need OCR
        print(f"Applying OCR to pages: {verification['needs_ocr']}")
        extracted_data = apply_ocr_fallback(file_path, extracted_data, verification, output_dir="extracted_images")
    
    markdown_content = convert_to_markdown(extracted_data)
    save_markdown(markdown_content=markdown_content,output_path=output_dir,file_name=output_file)
    print("Successfully saved results")
    

    

    

