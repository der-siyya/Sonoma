
import os
import sys
import winreg
import ctypes
import win32gui
import win32con
import win32api
from pathlib import Path
from typing import Optional, Dict, List, Tuple

class WindowsCoreUI:
    def __init__(self):
        self.xaml_path = Path("eternals/ui")
        self.styles_path = Path("eternals/ui/styles")
        self.resources_path = Path("eternals/Resources")
        self.window_handle = None
        self.active_controls = {}
        self.theme_settings = {}
        
    def initialize_window(self, title: str, width: int = 800, height: int = 600) -> None:
        wc = win32gui.WNDCLASS()
        wc.lpszClassName = "EternalsCustomWindow"
        wc.hbrBackground = win32gui.GetStockObject(win32con.WHITE_BRUSH)
        wc.lpfnWndProc = self._window_proc
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        
        win32gui.RegisterClass(wc)
        self.window_handle = win32gui.CreateWindow(
            wc.lpszClassName,
            title,
            win32con.WS_OVERLAPPEDWINDOW,
            win32con.CW_USEDEFAULT,
            win32con.CW_USEDEFAULT,
            width,
            height,
            0,
            0,
            0,
            None
        )
        
    def load_xaml_styles(self) -> None:
        self.theme_settings = {
            "primary_color": "#1E90FF",
            "secondary_color": "#4682B4",
            "background_color": "#FFFFFF",
            "text_color": "#000000",
            "font_family": "Segoe UI",
            "border_radius": "4px",
            "padding": "8px"
        }
        
        style_files = list(self.xaml_path.glob("*.xaml"))
        for style_file in style_files:
            self._parse_xaml_file(style_file)
            
    def _parse_xaml_file(self, file_path: Path) -> None:
        with open(file_path, 'r') as f:
            xaml_content = f.read()
            self._apply_xaml_styles(xaml_content)
            
    def _apply_xaml_styles(self, xaml_content: str) -> None:
        # Apply custom styles to window
        if self.window_handle:
            style = win32gui.GetWindowLong(self.window_handle, win32con.GWL_STYLE)
            win32gui.SetWindowLong(self.window_handle, win32con.GWL_STYLE, style)
            
    def create_custom_button(self, text: str, x: int, y: int, width: int, height: int) -> int:
        button_style = win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.BS_PUSHBUTTON
        button_handle = win32gui.CreateWindow(
            "BUTTON",
            text,
            button_style,
            x, y, width, height,
            self.window_handle,
            0,
            0,
            None
        )
        self._apply_control_styling(button_handle, "button")
        return button_handle
        
    def create_custom_textbox(self, x: int, y: int, width: int, height: int) -> int:
        textbox_style = win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.ES_MULTILINE
        textbox_handle = win32gui.CreateWindow(
            "EDIT",
            "",
            textbox_style,
            x, y, width, height,
            self.window_handle,
            0,
            0,
            None
        )
        self._apply_control_styling(textbox_handle, "textbox")
        return textbox_handle
        
    def _apply_control_styling(self, handle: int, control_type: str) -> None:
        if control_type == "button":
            win32gui.SendMessage(handle, win32con.WM_SETFONT, 
                               win32gui.CreateFont(-12, 0, 0, 0, 400, 0, 0, 0, 0, 0, 0, 0, 0, self.theme_settings["font_family"]),
                               True)
        elif control_type == "textbox":
            win32gui.SendMessage(handle, win32con.WM_SETFONT,
                               win32gui.CreateFont(-12, 0, 0, 0, 400, 0, 0, 0, 0, 0, 0, 0, 0, self.theme_settings["font_family"]),
                               True)
            
    def _window_proc(self, hwnd: int, msg: int, wparam: int, lparam: int) -> Optional[int]:
        if msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
        
    def set_window_icon(self, icon_path: str) -> None:
        if os.path.exists(icon_path):
            icon_handle = win32gui.LoadImage(
                0, icon_path, win32con.IMAGE_ICON,
                0, 0, win32con.LR_LOADFROMFILE
            )
            win32gui.SendMessage(
                self.window_handle,
                win32con.WM_SETICON,
                win32con.ICON_BIG,
                icon_handle
            )
            
    def create_custom_listview(self, x: int, y: int, width: int, height: int) -> int:
        listview_style = win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.LVS_REPORT
        listview_handle = win32gui.CreateWindow(
            "SysListView32",
            None,
            listview_style,
            x, y, width, height,
            self.window_handle,
            0,
            0,
            None
        )
        self._apply_control_styling(listview_handle, "listview")
        return listview_handle
        
    def create_custom_treeview(self, x: int, y: int, width: int, height: int) -> int:
        treeview_style = win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.TVS_HASLINES
        treeview_handle = win32gui.CreateWindow(
            "SysTreeView32",
            None,
            treeview_style,
            x, y, width, height,
            self.window_handle,
            0,
            0,
            None
        )
        self._apply_control_styling(treeview_handle, "treeview")
        return treeview_handle
        
    def set_dark_mode(self) -> None:
        self.theme_settings.update({
            "primary_color": "#2C2C2C",
            "secondary_color": "#3C3C3C",
            "background_color": "#1E1E1E",
            "text_color": "#FFFFFF"
        })
        self._refresh_window_style()
        
    def set_light_mode(self) -> None:
        self.theme_settings.update({
            "primary_color": "#1E90FF",
            "secondary_color": "#4682B4",
            "background_color": "#FFFFFF",
            "text_color": "#000000"
        })
        self._refresh_window_style()
        
    def _refresh_window_style(self) -> None:
        if self.window_handle:
            win32gui.InvalidateRect(self.window_handle, None, True)
            win32gui.UpdateWindow(self.window_handle)
            
    def show_window(self) -> None:
        win32gui.ShowWindow(self.window_handle, win32con.SW_SHOW)
        win32gui.UpdateWindow(self.window_handle)
        
    def message_loop(self) -> None:
        msg = ctypes.wintypes.MSG()
        while win32gui.GetMessage(msg, 0, 0, 0):
            win32gui.TranslateMessage(msg)
            win32gui.DispatchMessage(msg)
            
    def cleanup(self) -> None:
        if self.window_handle:
            win32gui.DestroyWindow(self.window_handle)
            
    def register_hotkey(self, id: int, modifiers: int, vk: int) -> bool:
        return win32api.RegisterHotKey(self.window_handle, id, modifiers, vk)
        
    def create_system_tray_icon(self, icon_path: str, tooltip: str) -> None:
        if os.path.exists(icon_path):
            nid = (self.window_handle, 0, win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
                   win32con.WM_USER + 20, win32gui.LoadImage(0, icon_path, win32con.IMAGE_ICON, 0, 0, win32con.LR_LOADFROMFILE),
                   tooltip)
            win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
            
    def remove_system_tray_icon(self) -> None:
        nid = (self.window_handle, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)

def main():
    ui = WindowsCoreUI()
    ui.initialize_window("Eternals Custom Window")
    ui.load_xaml_styles()
    ui.set_window_icon("eternals/Resources/icons/app.ico")
    
    # Create controls
    ui.create_custom_button("Click Me", 10, 10, 100, 30)
    ui.create_custom_textbox(10, 50, 200, 100)
    ui.create_custom_listview(10, 160, 200, 150)
    ui.create_custom_treeview(220, 10, 200, 300)
    
    # Show window and start message loop
    ui.show_window()
    ui.message_loop()
    
    # Cleanup
    ui.cleanup()

if __name__ == "__main__":
    main()
