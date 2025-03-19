
import ctypes
from ctypes import wintypes, windll, Structure, Union, POINTER, sizeof
import win32gui
import win32con
import win32api
import win32process
import time
import threading
from typing import Optional, Tuple
import logging

class RECT(Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG)
    ]

class POINT(Structure):
    _fields_ = [
        ("x", wintypes.LONG),
        ("y", wintypes.LONG)
    ]

class ActionCenter:
    def __init__(self):
        self.user32 = ctypes.WinDLL('user32', use_last_error=True)
        self.kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        self._action_center_hwnd = None
        self._is_visible = False
        self._monitor_thread = None
        self._should_monitor = False
        self.logger = logging.getLogger(__name__)
        
    def _find_action_center_window(self) -> Optional[int]:
        def callback(hwnd, ctx):
            if win32gui.GetClassName(hwnd) == "Windows.UI.Core.CoreWindow":
                text = win32gui.GetWindowText(hwnd)
                if "Action" in text:
                    ctx.append(hwnd)
            return True
        
        found = []
        win32gui.EnumWindows(callback, found)
        return found[0] if found else None

    def _get_window_rect(self, hwnd: int) -> RECT:
        rect = RECT()
        self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return rect

    def _is_point_in_rect(self, point: POINT, rect: RECT) -> bool:
        return (rect.left <= point.x <= rect.right and 
                rect.top <= point.y <= rect.bottom)

    def _get_cursor_pos(self) -> POINT:
        point = POINT()
        self.user32.GetCursorPos(ctypes.byref(point))
        return point

    def toggle(self):
        try:
            # Windows key + A simulation
            win32api.keybd_event(win32con.VK_LWIN, 0, 0, 0)
            win32api.keybd_event(ord('A'), 0, 0, 0)
            time.sleep(0.1)
            win32api.keybd_event(ord('A'), 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_LWIN, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            self._is_visible = not self._is_visible
            if self._is_visible and not self._monitor_thread:
                self._start_monitoring()
        except Exception as e:
            self.logger.error(f"Failed to toggle Action Center: {str(e)}")

    def _start_monitoring(self):
        self._should_monitor = True
        self._monitor_thread = threading.Thread(target=self._monitor_visibility)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def _monitor_visibility(self):
        while self._should_monitor:
            try:
                hwnd = self._find_action_center_window()
                if hwnd:
                    self._action_center_hwnd = hwnd
                    rect = self._get_window_rect(hwnd)
                    cursor = self._get_cursor_pos()
                    
                    if not self._is_point_in_rect(cursor, rect):
                        click_count = win32api.GetAsyncKeyState(win32con.VK_LBUTTON)
                        if click_count & 0x8000:
                            self.close()
                            break
                time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Error in monitor thread: {str(e)}")
                break

    def close(self):
        try:
            if self._action_center_hwnd:
                win32gui.PostMessage(self._action_center_hwnd, win32con.WM_CLOSE, 0, 0)
            self._is_visible = False
            self._should_monitor = False
            self._monitor_thread = None
        except Exception as e:
            self.logger.error(f"Failed to close Action Center: {str(e)}")

    def get_quick_actions(self) -> list:
        try:
            if not self._action_center_hwnd:
                return []
            
            actions = []
            def enum_child_proc(hwnd, param):
                class_name = win32gui.GetClassName(hwnd)
                if class_name == "Windows.UI.Core.CoreWindow":
                    text = win32gui.GetWindowText(hwnd)
                    if text:
                        actions.append({"hwnd": hwnd, "text": text})
                return True
            
            win32gui.EnumChildWindows(self._action_center_hwnd, enum_child_proc, None)
            return actions
        except Exception as e:
            self.logger.error(f"Failed to get quick actions: {str(e)}")
            return []

    def click_quick_action(self, action_name: str) -> bool:
        try:
            actions = self.get_quick_actions()
            for action in actions:
                if action["text"].lower() == action_name.lower():
                    rect = self._get_window_rect(action["hwnd"])
                    x = (rect.left + rect.right) // 2
                    y = (rect.top + rect.bottom) // 2
                    
                    # Simulate mouse click
                    win32api.SetCursorPos((x, y))
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
                    time.sleep(0.1)
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to click quick action: {str(e)}")
            return False

    def set_transparency(self, alpha: int):
        try:
            if self._action_center_hwnd:
                style = win32gui.GetWindowLong(self._action_center_hwnd, win32con.GWL_EXSTYLE)
                win32gui.SetWindowLong(
                    self._action_center_hwnd,
                    win32con.GWL_EXSTYLE,
                    style | win32con.WS_EX_LAYERED
                )
                win32gui.SetLayeredWindowAttributes(
                    self._action_center_hwnd,
                    0,
                    alpha,
                    win32con.LWA_ALPHA
                )
        except Exception as e:
            self.logger.error(f"Failed to set transparency: {str(e)}")

    def get_notification_count(self) -> int:
        try:
            if not self._action_center_hwnd:
                return 0
                
            notifications = []
            def enum_notifications(hwnd, param):
                if win32gui.GetClassName(hwnd) == "Windows.UI.Core.CoreWindow":
                    text = win32gui.GetWindowText(hwnd)
                    if "notification" in text.lower():
                        notifications.append(hwnd)
                return True
            
            win32gui.EnumChildWindows(self._action_center_hwnd, enum_notifications, None)
            return len(notifications)
        except Exception as e:
            self.logger.error(f"Failed to get notification count: {str(e)}")
            return 0

    def clear_all_notifications(self):
        try:
            if self._action_center_hwnd:
                # Find "Clear all" button
                def find_clear_button(hwnd, param):
                    if win32gui.GetClassName(hwnd) == "Windows.UI.Core.CoreWindow":
                        text = win32gui.GetWindowText(hwnd)
                        if "clear all" in text.lower():
                            param.append(hwnd)
                    return True
                
                clear_buttons = []
                win32gui.EnumChildWindows(self._action_center_hwnd, find_clear_button, clear_buttons)
                
                if clear_buttons:
                    rect = self._get_window_rect(clear_buttons[0])
                    x = (rect.left + rect.right) // 2
                    y = (rect.top + rect.bottom) // 2
                    
                    win32api.SetCursorPos((x, y))
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
                    time.sleep(0.1)
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
        except Exception as e:
            self.logger.error(f"Failed to clear notifications: {str(e)}")

    def __del__(self):
        self._should_monitor = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
