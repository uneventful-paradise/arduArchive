#ifndef _WIFI_H_
#define _WIFI_H

#include <WiFi.h>
#include "config.h"

struct PackageData{
  int command_type;
  int command_id;
  int opt_arg;
  int length;
  char contents[CHUNK_SIZE];
}data;

//change types to short unsigned etc to better match their purpose

WiFiClient client;
File file_obj = File();
int final_file_size = 0;
int current_file_size = 0;
float download_percentage = 0;


struct UI_update{   //what other data should update messages have?
  int type;
  int status;       //0 = start, 1 = in progress, 2 = finished
  float arg;
  char message[UPDATE_BUFFER_SIZE];
};

QueueHandle_t ui_updates_queue;

void printWifiStatus() {
  Serial.print("\nSSID: ");
  Serial.println(WiFi.SSID());

  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  Serial.print("Signal strength (RSSI): ");
  Serial.print(WiFi.RSSI());
  Serial.println(" dBm");
}

void send_request(int cmd_type, int cmd_id, int opt_arg, int req_len, char* req){
  PackageData data;
  data.command_type = htonl(cmd_type);
  data.command_id = htonl(cmd_id);
  data.opt_arg = htonl(opt_arg);
  data.length = htonl(req_len);
  memcpy(data.contents, req, req_len);

  int packet_size = sizeof(data.command_type) + sizeof(data.command_id) 
  + sizeof(data.opt_arg) + sizeof(data.length) + req_len;

  // int bytes_sent = client.write((uint8_t*)&data, packet_size) != packet_size
  // Serial.printf("Sent % of %d bytes for %d request.\n", bytes_sent, packet_size, cmd_id);

  int bytes_sent = 0;

  while (bytes_sent < packet_size) {
    int sent = client.write(((uint8_t*)&data) + bytes_sent, packet_size - bytes_sent);
    if (sent > 0) {
      bytes_sent += sent;  // move forward in the buffer
    } else {
      Serial.printf("Send %d failed at byte %d. Retrying...\n", cmd_id, bytes_sent);
      delay(10); 
    }
  }

  Serial.printf("Send %d %d %d %d successful\n\n", cmd_type, cmd_id, opt_arg, req_len);
}

//create/open the file where we have to write the data
File get_file_obj(const char* filename){
  //way to check this?

  // if(!SD.begin(SD_CS)){
  //   Serial.println("Failed to open SD card");
  //   return File();
  // }

  //filename must start with '/'
  Serial.printf("Attempting to open or create %s\n", filename);
  if(SD.exists(filename)){
    Serial.println("File already exists");
  }
  file_obj = SD.open(filename, FILE_WRITE);
  if(!file_obj){
    Serial.println("Error opening or creating file");
    return File();
  }
  Serial.println("File opened successfully");
  return file_obj;
}

void handle_download(PackageData pd){
  //file_obj will be true only while a transfer is active and right when it is initiated
  UI_update update;

  if(pd.command_type == 1){       //initiate download. initiation package contains the path to which the content ought to be written
    file_obj = get_file_obj(pd.contents);
    current_file_size = 0;
    final_file_size = pd.opt_arg;
    Serial.printf("INITIATED DOWNLOAD. Final size will be %d\n", final_file_size);
    
    update.type = 0;
    update.status = 0;
    update.arg = 0;
    if(sprintf(update.message, "Starting download") < 0){
      Serial.println("Update message creation failed");
    }

    xQueueSend(ui_updates_queue, &update, portMAX_DELAY);
  
  }
  else if(pd.command_type == 3){  //end of download
    //checking for eof_packet
    Serial.println("EOF reached. Ending download.");
    file_obj.flush();
    file_obj.close();
    file_obj = File();            //resetting file obj to evaluate to false once the download is complete
    final_file_size = 0;
    current_file_size = 0;
    Serial.println("DOWNLOAD STOPPED");

    update.type = 0;
    update.status = 2;
    update.arg = 100;
    if(sprintf(update.message, "Download finished") < 0){
      Serial.println("Update message creation failed");
    }

    xQueueSend(ui_updates_queue, &update, portMAX_DELAY);

  }else if(pd.command_type == 2){
    if(file_obj) {

      current_file_size += pd.length;
      download_percentage = round(((float)current_file_size/(float)final_file_size) * 100);
      
      update.type = 0;
      update.status = 1;
      update.arg = download_percentage;
      if(sprintf(update.message, "Download %f complete", download_percentage) < 0){
        Serial.println("Update message creation failed");
      }

      xQueueSend(ui_updates_queue, &update, portMAX_DELAY);
  
      file_obj.write((uint8_t*)pd.contents, pd.length);
      file_obj.flush();
      Serial.printf("Current progress %f\n", download_percentage);
    }else{
      Serial.println("Target file for upload is invalid");
    }
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