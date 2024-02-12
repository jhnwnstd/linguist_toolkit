import os
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from PIL import Image

# Specify the Tesseract command path if it's not in the system's PATH
# pytesseract.pytesseract.tesseract_cmd = r'<path_to_your_tesseract_executable>'


def is_image_file(filename: str) -> bool:
    """Check if a file is an image based on its extension."""
    return re.search(r'\.(jpe?g|png|gif|bmp|tiff?)$', filename, re.IGNORECASE) is not None


def preprocess_image(image_path: Path) -> Image.Image:
    """Preprocess the image for improved OCR accuracy."""
    image_cv = cv2.imread(str(image_path))
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binarized = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    kernel = np.ones((1, 1), np.uint8)
    img_dilated = cv2.dilate(binarized, kernel, iterations=1)
    img_eroded = cv2.erode(img_dilated, kernel, iterations=1)

    scale_percent = 150  # percent of original size
    width = int(img_eroded.shape[1] * scale_percent / 100)
    height = int(img_eroded.shape[0] * scale_percent / 100)
    resized = cv2.resize(img_eroded, (width, height), interpolation=cv2.INTER_AREA)

    return Image.fromarray(resized)


def extract_text(image_path: Path, output_file: Path, tesseract_config: str = ''):
    """Extract text from a single image and append it to the output file."""
    try:
        image = preprocess_image(image_path)
        text = pytesseract.image_to_string(image, config=tesseract_config)
        with output_file.open("a", encoding="utf-8") as file_out:
            file_out.write(f"--- {image_path.name} ---\n{text}\n\n")
        print(f"Processed: {image_path.name}")
    except Exception as e:
        print(f"Failed to process {image_path.name}: {e}")


def extract_text_from_images(directory: str, tesseract_config: str = ''):
    output_dir = Path(directory) / "extracted_texts"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "extracted_text.txt"
    output_file.write_text("", encoding="utf-8")  # Clear the output file at the start

    image_paths = [Path(root) / file for root, _, files in os.walk(directory) for file in files if is_image_file(file)]

    with ThreadPoolExecutor() as executor:
        executor.map(extract_text, image_paths, [output_file] * len(image_paths), [tesseract_config] * len(image_paths))


if __name__ == "__main__":
    directory_path = input("Enter the directory path to scan for images: ")
    tesseract_config = input("Enter Tesseract configuration options (e.g., '-l eng --oem 1'): ")
    extract_text_from_images(directory_path, tesseract_config)
    print("Text extraction completed.")
