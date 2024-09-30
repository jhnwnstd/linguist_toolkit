import re
from pathlib import Path
from typing import List
import nltk

def process_subtitle_file(input_file: Path) -> List[str]:
    """
    Processes the subtitle file by removing redundancy, cleaning up text,
    and tokenizing sentences using NLTK, while preserving punctuation.

    Args:
        input_file (Path): Path to the subtitle file.

    Returns:
        List[str]: A list of tokenized sentences.
    """
    # Initialize variables
    current_text = ''
    previous_text = ''

    # Regular expressions for cleaning
    timestamp_regex = re.compile(r'<\d{2}:\d{2}:\d{2}\.\d{3}>')
    tag_regex = re.compile(r'</?c>')
    timecode_line_regex = re.compile(
        r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}.*'
    )

    # Read and process the file line by line
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(('WEBVTT', 'Kind:', 'Language:')):
                continue
            if timecode_line_regex.match(line):
                continue
            if 'align:' in line or 'position:' in line:
                continue
            # Remove inline timestamps and tags
            cleaned_line = timestamp_regex.sub('', line)
            cleaned_line = tag_regex.sub('', cleaned_line)
            cleaned_line = cleaned_line.strip()
            if not cleaned_line:
                continue
            if cleaned_line != previous_text:
                current_text += ' ' + cleaned_line
                previous_text = cleaned_line

    # Ensure punctuation is preserved
    current_text = current_text.strip()

    # Tokenize sentences using NLTK
    nltk.download('punkt', quiet=True)
    sentences = nltk.sent_tokenize(current_text)

    return sentences

def main():
    # Path to the Subtitles folder
    subtitle_folder = Path('Subtitles')

    # Path to the Cleaned Subtitles folder
    cleaned_subtitles_folder = Path('Cleaned Subtitles')
    cleaned_subtitles_folder.mkdir(parents=True, exist_ok=True)  # Create folder if it doesn't exist

    # Iterate over all .vtt files in the Subtitles folder
    for subtitle_file in subtitle_folder.glob('*.vtt'):
        print(f"Processing file: {subtitle_file}")

        # Process the subtitle file
        sentences = process_subtitle_file(subtitle_file)

        # Generate a cleaned subtitle filename
        cleaned_file = cleaned_subtitles_folder / subtitle_file.name

        # Write the cleaned sentences to the new file
        with open(cleaned_file, 'w', encoding='utf-8') as f:
            for idx, sentence in enumerate(sentences, 1):
                f.write(f"{idx}. {sentence}\n")
        
        print(f"Saved cleaned subtitles to: {cleaned_file}")

if __name__ == '__main__':
    main()