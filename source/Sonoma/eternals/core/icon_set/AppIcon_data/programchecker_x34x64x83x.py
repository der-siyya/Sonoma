
import os
import sys
import winreg
import win32com.client
import win32gui
import win32con
import win32api
import win32process
import psutil
import pythoncom
from pathlib import Path
from typing import List, Dict, Tuple, Set
from xml.etree import ElementTree as ET
import logging
import hashlib
import threading
import queue
import time
import re

class ProgramIconScanner:
    def __init__(self):
        self.program_paths = {
            'x32': r'C:\Program Files (x86)',
            'x64': r'C:\Program Files',
            'x83': r'C:\Users\%USERNAME%\AppData\Local'
        }
        self.icon_cache = {}
        self.discovered_apps = set()
        self.logger = self._setup_logging()
        self.scan_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.worker_threads = []
        self.xaml_path = r"taskbar\appicons.xaml"
        
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('ProgramIconScanner')
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler('program_scanner.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def extract_icon_from_exe(self, exe_path: str) -> Tuple[str, bytes]:
        try:
            large, small = win32gui.ExtractIconEx(exe_path, 0)
            if large:
                icon_handle = large[0]
                icon_info = win32gui.GetIconInfo(icon_handle)
                icon_bitmap = win32gui.GetObject(icon_info[4])
                icon_bytes = icon_bitmap.GetBitmapBits(True)
                win32gui.DestroyIcon(icon_handle)
                return (exe_path, icon_bytes)
        except Exception as e:
            self.logger.error(f"Failed to extract icon from {exe_path}: {str(e)}")
        return (exe_path, None)

    def scan_directory_worker(self):
        while True:
            try:
                directory = self.scan_queue.get_nowait()
                self._scan_directory_recursive(directory)
                self.scan_queue.task_done()
            except queue.Empty:
                break

    def _scan_directory_recursive(self, directory: str):
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith('.exe'):
                        full_path = os.path.join(root, file)
                        self._process_executable(full_path)
        except Exception as e:
            self.logger.error(f"Error scanning directory {directory}: {str(e)}")

    def _process_executable(self, exe_path: str):
        try:
            file_info = win32api.GetFileVersionInfo(exe_path, '\\')
            ms_file_version = file_info['FileVersionMS']
            ls_file_version = file_info['FileVersionLS']
            version = f"{win32api.HIWORD(ms_file_version)}.{win32api.LOWORD(ms_file_version)}.{win32api.HIWORD(ls_file_version)}.{win32api.LOWORD(ls_file_version)}"
            
            program_info = {
                'path': exe_path,
                'name': os.path.splitext(os.path.basename(exe_path))[0],
                'version': version,
                'architecture': self._detect_architecture(exe_path),
                'icon': self.extract_icon_from_exe(exe_path)
            }
            
            self.result_queue.put(program_info)
            
        except Exception as e:
            self.logger.error(f"Error processing executable {exe_path}: {str(e)}")

    def _detect_architecture(self, exe_path: str) -> str:
        try:
            with open(exe_path, 'rb') as f:
                dos_header = f.read(2)
                if dos_header != b'MZ':
                    return 'unknown'
                
                f.seek(60)
                pe_offset = int.from_bytes(f.read(4), byteorder='little')
                f.seek(pe_offset)
                pe_header = f.read(6)
                
                if pe_header[4:6] == b'\x64\x86':
                    return 'x64'
                elif pe_header[4:6] == b'\x4C\x01':
                    return 'x32'
                else:
                    return 'x83'
        except Exception as e:
            self.logger.error(f"Error detecting architecture for {exe_path}: {str(e)}")
            return 'unknown'

    def generate_xaml(self, programs: List[Dict]) -> str:
        xaml = '''<ResourceDictionary xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
                    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
    <ItemsControl x:Key="TaskbarAppIcons">'''
        
        for program in programs:
            if program['icon'][1]:  # If icon data exists
                icon_hash = hashlib.md5(program['icon'][1]).hexdigest()
                xaml += f'''
        <AppIcon Path="{program['path']}"
                 Name="{program['name']}"
                 Version="{program['version']}"
                 Architecture="{program['architecture']}"
                 IconHash="{icon_hash}" />'''
        
        xaml += '''
    </ItemsControl>
</ResourceDictionary>'''
        return xaml

    def save_xaml(self, xaml_content: str):
        try:
            with open(self.xaml_path, 'w', encoding='utf-8') as f:
                f.write(xaml_content)
        except Exception as e:
            self.logger.error(f"Error saving XAML file: {str(e)}")

    def scan_registry_for_installed_programs(self):
        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
        ]

        for reg_root, reg_path in registry_paths:
            try:
                reg_key = winreg.OpenKey(reg_root, reg_path)
                for i in range(winreg.QueryInfoKey(reg_key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(reg_key, i)
                        subkey = winreg.OpenKey(reg_key, subkey_name)
                        try:
                            install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                            if install_location and os.path.exists(install_location):
                                self.scan_queue.put(install_location)
                        except:
                            pass
                        winreg.CloseKey(subkey)
                    except WindowsError:
                        continue
                winreg.CloseKey(reg_key)
            except WindowsError:
                self.logger.error(f"Error accessing registry path: {reg_path}")

    def start_scan(self):
        self.logger.info("Starting program scan...")
        
        # Add default program directories to scan queue
        for arch, path in self.program_paths.items():
            expanded_path = os.path.expandvars(path)
            if os.path.exists(expanded_path):
                self.scan_queue.put(expanded_path)

        # Scan registry for additional program locations
        self.scan_registry_for_installed_programs()

        # Create and start worker threads
        num_threads = os.cpu_count() or 4
        self.worker_threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=self.scan_directory_worker)
            thread.start()
            self.worker_threads.append(thread)

        # Wait for all scanning to complete
        for thread in self.worker_threads:
            thread.join()

        # Collect all results
        programs = []
        while not self.result_queue.empty():
            programs.append(self.result_queue.get())

        # Generate and save XAML
        xaml_content = self.generate_xaml(programs)
        self.save_xaml(xaml_content)
        
        self.logger.info(f"Scan completed. Found {len(programs)} programs.")
        return programs

class IconUpdateMonitor:
    def __init__(self, scanner: ProgramIconScanner):
        self.scanner = scanner
        self.last_scan_time = 0
        self.scan_interval = 3600  # 1 hour
        self.monitor_thread = None
        self.should_stop = threading.Event()

    def start_monitoring(self):
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.start()

    def stop_monitoring(self):
        self.should_stop.set()
        if self.monitor_thread:
            self.monitor_thread.join()

    def _monitor_loop(self):
        while not self.should_stop.is_set():
            current_time = time.time()
            if current_time - self.last_scan_time >= self.scan_interval:
                self.scanner.start_scan()
                self.last_scan_time = current_time
            time.sleep(60)  # Check every minute

def main():
    scanner = ProgramIconScanner()
    monitor = IconUpdateMonitor(scanner)
    
    try:
        # Perform initial scan
        scanner.start_scan()
        
        # Start monitoring for changes
        monitor.start_monitoring()
        
        # Keep the script running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        monitor.stop_monitoring()
        scanner.logger.info("Program scanner stopped by user.")
    except Exception as e:
        scanner.logger.error(f"Unexpected error: {str(e)}")
        monitor.stop_monitoring()

if __name__ == "__main__":
    main()
