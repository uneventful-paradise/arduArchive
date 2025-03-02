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

//change types to short unsigned etc to better match their purpose

WiFiClient client;
File file_obj = File();
int final_file_size = 0;
int current_file_size = 0;

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

void handle_download(PackageData pd){
  //file_obj will be true only while a transfer is active and right when it is initiated
  if(pd.command_type == 1){       //initiate download. initiation package contains the path to which the content ought to be written
    file_obj = get_file_obj(pd.contents);
    // Serial.printf("INITIATED DOWNLOAD. Final file size must be %d\n", final_file_size);
    // current_file_size = 0;
  }
  else if(pd.command_type == 3){  //end of download
    //checking for eof_packet
    Serial.println("EOF reached. Ending download.");
    file_obj.flush();
    file_obj.close();
    file_obj = File();            //resetting file obj to evaluate to false once the download is complete
    // final_file_size = 0;
    // current_file_size = 0;
    Serial.println("DOWNLOAD STOPPED");
    return;
  }else if(pd.command_type == 2){
     if (file_obj) {
      file_obj.write((uint8_t*)pd.contents, pd.length);
      file_obj.flush();
      // current_file_size += pd.length;
      // Serial.printf("Current progress %d", int(current_file_size/final_file_size * 100));
    }
  }
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

    //set a timeout limit for reading a packet's contents
    unsigned long long int start = millis();
    while(client.available() < req_len){
      if(millis() - start > 5000){
        Serial.println("Time limit exceeded for packet await");
        return;
      }
    }
    //only read the data if it follows the protocol defined maximum length
    if(req_len > CHUNK_SIZE){
      Serial.println("Chunk size exceeded for received data. Skipping request");
      return;
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
    memcpy(data.contents, req, req_len);

    // Serial.printf("Received content %d, length: %d\n", data.cmd_id, data.length);
    Serial.print("RECEIVED: ");
    Serial.println(data.contents);
    Serial.println("");

    if(data.command_type >= 1 && data.command_type <= 3){
      handle_download(data);
    }

    free(req);
    //send the packet index as an acknowledgement flag. convert it to bigendian representation before sending. we need to send aknowledgements so that the server doesn't immediately shut down after sending all the packets.
    // int ack = htonl(seq_index);  // Convert to network byte order
    // client.write((uint8_t*)&ack, sizeof(ack));
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


#endif