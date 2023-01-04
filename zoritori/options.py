import configargparse


def get_options():
    parser = configargparse.ArgParser(
        default_config_files=["config.ini"],
        description="Capture Japanese text from a screenshot or from the screen",
    )
    parser.add("-d", "--debug", action="store_true")
    parser.add("-n", "--no-watch", action="store_true")
    parser.add("-t", "--translate", action="store_true")
    parser.add("-p", "--parts-of-speech", action="store_true")
    parser.add("--fullscreen", action="store_true")
    parser.add(
        "-l", "--log-level", default="info", choices=["info", "debug"], action="store"
    )
    parser.add(
        "-f",
        "--furigana",
        default="none",
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
        "--engine",
        default="tesseract",
        choices=["tesseract", "google"],
        action="store",
        help=("Determines the OCR engine to use."),
    )
    parser.add(
        "--TesseractExePath", action="store", help=("Path to Tesseract executable")
    )
    parser.add("--DeepLUrl", action="store", help=("DeepL API translate URL"))
    parser.add("--DeepLKey", action="store", help=("DeepL API key"))
    parser.add("--NotesFolder", action="store", help=("Path to notes folder. If present, all notes and screenshots will be saved here."))
    parser.add("--NotesRoot", action="store", help=("Path to notes parent folder. If present, and NotesFolder is absent, will save notes and screenshots for each session as a new folder"))
    parser.add("--NotesPrefix", action="store", help=("Prefix for session folders"))
    parser.add("--ClickThroughMode", action="store_true", help=("If true, allow mouse clicks to pass through transparent window. Windows-only"))
    parser.add(
        "-c", "--config", required=True, is_config_file=True, help="Path to config file"
    )
    parser.add(
        "filename",
        metavar="filename",
        type=str,
        nargs="?",
        default=None,
        help="Path to a screenshot. If present, will output JSON; if absent, will start overlay.",
    )
    return parser.parse_args()
