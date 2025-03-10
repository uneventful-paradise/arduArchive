#ifndef _TASKS_H_
#define _TASKS_H_

#include "Display.h"
#include "WiFi_comms.h"

struct Touch_event{
  int x;
  int y;
  int buttonId;
};

QueueHandle_t selection_queue;
QueueHandle_t macro_queue;
QueueHandle_t wifi_request_queue;

void touch_check_task(void* params){
  while(true){
    if (get_pos() == 1){                                                        //screen has been touched
      for (int i = 0; i < SPRITE_COUNT; i++){
        int button_value = UNABLE;
        if ((button_value = sprites[i]->checkTouch(pos[0], pos[1])) != UNABLE){ //checking if button is bound to command
          Serial.printf("Pos is :%d,%d\n", pos[0], pos[1]);
          Serial.printf("Value is :%d\n", button_value);

          Touch_event event = {pos[0], pos[1], button_value};                    //creating event and sending it to queue to trigger the toiuch_handle task
          xQueueSend(selection_queue, &event, portMAX_DELAY);
          xQueueSend(macro_queue, &event, portMAX_DELAY);
        }
      }
    }
    vTaskDelay(200/portTICK_PERIOD_MS);
  }
}

void handle_command(void* params){
  Touch_event event;
  while(true){
    if(xQueueReceive(selection_queue, &event, portMAX_DELAY) == pdTRUE){
      Serial.printf("Button with id %d has been selected and path is %s\n", event.buttonId, paths[event.buttonId]);
      //update display 
      // access_path(event.buttonId);
    }
    // vTaskDelay(100/portTick_PERIOD_MS);    //do i need to delay or is this event driven?
  }
}

void update_screen_task(void*params){
  UI_update update;
  int screenWidth = gfx->width();
  int screenHeight = gfx->height();
  int barWidth = (screenWidth * 80) / 100;
  int barHeight = 10;
  int barX = (screenWidth - barWidth) / 2;
  int barY = screenHeight / 2 + 30;  // for example, 30 pixels below the centered text

  gfx->setTextSize(3);
  gfx->setTextColor(WHITE);
  int textWidth = strlen(update.message) * 3; // rough approximation
  int textX = (screenWidth - textWidth) / 2;
  int textY = screenHeight / 2 - 20;
  while(true){
    if(xQueueReceive(ui_updates_queue, &update, portMAX_DELAY) == pdTRUE){
      if(update.type == 0){ //dealing with download file screen update
        if(update.status == 0){
          gfx->fillScreen(BLACK);

          gfx->setCursor(textX, textY);
          gfx->println(update.message);

          gfx->drawRect(barX, barY, barWidth, barHeight, WHITE);
          delay(100);
        }else if(update.status == 2){
          gfx->setCursor(textX, textY + 100);
          gfx->println(update.message);
          delay(500);
          gfx->fillScreen(BLACK);
          draw_main_screen();
        }
        else if(update.status == 1){
          // gfx->fillRect(barX, barY, barWidth, barHeight, BLACK);
          // Calculate filled width based on update.arg (percentage 0 to 100)
          int filledWidth = (barWidth * update.arg) / 100;
          gfx->fillRect(barX, barY, filledWidth, barHeight, WHITE);
          delay(100);
        }
      }
    }
    vTaskDelay(10 / portTICK_PERIOD_MS);
  }
}

void establish_connection_task(void*params){
  //connect to wifi network
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PWD);

  Serial.print("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    vTaskDelay(500/portTICK_PERIOD_MS);
  }

  Serial.println("\nWiFi Connected!");
  printWifiStatus();

  //connect to server
  while(1){
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("WiFi disconnected! Reconnecting...");
      WiFi.begin(WIFI_SSID, WIFI_PWD);
    }

    if (!client.connected()) {
      Serial.println("Server disconnected! Reconnecting...");
      connect_to_server();
    }
    vTaskDelay(100/portTICK_PERIOD_MS);
  }
}

void send_request_task(void* params){
  Touch_event event;
  int client_cmd_id;
  while(1){
    if(client.connected()){

      if(xQueueReceive(macro_queue, &event, portMAX_DELAY) == pdTRUE){
        Serial.printf("SENDING command for %s to server\n", paths[event.buttonId]);
        char* req = paths[event.buttonId];
        send_request(MCCF, client_cmd_id, event.buttonId, strlen(req), req); //send request of press
        client_cmd_id++;
        // Serial.println("later entry");
        // handle_request();
      }
      //if response queue has something in it then send it
    }
    //no need to block since we are waiting for queue entries
  }
}

void handle_requests_task(void* params){  //check for commands and responses from server and push them to receiver queue
  //do we need to wait for connec,tion with mutexes?

  int read_threshold = 4 * sizeof(int);
  while(1){ 
    if(client.connected() && client.available() >= read_threshold){   
      int cmd_type, cmd_id, opt_arg, req_len;
      //read and parse the header data. readbytes blocks until the specified number of bytes is available to read from the socket
      //we use ntohl because the data is sent in big-endian (networking standard) while the esp device operates in little-endian. ntohl converts integers to host byte order
      client.readBytes((char*)&cmd_type, sizeof(int));
      client.readBytes((char*)&cmd_id, sizeof(int));
      client.readBytes((char*)&opt_arg, sizeof(int));
      client.readBytes((char*)&req_len, sizeof(int));
      cmd_type  = ntohl(cmd_type);
      cmd_id    = ntohl(cmd_id);
      opt_arg   = ntohl(opt_arg);
      req_len   = ntohl(req_len);

      Serial.printf("RECEIVED type %d id %d opt_arg %d size %d\n", cmd_type, cmd_id, opt_arg, req_len);

      //set a timeout limit for reading a packet's contents. readBytes has a builting timer (defaulting to 1000ms) can be changed using client.setTimeout()
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
      data.opt_arg = opt_arg;
      data.length = req_len;
      
      memset(data.contents, 0, sizeof(data.contents));
      memcpy(data.contents, req, req_len);

      // Serial.printf("Received content %d, length: %d\n", data.cmd_id, data.length);
      Serial.print("RECEIVED: ");
      Serial.println(data.contents);
      Serial.println("");

      if(data.command_type >= 1 && data.command_type <= 3){
        handle_download(data);
        
        char ACK[50];
        if(sprintf(ACK, "%d", data.command_id) < 0){
        Serial.println("Acknowledgement message creation failed");
        }
        send_request(CFCF, cmd_id, 0, strlen(ACK), ACK);
      }
      //send request to queue to be processed
      // xQueueSend(wifi_request_queue, &data, portMAX_DELAY);
      // xQueueSend(receive_queue, (void*)data, portMAX_DELAY);

      //sending acknowledgement that message with id cmd_id has been received and processed;

      free(req);
    }

    vTaskDelay(200/portTICK_PERIOD_MS); //is this needed?
  }
}

#endif