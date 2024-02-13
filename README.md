# linguist_tools
Python and coding tools for collecting text and audio data. This suite includes tools for downloading YouTube videos as audio files, converting images to text using OCR, and converting text or tokens to audio.

## Using you2wav.py

### Before running the script, make sure to install the required libraries using pip:
```sh
pip install pytube
```

Ensure that FFmpeg is installed on your system and added to the system's PATH environment variable.

You can download FFmpeg from https://ffmpeg.org/download.html and follow the installation instructions for your operating system.

### FFmpeg Installation Commands

- **Windows**:
  ```sh
  choco upgrade chocolatey -y
  choco install ffmpeg
  choco upgrade all -y
  ```

- **macOS**:
  ```sh
  brew update
  brew upgrade
  brew install ffmpeg
  ```

- **Ubuntu**:
  ```sh
  sudo apt update && sudo apt upgrade
  sudo apt install ffmpeg
  ```

## Using image_to_text.py

### Before running the script, make sure to install the required libraries using pip:
```sh
pip install numpy pytesseract opencv-python-headless Pillow tqdm
```

Ensure that Tesseract OCR is installed on your system and added to the system's PATH environment variable. Tesseract OCR is an open-source OCR engine used for text recognition.

You can download Tesseract OCR from https://github.com/tesseract-ocr/tesseract. Follow the installation instructions for your operating system.

### Tesseract OCR Installation Commands

- **Windows**:
  ```sh
  choco upgrade all -y
  choco install tesseract
  ```

- **macOS**:
  ```sh
  brew update
  brew upgrade
  brew install tesseract
  ```

- **Ubuntu**:
  ```sh
  sudo apt update && sudo apt upgrade
  sudo apt install tesseract-ocr
  ```

## Using tok2wav.py [UNDER CONSTRUCTION]

This tool converts downloads tiktok videos extracts the audio and converts it to a wav file.


## Using you2txt.py [UNDER CONSTRUCTION]

This tool downloads the subtitles of a YouTube video and saves them to a text file.