#ifndef _WIFI_H_
#define _WIFI_H

#include <WiFi.h>
#include "Utilities.h"

WiFiClient client;
int final_file_size = 0;
int current_file_size = 0;
float download_percentage = 0;
int client_cmd_id = 0;

struct UI_update{
  int type;         //0 = file trasnfer, 1 = connection checkup ...
  int status;       //0 = start_transfer, 1 = transfer_in_progress, 2 = transfer_finished, 3 = general_update
  float arg;
  char message[BUFFER_SIZE];
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
/*Build the Package_Data object given all the field values and send it to the server.*/
void send_request(int cmd_type, int cmd_id, int opt_arg, int req_len, unsigned int crc_value, char* req){
  Package_data data;
  //Convert data to big endian (network byte order) before sending (network standard).
  data.command_type = htonl(cmd_type);
  data.command_id = htonl(cmd_id);
  data.opt_arg = htonl(opt_arg);
  data.length = htonl(req_len);
  data.crc_value = htonl(crc_value);
  memcpy(data.contents, req, req_len);

  //Calculate total packet size
  int packet_size = sizeof(data.command_type) + sizeof(data.command_id) 
  + sizeof(data.opt_arg) + sizeof(data.length) + sizeof(data.crc_value) + req_len;

  int bytes_sent = 0;
  //Loop to send all the data in the packet (TCP can fail to send all the bytes in a single send call).
  while (bytes_sent < packet_size) {
    int sent = client.write(((uint8_t*)&data) + bytes_sent, packet_size - bytes_sent);
    if (sent > 0) {
      bytes_sent += sent;  // move forward in the buffer
    } else {
      Serial.printf("Send %d failed at byte %d. Retrying...\n", cmd_id, bytes_sent);
      delay(10); 
    }
  }

  Serial.printf("\nSend type %d id %d opt_arg %d len %d successful\n%s\n", cmd_type, cmd_id, opt_arg, req_len, req);
  client_cmd_id++;
}

/*Manage download process. This function uses a global File handle to 
handle writing received content on the SD card. The `file_obj` is a global
file handled initialized with null (value of File() default constructor).

Download data packets are handled based on the `command_type` argument:
command_type = 1 -> start download
command_type = 2 -> download in progress
command_type = 3 -> end download
Upon a "start download" request the file is created and its handle is assigned to `file_obj`.
This first request contains the total file size (necessary for the progress bar calculation) 
stored in the `opt_arg` field and the client sided file name as payload. 
The following FILE_SIZE/CHUNK packets are data transfer packets and will be written to the 
newly created file.
Finally, the "end download" request signalizes that EOF has been read on the server side. So 
the file is closed and the `file_obj` object is reasigned NULL. So, `file_obj` is NULL as
long as no file transfer is ongoing.
*/
char current_filename[100];
void handle_download(Package_data pd){
  UI_update update;
  BaseType_t xStatus;

  if(pd.command_type == 1){
    file_obj = get_file_obj(pd.contents);
    strcpy(current_filename, pd.contents);
    current_file_size = 0;
    final_file_size = pd.opt_arg;
    Serial.printf("INITIATED DOWNLOAD. Final size will be %d\n", final_file_size);
    
    update.type = 0;
    update.status = 0;
    update.arg = 0;
    if(sprintf(update.message, "Starting download") < 0){
      Serial.println("Update message creation failed");
    }
    //checking that the file has been created/opened without errors.
    if(file_obj){
      xStatus = xQueueSend(ui_updates_queue, &update, portMAX_DELAY);
      if(xStatus != pdPASS){
        vPrintString("handle_download failed to send download start data to ui_updates_queue.\r\n");
      }
    }else{
      Serial.println("Invalid download file");
    }
  
  }
  //EOF read on server side. Ending download.
  else if(pd.command_type == 3){
    Serial.println("EOF reached. Ending download.");
    file_obj.flush();
    file_obj.close();
    //resetting file obj to evaluate to false once the download is complete
    if(current_file_size != final_file_size){
      Serial.println("ERROR: Total written does not match target value");
    }else{
      Serial.printf("DOWNLOAD FINISHED. Wrote %d bytes\n", final_file_size);
    }
    file_obj = File();
    final_file_size = 0;
    current_file_size = 0;

    update.type = 0;
    update.status = 2;
    update.arg = 100;
    if(sprintf(update.message, "Download finished") < 0){
      Serial.println("Update message creation failed");
    }

    xStatus = xQueueSend(ui_updates_queue, &update, portMAX_DELAY);
    if(xStatus != pdPASS){
      vPrintString("handle_download failed to send end of download data to ui_updates_queue.\r\n");
    }
  //file content packet
  }else if(pd.command_type == 2){
    if(file_obj) {
      //checking cursor position
      unsigned long position = file_obj.position();
      Serial.printf("Before write cursor was at %lu\n", position);

      //Write bytes to file

      // size_t written = 0;
      // written = file_obj.write((uint8_t*)pd.contents, pd.length);
      // if (written != pd.length) {
      //   Serial.printf("Error: Expected to write %d bytes but wrote %d bytes\n", pd.length, written);
      //   // TODO: find a way to handle errors (e.g., retry, abort transfer, etc.)
      //   //currently trying calling flush more rarely and reopening file on fails
      //   //next should try aborting download 
      //   Serial.println("Attempting to reopen file");
      //   file_obj.flush();
      //   file_obj.close();

      //   file_obj = get_file_obj(current_filename, true);
      //   if(!file_obj){
      //     Serial.println("Failed to reopen file after write error");
      //   }else{
      //     written = file_obj.write((uint8_t*)pd.contents, pd.length);
      //     if(written != pd.length){
      //       Serial.printf("Failed second write attempt for packet %d", pd.command_id);
      //       written = 0;
      //     }
      //   }
      // }
      size_t total_written = 0;
      const unsigned int max_retries = 10;
      unsigned int retry_counter = 0;
      bool fatal_error = false;
      while(total_written < pd.length && !fatal_error){
        ssize_t bytes_written = file_obj.write((uint8_t*)pd.contents + total_written, pd.length - total_written);
        if(file_obj.position() == 4294967295 && retry_counter < max_retries){
          Serial.println("Encountered cursor error, attempting to reopen file");
          file_obj.flush();
          file_obj.close();
          file_obj = SD.open(current_filename, FILE_APPEND);
          if(!file_obj){
            Serial.println("File reopening failed");
            fatal_error = true;
          }else{
            Serial.printf("Reopened at position %lu\n", file_obj.position());
            //resetting the pointer
            file_obj.seek(position);
            Serial.printf("Repositioned cursor at %lu\n", file_obj.position());
            retry_counter++;
          }
        }
        if(bytes_written < 0){
          Serial.println("Error occured during download write");
          //handle this gracefully:)
        }

        if(bytes_written == 0 && retry_counter < max_retries){
          Serial.printf("ERROR: Wrote 0 bytes on attempt %d! Retrying\n", retry_counter);
          retry_counter++;
        }else if(bytes_written == 0 && retry_counter == max_retries){
          fatal_error = true;
          Serial.println("Fatal error. Stopping transfer!");
        }
        total_written += bytes_written;
      }
      //when to flush?
      //write successful
      //file_obj.flush();
      position = file_obj.position();
      Serial.printf("After write cursor was at %lu\n", position);

      Serial.printf("Current progress %f\n", download_percentage);
      // delay(500);

      // current_file_size += pd.length;
      current_file_size += total_written;
      download_percentage = round(((float)current_file_size/(float)final_file_size) * 100);
      
      update.type = 0;
      update.status = 1;
      update.arg = download_percentage;
      if(sprintf(update.message, "Download %f complete", download_percentage) < 0){
        Serial.println("Update message creation failed");
      }

      xStatus= xQueueSend(ui_updates_queue, &update, portMAX_DELAY);
      if(xStatus != pdPASS){
        vPrintString("handle_download failed to send file trasnfer data to ui_updates_queue.\r\n");
      }
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