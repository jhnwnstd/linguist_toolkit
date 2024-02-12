# linguist_tools
Python and coding tools for collecting text and audio data.

## Using you2wav.py

### Before running the script, make sure to install the required libraries using pip:
`pip install pytube`

Ensure that FFmpeg is installed on your system and added to the system's PATH environment variable.

You can download FFmpeg from https://ffmpeg.org/download.html and follow the installation instructions for your operating system.

### You can downalod FFmpeg with chocolatey on Windows by running the following command in the terminal:
`choco upgrade all -y`

`choco install ffmpeg`

### You can download FFmpeg with Homebrew on macOS by running the following command in the terminal:
`brew update`

`brew upgrade`

`brew install ffmpeg`

### You can download FFmpeg with apt on Ubuntu by running the following command in the terminal:
`sudo apt update && sudo apt upgrade`

`sudo apt install ffmpeg`

## Using image_to_text.py

### Before running the script, make sure to install the required libraries using pip:
`pip install pytesseract opencv-python-headless Pillow tqdm`

Ensure that Tesseract OCR is installed on your system and added to the system's PATH environment variable. Tesseract OCR is an open-source OCR engine used for text recognition.

You can download Tesseract OCR from https://github.com/tesseract-ocr/tesseract. Follow the installation instructions for your operating system.

### You can install Tesseract OCR with chocolatey on Windows by running the following command in the terminal:
`choco upgrade all -y`

`choco install tesseract`

### You can install Tesseract OCR with Homebrew on macOS by running the following command in the terminal:
`brew update`

`brew upgrade`

`brew install tesseract`

### You can install Tesseract OCR with apt on Ubuntu by running the following command in the terminal:
`sudo apt update && sudo apt upgrade`

`sudo apt install tesseract-ocr`
