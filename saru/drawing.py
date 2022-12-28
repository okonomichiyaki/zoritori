import logging

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
        draw_parts_of_speech(c, clip, sdata)

    if render_state.debug:
        c.drawRect(clip, STROKE_BLUE)
        if secondary_clip:
            c.drawRect(secondary_clip, STROKE_BLUE)

    if sdata.cdata:
        draw_low_confidence(c, clip, sdata.cdata, 50)

    if render_state.debug and sdata.raw_data.blocks:
        draw_block_boxes(c, clip, sdata.raw_data.blocks)

    if sdata.furigana:
        draw_furigana(c, render_state.furigana_size, clip, sdata.furigana)

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
    layer_size = c.getBaseLayerSize()
    screen_width = layer_size.width()
    screen_height = layer_size.height()
    if not text or len(text) == 0:
        return
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
            typeface = skia.Typeface("meiryo")
        font = skia.Font(typeface, subtitle_size)
        w = font.measureText(line)
        height = font.getSpacing()
        if x0 < 0:
            x0 = screen_width / 2
        if y0 < 0:
            y0 = screen_height
        x = x0 - (w + subtitle_margin) / 2
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


def draw_furigana(c, size, clip, fs):
    for f in fs:
        text = f.reading
        x = clip.x() + f.x
        y = clip.y() + f.y
        typeface = skia.Typeface("meiryo", skia.FontStyle.Bold())
        # "ms gothic"
        font = skia.Font(typeface, size)
        width = font.measureText(text)
        x = x - width / 2
        # y parameter to draw_text appears to be the baseline, and text is drawn above it
        c.drawString(text, x, y - 4, font, FILL_BLACK)  # TODO: magic number


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
    for line in lines:
        for cdata in line:
            rect = shift(cdata_to_rect(cdata), clip)
            c.drawRect(rect, STROKE_GREEN)


def draw_block_boxes(c, clip, blocks):
    for block in blocks:
        rect = shift(cdata_to_rect(block), clip)
        c.drawRect(rect, STROKE_GREEN)


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
        c.drawCircle(x, y, radius, STROKE_RED)


def draw_laser_point(c, x, y):
    radius = 2
    c.drawCircle(x, y, radius, FILL_RED)
