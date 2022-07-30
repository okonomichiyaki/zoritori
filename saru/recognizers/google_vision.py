import io
import os
import sys
from itertools import groupby

from google.cloud import vision_v1 as vision

from saru.types import CharacterData


class Recognizer:
    def __init__(self):
        self._client = vision.ImageAnnotatorClient()

    def recognize(self, path) -> list[list[CharacterData]]:
        response = self._detect_text(path)
        return self._collect_symbols(response)

    def _detect_text(self, path):
        with io.open(path, "rb") as image_file:
            content = image_file.read()
        image = vision.Image(content=content)
        response = self._client.text_detection(image=image)
        if response.error.message:
            raise Exception(
                "{}\nFor more info on error messages, check: "
                "https://cloud.google.com/apis/design/errors".format(
                    response.error.message
                )
            )
        return response

    def _collect_symbols(self, response):
        annotation = response.full_text_annotation

        def has_line_break(symbol):
            line_break = vision.types.TextAnnotation.DetectedBreak.BreakType.LINE_BREAK
            return (
                symbol.property and symbol.property.detected_break.type_ == line_break
            )

        line_number = 0
        lines = []
        line = []
        for page in annotation.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        for symbol in word.symbols:
                            cdata = self._convert(symbol, line_number)
                            line.append(cdata)
                            if has_line_break(symbol):
                                line_number += 1
                                lines.append(line)
                                line = []
        return lines

    def _convert(self, symbol, line_number):
        vertices = symbol.bounding_box.vertices
        upper_left = vertices[0]
        lower_right = vertices[2]
        x = upper_left.x
        y = upper_left.y
        w = lower_right.x - x
        h = lower_right.y - y
        text = symbol.text
        conf = 100.0  # symbol.confidence # TODO ?
        return CharacterData(text, line_number, conf, x, y, w, h)
