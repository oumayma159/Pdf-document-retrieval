import os

def convert_text_to_markdown(md_text):
    if not md_text:
        return ""
    return md_text.replace('\\', '\\\\').replace('*', '\\*').replace('_', '\\_') + '\n\n'
   

def convert_images_to_markdown(images, markdown_text, page_num):
    if not images:
        return markdown_text
    for i, img in enumerate(images, 1):
        if isinstance(img, dict) and 'path' in img:
            markdown_text += f"![Image {i} from page {page_num+1}]({img['path']})\n\n"
        elif hasattr(img, 'save'): 
            markdown_text += f"<!-- Image {i} from page {page_num+1} (not saved) -->\n\n"   
    return markdown_text
    
       
def convert_tables_to_markdown(tables, markdown_text):
    if not tables:
        return markdown_text
    
    markdown_text += "### Tables\n\n"   
    for i, table in enumerate(tables, 1):
        if isinstance(table, dict):
            rows = table.get('rows', [])
            header = table.get('header')
        else:
            rows = table
            header = None
            
        if not rows:
            markdown_text += f"**Table {i}**\n\n<!-- Empty table -->\n\n"
            continue
        if header:
            markdown_text += f"**Table {i}**\n\n"
            markdown_text += "| " + " | ".join(str(cell) for cell in header) + " |\n"
            markdown_text += "| " + " | ".join(["---"] * len(header)) + " |\n"
        for row in rows:
            markdown_text += "| " + " | ".join(str(cell).replace('\n', ' ').replace('|', '\\|') if cell else "" for cell in row) + " |\n" 
        markdown_text += '\n'  
    return markdown_text


def convert_to_markdown(extracted_data):
    markdown_content = "# PDF Extraction Result\n\n"
    markdown_content += f"- Total Pages: {extracted_data['total_pages_treated']}\n"
    markdown_content += f"- Total Text Characters: {extracted_data['total_text_extracted']}\n"
    markdown_content += f"- Total Images: {extracted_data['total_images_extracted']}\n"
    markdown_content += f"- Total Tables: {extracted_data['total_tables_extracted']}\n\n"  
    for page in extracted_data['data_per_page']:
        page_content = f"## Page {page['page_number']+1}\n\n"      
        if page['text']:
            page_content += convert_text_to_markdown(page['text'])
        if page['tables']:
            page_content = convert_tables_to_markdown(page['tables'], page_content)
        if page['images']:
            page_content = convert_images_to_markdown(page['images'], page_content,page['page_number'])     
        markdown_content += page_content + "\n---\n\n"    
    return markdown_content


def save_markdown(markdown_content, output_path, file_name):
    os.makedirs(output_path, exist_ok=True)  
    md_file_path = os.path.join(output_path, f"{file_name}.md")
    with open(md_file_path, "w", encoding="utf-8") as md_file:
        md_file.write(markdown_content)



        
