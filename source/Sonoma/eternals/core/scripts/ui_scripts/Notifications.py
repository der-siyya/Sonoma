
import win32api
import win32con
import win32gui
import win32ui
import ctypes
from ctypes import wintypes
import time
import threading
from PIL import Image, ImageDraw
import os
import sys
import logging
from typing import Optional, Tuple, Dict

class NotificationManager:
    def __init__(self):
        self.notifications: Dict[int, dict] = {}
        self.notification_id = 0
        self.notification_window = None
        self.is_initialized = False
        self._setup_logging()
        
    def _setup_logging(self):
        self.logger = logging.getLogger('NotificationManager')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler('notification.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def initialize_notification_window(self):
        if self.is_initialized:
            return

        wc = win32gui.WNDCLASS()
        hinst = wc.hInstance = win32gui.GetModuleHandle(None)
        wc.lpszClassName = "EternalsNotificationClass"
        wc.lpfnWndProc = self._window_proc
        
        try:
            win32gui.RegisterClass(wc)
            self.notification_window = win32gui.CreateWindow(
                wc.lpszClassName,
                "Eternals Notifications",
                win32con.WS_OVERLAPPED,
                0, 0, 0, 0,
                0, 0, hinst, None
            )
            self.is_initialized = True
            self.logger.info("Notification window initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize notification window: {str(e)}")

    def _window_proc(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        if msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def create_notification(self, title: str, message: str, icon_path: Optional[str] = None, 
                          duration: int = 5000, priority: str = "normal") -> int:
        if not self.is_initialized:
            self.initialize_notification_window()

        notification_id = self.notification_id
        self.notification_id += 1

        notification = {
            "title": title,
            "message": message,
            "icon_path": icon_path,
            "duration": duration,
            "priority": priority,
            "creation_time": time.time(),
            "shown": False
        }

        self.notifications[notification_id] = notification
        
        threading.Thread(target=self._show_notification, 
                        args=(notification_id,), 
                        daemon=True).start()
        
        return notification_id

    def _show_notification(self, notification_id: int):
        notification = self.notifications.get(notification_id)
        if not notification:
            return

        try:
            nid = (self.notification_window, notification_id,
                   win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP | win32gui.NIF_INFO,
                   win32con.WM_USER + 20)

            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            if notification["icon_path"] and os.path.exists(notification["icon_path"]):
                hicon = win32gui.LoadImage(0, notification["icon_path"], 
                                         win32con.IMAGE_ICON, 0, 0, icon_flags)
            else:
                hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

            notification_data = (
                nid[0], nid[1], nid[2], nid[3],
                hicon, notification["title"],
                notification["message"],
                200,  # Timeout
                notification["title"]
            )

            win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, notification_data)
            notification["shown"] = True
            
            time.sleep(notification["duration"] / 1000)
            self._remove_notification(notification_id)
            
        except Exception as e:
            self.logger.error(f"Error showing notification {notification_id}: {str(e)}")

    def _remove_notification(self, notification_id: int):
        if notification_id in self.notifications:
            try:
                nid = (self.notification_window, notification_id, 0)
                win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
                del self.notifications[notification_id]
                self.logger.info(f"Notification {notification_id} removed successfully")
            except Exception as e:
                self.logger.error(f"Error removing notification {notification_id}: {str(e)}")

    def update_notification(self, notification_id: int, title: Optional[str] = None, 
                          message: Optional[str] = None, icon_path: Optional[str] = None):
        if notification_id not in self.notifications:
            return False

        notification = self.notifications[notification_id]
        
        if title:
            notification["title"] = title
        if message:
            notification["message"] = message
        if icon_path:
            notification["icon_path"] = icon_path

        if notification["shown"]:
            try:
                self._show_notification(notification_id)
                return True
            except Exception as e:
                self.logger.error(f"Error updating notification {notification_id}: {str(e)}")
                return False
        return True

    def clear_all_notifications(self):
        notification_ids = list(self.notifications.keys())
        for notification_id in notification_ids:
            self._remove_notification(notification_id)

    def __del__(self):
        self.clear_all_notifications()
        if self.notification_window:
            win32gui.DestroyWindow(self.notification_window)

class NotificationFactory:
    @staticmethod
    def create_success_notification(title: str, message: str) -> dict:
        return {
            "type": "success",
            "title": title,
            "message": message,
            "icon": "assets/success.png",
            "duration": 3000,
            "priority": "high"
        }

    @staticmethod
    def create_error_notification(title: str, message: str) -> dict:
        return {
            "type": "error",
            "title": title,
            "message": message,
            "icon": "assets/error.png",
            "duration": 5000,
            "priority": "critical"
        }

    @staticmethod
    def create_warning_notification(title: str, message: str) -> dict:
        return {
            "type": "warning",
            "title": title,
            "message": message,
            "icon": "assets/warning.png",
            "duration": 4000,
            "priority": "medium"
        }

class NotificationService:
    def __init__(self):
        self.notification_manager = NotificationManager()
        self.notification_factory = NotificationFactory()
        
    def show_success(self, title: str, message: str) -> int:
        notification = self.notification_factory.create_success_notification(title, message)
        return self.notification_manager.create_notification(
            notification["title"],
            notification["message"],
            notification["icon"],
            notification["duration"],
            notification["priority"]
        )
        
    def show_error(self, title: str, message: str) -> int:
        notification = self.notification_factory.create_error_notification(title, message)
        return self.notification_manager.create_notification(
            notification["title"],
            notification["message"],
            notification["icon"],
            notification["duration"],
            notification["priority"]
        )
        
    def show_warning(self, title: str, message: str) -> int:
        notification = self.notification_factory.create_warning_notification(title, message)
        return self.notification_manager.create_notification(
            notification["title"],
            notification["message"],
            notification["icon"],
            notification["duration"],
            notification["priority"]
        )
