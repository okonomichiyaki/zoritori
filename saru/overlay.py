import logging
import platform
from queue import Queue

import contextlib
import glfw
import skia
from OpenGL import GL

from saru.events import KeyEvent, ClipEvent
from saru.types import Box, Root


class Overlay:
    def __init__(self, title, event_queue):
        self._logger = logging.getLogger("saru")
        self._title = title
        self._event_queue = event_queue
        self._draw_queue = Queue()
        self._start_pos = None
        self._stop = False
        self._window = None

    def get_screen_size(self):
        monitor = glfw.get_primary_monitor()
        video_mode = glfw.get_video_mode(monitor)
        return (video_mode.size.width, video_mode.size.height)

    def get_window_pos(self):
        if self._window:
            return glfw.get_window_pos(self._window)
        else:
            return None

    @contextlib.contextmanager
    def _glfw_window(self):
        if not glfw.init():
            raise RuntimeError("glfw.init() failed")

        glfw.window_hint(glfw.STENCIL_BITS, 8)  # ?
        glfw.window_hint(glfw.SAMPLES, 14)  # ?
        glfw.window_hint(glfw.DECORATED, 0)
        glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, 1)
        glfw.window_hint(glfw.FLOATING, 1)

        (width, height) = self.get_screen_size()
        monitor = None  # glfw.get_primary_monitor()
        # https://stackoverflow.com/questions/72588667/
        self._window = glfw.create_window(
            width - 1, height - 1, self._title, monitor, None
        )

        def key_callback(window, key, scancode, action, mods):
            # self._logger.debug(
            #    f"key_callback: key={key} scancode={scancode} action={action}"
            # )
            if action == glfw.RELEASE:
                if key == glfw.KEY_R or key == glfw.KEY_Q:
                    clip = self._get_clip(window)
                    self._start_pos = None
                    if clip.width > 0 and clip.height > 0:
                        self._event_queue.put_nowait(ClipEvent(key, clip))
                    else:
                        self._event_queue.put_nowait(KeyEvent(key))
                else:
                    self._event_queue.put_nowait(KeyEvent(key))
            elif action == glfw.PRESS and (glfw.KEY_R == key or glfw.KEY_Q == key):
                self._start_pos = glfw.get_cursor_pos(window)

        glfw.set_key_callback(self._window, key_callback)
        glfw.make_context_current(self._window)
        yield self._window
        glfw.terminate()

    @contextlib.contextmanager
    def _skia_surface(self, window):
        context = skia.GrDirectContext.MakeGL()
        (fb_width, fb_height) = glfw.get_framebuffer_size(window)
        backend_render_target = skia.GrBackendRenderTarget(
            fb_width,
            fb_height,
            0,  # sampleCnt
            0,  # stencilBits
            skia.GrGLFramebufferInfo(0, GL.GL_RGBA8),
        )
        surface = skia.Surface.MakeFromBackendRenderTarget(
            context,
            backend_render_target,
            skia.kBottomLeft_GrSurfaceOrigin,
            skia.kRGBA_8888_ColorType,
            skia.ColorSpace.MakeSRGB(),
        )
        assert surface is not None
        yield surface
        context.abandonContext()

    def signal(self):
        glfw.post_empty_event()

    def stop(self):
        self._stop = True
        self.signal()

    def _get_window_ctx(self):
        (x, y) = glfw.get_window_pos(self._window)
        return Root(x, y, 0, 0)

    def _get_clip(self, window):
        (startx, starty) = self._start_pos
        (endx, endy) = glfw.get_cursor_pos(window)
        x = min(startx, endx)
        y = min(starty, endy)
        w = abs(endx - startx)
        h = abs(endy - starty)
        ctx = self._get_window_ctx()
        return Box(x, y, w, h, ctx)

    def _draw_clip(self, window, surface, canvas):
        canvas.clear(skia.ColorTRANSPARENT)
        paint = skia.Paint(Color=skia.ColorGREEN, Style=skia.Paint.kStroke_Style)
        clip = self._get_clip(window)
        canvas.drawRect(clip.to_skia_rect(), paint)
        surface.flushAndSubmit()
        glfw.swap_buffers(window)

    def ui_loop(self):
        """Primary UI loop: sets up GLFW window, then waits for input and draw events"""
        with self._glfw_window() as window:
            if platform.system() == "Windows":
                from saru.windows import enable_click_through

                if not enable_click_through(self._title):
                    self._logger.warning(
                        f"Failed to enable click through for window {self._title}"
                    )

            GL.glClear(GL.GL_COLOR_BUFFER_BIT)
            with self._skia_surface(window) as surface:
                with surface as canvas:
                    while (
                        glfw.get_key(window, glfw.KEY_ESCAPE) != glfw.PRESS
                        and not glfw.window_should_close(window)
                        and not self._stop
                    ):
                        if self._start_pos:
                            self._draw_clip(window, surface, canvas)
                        elif self._should_draw():
                            self._on_draw(window, surface, canvas)
                        glfw.wait_events()

    def _should_draw(self):
        return self._draw_queue.qsize()

    def _on_draw(self, window, surface, canvas):
        on_draw = self._draw_queue.get_nowait()
        if on_draw:
            canvas.clear(skia.ColorTRANSPARENT)
            on_draw(canvas)
            surface.flushAndSubmit()
            glfw.swap_buffers(window)
            self._draw_queue.task_done()

    def clear(self, block=False):
        self._draw_queue.put_nowait(lambda c: None)
        self.signal()
        if block:
            self._draw_queue.join()

    def draw(self, on_draw, block=False):
        self._draw_queue.put_nowait(on_draw)
        self.signal()
        if block:
            self._draw_queue.join()
