# 🐒 saru 猿

a tool to help you read text in Japanese video games

## features

* adds furigana to kanji
* color code proper nouns (like NHK News Web Easy)
* quickly look up words in Jisho and Wikipedia
* automatically collects vocabulary
* English subtitles via machine translation

Note: This is very much a work in progress and is rough around the edges.

## requirements

* Windows (tested on Windows 10)
* Python (tested with 3.10)
* [Poetry](https://python-poetry.org/)
* either [Tesseract](https://tesseract-ocr.github.io/)...
* ... or a [Google Cloud Vision API](https://cloud.google.com/vision) account
* (optional) DeepL API account for subtitles

## installation

1. [Install Python 3](https://docs.python.org/3/using/windows.html) (tested with version 3.10)
2. [Install Poetry](https://python-poetry.org/docs/#installation)
3. Clone this repository
4. Install requirements: `poetry install`
6. If using Tesseract, configure it by specifying the path to `tesseract.exe` in `config.ini`
7. If using Google Cloud Vision, add credentials to your shell's environment variable: `$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\json"`
8. (optional) Configure for DeepL by specifying the API key in `example-config.ini`
9. (optional) Configure directory for saving vocabulary in `example-config.ini`

## usage

Start: `poetry run python -m saru -e <tesseract|google> -c .\config.ini`.
Optionally specify furigana with the argument `--furigana`, and subtitles with the argument `--translate`.
See more details using `--help`.

After starting the program there should be an invisible window with an icon in your taskbar. Make sure this is the active window, and then select a region on the screen to watch. Do this by holding the `r` key and moving your mouse cursor (do not press any mouse buttons). You should see a green rectangle where you're selecting. Once you release the `r` key, `saru` will watch that region of the screen for changes.
