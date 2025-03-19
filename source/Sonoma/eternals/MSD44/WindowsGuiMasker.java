
import java.io.*;
import java.nio.file.*;
import javax.xml.parsers.*;
import org.w3c.dom.*;

public class WindowsGuiMasker {
    private static final String[] LEGACY_UI_PATTERNS = {".xaml", ".baml", ".resources"};
    private static final String BACKUP_SUFFIX = ".bak";
    
    public void maskOldGui(String workspacePath) throws IOException {
        try {
            Files.walk(Paths.get(workspacePath))
                .filter(Files::isRegularFile)
                .filter(this::isLegacyUiFile)
                .forEach(this::processUiFile);
        } catch (IOException e) {
            throw new IOException("Failed to process workspace: " + e.getMessage());
        }
    }

    private boolean isLegacyUiFile(Path path) {
        String fileName = path.toString().toLowerCase();
        for (String pattern : LEGACY_UI_PATTERNS) {
            if (fileName.endsWith(pattern)) {
                return true;
            }
        }
        return false;
    }

    private void processUiFile(Path file) {
        try {
            // Create backup of original file
            Path backupFile = Paths.get(file.toString() + BACKUP_SUFFIX);
            Files.copy(file, backupFile, StandardCopyOption.REPLACE_EXISTING);

            // Read and parse XAML
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            DocumentBuilder builder = factory.newDocumentBuilder();
            Document doc = builder.parse(file.toFile());

            // Update UI elements with modern equivalents
            updateUiElements(doc);

            // Write updated XAML back to file
            TransformerFactory transformerFactory = TransformerFactory.newInstance();
            Transformer transformer = transformerFactory.newTransformer();
            DOMSource source = new DOMSource(doc);
            StreamResult result = new StreamResult(file.toFile());
            transformer.transform(source, result);

        } catch (Exception e) {
            System.err.println("Error processing file " + file + ": " + e.getMessage());
        }
    }

    private void updateUiElements(Document doc) {
        // Replace old Window elements
        replaceElements(doc, "Window", "modern:Window");
        
        // Update legacy controls
        replaceElements(doc, "Button", "modern:Button");
        replaceElements(doc, "TextBox", "modern:TextBox");
        replaceElements(doc, "ComboBox", "modern:ComboBox");
        replaceElements(doc, "ListBox", "modern:ListBox");
        
        // Add modern styling
        Element root = doc.getDocumentElement();
        root.setAttribute("xmlns:modern", "http://schemas.microsoft.com/winfx/2006/xaml/presentation");
    }

    private void replaceElements(Document doc, String oldTag, String newTag) {
        NodeList elements = doc.getElementsByTagName(oldTag);
        for (int i = 0; i < elements.getLength(); i++) {
            Element oldElement = (Element) elements.item(i);
            Element newElement = doc.createElement(newTag);
            
            // Copy attributes
            NamedNodeMap attributes = oldElement.getAttributes();
            for (int j = 0; j < attributes.getLength(); j++) {
                Node attribute = attributes.item(j);
                newElement.setAttribute(attribute.getNodeName(), attribute.getNodeValue());
            }
            
            // Copy children
            while (oldElement.hasChildNodes()) {
                newElement.appendChild(oldElement.getFirstChild());
            }
            
            oldElement.getParentNode().replaceChild(newElement, oldElement);
        }
    }
}
