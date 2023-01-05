There are a lot of alternatives to `zoritori`, some of which inspired its development, and one of them may suit your needs better.

## text extraction

There seem to be two main approaches to the problem of extracting text from video games for analysis: optical character recognition (OCR) and ["text hooking"](https://www.reddit.com/r/visualnovels/wiki/vnhooking/). This list is focused on tools using OCR, because that is what `zoritori` uses.

## comparisons

[Capture2Text](https://capture2text.sourceforge.net/) plus [JL](https://github.com/rampaa/JL)
* Windows only
* OCR via Tesseract
* dictionary lookup via hover

[Game2Text](https://game2text.com/)
* cross platform (Mac and Windows support, maybe Linux?)
* OCR via Tesseract or OCR Space
* translation via DeepL, Papago, and Google
* also supports text hooking for visual novels
* watches screen for changes
* dictionary lookup via hover (using browser plugins like Yomichan and Rikaichan)

[Universal Game Translator](https://www.codedojo.com/?p=2426)
* Windows only
* supports multiple languages
* OCR via Google Cloud Vision
* translation via Google or DeepL
* translations are overlaid on top of original text, with a hotkey to see the original text and look up words by clicking on them
* includes an [export to HTML](https://twitter.com/rtsoft/status/1357498198223278080) function for lookup via browser plugins

[pyugt](https://github.com/lrq3000/pyugt)
* supposedly cross platform, but README says it is untested on Linux and Mac
* supports multiple languages
* OCR via Tesseract
* translation via Google
* translations are displayed in a separate window along with the original text
