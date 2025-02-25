#include <WiFi.h>
#include <SD.h>

#define SD_CS 10
#define CHUNK_SIZE 1024
//I chose to have the desktop application to act as a server because i wanted multiple esp devices to be able to connect to and interact with it via threads and tasks(so the esps will serve as clients)
WiFiClient client;
File file_obj;
//name will be sent in the first package of the transfer. this is just a testing script alex:) (non passive-aggressive smile)
const char* filename = "/test_img.jpg";

//Wi-Fi network details. Both devices need to be connected to the same network
const char* ssid = "DIGI-yWsT";
const char* passwd = "74F8ghZw";

//server information
const char* server_ip = "192.168.100.63";
const int   server_port = 65432;

//every data packet received will have the following format. the length attribute tells us how much data we ought to read from the socket, while the seq_index helps in the acknowledgment process
struct Data{
  int seq_index;
  int length;
  char contents[CHUNK_SIZE];
}data;

//create/open the file where we have to write the data
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
//reads will only occur when there is a header available to read from the socket. after that we will read the proper data and write it in the file opened previously on the sd card
void read_message() {
  //only read when the entire header has been sent
  int read_threshold = 2 * sizeof(int);
  if (client.connected() && client.available() >= read_threshold) {
    int seq_index, packet_len;
    //read and parse the header data. we use ntohl because the data is sent in big-endian (networking standard) while the esp device operates in little-endian. ntohl converts integers to host byte order
    client.readBytes((char*)&seq_index, sizeof(int));
    client.readBytes((char*)&packet_len, sizeof(int));
    seq_index = ntohl(seq_index);
    packet_len = ntohl(packet_len);

    Serial.printf("Client received packet %d of size %d\n", seq_index, packet_len);
    //checking for eof_packet
    if(packet_len == 0) {
      Serial.println("EOF reached. Closing connection.");
      client.stop();
      file_obj.flush();
      file_obj.close();
      return;
    } 

    //set a timeout limit for reading a packet's contents
    unsigned long long int start = millis();
    while(client.available() < packet_len){
      if(millis() - start > 5000){
        Serial.println("Time limit exceeded for packet await");
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
    
    memset(data.contents, 0, sizeof(data.contents));
    // printing for debugging purposes. comment this out before writing to file
    // contents[packet_len] = '\0';
    memcpy(data.contents, contents, packet_len);

    Serial.printf("Received packet %d, length: %d\n", data.seq_index, data.length);
    Serial.print("Received: ");
    Serial.println(data.contents);

    free(contents);
    //send the packet index as an acknowledgement flag. convert it to bigendian representation before sending. we need to send aknowledgements so that the server doesn't immediately shut down after sending all the packets.
    int ack = htonl(seq_index);  // Convert to network byte order
    client.write((uint8_t*)&ack, sizeof(ack));

     if (file_obj) {
      file_obj.write((uint8_t*)data.contents, data.length);
      file_obj.flush();
    }
  }
}

void setup() {
  Serial.begin(115200);
  //station more for end user device
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
