#ifndef _TASKS_H_
#define _TASKS_H_

#include "Display.h"
#include "WiFi_comms.h"

struct TouchEvent{
  int x;
  int y;
  int buttonId;
};

QueueHandle_t selection_queue;
QueueHandle_t macro_queue;

void touch_check_task(void* params){
  while(true){
    if (get_pos() == 1){                                                        //screen has been touched
      for (int i = 0; i < SPRITE_COUNT; i++){
        int button_value = UNABLE;
        if ((button_value = sprites[i]->checkTouch(pos[0], pos[1])) != UNABLE){ //checking if button is bound to command
          Serial.printf("Pos is :%d,%d\n", pos[0], pos[1]);
          Serial.printf("Value is :%d\n", button_value);

          TouchEvent event = {pos[0], pos[1], button_value};                    //creating event and sending it to queue to trigger the toiuch_handle task
          xQueueSend(selection_queue, &event, portMAX_DELAY);
          xQueueSend(macro_queue, &event, portMAX_DELAY);
        }
      }
    }
    vTaskDelay(200/portTICK_PERIOD_MS);
  }
}

void handle_command(void* params){
  TouchEvent event;
  while(true){
    if(xQueueReceive(selection_queue, &event, portMAX_DELAY) == pdTRUE){
      Serial.printf("Button with id %d has been selected and path is %s\n", event.buttonId, paths[event.buttonId]);
      //update display 
      // access_path(event.buttonId);
    }
    // vTaskDelay(100/portTick_PERIOD_MS);    //do i need to delay or is this event driven?
  }
}

void wifi_comms_task(void*params){
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

  int cmd_id = 0;
  char* messages[3]={
    "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum",
    "mama face mere nihahaha cal cal cal cal cal",
    "salutari osteni"
  };

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
    // if(cmd_id < 3 && client.connected()){
    //   char*msg = messages[cmd_id];
    //   send_request(0, cmd_id, 69, strlen(msg), msg);
    //   cmd_id++;
    // }
    TouchEvent event;
    if(xQueueReceive(macro_queue, &event, portMAX_DELAY) == pdTRUE){
      Serial.printf("SENDING command for %s to server\n", paths[event.buttonId]);
      char* req = paths[event.buttonId];
      send_request(1, cmd_id, 88, strlen(req), req);
      cmd_id++;
    handle_request();
    // Serial.println("later entry");
    vTaskDelay(500/portTICK_PERIOD_MS);
    }
  }
}

// struct Task2_params{
//   Arduino_RPi_DPI_RGBPanel* gfx;
//   JPEG_DRAW_CALLBACK *jpegDrawCallback;
//   Button** buttons;
//   int button_count;
// };

// static void display_text_task(void* params){
//   // unsigned long long int start = millis();   //what is a good way to print every other second?
//   Arduino_RPi_DPI_RGBPanel* gfx = (Arduino_RPi_DPI_RGBPanel *)params;
//   gfx->fillRect(200, 160, 260, 160, WHITE);
//   gfx->setCursor(220, 180);
//   gfx->setTextSize(4);
//   gfx->setTextColor(BLACK);
//   gfx->println("Task 1 is displaying");

//   for(;;){
//     //waiting for event (touches?)
    
//     Serial.println("Task 1 is running");
//     vTaskDelay(1000 / portTICK_PERIOD_MS);
//   }
//   vTaskDelete(NULL);
// }

// static void display_icon_task(void* params){
//   Task2_params t2p = *(Task2_params*)params;

//   for(;;){
//     //waiting for event (touches?)
    
//     Serial.println("Task 2 is running");
//     int rand_index = random(0, t2p.button_count);
//     t2p.buttons[rand_index]->draw(t2p.jpegDrawCallback);
//     vTaskDelay(1000 / portTICK_PERIOD_MS);
//   }
//   vTaskDelete(NULL);
// }

#endif