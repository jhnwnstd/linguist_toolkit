import logging
import multiprocessing
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from PIL import Image
from tqdm import tqdm

# Specify the Tesseract command path if it's not in the system's PATH
# pytesseract.pytesseract.tesseract_cmd = r'<path_to_your_tesseract_executable>'

def check_tesseract_installed(min_version=5):
    """Check if Tesseract is installed and meets the minimum version requirement."""
    try:
        # Run the Tesseract command to get its version
        result = subprocess.run(["tesseract", "--version"], capture_output=True, text=True, check=True)
        # Extract the version number from the output
        match = re.search(r'tesseract (\d+)', result.stdout)
        if match:
            version = int(match.group(1))
            if version >= min_version:
                print(f"Tesseract version {version} is installed.")
                return True
            else:
                print(f"Tesseract version {version} is installed, but version {min_version} or higher is required.")
                return False
        else:
            print("Failed to parse Tesseract version.")
            return False
    except subprocess.CalledProcessError:
        print("Tesseract is not installed or not found in PATH.")
        return False
    except FileNotFoundError:
        print("Tesseract command is not found. Ensure Tesseract is installed and added to your system's PATH.")
        return False


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


def extract_text_from_images(directory: str, tesseract_config: str = '', output_dir: str = None):
    """
    Extract text from images in the specified directory and save the extracted text to a file.
    """
    if output_dir is None:
        output_dir = Path(directory) / "extracted_texts"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "extracted_text.txt"
    output_file.write_text("", encoding="utf-8")  # Clear the output file at the start

    image_paths = [file for file in Path(directory).glob('*') if is_image_file(file.name)]

    executor_workers = min(32, max(4, multiprocessing.cpu_count() + 4))
    with ThreadPoolExecutor(max_workers=executor_workers) as executor:
        future_to_image = {executor.submit(extract_text, image_path, output_file, tesseract_config): image_path for image_path in image_paths}
        
        # Wrap the as_completed iterator with tqdm for progress visualization
        for future in tqdm(as_completed(future_to_image), total=len(future_to_image), desc="Processing Images"):
            image_path = future_to_image[future]
            try:
                future.result()
                logging.info(f"Processed: {image_path}")
            except Exception as e:
                logging.error(f"Failed to process {image_path}: {e}")


if __name__ == "__main__":
    if not check_tesseract_installed():
        print("Exiting due to Tesseract requirements not being met.")
    else:
        directory_path = input("Enter the directory path to scan for images: ")

        # Set the default Tesseract configuration to use English and LSTM engine
        default_tesseract_config = "-l eng --oem 1"
        user_input = input(f"Enter Tesseract configuration options (default is '{default_tesseract_config}'). Press Enter to use default or specify new options: ")
        tesseract_config = user_input.strip() if user_input.strip() else default_tesseract_config

        extract_text_from_images(directory_path, tesseract_config)
        print("Text extraction completed.")
