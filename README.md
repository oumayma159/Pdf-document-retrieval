# Pdf-document-retrieval

This project extracts the contents of PDF files and stores them as Markdown.

## Key Features

* Extract text, images and tables.
* Respect the layout of the files.
* Offer fallback extraction using OCR for pages which are:
  * Mostly invalid paragraphs.
  * Mainly a single image.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

The things you need before installing the software.

* [Python](https://www.python.org/)
* [pip](https://pip.pypa.io/en/stable/installation/)

### Setup

A step by step guide that will tell you how to get the development environment up and running.

1. Clone the repository.

    ```sh
   git clone https://github.com/oumayma159/Pdf-document-retrieval.git
    ```

1. Create a virtual environment.

    ```sh
    python -m venv .venv
    ```

1. Activate the virtual environment.

    ```sh
    # On Windows
    ./.venv/Scripts/activate
    # On Linux
    source ./.venv/bin/activate
    ```

1. Install the requirements.

    ```sh
    python -m pip install -r requirements.txt
    ```

    For GPU acceleration, you can visite PyTorch’s [Start Locally](https://pytorch.org/get-started/locally/) page.

## Usage

1. Choose the pdf file to convert using the `file_path` variable.
1. Choose the location and the name of the output file using the `output_dir` and the `output_file` variables respectively.
1. Convert the file.

    ```sh
    python main.py
    ```
