
import ctypes
import win32gui
import win32con
import win32api
from ctypes import wintypes
import time
import threading
from queue import Queue

class ProgramNotificationHandler:
    def __init__(self):
        self.notification_queue = Queue()
        self.running = True
        self.notification_thread = None
        self.registered_programs = set()
        
    def start_monitoring(self):
        self.notification_thread = threading.Thread(target=self._monitor_notifications)
        self.notification_thread.daemon = True
        self.notification_thread.start()
        
    def stop_monitoring(self):
        self.running = False
        if self.notification_thread:
            self.notification_thread.join()
            
    def register_program(self, program_name):
        self.registered_programs.add(program_name.lower())
        
    def _monitor_notifications(self):
        # Create window class
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self._window_proc
        wc.lpszClassName = "NotificationListener"
        
        try:
            win32gui.RegisterClass(wc)
            hwnd = win32gui.CreateWindow(
                wc.lpszClassName,
                "Notification Listener",
                0,
                0, 0, 0, 0,
                0,
                0,
                0,
                None
            )
            
            while self.running:
                win32gui.PumpWaitingMessages()
                time.sleep(0.1)
                
        except Exception as e:
            print(f"Error in notification monitoring: {e}")
            
    def _window_proc(self, hwnd, msg, wparam, lparam):
        WM_SHELLNOTIFY = win32con.WM_USER + 1
        if msg == WM_SHELLNOTIFY:
            self._handle_notification(wparam, lparam)
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)        
    def _handle_notification(self, wparam, lparam):
        try:
            # Get process information
            pid = wparam
            hProcess = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | 
                                         win32con.PROCESS_VM_READ, False, pid)
            
            if hProcess:
                # Get process name
                process_name = win32gui.GetWindowText(lparam).lower()
                
                if process_name in self.registered_programs:
                    notification = {
                        'process_id': pid,
                        'process_name': process_name,
                        'timestamp': time.time(),
                        'window_handle': lparam
                    }
                    self.notification_queue.put(notification)
                    
                win32api.CloseHandle(hProcess)
                
        except Exception as e:
            print(f"Error handling notification: {e}")
            
    def get_pending_notifications(self):
        notifications = []
        while not self.notification_queue.empty():
            notifications.append(self.notification_queue.get())
        return notifications

    def clear_notifications(self):
        while not self.notification_queue.empty():
            self.notification_queue.get()
            
    def set_notification_callback(self, callback):
        def notification_handler():
            while self.running:
                if not self.notification_queue.empty():
                    notification = self.notification_queue.get()
                    callback(notification)
                time.sleep(0.1)
                
        handler_thread = threading.Thread(target=notification_handler)
        handler_thread.daemon = True
        handler_thread.start()
