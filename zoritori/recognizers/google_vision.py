import logging
import time
import io
import os
import sys
from itertools import groupby

from google.cloud import vision_v1 as vision

from zoritori.types import CharacterData, BlockData, RawData, Box
from zoritori.recognizers.exceptions import RecognizerException


_logger = logging.getLogger("zoritori")


class Recognizer:
    def __init__(self):
        self._client = vision.ImageAnnotatorClient()

    def recognize(self, path: str, context=None) -> RawData:
        response = self._detect_text(path)
        return self._collect_symbols(response, context)

    def _detect_text(self, path):
        with io.open(path, "rb") as image_file:
            content = image_file.read()
        image = vision.Image(content=content)
        try:
            start = time.perf_counter()
            response = self._client.text_detection(image=image)
            elapsed = time.perf_counter() - start
            _logger.debug("received response from google vision in %.2f", elapsed)
            if response.error.message:
                raise RecognizerException(
                    "Google Cloud Vision response contained error message: "
                    + response.error.message
                )
            return response
        except Exception as e:
            raise RecognizerException(
                "Google Cloud Vision client threw exception: " + e.message
            ) from e

    def _vertices_to_box(self, vertices, context):
        upper_left = vertices[0]
        lower_right = vertices[2]
        x = upper_left.x
        y = upper_left.y
        w = lower_right.x - x
        h = lower_right.y - y
        return Box(x, y, w, h, context)

    def _collect_symbols(self, response, context):
        annotation = response.full_text_annotation

        def has_line_break(symbol):
            line_break = vision.types.TextAnnotation.DetectedBreak.BreakType.LINE_BREAK
            return (
                symbol.property and symbol.property.detected_break.type_ == line_break
            )

        all_lines = []
        line_number = 0
        blocks = []
        for page in annotation.pages:
            for block in page.blocks:
                lines = []
                line = []
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        for symbol in word.symbols:
                            cdata = self._convert(symbol, line_number, context)
                            line.append(cdata)
                            if has_line_break(symbol):
                                line_number += 1
                                lines.append(line)
                                all_lines.append(line)
                                line = []
                vertices = block.bounding_box.vertices
                box = self._vertices_to_box(vertices, context)
                blocks.append(BlockData(lines, box))

        return RawData(all_lines, blocks)

    def _convert(self, symbol, line_number, context):
        vertices = symbol.bounding_box.vertices
        box = self._vertices_to_box(vertices, context)
        text = symbol.text
        conf = 100.0  # symbol.confidence # TODO ?
        return CharacterData(text, line_number, conf, box)
