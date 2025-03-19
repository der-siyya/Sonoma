package eternals.core.scripts.ui_scripts.AGX;

import java.io.*;
import java.net.*;
import java.util.concurrent.*;
import java.util.HashMap;
import java.util.Map;

public class XamlDeliveryService {
    private static final String XAML_SERVICE_URL = "http://localhost:8080/xaml-service";
    private static XamlDeliveryService instance;
    private final Map<String, String> xamlCache;
    private final ExecutorService executorService;

    private XamlDeliveryService() {
        xamlCache = new ConcurrentHashMap<>();
        executorService = Executors.newCachedThreadPool();
    }

    public static XamlDeliveryService getInstance() {
        if (instance == null) {
            instance = new XamlDeliveryService();
        }
        return instance;
    }

    public String loadXamlProcess(String processId) throws IOException {
        if (xamlCache.containsKey(processId)) {
            return xamlCache.get(processId);
        }

        String xamlContent = fetchFromService("/process/" + processId);
        xamlCache.put(processId, xamlContent);
        return xamlContent;
    }

    public String loadUIObject(String objectId) throws IOException {
        if (xamlCache.containsKey(objectId)) {
            return xamlCache.get(objectId);
        }

        String xamlContent = fetchFromService("/ui-object/" + objectId);
        xamlCache.put(objectId, xamlContent);
        return xamlContent;
    }

    public byte[] loadXamlBinary(String binaryId) throws IOException {
        URL url = new URL(XAML_SERVICE_URL + "/binary/" + binaryId);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("GET");

        try (InputStream inputStream = connection.getInputStream();
             ByteArrayOutputStream outputStream = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[4096];
            int bytesRead;
            while ((bytesRead = inputStream.read(buffer)) != -1) {
                outputStream.write(buffer, 0, bytesRead);
            }
            return outputStream.toByteArray();
        }
    }

    public Future<String> loadXamlCodeAsync(String codeId) {
        return executorService.submit(() -> {
            if (xamlCache.containsKey(codeId)) {
                return xamlCache.get(codeId);
            }

            String xamlContent = fetchFromService("/code/" + codeId);
            xamlCache.put(codeId, xamlContent);
            return xamlContent;
        });
    }

    public void clearCache() {
        xamlCache.clear();
    }

    public void shutdown() {
        executorService.shutdown();
        try {
            if (!executorService.awaitTermination(60, TimeUnit.SECONDS)) {
                executorService.shutdownNow();
            }
        } catch (InterruptedException e) {
            executorService.shutdownNow();
            Thread.currentThread().interrupt();
        }
    }

    private String fetchFromService(String path) throws IOException {
        URL url = new URL(XAML_SERVICE_URL + path);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("GET");

        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(connection.getInputStream()))) {
            StringBuilder response = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                response.append(line);
            }
            return response.toString();
        }
    }
}
