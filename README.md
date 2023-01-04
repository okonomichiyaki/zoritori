# zōritori 草履取り

yet another tool to help Japanese language learners read text in video games

## features

* annotate kanji with furigana
* color code proper nouns (like NHK News Web Easy)
* look up words on mouse hover, or open Jisho or Wikipedia
* automatically collect vocabulary with context
* (optional) English subtitles via machine translation

![Taiko Risshiden V](/screenshots/taiko1.png?raw=true "Taiko Risshiden V")

This is a work in progress and is rough around the edges.

## requirements:

* Windows, Linux, or Mac (tested on Windows 10, Ubuntu 22.04, and macOS Montery
* Python 3.10.x)
* either Tesseract or a Google Cloud Vision API account
* *(optional) DeepL API account for machine translated subtitles*
* *(Linux only) scrot, python3-tk, python3-dev. X11 only for now, Wayland may not work*

## installation:

* install Python 3.10.x
* install `zoritori` via pip (optionally via pipx, recommended)
* download the example config file from [here](https://github.com/okonomichiyaki/zoritori/blob/main/config.ini)
* if using Tesseract, [follow these instructions](https://github.com/tesseract-ocr/tesseract) to install it, then configure it by specifying the path to the `tesseract` binary in `config.ini`
* if using Google Cloud Vision, [follow these steps](https://cloud.google.com/vision/docs/detect-labels-image-client-libraries) to create a project and download a credentials JSON file. then add that as an environment variable: `$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\json"`

## usage

* start: `zoritori -e <tesseract|google> -c /path/to/config.ini`
* an invisible window (with title "zoritori") should appear. make sure this window has focus
* identify the region of the screen containing text you want to read
* using your mouse, (left) click and drag a rectangle around the text
* after a moment, you should see furigana over any kanji in the region, and proper nouns highlighted (blue, orange, and green boxes). hovering over words inside the region should display a dictionary result, if one is found

### keyboard shortcuts

| key | Description |
| ----------- | ----------- |
| T | toggle translation    |
| C | manual refresh        |
| J | open Jisho search for word under cursor |
| W | open Japanese Wikipedia search for word under cursor |
| E | open English Wikipedia search for word under cursor  |
| R + mouse-drag | select main region when in click through mode |
| Q + mouse-drag | select one time lookup when in click through mode |

## more options/etc

### secondary clipping

After selecting a region, `zoritori` will watch that area for changes, and refresh if any are detected. If you want to select a new region, just click and drag again. If you want to keep your original region, but want to do a one-time look up a word outside the region, right click and drag around the word.

### click through mode

By default, the transparent overlay won't send clicks through to underlying applications, including your game. It will steal focus if you click anywhere on the screen. On Windows only (for now) you can enable click through mode in the `config.ini` file or command-line parameters. On Mac and Linux, this is not supported at the moment.

When click through mode is enabled, use R (without mouse clicking) to drag select a region, and use Q to select a region for a one-time lookup.

### comparing OCR engines

Tesseract is free, open source, and works offline. Unfortunately, in my experience it has less accurate recognition, and sometimes returns very messy bounding box data, making it difficult to accurately place furigana.

Google Cloud Vision has [per usage costs](https://cloud.google.com/vision/pricing), but should be free for low usage, and is closed source and requires an Internet connection (the selected region is sent as an image to Google for processing)

### saving vocabulary

By default nothing is saved. But if you want to save vocabulary words, add a folder name in the `config.ini` file or command-line parameters. 

With only `NotesFolder` set, all vocabulary will be saved in one folder. Fullscreen screenshots are saved each time OCR runs, along with a markdown file that include new vocabulary found, for later review.

With only `NotesRoot` set, vocabulary will be saved as above but inside individual folders for each session (once for each time you start `zoritori`) to make review less cumbersome.

With both `NotesFolder` and `NotesRoot` set, `NotesFolder` behavior takes precedence (everything saved in one folder).
