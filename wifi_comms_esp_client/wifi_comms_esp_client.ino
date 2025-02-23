#include <WiFi.h>
#include <SD.h>

#define SD_CS 10
#define CHUNK_SIZE 1024

WiFiClient client;
File file_obj;
const char* filename = "/testFile.txt";

const char* ssid = "DIGI-yWsT";
const char* passwd = "74F8ghZw";

// const char* ssid = "testesp32";
// const char* passwd = "javabanana";

const char* server_ip = "192.168.100.63";
const int   server_port = 65432;

struct Data{
  int seq_index;
  int length;
  char contents[CHUNK_SIZE];
}data;

File get_file_obj(const char* filename){
  if(!SD.begin(SD_CS)){
    Serial.println("Failed to open SD card");
    return File();
  }
  File file_obj = SD.open(filename, FILE_WRITE);
  if(!file_obj){
    Serial.println("Error opening or creating file");
    return File();
  }
  return file_obj;
}

void connect_to_server() {
  Serial.println("\nConnecting to server...");
  if (!client.connect(server_ip, server_port)) {
    Serial.println("Connection failed!");
    delay(1000);
  } else {
    Serial.println("Connected to server.");
  }
}

void read_message() {
  int read_threshold = 2 * sizeof(int);
  if (client.connected() && client.available() >= read_threshold) {
    int seq_index, packet_len;
    client.readBytes((char*)&seq_index, sizeof(int));
    client.readBytes((char*)&packet_len, sizeof(int));
    seq_index = ntohl(seq_index);
    packet_len = ntohl(packet_len);

    Serial.printf("Client received packet %d of size %d\n", seq_index, packet_len);

    unsigned long long int start = millis();
    while(client.available() < packet_len){
      if(millis() - start > 5000){
        Serial.println("Time limit exceeded for package await");
        return;
      }
    }
    char* contents = (char*)malloc(packet_len);
    if(!contents){
      Serial.println("Malloc fail for contents allocation");
      return;
    }
    client.readBytes(contents, packet_len);

    data.seq_index = seq_index;
    data.length = packet_len;
    memcpy(data.contents, contents, packet_len);

    Serial.printf("Received packet %d, length: %d\n", data.seq_index, data.length);
    Serial.print("Received: ");
    Serial.println(data.contents);

    free(contents);

    int ack = htonl(seq_index);  // Convert to network byte order
    client.write((uint8_t*)&ack, sizeof(ack));

    //  if (file_obj) {
    //   file_obj.write((uint8_t*)data.contents, data.length);
    //   file_obj.flush();
    // }
  }
}

void setup() {
  Serial.begin(115200);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, passwd);

  Serial.print("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }

  Serial.println("\nWiFi Connected!");
  printWifiStatus();

  file_obj = get_file_obj(filename);
  if(file_obj){
    connect_to_server();
  }else{
    Serial.println("Aborted connection. Could not open file for transfer");
  }
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected! Reconnecting...");
    WiFi.begin(ssid, passwd);
  }

  if (!client.connected()) {
    Serial.println("Server disconnected! Reconnecting...");
    connect_to_server();
  }

  read_message();
  delay(100);
}

void printWifiStatus() {
  Serial.print("\nSSID: ");
  Serial.println(WiFi.SSID());

  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  Serial.print("Signal strength (RSSI): ");
  Serial.print(WiFi.RSSI());
  Serial.println(" dBm");
}
