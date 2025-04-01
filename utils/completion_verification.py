import pdfplumber
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

tokenizer = AutoTokenizer.from_pretrained("textattack/distilbert-base-uncased-CoLA")
model = AutoModelForSequenceClassification.from_pretrained("textattack/distilbert-base-uncased-CoLA")

# for completeness verification = we will check page coverage/ linguistic acceptability/

    
def check_linguistic_acceptability(texts, threshold=0.7):
    if not texts:
        return 0.0
    accepted = 0
    for text in texts:
        inputs = tokenizer(text, return_tensors="pt", truncation=True)
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=1)
        if probs[0][1] > threshold:
            accepted += 1
    return accepted / len(texts)
    

def verify_completeness(file_path, extracted_data): 
    with pdfplumber.open(file_path) as pdf:
        for page_data in extracted_data['data_per_page']:
            page_num = page_data['page_number'] - 1
            page = pdf.pages[page_num]
            # Check page textual coverage
            page_height = page.height
            text_blocks = [
                b for b in page_data["ordered_content"]
                if b["type"] == "text" and "top" in b and "bottom" in b
            ]
            total_text_height = sum(b["bottom"] - b["top"] for b in text_blocks)
            page_coverage = total_text_height / page_height
            # Check linguistic acceptability
            text_sentences = [b["content"] for b in text_blocks if b["content"].strip()]
            acceptability_ratio = check_linguistic_acceptability(text_sentences)
            
            if (page_coverage < 0.25) or (acceptability_ratio < 0.5):
                page_data["verification"] = "needs_ocr"
            else:
                page_data["verification"] = "complete"
    return extracted_data
                 
