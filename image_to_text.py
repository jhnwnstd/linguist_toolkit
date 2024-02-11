import os
import pytesseract
from PIL import Image, ImageFilter, ImageOps
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import re
import cv2
import numpy as np

# Specify the Tesseract command path if it's not in the system's PATH
# pytesseract.pytesseract.tesseract_cmd = r'<path_to_your_tesseract_executable>'

def is_image_file(filename: str) -> bool:
    """Check if a file is an image based on its extension."""
    return re.search(r'\.(jpe?g|png|gif|bmp|tiff?)$', filename, re.IGNORECASE) is not None

def preprocess_image(image_path: Path) -> Image.Image:
    """Preprocess the image for improved OCR accuracy."""
    # Open the image using OpenCV
    image_cv = cv2.imread(str(image_path))
    
    # Convert to grayscale
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur for noise reduction
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Apply adaptive thresholding (Otsu's method)
    _, binarized = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Dilation and erosion to strengthen the text
    kernel = np.ones((1, 1), np.uint8)
    img_dilated = cv2.dilate(binarized, kernel, iterations=1)
    img_eroded = cv2.erode(img_dilated, kernel, iterations=1)
    
    # Scaling the image
    scale_percent = 150 # percent of original size
    width = int(img_eroded.shape[1] * scale_percent / 100)
    height = int(img_eroded.shape[0] * scale_percent / 100)
    dim = (width, height)
    resized = cv2.resize(img_eroded, dim, interpolation = cv2.INTER_AREA)
    
    # Convert back to PIL image
    final_image = Image.fromarray(resized)
    
    return final_image

def extract_text(image_path: Path, output_file: Path, tesseract_config: str = '') -> None:
    """Extract text from a single image and append it to the output file."""
    try:
        image = preprocess_image(image_path)
        text = pytesseract.image_to_string(image, config=tesseract_config)
        with output_file.open("a", encoding="utf-8") as file_out:
            file_out.write(f"--- {image_path.name} ---\n{text}\n\n")
        print(f"Processed: {image_path.name}")
    except Exception as e:
        print(f"Failed to process {image_path.name}: {e}")

def extract_text_from_images(directory: str, tesseract_config: str = '') -> None:
    output_dir = Path(directory) / "extracted_texts"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "extracted_text.txt"
    output_file.write_text("", encoding="utf-8")  # Clear the output file at the start

    image_paths = [Path(root) / file for root, _, files in os.walk(directory) for file in files if is_image_file(file)]

    with ThreadPoolExecutor() as executor:
        for image_path in image_paths:
            executor.submit(extract_text, image_path, output_file, tesseract_config)

if __name__ == "__main__":
    directory_path = input("Enter the directory path to scan for images: ")
    tesseract_config = input("Enter Tesseract configuration options (e.g., '-l eng --oem 1'): ")
    extract_text_from_images(directory_path, tesseract_config)
    print("Text extraction completed.")
