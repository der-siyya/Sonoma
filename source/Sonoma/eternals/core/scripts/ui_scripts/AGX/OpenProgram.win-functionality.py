
import ctypes
from ctypes import wintypes, windll, c_wchar_p, c_int, POINTER, Structure
import win32gui
import win32con
import win32api
import win32process
import os
import sys
import logging
from typing import Optional, Tuple, Union
from pathlib import Path

# Windows API constants and structures
class SHELLEXECUTEINFO(Structure):
    _fields_ = [
        ('cbSize', wintypes.DWORD),
        ('fMask', wintypes.ULONG),
        ('hwnd', wintypes.HWND),
        ('lpVerb', c_wchar_p),
        ('lpFile', c_wchar_p),
        ('lpParameters', c_wchar_p),
        ('lpDirectory', c_wchar_p),
        ('nShow', c_int),
        ('hInstApp', wintypes.HINSTANCE),
        ('lpIDList', wintypes.LPVOID),
        ('lpClass', c_wchar_p),
        ('hkeyClass', wintypes.HKEY),
        ('dwHotKey', wintypes.DWORD),
        ('hIcon', wintypes.HANDLE),
        ('hProcess', wintypes.HANDLE)
    ]

class ProgramLauncher:
    def __init__(self):
        self.shell32 = windll.shell32
        self.kernel32 = windll.kernel32
        self.user32 = windll.user32
        self._setup_logging()
        
    def _setup_logging(self):
        self.logger = logging.getLogger('ProgramLauncher')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler('program_launcher.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def launch_program(self, program_path: Union[str, Path], 
                      params: Optional[str] = None, 
                      working_dir: Optional[str] = None,
                      show_cmd: int = win32con.SW_SHOWNORMAL) -> Tuple[bool, Optional[int]]:
        try:
            sei = SHELLEXECUTEINFO()
            sei.cbSize = ctypes.sizeof(sei)
            sei.fMask = (win32con.SEE_MASK_NOCLOSEPROCESS | 
                        win32con.SEE_MASK_NOASYNC | 
                        win32con.SEE_MASK_FLAG_NO_UI)
            sei.lpVerb = "open"
            sei.lpFile = str(program_path)
            sei.lpParameters = params
            sei.lpDirectory = working_dir
            sei.nShow = show_cmd
            sei.hProcess = None

            success = self.shell32.ShellExecuteExW(ctypes.byref(sei))
            
            if not success:
                error_code = self.kernel32.GetLastError()
                self.logger.error(f"Failed to launch program: {error_code}")
                return False, error_code

            if sei.hProcess:
                process_id = win32process.GetProcessId(sei.hProcess)
                self.kernel32.CloseHandle(sei.hProcess)
                return True, process_id
            
            return True, None

        except Exception as e:
            self.logger.exception("Exception occurred while launching program")
            return False, None

    def set_program_icon(self, hwnd: int, icon_path: str) -> bool:
        try:
            # Load icon
            icon_handle = self.user32.LoadImageW(
                None,
                icon_path,
                win32con.IMAGE_ICON,
                0,
                0,
                win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            )

            if not icon_handle:
                self.logger.error("Failed to load icon")
                return False

            # Set window icon
            self.user32.SendMessageW(
                hwnd,
                win32con.WM_SETICON,
                win32con.ICON_BIG,
                icon_handle
            )
            
            self.user32.SendMessageW(
                hwnd,
                win32con.WM_SETICON,
                win32con.ICON_SMALL,
                icon_handle
            )

            return True

        except Exception as e:
            self.logger.exception("Exception occurred while setting program icon")
            return False

    def create_program_shortcut(self, 
                              target_path: str,
                              shortcut_path: str,
                              description: str = "",
                              icon_path: Optional[str] = None) -> bool:
        try:
            import pythoncom
            import win32com as shell
            import win32com.shell as shellcon # type: ignore

            shortcut = pythoncom.CoCreateInstance(
                shell.CLSID_ShellLink,
                None,
                pythoncom.CLSCTX_INPROC_SERVER,
                shell.IID_IShellLink
            )

            shortcut.SetPath(target_path)
            shortcut.SetDescription(description)
            
            if icon_path:
                shortcut.SetIconLocation(icon_path, 0)

            persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
            persist_file.Save(shortcut_path, 0)
            
            return True

        except Exception as e:
            self.logger.exception("Exception occurred while creating shortcut")
            return False
    def get_window_handle_by_pid(self, process_id: int, timeout_ms: int = 5000) -> Optional[int]:
        class WindowInfo:
            def __init__(self):
                self.hwnd = None
                self.pid = process_id

            def enum_callback(self, hwnd, _):
                _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                if found_pid == self.pid and win32gui.IsWindowVisible(hwnd):
                    self.hwnd = hwnd
                    return False
                return True

        wi = WindowInfo()
        start_time = win32api.GetTickCount()

        while win32api.GetTickCount() - start_time < timeout_ms:
            win32gui.EnumWindows(wi.enum_callback, None)
            if wi.hwnd:
                return wi.hwnd
            win32api.Sleep(100)

        return None

class XAMLIconHandler:
    XAML_TEMPLATE = """
<Button x:Class="ProgramLauncher.IconButton"
        xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Width="48" Height="48"
        Style="{StaticResource ProgramIconButtonStyle}"
        Click="OnProgramIconClick">
    <Button.Content>
        <Grid>
            <Image Source="{Binding IconSource}"
                   Width="32" Height="32"
                   RenderOptions.BitmapScalingMode="HighQuality"/>
            <TextBlock Text="{Binding ProgramName}"
                      TextAlignment="Center"
                      TextWrapping="Wrap"
                      VerticalAlignment="Bottom"/>
        </Grid>
    </Button.Content>
</Button>
"""

    def __init__(self):
        self.launcher = ProgramLauncher()
        
    def create_icon_button(self, 
                          program_path: str, 
                          icon_path: str, 
                          program_name: str) -> None:
        # This would typically be handled by a XAML parser/compiler
        # Here we're just demonstrating the structure
        pass

    def handle_icon_click(self, program_path: str) -> None:
        success, process_id = self.launcher.launch_program(program_path)
        if success and process_id:
            hwnd = self.launcher.get_window_handle_by_pid(process_id)
            if hwnd:
                self.launcher.set_program_icon(hwnd, 
                    os.path.join(os.path.dirname(program_path), "icon.ico"))

# Usage example
if __name__ == "__main__":
    launcher = ProgramLauncher()
    xaml_handler = XAMLIconHandler()
    
    # Example program launch
    program_path = r"C:\Program Files\Example\program.exe"
    success, pid = launcher.launch_program(program_path)
    
    if success and pid:
        # Get window handle and set icon
        hwnd = launcher.get_window_handle_by_pid(pid)
        if hwnd:
            launcher.set_program_icon(hwnd, "path/to/icon.ico")
            
        # Create shortcut
        launcher.create_program_shortcut(
            program_path,
            os.path.join(os.environ["USERPROFILE"], "Desktop", "Program.lnk"),
            "Program Description",
            "path/to/icon.ico"
        )
