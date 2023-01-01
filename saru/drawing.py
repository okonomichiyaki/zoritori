import logging
import platform

import glfw
import skia

from saru.strings import is_ascii


FILL_BLACK = skia.Paint(Style=skia.Paint.kFill_Style, Color=skia.ColorBLACK)
FILL_WHITE = skia.Paint(Style=skia.Paint.kFill_Style, Color=skia.ColorWHITE)
FILL_RED = skia.Paint(Style=skia.Paint.kFill_Style, Color=skia.ColorRED)
STROKE_BLUE = skia.Paint(Style=skia.Paint.kStroke_Style, Color=skia.ColorBLUE)
STROKE_GREEN = skia.Paint(Style=skia.Paint.kStroke_Style, Color=skia.ColorGREEN)
STROKE_RED = skia.Paint(Style=skia.Paint.kStroke_Style, Color=skia.ColorRED)


_logger = logging.getLogger("saru")


def draw(c, render_state):
    sdata = render_state.primary_data
    clip = render_state.primary_clip
    secondary_clip = render_state.secondary_clip
    secondary_data = render_state.secondary_data

    if render_state.parts_of_speech:
        draw_parts_of_speech(c, sdata)

    if render_state.debug:
        c.drawRect(clip, STROKE_BLUE)
        if secondary_clip:
            c.drawRect(secondary_clip, STROKE_BLUE)

    if sdata.cdata:
        draw_low_confidence(c, sdata.cdata, 50)

    if render_state.debug and sdata.raw_data.blocks:
        draw_block_boxes(c, sdata.raw_data.blocks)

    if sdata.furigana:
        draw_furigana(c, render_state.furigana_size, sdata.furigana)

    if sdata.translation:
        draw_subtitles(
            c,
            render_state.subtitle_size,
            render_state.subtitle_margin,
            sdata.translation,
            debug=render_state.debug,
        )
    elif render_state.debug and sdata.original:
        draw_subtitles(
            c,
            render_state.subtitle_size,
            render_state.subtitle_margin,
            sdata.original,
            debug=render_state.debug,
        )

    if secondary_data:
        draw_subtitles(
            c,
            render_state.subtitle_size,
            render_state.subtitle_margin,
            "\n".join(secondary_data),
            x0=secondary_clip.x() + secondary_clip.width() / 2,
            y0=secondary_clip.y() + secondary_clip.height(),
            direction=1,
            debug=render_state.debug,
        )


def draw_subtitles(
    c, subtitle_size, subtitle_margin, text, x0=-1, y0=-1, direction=-1, debug=False
):
    if not text or len(text) == 0:
        return
    layer_size = c.getBaseLayerSize()
    screen_width = layer_size.width()
    screen_height = layer_size.height()
    if x0 < 0:
        x0 = screen_width / 2
    if y0 < 0:
        y0 = screen_height
    if debug:
        draw_laser_point(c, x0, y0)
    lines = text.split("\n")
    lines = map(lambda line: line.strip(), lines)
    lines = filter(lambda line: len(line) > 0, lines)
    lines = list(lines)
    if direction < 0:
        lines.reverse()
    previous_height = 0
    for idx, line in enumerate(lines):
        typeface = None
        if is_ascii(line):
            typeface = skia.Typeface("arial")
        else:
            if platform.system() == "Windows":
                typeface = skia.Typeface("meiryo")
            else:
                typeface = skia.Typeface("Noto Sans CJK JP")  # TODO: magic string
        font = skia.Font(typeface, subtitle_size)
        w = font.measureText(line)
        height = font.getSpacing()
        x = x0 - (w + subtitle_margin) / 2
        # depending on the direction, shift vertically based on current line height or previous line height:
        if direction < 0:
            yshift = direction * (idx + 1) * (height + subtitle_margin)
        else:
            yshift = direction * idx * (previous_height + subtitle_margin)
        y = y0 + yshift
        h = height + subtitle_margin
        if debug:
            draw_laser_point(c, x, y)
        c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), FILL_BLACK)
        c.drawString(
            line,
            x + subtitle_margin / 2,
            y + height + subtitle_margin / 2,
            font,
            FILL_WHITE,
        )
        previous_height = height


def draw_furigana(c, size, fs):
    for f in fs:
        text = f.reading
        x = f.x
        y = f.y
        typeface = skia.Typeface("meiryo", skia.FontStyle.Bold())
        # "ms gothic"
        font = skia.Font(typeface, size)
        width = font.measureText(text)
        x = x - width / 2
        # y parameter to draw_text appears to be the baseline, and text is drawn above it
        buffer = size / 4
        c.drawString(text, x, y - buffer, font, FILL_BLACK)


def draw_parts_of_speech(c, sdata):
    part_of_speech_border_width = 3.0  # TODO: magic number
    paint = skia.Paint(
        Style=skia.Paint.kStroke_Style, StrokeWidth=part_of_speech_border_width
    )
    for t in sdata.tokens:
        if t.part_of_speech(2) == "人名":
            paint.setColor(skia.ColorSetARGB(0xFF, 0x35, 0xA1, 0x6B))
        elif t.part_of_speech(2) == "地名":
            paint.setColor(skia.ColorSetARGB(0xFF, 0xFF, 0x7F, 0x00))
        else:
            continue
        c.drawRect(t.box(), paint)


# TODO: rename this
def cdata_to_rect(cdata):
    return skia.Rect.MakeXYWH(cdata.left, cdata.top, cdata.width, cdata.height)


def draw_character_boxes(c, lines):
    for line in lines:
        for cdata in line:
            rect = cdata_to_rect(cdata)
            c.drawRect(rect, STROKE_GREEN)


def draw_block_boxes(c, blocks):
    for block in blocks:
        rect = cdata_to_rect(block)
        c.drawRect(rect, STROKE_GREEN)


def draw_low_confidence(c, lines, threshold=50):
    boxes = []
    for line in lines:
        for cdata in line:
            if cdata.conf < threshold:
                boxes.append(cdata)
    for box in boxes:
        x = box.left + box.width / 2
        y = box.top + box.height / 2
        radius = box.width / 2
        c.drawCircle(x, y, radius, STROKE_RED)


def draw_laser_point(c, x, y):
    radius = 2
    c.drawCircle(x, y, radius, FILL_RED)
