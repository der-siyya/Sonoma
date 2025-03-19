
import win32com.client
import win32api
import win32con
import win32com.server.util
import win32gui
import win32process
import win32security
import win32service
import win32event
import win32pipe
import win32file
import pythoncom
import pywintypes
import sys
import os
import time
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

class Win32ComClient:
    def __init__(self, progid: str = None, clsid: str = None, machine: str = None):
        self.progid = progid
        self.clsid = clsid
        self.machine = machine
        self.dispatch = None
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('Win32ComClient')
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def initialize_com(self) -> None:
        try:
            pythoncom.CoInitialize()
            self.logger.info("COM interface initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize COM interface: {str(e)}")
            raise

    def create_dispatch(self, dispatch_type: str = None) -> None:
        try:
            if self.progid:
                self.dispatch = win32com.client.Dispatch(self.progid)
            elif self.clsid:
                self.dispatch = win32com.client.Dispatch(self.clsid)
            else:
                self.dispatch = win32com.client.Dispatch(dispatch_type)
            self.logger.info(f"Successfully created dispatch for {dispatch_type or self.progid or self.clsid}")
        except Exception as e:
            self.logger.error(f"Failed to create dispatch: {str(e)}")
            raise

    def create_event_sink(self, event_class: Any) -> None:
        try:
            return win32com.client.WithEvents(self.dispatch, event_class)
        except Exception as e:
            self.logger.error(f"Failed to create event sink: {str(e)}")
            raise

    def get_active_object(self, progid: str) -> Any:
        try:
            return win32com.client.GetActiveObject(progid)
        except Exception as e:
            self.logger.error(f"Failed to get active object: {str(e)}")
            raise

    def create_new_instance(self) -> None:
        try:
            self.dispatch = win32com.client.DispatchEx(self.progid or self.clsid)
            self.logger.info("Created new instance successfully")
        except Exception as e:
            self.logger.error(f"Failed to create new instance: {str(e)}")
            raise

    def handle_system_flags(self, flags: Dict[str, int]) -> int:
        try:
            result = 0
            for flag_name, flag_value in flags.items():
                if isinstance(flag_value, int):
                    result |= flag_value
            return result
        except Exception as e:
            self.logger.error(f"Failed to handle system flags: {str(e)}")
            raise

    def create_security_attributes(self, inherit_handle: bool = False) -> win32security.SECURITY_ATTRIBUTES:
        try:
            sa = win32security.SECURITY_ATTRIBUTES()
            sa.bInheritHandle = inherit_handle
            return sa
        except Exception as e:
            self.logger.error(f"Failed to create security attributes: {str(e)}")
            raise

    def create_process(self, command: str, working_dir: str = None, show_window: bool = True) -> Tuple[int, int]:
        try:
            si = win32process.STARTUPINFO()
            if not show_window:
                si.dwFlags |= win32process.STARTF_USESHOWWINDOW
                si.wShowWindow = win32con.SW_HIDE

            security_attributes = self.create_security_attributes()
            
            process_flags = win32process.CREATE_NEW_CONSOLE
            if working_dir is None:
                working_dir = os.getcwd()

            process_handle, thread_handle, pid, tid = win32process.CreateProcess(
                None,
                command,
                security_attributes,
                security_attributes,
                False,
                process_flags,
                None,
                working_dir,
                si
            )

            return pid, tid
        except Exception as e:
            self.logger.error(f"Failed to create process: {str(e)}")
            raise

    def create_named_pipe(self, pipe_name: str) -> win32file.PyHANDLE:
        try:
            pipe_handle = win32pipe.CreateNamedPipe(
                pipe_name,
                win32pipe.PIPE_ACCESS_DUPLEX,
                win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                win32pipe.PIPE_UNLIMITED_INSTANCES,
                65536,
                65536,
                0,
                self.create_security_attributes()
            )
            return pipe_handle
        except Exception as e:
            self.logger.error(f"Failed to create named pipe: {str(e)}")
            raise

    def handle_windows_messages(self, timeout: int = 1000) -> None:
        try:
            while True:
                if win32gui.PumpWaitingMessages() == 0:
                    time.sleep(timeout / 1000)
        except Exception as e:
            self.logger.error(f"Failed to handle Windows messages: {str(e)}")
            raise

    def create_event(self, event_name: str, manual_reset: bool = True, initial_state: bool = False) -> win32event.PyHANDLE:
        try:
            return win32event.CreateEvent(None, manual_reset, initial_state, event_name)
        except Exception as e:
            self.logger.error(f"Failed to create event: {str(e)}")
            raise

    def wait_for_single_object(self, handle: win32event.PyHANDLE, timeout: int = win32event.INFINITE) -> int:
        try:
            return win32event.WaitForSingleObject(handle, timeout)
        except Exception as e:
            self.logger.error(f"Failed to wait for single object: {str(e)}")
            raise

    def register_message_filter(self, filter_class: Any) -> None:
        try:
            win32com.server.util.wrap(filter_class())
            self.logger.info("Message filter registered successfully")
        except Exception as e:
            self.logger.error(f"Failed to register message filter: {str(e)}")
            raise

    def cleanup(self) -> None:
        try:
            if self.dispatch:
                del self.dispatch
            pythoncom.CoUninitialize()
            self.logger.info("Cleanup completed successfully")
        except Exception as e:
            self.logger.error(f"Failed during cleanup: {str(e)}")
            raise

    def create_service_manager(self) -> win32service.PyHANDLE:
        try:
            return win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
        except Exception as e:
            self.logger.error(f"Failed to create service manager: {str(e)}")
            raise

    def create_service(self, service_name: str, display_name: str, path_name: str) -> None:
        try:
            scm = self.create_service_manager()
            win32service.CreateService(
                scm,
                service_name,
                display_name,
                win32service.SERVICE_ALL_ACCESS,
                win32service.SERVICE_WIN32_OWN_PROCESS,
                win32service.SERVICE_AUTO_START,
                win32service.SERVICE_ERROR_NORMAL,
                path_name,
                None,
                0,
                None,
                None,
                None
            )
            win32service.CloseServiceHandle(scm)
            self.logger.info(f"Service '{service_name}' created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create service: {str(e)}")
            raise

    def get_system_metrics(self) -> Dict[str, int]:
        try:
            metrics = {
                'screen_width': win32api.GetSystemMetrics(win32con.SM_CXSCREEN),
                'screen_height': win32api.GetSystemMetrics(win32con.SM_CYSCREEN),
                'virtual_screen_width': win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN),
                'virtual_screen_height': win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN),
                'monitors': win32api.GetSystemMetrics(win32con.SM_CMONITORS)
            }
            return metrics
        except Exception as e:
            self.logger.error(f"Failed to get system metrics: {str(e)}")
            raise

    def register_window_class(self, class_name: str, window_proc: Any) -> None:
        try:
            wc = win32gui.WNDCLASS()
            wc.lpfnWndProc = window_proc
            wc.lpszClassName = class_name
            wc.hInstance = win32api.GetModuleHandle(None)
            win32gui.RegisterClass(wc)
            self.logger.info(f"Window class '{class_name}' registered successfully")
        except Exception as e:
            self.logger.error(f"Failed to register window class: {str(e)}")
            raise

    def create_window(self, class_name: str, window_name: str, style: int, rect: Tuple[int, int, int, int]) -> int:
        try:
            return win32gui.CreateWindow(
                class_name,
                window_name,
                style,
                rect[0],
                rect[1],
                rect[2],
                rect[3],
                0,
                0,
                win32api.GetModuleHandle(None),
                None
            )
        except Exception as e:
            self.logger.error(f"Failed to create window: {str(e)}")
            raise

    @staticmethod
    def get_error_message(error_code: int) -> str:
        try:
            return win32api.FormatMessage(error_code)
        except Exception:
            return f"Unknown error code: {error_code}"

    def __enter__(self) -> 'Win32ComClient':
        self.initialize_com()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cleanup()
