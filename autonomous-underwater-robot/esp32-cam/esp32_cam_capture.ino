// This is the Arduino sketch for your ESP32-CAM.
// It handles Wi-Fi connection, camera capture, saving to its internal SD card,
// and then uploading the image data to your Flask API on the Raspberry Pi.

// --- Libraries ---
#include "esp_camera.h" // For camera functions
#include "WiFi.h"       // For Wi-Fi connection
#include "HTTPClient.h" // For making HTTP requests (e.g., POSTing images)
#include "FS.h"         // File System for SD card
#include "SD_MMC.h"     // For SD_MMC (native SD card interface on ESP32-CAM)

// --- Configuration ---

// Wi-Fi credentials
const char* ssid = "kram 2.4g"; // Your Wi-Fi SSID
const char* password = "244466666"; // Your Wi-Fi Password

// Raspberry Pi Flask API configuration
// IMPORTANT: Replace with the actual IP address of your Raspberry Pi.
// This must be the same IP your web dashboard uses to fetch data.
const char* raspberryPiIp = "192.168.1.15"; // e.g., "192.168.100.216"
const int flaskApiPort = 5000; // Default Flask port
const char* uploadEndpoint = "/upload_image"; // Endpoint on Flask API to receive image uploads

// Camera settings (adjusted for ESP32-CAM module)
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

#define LED_GPIO_NUM      -1 // Using default board LED, if any, often GPIO4
#define BOARD_LED_GPIO    4 // GPIO for the flash LED on ESP32-CAM AI-Thinker board
#define FLASH_LED_CHANNEL 0 // PWM channel for LED control

// Global variables
unsigned long lastCaptureTime = 0;
const long captureInterval = 10000; // Capture every 10 seconds (10000 ms)

// --- Setup Function ---
void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  // Initialize LED (optional, for visual feedback)
  pinMode(BOARD_LED_GPIO, OUTPUT);
  digitalWrite(BOARD_LED_GPIO, HIGH); // Turn off LED initially (LED is active low on some boards)

  // Configure camera
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_siod = SIOD_GPIO_NUM;
  config.pin_sioc = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG; 
  
  // Frame size, can be adjusted for memory/transmission needs
  // Recommended to start with a smaller resolution like QVGA or CIF for testing
  // to avoid memory issues and speed up uploads.
  config.frame_size = FRAMESIZE_SVGA; // SVGA (800x600) is a good balance. Other options: UXGA, SXGA, XGA, VGA, CIF, QVGA, QQVGA, QQCIF
  config.jpeg_quality = 10; // 0-63, lower number means higher quality
  config.fb_count = 1;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }
  Serial.println("Camera initialized.");

  // Configure camera parameters (optional, uncomment as needed)
  sensor_t * s = esp_camera_sensor_get();
  // s->set_vflip(s, 1);       // Flip vertically
  // s->set_hmirror(s, 1);    // Mirror horizontally
  // s->set_brightness(s, 0); // -2 to 2
  // s->set_contrast(s, 0);   // -2 to 2
  // s->set_saturation(s, 0); // -2 to 2

  // Initialize SD_MMC (native SD card interface)
  if (!SD_MMC.begin()) {
    Serial.println("SD Card Mount Failed. Please check the SD card module and connections.");
    return;
  }
  Serial.println("SD Card mounted successfully.");
  card_type_t cardType = SD_MMC.cardType();
  if (cardType == CARD_NONE) {
    Serial.println("No SD card attached.");
  } else {
    Serial.print("SD Card Type: ");
    if (cardType == CARD_MMC) Serial.println("MMC");
    else if (cardType == CARD_SD) Serial.println("SDSC");
    else if (cardType == CARD_SDHC) Serial.println("SDHC");
    else Serial.println("UNKNOWN");
    Serial.printf("SD Card Size: %lluMB\n", SD_MMC.cardSize() / (1024 * 1024));
  }

  // Connect to Wi-Fi
  Serial.printf("Connecting to WiFi: %s\n", ssid);
  WiFi.begin(ssid, password);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected.");
    Serial.printf("IP Address: %s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println("\nWiFi connection failed!");
  }
}

// --- Loop Function ---
void loop() {
  // Capture and upload image at specified interval
  if (millis() - lastCaptureTime > captureInterval) {
    captureAndUploadImage();
    lastCaptureTime = millis();
  }
  delay(100); // Small delay to prevent busy-looping
}

// --- Functions ---

void captureAndUploadImage() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected. Cannot capture or upload.");
    return;
  }

  Serial.println("Taking a picture...");
  digitalWrite(BOARD_LED_GPIO, LOW); // Turn on flash LED (if connected, active low)
  delay(100); // Small delay for LED to stabilize

  camera_fb_t * fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed!");
    digitalWrite(BOARD_LED_GPIO, HIGH); // Turn off LED
    return;
  }
  Serial.printf("Picture taken! Size: %u bytes\n", fb->len);

  // Save image to SD card (optional, but good for local storage)
  char filename[30];
  snprintf(filename, sizeof(filename), "/image_%lu.jpg", millis());
  Serial.printf("Saving image to SD: %s\n", filename);
  File file = SD_MMC.open(filename, FILE_WRITE);
  if (!file) {
    Serial.println("Failed to open file in writing mode");
  } else {
    file.write(fb->buf, fb->len);
    file.close();
    Serial.println("Image saved to SD card.");
  }
  
  digitalWrite(BOARD_LED_GPIO, HIGH); // Turn off flash LED

  // Upload image to Raspberry Pi Flask API
  Serial.println("Uploading image to Raspberry Pi...");
  HTTPClient http;
  String serverPath = "http://" + String(raspberryPiIp) + ":" + String(flaskApiPort) + String(uploadEndpoint);
  http.begin(serverPath); // Your Raspberry Pi's IP address and port

  // Set HTTP headers for multipart form data
  http.addHeader("Content-Type", "image/jpeg"); // Indicate that we are sending a JPEG image

  // Perform POST request
  int httpResponseCode = http.POST(fb->buf, fb->len);

  if (httpResponseCode > 0) {
    Serial.printf("[HTTP] POST... code: %d\n", httpResponseCode);
    if (httpResponseCode == HTTP_CODE_OK || httpResponseCode == HTTP_CODE_MOVED_PERMANENTLY) {
      String payload = http.getString();
      Serial.println("Image upload success. Response from server:");
      Serial.println(payload);
    }
  } else {
    Serial.printf("[HTTP] POST... failed, error: %s\n", http.errorToString(httpResponseCode).c_str());
  }

  http.end(); // Free resources
  esp_camera_fb_return(fb); // Return the frame buffer to the camera for reuse
}
