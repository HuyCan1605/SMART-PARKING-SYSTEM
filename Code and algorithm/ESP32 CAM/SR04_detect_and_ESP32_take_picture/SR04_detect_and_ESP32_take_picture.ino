#include <Arduino.h>
#include <WiFi.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"
#include "esp_camera.h"
#include <PubSubClient.h>
#include <NewPing.h>

//const char* ssid = "D112R";
//const char* password = "11223344";
//String serverName = "192.168.1.236";
//const char* mqtt_server = "192.168.1.236";

const char* ssid = "abcde";
const char* password = "khongchodau";
const char* mqtt_server = "192.168.43.198";
String serverName = "192.168.43.198";   // REPLACE WITH YOUR Raspberry Pi IP ADDRESS



const char* mqttUser = "huycanpi";
const char* mqttPassword = "123456";

String serverPath = "/upload.php";     // The default serverPath should be upload.php

const int serverPort = 80;

WiFiClient espClient;
PubSubClient client(mqtt_server, 1883, espClient);


// CAMERA_MODEL_AI_THINKER
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
#define FLASH_GPIO_NUM     4
#define trigPin  12 // Chân GPIO kết nối với chân Trigger của HC-SR04
#define echoPin  13 // Chân GPIO kết nối với chân Echo của HC-SR04
#define buzzer 15
#define MAX_DISTANCE 200
NewPing sonar(trigPin, echoPin, MAX_DISTANCE);



unsigned long lastMsg = 0;
unsigned long lastDelayTimeHCSR04 = 0;
int MQTTmessage;
short number_sended_photo = 0;
bool carDetection = false;
bool takeNewPhoto = false;

//int value = 0;
//#define MSG_BUFFER_SIZE  (50)
//char msg[MSG_BUFFER_SIZE];

void flash(int N)
{
  digitalWrite(FLASH_GPIO_NUM, HIGH);
  delay(N * 1000);
  digitalWrite(FLASH_GPIO_NUM, LOW);
}

void receive_MQTT_message() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}
void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Create a client ID
    String clientId = "ESP32Client_A1";

    // Attempt to connect
    if (client.connect(clientId.c_str(), mqttUser, mqttPassword)) {
      Serial.println("connected");
      // Once connected, publish an announcement...
      // ... and resubscribe
      client.subscribe("rpi/broadcast");
      client.subscribe("example/topic");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}
void callback(char* topic, byte* message, unsigned int length) {
  Serial.print("Message arrived on topic: ");
  Serial.print(topic);
  Serial.print(". Message: ");
  String messageTemp;

  for (int i = 0; i < length; i++) {
    Serial.print((char)message[i]);
    messageTemp += (char)message[i];
  }
  MQTTmessage = messageTemp.toInt();

  Serial.println();
}
String sendPhoto() {
  String getAll;
  String getBody;

  camera_fb_t * fb = NULL;
  fb = esp_camera_fb_get();
  flash(1);
  if (!fb) {
    Serial.println("Camera capture failed");
    delay(1000);
    ESP.restart();
  } else {
    Serial.println("Camera capture successed");
  }

  Serial.println("Connecting to server: " + serverName);

  if (espClient.connect(serverName.c_str(), serverPort)) {
    Serial.println("Connection successful!");
    String head = "--RandomNerdTutorials\r\nContent-Disposition: form-data; name=\"imageFile\"; filename=\"A1.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n";
    String tail = "\r\n--RandomNerdTutorials--\r\n";

    uint32_t imageLen = fb->len;
    uint32_t extraLen = head.length() + tail.length();
    uint32_t totalLen = imageLen + extraLen;

    espClient.println("POST " + serverPath + " HTTP/1.1");
    espClient.println("Host: " + serverName);
    espClient.println("Content-Length: " + String(totalLen));
    espClient.println("Content-Type: multipart/form-data; boundary=RandomNerdTutorials");
    espClient.println();
    espClient.print(head);

    uint8_t *fbBuf = fb->buf;
    size_t fbLen = fb->len;
    for (size_t n = 0; n < fbLen; n = n + 1024) {
      if (n + 1024 < fbLen) {
        espClient.write(fbBuf, 1024);
        fbBuf += 1024;
      }
      else if (fbLen % 1024 > 0) {
        size_t remainder = fbLen % 1024;
        espClient.write(fbBuf, remainder);
      }
    }
    espClient.print(tail);

    esp_camera_fb_return(fb);

    int timoutTimer = 10000;
    long startTimer = millis();
    boolean state = false;

    while ((startTimer + timoutTimer) > millis()) {
      Serial.print(".");
      delay(100);
      while (espClient.available()) {
        char c = espClient.read();
        if (c == '\n') {
          if (getAll.length() == 0) {
            state = true;
          }
          getAll = ""; //helloworld/r/n every one/r
        }
        else if (c != '\r') {
          getAll += String(c);
        }
        if (state == true) {
          getBody += String(c);
        }
        startTimer = millis();
      }
      if (getBody.length() > 0) {
        break;
      }
    }
    Serial.println();
    espClient.stop();
    Serial.println(getBody);
  }
  else {
    getBody = "Connection to " + serverName +  " failed.";
    Serial.println(getBody);
  }
  return getBody;
}

long getDuration() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(10);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);

  digitalWrite(trigPin, LOW);
  return pulseIn(echoPin, HIGH);
}

void sr04_detect_car() {
  float duration = 0, distance = 0;
  duration = sonar.ping_median(20);
  distance = sonar.convert_cm(duration);
  //  Serial.print("Khoang cach: ");
  Serial.println(distance);
  //  Serial.println(" cm");
  if (distance < 80 && distance > 40 ) {
    if (!carDetection) {
      takeNewPhoto = true;
      carDetection = true;
      client.publish("esp32/A1", "1");
    }
  } else {
    if (carDetection) {
      client.publish("esp32/A1", "0");
    }
    carDetection = false;
  }

  if (carDetection && takeNewPhoto) {
    takeNewPhoto = false;
    number_sended_photo = 0;
    sendPhoto();
  }
  delay(1000);

}

void alert_to_user() {
  if (MQTTmessage == 1 && carDetection && number_sended_photo < 6) {
    if (number_sended_photo == 4) {
      client.publish("esp32/A1", "2");
    }
    digitalWrite(buzzer, HIGH);

    //    Serial.println(MQTTmessage);
    unsigned long now = millis();
    if (now - lastMsg > 20000) {
      number_sended_photo++;
      MQTTmessage = 0;
      lastMsg = now;
      sendPhoto();
      Serial.print("So lan chup anh: ");
      Serial.println(number_sended_photo);
    }
  } else {
    digitalWrite(buzzer, LOW);
    //Serial.println(MQTTmessage);
  }
}

void setup() {
  pinMode(FLASH_GPIO_NUM, OUTPUT);
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);
  Serial.begin(115200);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(buzzer, OUTPUT);
  WiFi.mode(WIFI_STA);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }
  Serial.println();
  Serial.print("ESP32-CAM IP Address: ");
  Serial.println(WiFi.localIP());

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
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  // init with high specs to pre-allocate larger buffers
  if (psramFound()) {
    config.frame_size = FRAMESIZE_SVGA;
    config.jpeg_quality = 10;  //0-63 lower number means higher quality
    config.fb_count = 2;
    config.grab_mode = CAMERA_GRAB_LATEST;
  } else {
    config.frame_size = FRAMESIZE_CIF;
    config.jpeg_quality = 12;  //0-63 lower number means higher quality
    config.fb_count = 1;
    config.grab_mode = CAMERA_GRAB_LATEST;
  }

  // camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    delay(1000);
    ESP.restart();
  }
  sensor_t * s = esp_camera_sensor_get();
  s->set_special_effect(s, 2);

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}



void loop() {
  receive_MQTT_message();
  alert_to_user();
  sr04_detect_car();
}
