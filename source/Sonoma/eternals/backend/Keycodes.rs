
use std::collections::HashMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum KeyCode {
    // System Controls
    WindowKey,
    Alt,
    Control,
    Shift,
    Escape,
    Tab,
    
    // Window Management
    Close,
    Minimize,
    Maximize,
    Restore,
    
    // Application Controls
    AppSwitch,
    AppLaunch,
    TaskView,
    
    // Desktop Navigation
    DesktopLeft,
    DesktopRight,
    ShowDesktop,
    
    // Taskbar
    TaskbarPin,
    TaskbarUnpin,
    TaskbarShow,
    TaskbarHide,
    
    // Quick Settings
    NotificationCenter,
    QuickSettings,
    
    // Media Controls
    VolumeUp,
    VolumeDown,
    VolumeMute,
    MediaPlayPause,
    
    // Utility Shortcuts
    Screenshot,
    ScreenSnip,
    Search,
    
    // Custom Actions
    Custom(u32),
}

pub struct KeycodeHandler {
    keymap: HashMap<KeyCode, Box<dyn Fn() -> bool>>,
}

impl KeycodeHandler {
    pub fn new() -> Self {
        Self {
            keymap: HashMap::new(),
        }
    }

    pub fn register_handler(&mut self, keycode: KeyCode, handler: Box<dyn Fn() -> bool>) {
        self.keymap.insert(keycode, handler);
    }

    pub fn handle_keycode(&self, keycode: KeyCode) -> bool {
        if let Some(handler) = self.keymap.get(&keycode) {
            handler()
        } else {
            false
        }
    }

    pub fn is_system_key(&self, keycode: &KeyCode) -> bool {
        matches!(
            keycode,
            KeyCode::WindowKey | KeyCode::Alt | KeyCode::Control | KeyCode::Shift
        )
    }

    pub fn get_modifier_combination(&self, keycodes: &[KeyCode]) -> Vec<KeyCode> {
        keycodes
            .iter()
            .filter(|k| self.is_system_key(k))
            .cloned()
            .collect()
    }
}

impl Default for KeycodeHandler {
    fn default() -> Self {
        Self::new()
    }
}
