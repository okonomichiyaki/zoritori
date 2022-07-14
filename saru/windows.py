import win32api
import win32con
import win32gui


# workaround for glfw: https://github.com/FlorianRhiem/pyGLFW/issues/53
def enable_click_through(title):
    hwnd = win32gui.FindWindowEx(0, 0, None, title)
    if hwnd:
        # these flags allow clicking through the window (WS_EX_NOACTIVATE),
        # while still appearing in the taskbar (WS_EX_APPWINDOW)
        # https://docs.microsoft.com/en-us/windows/win32/winmsg/extended-window-styles
        exStyle = win32con.WS_EX_COMPOSITED | win32con.WS_EX_LAYERED | win32con.WS_EX_NOACTIVATE | win32con.WS_EX_TOPMOST | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_APPWINDOW
        win32api.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, exStyle)
        return True
    else:
        return False
