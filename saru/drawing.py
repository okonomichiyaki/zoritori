import logging

import glfw
import skia

from saru.strings import is_ascii


_logger = logging.getLogger("saru")


def draw(c, options, clip, sdata):
    if options.parts_of_speech:
        draw_parts_of_speech(c, clip, sdata)
    if options.debug:
        paint = skia.Paint(Color=skia.ColorBLUE, Style=skia.Paint.kStroke_Style)
        c.drawRect(clip, paint)
    if sdata.cdata:
        draw_low_confidence(c, clip, sdata.cdata, 50)
    if options.debug and sdata.raw_data.blocks:
        draw_block_boxes(c, clip, sdata.raw_data.blocks)
    if sdata.furigana:
        draw_furigana(c, options, clip, sdata.furigana)
    if sdata.translation:
        draw_subtitles(c, options, sdata.translation)
    elif options.debug and sdata.original:
        draw_subtitles(c, options, sdata.original)


def draw_subtitles(c, options, text, xd=0, yd=0):
    layer_size = c.getBaseLayerSize()
    screen_width = layer_size.width()
    screen_height = layer_size.height()
    subtitle_size = options.SubtitleSize
    subtitle_margin = options.SubtitleMargin
    if not text or len(text) == 0:
        return
    typeface = None
    if is_ascii(text):
        typeface = skia.Typeface("arial")
    else:
        typeface = skia.Typeface("meiryo")
    lines = text.split("\n")
    lines = map(lambda line: line.strip(), lines)
    lines = filter(lambda line: len(line) > 0, lines)
    lines = list(lines)
    lines.reverse()
    for idx, line in enumerate(lines):
        font = skia.Font(typeface, subtitle_size)
        paint = skia.Paint(
            AntiAlias=True, Style=skia.Paint.kFill_Style, Color=skia.ColorBLACK
        )
        w = font.measureText(line)
        height = font.getSpacing()
        x = screen_width / 2 - (w + subtitle_margin) / 2 + xd
        y = screen_height - (idx + 1) * (height + subtitle_margin) + yd
        h = height + subtitle_margin
        c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), paint)
        paint = skia.Paint(
            AntiAlias=True, Style=skia.Paint.kFill_Style, Color=skia.ColorWHITE
        )
        c.drawString(
            line, x + subtitle_margin / 2, y + height + subtitle_margin / 2, font, paint
        )


def draw_furigana(c, options, clip, fs):
    for f in fs:
        text = f.reading
        x = clip.x() + f.x
        y = clip.y() + f.y
        paint = skia.Paint(AntiAlias=True, Color=skia.ColorBLACK)
        typeface = skia.Typeface("meiryo", skia.FontStyle.Bold())
        # "ms gothic"
        font = skia.Font(typeface, options.FuriganaSize)
        width = font.measureText(text)
        x = x - width / 2
        # y parameter to draw_text appears to be the baseline, and text is drawn above it
        c.drawString(text, x, y - 4, font, paint)  # TODO: magic number


def shift(a, b):
    return skia.Rect.MakeXYWH(a.x() + b.x(), a.y() + b.y(), a.width(), a.height())


def draw_parts_of_speech(c, clip, sdata):
    paint = skia.Paint(
        Style=skia.Paint.kStroke_Style, StrokeWidth=3.0
    )  # TODO: magic number
    for t in sdata.tokens:
        if t.part_of_speech(2) == "人名":
            paint.setColor(skia.ColorSetARGB(0xFF, 0x35, 0xA1, 0x6B))
        elif t.part_of_speech(2) == "地名":
            paint.setColor(skia.ColorSetARGB(0xFF, 0xFF, 0x7F, 0x00))
        else:
            continue
        rect = shift(t.box(), clip)
        c.drawRect(rect, paint)


# TODO: rename this
def cdata_to_rect(cdata):
    return skia.Rect.MakeXYWH(cdata.left, cdata.top, cdata.width, cdata.height)


def draw_character_boxes(c, clip, lines):
    paint = skia.Paint(Color=skia.ColorGREEN, Style=skia.Paint.kStroke_Style)
    for line in lines:
        for cdata in line:
            rect = shift(cdata_to_rect(cdata), clip)
            c.drawRect(rect, paint)


def draw_block_boxes(c, clip, blocks):
    paint = skia.Paint(Color=skia.ColorGREEN, Style=skia.Paint.kStroke_Style)
    for block in blocks:
        rect = shift(cdata_to_rect(block), clip)
        c.drawRect(rect, paint)


def draw_low_confidence(c, clip, lines, threshold=50):
    boxes = []
    for line in lines:
        for cdata in line:
            if cdata.conf < threshold:
                boxes.append(cdata)
    for box in boxes:
        x = clip.x() + box.left + box.width / 2
        y = clip.y() + box.top + box.height / 2
        radius = box.width / 2
        paint = skia.Paint(Color=skia.ColorRED, Style=skia.Paint.kStroke_Style)
        c.drawCircle(x, y, radius, paint)
