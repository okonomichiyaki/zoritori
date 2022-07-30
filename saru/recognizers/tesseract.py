import logging
from io import StringIO
from csv import DictReader
from statistics import median, mean
from itertools import groupby
from dataclasses import dataclass

import pytesseract
from PIL import Image

from saru.types import CharacterData


_logger = logging.getLogger("saru")


def _cast(row):
    """Convert raw strings from Tesseract tsv to appropriate numeric types"""
    for key, value in row.items():
        if key == "conf":
            row[key] = float(value)
        elif key != "text":
            row[key] = int(value)


def _split(row):
    """Split a multi character into individual characters"""
    # tesseract sometimes returns multiple characters together,
    # so split them and calculate the resulting box data:
    result = []
    # bounding boxes are somewhat unreliable, but split the width anyway:
    w = int(row["width"] / len(row["text"]))
    for i, c in enumerate(row["text"]):
        new_data = row.copy()
        new_data["width"] = w
        new_data["text"] = c
        new_data["left"] = row["left"] + w * i
        result.append(new_data)
    return result


def _probably_line_break(c):
    """Infers line break from Tesseract row"""
    return (
        c["conf"] == -1 and c["text"] == ""
    )  # TODO does this mistake spaces for line breaks?


def _fix_line_numbers(cdata):
    """Fixes line numbers in the Tesseract data by detecting line breaks"""
    line_number = 1
    idx = 0

    def skip_line_break():
        nonlocal idx
        while idx < len(cdata) and _probably_line_break(cdata[idx]):
            text = cdata[idx]["text"]
            _logger.debug(f"skipping whitespace {idx} '{text}'")
            idx += 1

    skip_line_break()
    while idx < len(cdata):
        text = cdata[idx]["text"]
        if _probably_line_break(cdata[idx]):
            line_number += 1
            _logger.debug(f"incrementing line number {idx} '{text}' {line_number}")
            skip_line_break()
        else:
            _logger.debug(f"setting line number {idx} '{text}' {line_number}")
            cdata[idx]["line_num"] = line_number
            idx += 1


def _get_extent(line):
    leftmost = line[0]["left"]
    rightmost = line[-1]["left"] + line[-1]["width"]
    return {"top": line[0]["top"], "rightmost": rightmost, "leftmost": leftmost}


def _estimate_gaps(line):
    gaps = []
    for i in range(1, len(line)):
        a = line[i - 1]
        b = line[i]
        gap = b["left"] - a["left"] - a["width"]
        if gap > 0:
            gaps.append(gap)
    if len(gaps) == 0:
        return 0
    return median(gaps)


def _estimate_cwidth(line):
    leftmost = line[0]["left"]
    rightmost = line[-1]["left"] + line[-1]["width"]
    return (rightmost - leftmost) / len(line)


def _get_median(cdata, field):
    values = map(lambda d: d[field], cdata)
    return median(values)


def _calculate_boxes(actuals, lines):
    """Extract bounding box data from Tesseract tsv row"""

    def _calculate_boxes_for_line(actuals, line):
        estimated_cwidth = _estimate_cwidth(line)
        estimated_cheight = _get_median(line, "height")
        estimated_top = _get_median(line, "top")
        extent = _get_extent(line)
        leftmost = extent["leftmost"]
        for i, d in enumerate(line):
            if actuals:
                d["box"] = (d["left"], d["top"], d["width"], d["height"])
            else:
                # actual box data from Tesseract is sometimes wildly off
                # this returns a best estimate, based on median width/top/height per line
                d["box"] = (
                    leftmost + i * estimated_cwidth,
                    estimated_top,
                    estimated_cwidth,
                    estimated_cheight,
                )

    for line in lines:
        _calculate_boxes_for_line(actuals, line)


def _convert_to_cdata(lines):
    """Convert Tesseract tsv rows to CharacterData"""

    def _row_to_cdata(row):
        return CharacterData(
            row["text"],
            row["line_num"],
            row["conf"],
            row["box"][0],
            row["box"][1],
            row["box"][2],
            row["box"][3],
        )

    return [[_row_to_cdata(row) for row in line] for line in lines]


class Recognizer:
    def __init__(self, tesseract_cmd, actual_boxes=False):
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        self.actual_boxes = actual_boxes

    def recognize(self, filename: str) -> list[list[CharacterData]]:
        """
        Extract character data from image (expected path to image file), returns parsed Tesseract data
        Tesseract data headers:
        level, page_num, block_num, par_num, line_num, word_num, left, top, width, height, conf, text
        """
        tsv = pytesseract.image_to_data(Image.open(filename), lang="jpn")
        _logger.debug(f"raw tsv from Tesseract:\n{tsv}")
        f = StringIO(tsv)
        reader = DictReader(f, delimiter="\t")
        lines = []
        for row in reader:
            _cast(row)
            # leave single characters and whitespace alone:
            if len(row["text"]) <= 1:
                lines.append(row)
            else:
                # but split up multi character rows:
                lines.extend(_split(row))
        _fix_line_numbers(lines)
        lines = [c for c in lines if not _probably_line_break(c)]
        lines = [list(it) for k, it in groupby(lines, lambda d: d["line_num"])]
        _calculate_boxes(self.actual_boxes, lines)
        return _convert_to_cdata(lines)
