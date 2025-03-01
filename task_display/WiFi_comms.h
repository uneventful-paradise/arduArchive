#ifndef _WIFI_H_
#define _WIFI_H

#include <WiFi.h>
#include "config.h"

struct PackageData{
  int command_type;
  int command_id;
  int file_id;
  int length;
  char contents[CHUNK_SIZE];
}data;

WiFiClient client;

void printWifiStatus() {
  Serial.print("\nSSID: ");
  Serial.println(WiFi.SSID());

  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  Serial.print("Signal strength (RSSI): ");
  Serial.print(WiFi.RSSI());
  Serial.println(" dBm");
}

void send_request(int cmd_type, int cmd_id, int file_id, int req_len, char* req){
  PackageData data;
  data.command_type = htonl(cmd_type);
  data.command_id = htonl(cmd_id);
  data.file_id = htonl(file_id);
  data.length = htonl(req_len);
  memcpy(data.contents, req, req_len);

  int packet_size = sizeof(data.command_type) + sizeof(data.command_id) 
  + sizeof(data.file_id) + sizeof(data.length) + req_len;

  while(client.write((uint8_t*)&data, packet_size) != packet_size){
    Serial.printf("Send %d failed. Retrying\n", cmd_id);
  }
  Serial.printf("Send %d %d %d %d successful\n\n", cmd_type, cmd_id, file_id, req_len);
}

void handle_request() {
  //only read when the entire header has been sent
  int read_threshold = 4 * sizeof(int);
  if (client.connected() && client.available() >= read_threshold) {
    int cmd_type, cmd_id, file_id, req_len;
    //read and parse the header data. we use ntohl because the data is sent in big-endian (networking standard) while the esp device operates in little-endian. ntohl converts integers to host byte order
    client.readBytes((char*)&cmd_type, sizeof(int));
    client.readBytes((char*)&cmd_id, sizeof(int));
    client.readBytes((char*)&file_id, sizeof(int));
    client.readBytes((char*)&req_len, sizeof(int));
    cmd_type  = ntohl(cmd_type);
    cmd_id    = ntohl(cmd_id);
    file_id   = ntohl(file_id);
    req_len   = ntohl(req_len);

    Serial.printf("RECEIVED type %d id %d fid %d size %d\n", cmd_type, cmd_id, file_id, req_len);
    //checking for eof_packet
    // if(packet_len == 0) {
    //   Serial.println("EOF reached. Closing connection.");
    //   client.stop();
    //   file_obj.flush();
    //   file_obj.close();
    //   return;
    // } 

    //set a timeout limit for reading a packet's contents
    unsigned long long int start = millis();
    while(client.available() < req_len){
      if(millis() - start > 5000){
        Serial.println("Time limit exceeded for packet await");
        return;
      }
    }
    char* req = (char*)malloc(req_len);
    if(!req){
      Serial.println("Malloc fail for request contents allocation");
      return;
    }
    client.readBytes(req, req_len);

    PackageData data;
    data.command_type = cmd_type;
    data.command_id = cmd_id;
    data.file_id = file_id;
    data.length = req_len;
    
    memset(data.contents, 0, sizeof(data.contents));
    // contents[packet_len] = '\0';
    memcpy(data.contents, req, req_len);

    // Serial.printf("Received content %d, length: %d\n", data.cmd_id, data.length);
    Serial.print("RECEIVED: ");
    Serial.println(data.contents);
    Serial.println("");

    free(req);
    //send the packet index as an acknowledgement flag. convert it to bigendian representation before sending. we need to send aknowledgements so that the server doesn't immediately shut down after sending all the packets.
    // int ack = htonl(seq_index);  // Convert to network byte order
    // client.write((uint8_t*)&ack, sizeof(ack));

    //  if (file_obj) {
    //   file_obj.write((uint8_t*)data.contents, data.length);
    //   file_obj.flush();
    // }
  }
}

void connect_to_server() {
  Serial.println("\nConnecting to server...");
  if (!client.connect(SERVER_IP, PORT)) {
    Serial.println("Connection failed!");
    delay(1000);
  } else {
    Serial.println("Connected to server.");
  }
}
//2.0.17


#endif
//for tasks - a. 2 queues for the same touch event so display and send can manage the event independently
//b. same queue but one peeks with higher priority and the other takes 