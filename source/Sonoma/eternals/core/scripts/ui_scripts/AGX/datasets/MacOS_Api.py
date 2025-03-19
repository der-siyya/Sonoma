
import platform
import subprocess
import os
from typing import Optional, Dict, List, Union

class MacOSApiHandler:
    def __init__(self):
        self.is_macos = platform.system().lower() == 'darwin'
        
    def execute_macos_command(self, command: str) -> Optional[str]:
        """Execute MacOS specific commands and return the output"""
        if not self.is_macos:
            return None
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return result.stdout.strip()
        except Exception:
            return None

    def get_system_info(self) -> Dict[str, str]:
        """Get MacOS system information"""
        info = {}
        if self.is_macos:
            info['os_version'] = self.execute_macos_command('sw_vers -productVersion')
            info['build_version'] = self.execute_macos_command('sw_vers -buildVersion')
            info['computer_name'] = self.execute_macos_command('scutil --get ComputerName')
        return info

    def get_installed_apps(self) -> List[str]:
        """Get list of installed applications"""
        apps = []
        if self.is_macos:
            apps_dir = '/Applications'
            if os.path.exists(apps_dir):
                apps = [app.replace('.app', '') for app in os.listdir(apps_dir) if app.endswith('.app')]
        return apps

    def get_system_preferences(self) -> Dict[str, Union[str, bool]]:
        """Get MacOS system preferences"""
        prefs = {}
        if self.is_macos:
            # Get dark mode status
            dark_mode = self.execute_macos_command('defaults read -g AppleInterfaceStyle')
            prefs['dark_mode'] = dark_mode == 'Dark'
            
            # Get screen resolution
            display_info = self.execute_macos_command('system_profiler SPDisplaysDataType')
            if display_info:
                prefs['display_info'] = display_info
                
            # Get volume level
            volume = self.execute_macos_command('osascript -e "output volume of (get volume settings)"')
            if volume:
                prefs['volume'] = int(volume)
        
        return prefs

    def simulate_macos_behavior(self) -> None:
        """Simulate MacOS-specific behaviors in Windows"""
        if not self.is_macos:
            # Map common MacOS paths to Windows equivalents
            self.path_mappings = {
                '/Applications': os.environ.get('PROGRAMFILES', 'C:\\Program Files'),
                '/Users': os.environ.get('USERPROFILE', 'C:\\Users'),
                '/Library': os.path.join(os.environ.get('SYSTEMROOT', 'C:\\Windows'), 'System32')
            }
            
            # Map common MacOS commands to Windows equivalents
            self.command_mappings = {
                'open': 'start',
                'say': 'powershell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak"',
                'pbcopy': 'clip',
                'pbpaste': 'powershell -command "Get-Clipboard"'
            }
