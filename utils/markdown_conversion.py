import os


def convert_text_to_markdown(text):
    return (
        "\n".join(
            [
                line["text"]
                .replace("\\", "\\\\")
                .replace("*", "\\*")
                .replace("_", "\\_")
                + "  "
                for line in text["lines"]
            ]
        )
        + "\n\n"
    )


def convert_table_to_markdown(table):
    rows = table["rows"]

    if not rows:
        return "<!-- Empty table -->\n\n"

    markdown_content = "| " + " | ".join(str(cell) for cell in rows[0]) + " |\n"
    markdown_content += "| " + " | ".join(["---"] * len(rows[0])) + " |\n"

    markdown_content += (
        "\n".join(
            "| "
            + " | ".join(
                str(cell).replace("\n", " ").replace("|", "\\|") if cell else ""
                for cell in row
            )
            + " |"
            for row in rows[1:]
        )
        + "\n\n"
    )

    return markdown_content


def convert_image_to_markdown(image):
    return f"![Image {image['name']}]({image['path']})\n\n"


def convert_ocr_to_markdown(data):
    markdown_content = "## OCR Fallback\n\n"
    markdown_content += convert_data_to_markdown(data)

    return markdown_content


def convert_fallback(item):
    print(f"Unknown item type: {item.get('type')}")

    return "<!-- Unknown item -->\n\n"


def convert_data_to_markdown(data):
    markdown_content = ""

    convert = {
        "text": convert_text_to_markdown,
        "table": convert_table_to_markdown,
        "image": convert_image_to_markdown,
        "ocr": convert_ocr_to_markdown,
    }

    for item in data:
        markdown_content += convert.get(item["type"], convert_fallback)(item)

    return markdown_content


def convert_document_to_markdown(extracted_data):
    markdown_content = "# PDF Extraction Result\n\n"
    markdown_content += f"- Total Pages: {extracted_data['total_pages_treated']}\n"
    markdown_content += (
        f"- Total Text Characters: {extracted_data['total_text_extracted']}\n"
    )
    markdown_content += f"- Total Images: {extracted_data['total_images_extracted']}\n"
    markdown_content += (
        f"- Total Tables: {extracted_data['total_tables_extracted']}\n\n"
    )

    for page in extracted_data["pages"]:
        page_content = f"## Page {page['page_number']}\n\n"
        page_content += convert_data_to_markdown(page["contents"])
        page_content += "---\n\n"

        markdown_content += page_content

    return markdown_content[:-1]


def save_markdown(markdown_content, output_path, file_name):
    os.makedirs(output_path, exist_ok=True)
    md_file_path = os.path.join(output_path, f"{file_name}.md")

    with open(md_file_path, "w", encoding="utf-8") as md_file:
        md_file.write(markdown_content)
