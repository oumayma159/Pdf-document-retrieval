import pdfplumber
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch.nn.functional as F
import numpy as np

tokenizer = AutoTokenizer.from_pretrained("textattack/distilbert-base-uncased-CoLA")
model = AutoModelForSequenceClassification.from_pretrained(
    "textattack/distilbert-base-uncased-CoLA"
)

# for completeness verification, we will check the surface of each image
# individually and the linguistic acceptability of each paragraph


def check_linguistic_acceptability(paragraphs):
    linguistic_acceptabilities = []

    for text in paragraphs:
        inputs = tokenizer(text, return_tensors="pt", truncation=True)
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=1)

        linguistic_acceptabilities.append(probs[0][1].item())

    return np.mean(linguistic_acceptabilities)


def get_pages_to_verify(file_path, extracted_data):
    pages_to_verify = []

    with pdfplumber.open(file_path) as pdf:
        for page_data in extracted_data["pages"]:
            page_num = page_data["page_number"] - 1
            page_contents = page_data["contents"]

            page = pdf.pages[page_num]

            # Check the surface of each image
            surface_threshold = 0.7 * (page.height * page.width)

            if any(
                ((item["x1"] - item["x0"]) * (item["bottom"] - item["top"]))
                > surface_threshold
                for item in page_contents
                if item["type"] == "image"
            ):
                pages_to_verify.append(page_num)

                continue

            # Check linguistic acceptability
            linguistic_acceptability_threshold = 0.7

            paragraphs = [
                " ".join(line["text"] for line in item["lines"])
                for item in page_contents
                if item["type"] == "text"
            ]

            if not paragraphs:
                continue

            linguistic_acceptability = check_linguistic_acceptability(paragraphs)

            if linguistic_acceptability < linguistic_acceptability_threshold:
                pages_to_verify.append(page_num)

    return pages_to_verify
