import configargparse


def get_options():
    parser = configargparse.ArgParser(
        default_config_files=["config.ini"],
        description="Capture Japanese text from a screenshot or from the screen",
    )
    parser.add("-d", "--debug", action="store_true")
    parser.add("-n", "--no-watch", action="store_true")
    parser.add(
        "-l", "--log-level", default="info", choices=["info", "debug"], action="store"
    )
    parser.add(
        "-c", "--config", required=True, is_config_file=True, help="Path to config file"
    )
    parser.add(
        "-f",
        "--Furigana",
        default="all",
        choices=["none", "some", "all", "hover"],
        action="store",
        help=(
            "Determines the level of furigana attached to kanji. "
            "If `some`, only include for proper nouns; if `all`, include for all kanji."
        ),
    )
    parser.add(
        "--FuriganaSize", action="store", type=int, help=("Font size for furigana")
    )
    parser.add(
        "--SubtitleSize", action="store", type=int, help=("Font size for subtitles")
    )
    parser.add(
        "--SubtitleMargin", action="store", type=int, help=("Margin between subtitles")
    )
    parser.add(
        "-e",
        "--Engine",
        default="tesseract",
        choices=["tesseract", "google"],
        action="store",
        help=("Determines the OCR engine to use."),
    )
    parser.add(
        "--TesseractExePath", action="store", help=("Path to Tesseract executable")
    )
    parser.add("-t", "--Translate", action="store_true")
    parser.add("--Fullscreen", action="store_true", help=(
        "If true, attempts to detect any and all text on the screen.",
        "This is slower and less reliable then using a specific region.",
        "Only really works with Google Cloud Vision API."
    ))
    parser.add("--ProperNouns", action="store_true", default=True)
    parser.add("--DeepLUrl", action="store", help=("DeepL API translate URL"))
    parser.add("--DeepLKey", action="store", help=("DeepL API key"))
    parser.add("--NotesFolder", action="store", help=("Path to notes folder. If present, all notes and screenshots will be saved here."))
    parser.add("--NotesRoot", action="store", help=("Path to notes parent folder. If present, and NotesFolder is absent, will save notes and screenshots for each session as a new folder"))
    parser.add("--NotesPrefix", action="store", help=("Prefix for session folders"))
    parser.add("--ClickThroughMode", action="store_true", help=("If true, allow mouse clicks to pass through transparent window. Windows-only"))
    return parser.parse_args()
