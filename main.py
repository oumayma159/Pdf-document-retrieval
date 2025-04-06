from utils.information_extraction import extract_all
from utils.completion_verification import get_pages_to_verify
from utils.fallback import apply_ocr_fallback
from utils.markdown_conversion import convert_document_to_markdown, save_markdown


file_path = "data/pdf/multiple.pdf"
output_dir = "results"
output_file = "result"


if __name__ == "__main__":
    extracted_data = extract_all(file_path, results_dir=output_dir)

    print("Extraction completed. Data ready for verification.")

    pages_to_verify = get_pages_to_verify(file_path, extracted_data)

    if pages_to_verify:
        print(f"Applying OCR to pages: {pages_to_verify}")
        extracted_data = apply_ocr_fallback(file_path, extracted_data, pages_to_verify)

    markdown_content = convert_document_to_markdown(extracted_data)
    save_markdown(
        markdown_content=markdown_content, output_path=output_dir, file_name=output_file
    )

    print("Successfully saved results")
