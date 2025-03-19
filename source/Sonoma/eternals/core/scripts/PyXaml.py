
import os
import sys
from typing import Any, Dict, List, Optional, Union
from xml.etree import ElementTree as ET

class PyXamlParser:
    def __init__(self, xaml_path: str):
        self.xaml_path = xaml_path
        self.root = None
        self.namespaces = {}
        self.bindings = {}
        self.signals = {}
        self.styles = {}
        
    def parse(self) -> None:
        """Parse the XAML file and initialize components"""
        try:
            tree = ET.parse(self.xaml_path)
            self.root = tree.getroot()
            self._parse_namespaces()
            self._parse_resources()
            self._parse_bindings()
            self._parse_signals()
        except ET.ParseError as e:
            raise XamlParseError(f"Failed to parse XAML file: {str(e)}")

    def _parse_namespaces(self) -> None:
        """Extract and store namespace declarations"""
        for key, value in self.root.attrib.items():
            if key.startswith("xmlns:"):
                self.namespaces[key.split(':')[1]] = value

    def _parse_resources(self) -> None:
        """Parse resource dictionaries and styles"""
        resource_dict = self.root.find(".//ResourceDictionary")
        if resource_dict is not None:
            for resource in resource_dict:
                if "Key" in resource.attrib:
                    self.styles[resource.attrib["Key"]] = self._parse_style(resource)

    def _parse_style(self, element: ET.Element) -> Dict[str, Any]:
        """Parse style definitions"""
        style = {
            "Type": element.get("TargetType", ""),
            "Setters": [],
            "Triggers": []
        }
        
        for setter in element.findall(".//Setter"):
            style["Setters"].append({
                "Property": setter.get("Property", ""),
                "Value": setter.get("Value", "")
            })
            
        for trigger in element.findall(".//Trigger"):
            style["Triggers"].append({
                "Property": trigger.get("Property", ""),
                "Value": trigger.get("Value", ""),
                "Setters": self._parse_trigger_setters(trigger)
            })
            
        return style

    def _parse_trigger_setters(self, trigger: ET.Element) -> List[Dict[str, str]]:
        """Parse setters within triggers"""
        setters = []
        for setter in trigger.findall(".//Setter"):
            setters.append({
                "Property": setter.get("Property", ""),
                "Value": setter.get("Value", "")
            })
        return setters

    def _parse_bindings(self) -> None:
        """Parse data bindings"""
        for element in self.root.iter():
            for key, value in element.attrib.items():
                if value.startswith("{Binding"):
                    binding_info = self._parse_binding_expression(value)
                    self.bindings[element.tag + "." + key] = binding_info

    def _parse_binding_expression(self, expression: str) -> Dict[str, str]:
        """Parse binding expression syntax"""
        binding = {
            "Path": "",
            "Mode": "OneWay",
            "UpdateSourceTrigger": "PropertyChanged",
            "Converter": None
        }
        
        expression = expression.strip("{Binding").strip("}")
        parts = [p.strip() for p in expression.split(",")]
        
        for part in parts:
            if "=" in part:
                key, value = part.split("=")
                binding[key.strip()] = value.strip()
            else:
                binding["Path"] = part.strip()
                
        return binding

    def _parse_signals(self) -> None:
        """Parse event signals and handlers"""
        for element in self.root.iter():
            for key, value in element.attrib.items():
                if key.startswith("on_") or key.endswith("Command"):
                    self.signals[element.tag + "." + key] = value

    def generate_code(self) -> str:
        """Generate Python code from XAML"""
        code = []
        code.append("import sys")
        code.append("from PyQt5 import QtWidgets, QtCore")
        code.append("\n")
        
        # Generate class definition
        class_name = os.path.splitext(os.path.basename(self.xaml_path))[0]
        code.append(f"class {class_name}(QtWidgets.QWidget):")
        code.append("    def __init__(self, parent=None):")
        code.append("        super().__init__(parent)")
        code.append("        self.setup_ui()")
        code.append("        self.setup_signals()")
        code.append("\n")
        
        # Generate UI setup
        self._generate_ui_setup(code)
        
        # Generate signal connections
        self._generate_signal_setup(code)
        
        return "\n".join(code)

    def _generate_ui_setup(self, code: List[str]) -> None:
        """Generate UI setup code"""
        code.append("    def setup_ui(self):")
        code.append("        self.setObjectName(self.__class__.__name__)")
        
        # Layout setup
        layout = self.root.find(".//Layout")
        if layout is not None:
            layout_type = layout.get("type", "vbox")
            code.append(f"        self.layout = QtWidgets.Q{layout_type.capitalize()}Layout()")
            code.append("        self.setLayout(self.layout)")
            
        # Generate widget creation code
        self._generate_widgets(code, self.root, "self.layout")

    def _generate_widgets(self, code: List[str], parent: ET.Element, parent_layout: str, indent: str = "        ") -> None:
        """Generate widget creation and setup code"""
        for child in parent:
            if child.tag in ["Button", "Label", "TextBox", "ComboBox"]:
                widget_name = child.get("Name", f"{child.tag.lower()}_{len(code)}")
                code.append(f"{indent}self.{widget_name} = QtWidgets.Q{child.tag}()")
                
                # Set properties
                for key, value in child.attrib.items():
                    if key not in ["Name"] and not key.startswith("on_"):
                        code.append(f"{indent}self.{widget_name}.set{key}({repr(value)})")
                
                code.append(f"{indent}{parent_layout}.addWidget(self.{widget_name})")

    def _generate_signal_setup(self, code: List[str]) -> None:
        """Generate signal connection code"""
        code.append("    def setup_signals(self):")
        
        for signal_key, handler in self.signals.items():
            widget, event = signal_key.split(".")
            widget_name = widget.split("}")[-1]
            code.append(f"        self.{widget_name}.{event}.connect(self.{handler})")

class XamlParseError(Exception):
    """Exception raised for XAML parsing errors"""
    pass

class XamlBindingManager:
    """Manages data bindings between model and UI"""
    def __init__(self):
        self.bindings = {}
        self.property_changed_handlers = {}

    def register_binding(self, source: Any, property_name: str, target: Any, target_property: str,
                        mode: str = "OneWay", converter: Optional[callable] = None) -> None:
        """Register a new data binding"""
        binding_key = f"{id(source)}_{property_name}"
        self.bindings[binding_key] = {
            "source": source,
            "property": property_name,
            "target": target,
            "target_property": target_property,
            "mode": mode,
            "converter": converter
        }
        
        # Set up property changed notification
        if hasattr(source, "property_changed"):
            source.property_changed.connect(
                lambda p: self._handle_property_changed(source, p)
            )

    def _handle_property_changed(self, source: Any, property_name: str) -> None:
        """Handle property changed notifications"""
        binding_key = f"{id(source)}_{property_name}"
        if binding_key in self.bindings:
            binding = self.bindings[binding_key]
            value = getattr(source, property_name)
            
            if binding["converter"]:
                value = binding["converter"](value)
                
            setattr(binding["target"], binding["target_property"], value)

class StyleManager:
    """Manages UI styles and themes"""
    def __init__(self):
        self.styles = {}
        self.active_theme = "default"

    def register_style(self, style_key: str, style_dict: Dict[str, Any]) -> None:
        """Register a new style"""
        self.styles[style_key] = style_dict

    def apply_style(self, widget: Any, style_key: str) -> None:
        """Apply a style to a widget"""
        if style_key in self.styles:
            style = self.styles[style_key]
            
            # Apply basic properties
            for setter in style["Setters"]:
                property_name = setter["Property"]
                value = setter["Value"]
                if hasattr(widget, f"set{property_name}"):
                    getattr(widget, f"set{property_name}")(value)
            
            # Apply style sheet
            self._apply_style_sheet(widget, style)

    def _apply_style_sheet(self, widget: Any, style: Dict[str, Any]) -> None:
        """Apply Qt style sheet"""
        style_sheet = []
        
        # Basic properties
        for setter in style["Setters"]:
            if setter["Property"].lower() in ["background", "color", "font"]:
                style_sheet.append(f"{setter['Property'].lower()}: {setter['Value']};")
        
        # Triggers/States
        for trigger in style["Triggers"]:
            state = trigger["Property"].lower()
            style_sheet.append(f":{state} {{")
            for setter in trigger["Setters"]:
                style_sheet.append(f"    {setter['Property'].lower()}: {setter['Value']};")
            style_sheet.append("}")
        
        widget.setStyleSheet(" ".join(style_sheet))

class SignalManager:
    """Manages UI event signals and handlers"""
    def __init__(self):
        self.signals = {}
        self.handlers = {}

    def register_signal(self, widget: Any, signal_name: str, handler: callable,
                       filter_func: Optional[callable] = None) -> None:
        """Register a signal handler"""
        signal_key = f"{id(widget)}_{signal_name}"
        self.signals[signal_key] = {
            "widget": widget,
            "signal": signal_name,
            "handler": handler,
            "filter": filter_func
        }
        
        # Connect the signal
        if hasattr(widget, signal_name):
            signal = getattr(widget, signal_name)
            if filter_func:
                signal.connect(lambda *args: self._filtered_handler(signal_key, *args))
            else:
                signal.connect(handler)

    def _filtered_handler(self, signal_key: str, *args) -> None:
        """Handle filtered signals"""
        signal_info = self.signals[signal_key]
        if signal_info["filter"](*args):
            signal_info["handler"](*args)

    def unregister_signal(self, widget: Any, signal_name: str) -> None:
        """Unregister a signal handler"""
        signal_key = f"{id(widget)}_{signal_name}"
        if signal_key in self.signals:
            signal_info = self.signals[signal_key]
            if hasattr(signal_info["widget"], signal_name):
                signal = getattr(signal_info["widget"], signal_name)
                signal.disconnect(signal_info["handler"])
            del self.signals[signal_key]
 