#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESP32Servo.h>

// ==========================================
// ⚙️ WIFI SETTINGS
// ==========================================
const char* ssid = "YOUR_WIFI_SSID";       // Enter your WiFi name here
const char* password = "YOUR_WIFI_PASSWORD"; // Enter your WiFi password here

// ==========================================
// 🛠️ HARDWARE SETTINGS
// ==========================================
Servo doorServo;
int doorServoPin = 13; // The pin connected to the door lock servo

WiFiUDP Udp;
unsigned int localPort = 4210;
char packetBuffer[255];

void setup() {
  Serial.begin(115200);

  // Attach the servo for the door mechanism
  doorServo.attach(doorServoPin);

  // Initial Door Status: CLOSED (0 degrees)
  doorServo.write(0);
  delay(500);

  // Connect to WiFi
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\n✅ WiFi Connected!");
  Serial.print("ESP32 IP Address: ");
  Serial.println(WiFi.localIP()); 
  // NOTE: Make sure this IP matches the '192.168.1.15' in your Python script!
  // If your router gives a different IP, update the Python script.

  Udp.begin(localPort);
  Serial.println("🎧 UDP Server listening on port 4210...");
}

void loop() {
  int packetSize = Udp.parsePacket();
  if (packetSize) {
    int len = Udp.read(packetBuffer, 255);
    if (len > 0) packetBuffer[len] = 0;
    
    String incomingData = String(packetBuffer);
    int commaIndex = incomingData.indexOf(',');
    
    if (commaIndex > 0) {
      // The Python script sends "angle,angle" (e.g., "90,90" for open or "0,0" for close)
      // We only need the first value for our single door servo
      int doorAngle = incomingData.substring(0, commaIndex).toInt();
      
      // Constrain the angle to prevent physical damage to the lock mechanism
      if(doorAngle < 0) doorAngle = 0;
      if(doorAngle > 180) doorAngle = 180;

      // Actuate the door mechanism
      doorServo.write(doorAngle);
      
      // Print the status to Serial Monitor for debugging
      if (doorAngle > 0) {
        Serial.println("🔓 Door OPENED!");
      } else {
        Serial.println("🔒 Door CLOSED!");
      }
    }
  }
}
