#include "Tasks.h"


EventGroupHandle_t connection_event_group;
QueueHandle_t wifi_request_queue; 

SrClient* sr_client;
NwClient* nw_client;
BaseClient* current_client;

//dynamic_cast would be cool to use to check current client type but has large memory footprint
int current_client_type = NW_CLIENT_MODE;

void protected_check_connection(){
  if (xConnCheckMutex != NULL) {
    if (xSemaphoreTake(xConnCheckMutex, portMAX_DELAY) != pdTRUE){
      A_ERR("Failed to take client mutex");
      return;
    }

    current_client -> check_connection();

    if(xSemaphoreGive(xConnCheckMutex) != pdTRUE){
      A_ERR("Failed to give client mutex");
    }
  }
}

void touch_check_task(void* params) {
  // BaseType_t watermark = uxTaskGetStackHighWaterMark(NULL);                    //checking for available stack
  // Serial.printf("touch_check_task stack high water mark: %u\n", watermark);

  BaseType_t xStatus;
  Sprite** nav_btn = sprite_manager.getNavButtons();
  while (true) {
    //screen has been touched
    if (get_pos() == 1) {
      // watermark = uxTaskGetStackHighWaterMark(NULL);
      // Serial.printf("touch_check_task stack high water mark: %u\n", watermark);
      int btn_id = UNABLE;
      for (int i = 0; i < NAV_BTN_COUNT; ++i){
        if((nav_btn[i] != nullptr) && (btn_id = nav_btn[i] -> checkTouch(pos[0], pos[1])) != UNABLE) {
          A_DBG("button is a nav button");
          if (btn_id == BUTTON_PREV || btn_id == BUTTON_NEXT) {
              sprite_manager.switchPage(btn_id);
              if (sprite_manager.getMaxPage() > 0) {
                clear_screen();
                draw_main_screen();
              }
          } else if (btn_id == BUTTON_SWAP) {
            swap_client_type();
          }
          break;
        }
      }
      if (btn_id != UNABLE){
        A_DBG("skipping cmd btn checks");
        continue;
      }
      //!avoid maxdelay? does it make sense to allow multiple button presses?
      /* wait for task to acquire mutex before moving on
      As noted earlier in this book, indefinite time outs are not
      recommended for production code. */
      if(xButtonsMutex != NULL){
        if (xSemaphoreTake(xButtonsMutex, portMAX_DELAY) != pdTRUE){
          A_ERR("Failed to get buttons mutex");
        }
        Sprite** buttons = sprite_manager.getButtons();

        // A_DBG("Pos is: %d, %d\n", pos[0], pos[1]);
        // A_DBG("Count is %d", (sprite_manager.getCount()));

        int button_id = sprite_manager.get_id_by_coords(pos[0], pos[1]);
        A_DBG("Value is: %d\n", button_id);

        if (button_id != UNABLE) {
          //creating a data packet to send command information to server
          Package_data data;
          Header_data header;
          // Serial.printf("SENDING command for %s to server\n", paths[event.buttonId]);
  
          memset(data.contents, 0, sizeof(data.contents));
          if (snprintf(data.contents, sizeof(data.contents), "%d", button_id) < 0) {
            A_ERR("snprintf failed in touch_check_task");
            continue;
          }
  
          header.command_type = MACRO_COMMAND;
          header.command_id = 0;
          header.length = strlen(data.contents);
          header.crc_value = crc_string(data.contents, header.length);
          data.header = header;
          A_DBG("Selected value is %s\n", data.contents);
  
          // watermark = uxTaskGetStackHighWaterMark(NULL);
          // Serial.printf("touch_check_task stack high water mark (MID): %u\n", watermark);
        
  
          xStatus = xQueueSend(send_queue, &data, portMAX_DELAY);
          if (xStatus != pdPASS) {
            vPrintString("touch_check_task failed to send data to the send_queue.\r\n");
          }
        }

        if (xSemaphoreGive(xButtonsMutex) != pdTRUE){
          A_ERR("Failed to give buttons mutex");
        }
      }
    }
    vTaskDelay(200 / portTICK_PERIOD_MS);
  }
}


/*This task displays updates on the screen based on the type and status arguments of the UI_update struct type.
type = 0 -> file transfer

status = 0 -> start
status = 1 -> ongoing
status = 2 -> finsihed

for now this tasks is only used for download progress display (display a progress bar)

TODO: loading icon for awaiting internet connection*/
void update_screen_task(void* params) {
  // UBaseType_t watermark = uxTaskGetStackHighWaterMark(NULL);
  // A_DBG("stack high water mark (BEGIN) : %u\n", watermark);
  BaseType_t xStatus;
  UI_update update;

  //centering the progress bar position
  int screenWidth = gfx->width();
  int screenHeight = gfx->height();
  int barWidth = (screenWidth * 80) / 100;
  int barHeight = 10;
  int barX = (screenWidth - barWidth) / 2;
  int barY = screenHeight / 2 + 30;  // for example, 30 pixels below the centered text

  //centering text
  int textWidth = strlen(update.message) * 3;  // rough approximation
  int textX = (screenWidth - textWidth) / 2;
  int textY = screenHeight / 2 - 20;

  while (true) {
    /*If a block time was specified (xTicksToWait was not zero), then it is possible the calling 
    task was placed into the Blocked state to wait for data to become available on the queue, 
    but data was successfully read from the queue before the block time expired.*/
    xStatus = xQueueReceive(ui_updates_queue, &update, portMAX_DELAY);
    if (xStatus == pdPASS) {
      // A_DBG("message is %s", update.message);
      //file transfer related upload
      textWidth = strlen(update.message) * 20;
      textX = (screenWidth - textWidth) / 2;

      switch (update.type) {
        case START_DOWNLOAD:{
          // A_DBG("case is start_download");
          clear_screen();
          draw_text(textX, textY, 3, WHITE, update.message);
  
          gfx->drawRect(barX, barY, barWidth, barHeight, WHITE);
          vTaskDelay(100 / portTICK_PERIOD_MS);
          break;
        }
        case FILE_TRANSFER:{
          //Transfer ongoing
          // A_DBG("case is file_transfer");
          // gfx->fillRect(barX, barY, barWidth, barHeight, BLACK);
          // Calculate filled width based on update.arg (percentage 0 to 100)
          int filledWidth = (barWidth * update.status) / 100;
          gfx->fillRect(barX, barY, filledWidth, barHeight, WHITE);
          vTaskDelay(100 / portTICK_PERIOD_MS);
          break;
        }
        case END_DOWNLOAD: {
          // A_DBG("case is end_download");
          draw_text(textX, textY + 100, 3, WHITE, update.message);
          vTaskDelay(500 / portTICK_PERIOD_MS);
          
          // clear_screen(gfx);
          // draw_main_screen(gfx);
          vTaskDelay(1000 / portTICK_PERIOD_MS);
          break;
        }
        case CONNECTION_CHECK: {
          // A_DBG("update message length is %d\n", strlen(update.message));
         
          if (update.status != 1) {
            // A_DBG("case is connection lost");
            //TODO: add animation
            //connection dropped
            clear_screen();
            draw_text(textX, textY, 3, WHITE, update.message);
          } else if (update.status == 1) {
            // A_DBG("case is connection gained");
            clear_screen();
            draw_text(textX, textY, 3, WHITE, update.message);
            vTaskDelay(500 / portTICK_PERIOD_MS);
            clear_screen();
            draw_main_screen();
          }
          break;
        }
        case REDRAW_COMMAND: {
          // A_DBG("case is redraw screen");
          clear_screen();
          
          if (xButtonsMutex != NULL) {
            if (xSemaphoreTake(xButtonsMutex, portMAX_DELAY) != pdTRUE){
              A_ERR("Failed to take buttons mutex");
            }

            sprite_manager.clear_buttons();
            sprite_manager.setMaxPage(0);
            sprite_manager.setCurrentPage(0);

            if (xSemaphoreGive(xButtonsMutex) != pdTRUE) {
              A_ERR("Failed to give buttons mutex");
            }

            A_DBG("Free heap after modification %u", ESP.getFreeHeap());
          }

          if (!init_icons_from_config("/configs/btn_config.txt")) {
            A_ERR("Icon read failed");
          }
          A_DBG("Free heap after modification %u", ESP.getFreeHeap());
          draw_main_screen();
          break;
        }
        default:{
          A_ERR("Invalid update type");
        }
      }
      //status returned pdFAIL or errQUEUE EMPTY
    } else {
      vPrintString("update_screen task failed to receive from ui_updates_queue.\r\n");
    }

    vTaskDelay(10 / portTICK_PERIOD_MS);
  }
}

//!try event driven approach in case this fails to reestablish connection
void establish_connection_task(void* params) {
  current_client -> initiate_connection();
  // UBaseType_t watermark = uxTaskGetStackHighWaterMark(NULL);
  // A_DBG("stack high water mark (PRE-LOOP): %u\n", watermark);

  //Connecting to and monitoring connection to server and network.
  while (true) {
    protected_check_connection();
    vTaskDelay(500 / portTICK_PERIOD_MS);
  }
}

/*This task polls message requests from all other tasks and sends them to the server*/
void send_request_task(void* params) {
  // UBaseType_t watermark = uxTaskGetStackHighWaterMark(NULL);
  // Serial.printf("\nsend_request_task stack high water mark (BEGIN) : %u\n", watermark);

  BaseType_t xStatus;
  Package_data data;

  while (true) {
    current_client -> wait_on_connection();
    //!only attempt to send while client is connected otherwise go back to waiting/blocked state
    // if (client.connected()) {
    // }
    xStatus = xQueueReceive(send_queue, &data, portMAX_DELAY);
    if (xStatus == pdPASS) {
      //send request to server
      data.header.command_id = client_cmd_id;
      send_request(&data, current_client);
    } else {
      vPrintString("[ERROR] [send_request_task] failed to receive from send_queue.\r\n");
    }
  }
}

void swap_client_type(){
    //make a func for creating a pd with given info
    Package_data data;
    Header_data header;
    memset(data.contents, 0, sizeof(data.contents));
    if (snprintf(data.contents, sizeof(data.contents), "Request to swap") < 0) {
        A_ERR("snprintf failed");
        return;
    }
    header.command_type = CLIENT_SWAP;
    header.command_id = 0;
    header.length = strlen(data.contents);
    header.crc_value = crc_string(data.contents, header.length);
    data.header = header;

    BaseType_t xStatus = xQueueSend(send_queue, &data, portMAX_DELAY);
    if (xStatus != pdPASS) {
      vPrintString("touch_check_task failed to send data to the send_queue.\r\n");
    }
    A_DBG("Sending request to swap client type");

    //waiting for client to confirm that it is ready to swap modes
    xStatus = xQueueReceive(conf_queue, &data, portMAX_DELAY);
    if(xStatus != pdPASS){
        A_ERR("Failed to receive confirmation");
        return;
    }
    /* at this point confirmation is received so client type can be switched on esp
    this busy waiting method is innefficient and potentially not needed at all? */
    while (uxQueueMessagesWaiting(send_queue) || uxQueueMessagesWaiting(wifi_request_queue)) {
        vTaskDelay(pdMS_TO_TICKS(1));
    }
    A_DBG("Queues are empty and confirmation received, starting swap");
    switch(current_client_type){
        case NW_CLIENT_MODE:{
          //client is in wifi mode and wants to go serial
          //!disconnect wifi and block read/write tasks
          //?vTaskDelay here?
          //!while reading and writing tasks are blocked waiting for connection
          if (xConnCheckMutex != NULL) {
            if (xSemaphoreTake(xConnCheckMutex, portMAX_DELAY) != pdTRUE){
              A_ERR("Failed to take client mutex");
              return;
            }
            current_client -> close();
            send_connection_status(-3);

            current_client = sr_client;
            //!put a lock/sem here to prevent the conn_check task from updating this again
            nw_client -> mark_connected();
            current_client -> initiate_connection();
                  
            current_client_type = SR_CLIENT_MODE;
            if(xSemaphoreGive(xConnCheckMutex) != pdTRUE){
              A_ERR("Failed to give client mutex");
            }
          }
          break;
        }
        case SR_CLIENT_MODE:{
          if (xConnCheckMutex != NULL) {
            if (xSemaphoreTake(xConnCheckMutex, portMAX_DELAY) != pdTRUE){
              A_ERR("Failed to take client mutex");
              return;
            }
            current_client -> close();
            send_connection_status(-3);

            current_client = nw_client;
            nw_client -> mark_disconnected();
            current_client -> initiate_connection();
        
            current_client_type = NW_CLIENT_MODE;
            if(xSemaphoreGive(xConnCheckMutex) != pdTRUE){
              A_ERR("Failed to give client mutex");
            }
          }
          break;
        }
        default:{
          A_ERR("Unrecognized client case");
          break;
        }
    }
}

void send_ack(int ack) {
  BaseType_t xStatus;
  Package_data data;
  Header_data header;
  //creating acknowledgment message and sending it
  memset(data.contents, 0, sizeof(data.contents));
  if (snprintf(data.contents, sizeof(data.contents), "%d", ack) < 0) {
    A_ERR("Acknowledgement message creation failed");
  }
  int size = strlen(data.contents);
  // A_DBG("Acknowledge value is %s of size %d\n", data.contents, size);
  header = { CONFIRMATION_FLAG, 0, size, crc_string(data.contents, size) };
  data.header = header;

  xStatus = xQueueSend(send_queue, &data, portMAX_DELAY);
  if (xStatus != pdPASS) {
    vPrintString("[ERROR] [send_ack] failed to send data to send_queue.\r\n");
  }
}

/*This task waits to retrieve server requests. It checks for the existence of a message header inside the connection socket 
before reading the whole header. Once the header is read, the payload length is accessible. The function dynamically allocates 
memory for and reads the payload. Once succesfully reading the whole payload, the request is sent to a different task to be
parsed and executed so that the reading task isn't blocked by those operations.*/
void receive_request_task(void* params) {
  // UBaseType_t watermark = uxTaskGetStackHighWaterMark(NULL);
  // Serial.printf("\nreceive_request_task stack high water mark (BEGIN) : %u\n", watermark);

  // const TickType_t xTicksToWait = pdMS_TO_TICKS(100);
  BaseType_t xStatus;
    
  int read_threshold = HEADER_SIZE;
  size_t bytes_read = 0;

  while (true) {
    current_client -> wait_on_connection();
    //TODO: can this busy loop be removed?
    // A_DBG("Ser available is %d", current_client -> get_available());
    if ( current_client -> get_available() >= read_threshold) {
      //read and parse the header data. readbytes blocks until the specified number of bytes is available to read from the socket
      //we use ntohl because the data is sent in big-endian (networking standard) while the esp device operates in little-endian. ntohl converts integers to host byte order
      
      Header_data header;
      bytes_read = current_client -> read_all((char*)&header, sizeof(header));

      //!if bytes_read is 0 then no data is available
      if (bytes_read != sizeof(header)) {
        A_ERR("Error: Expected to read %u bytes but got %u bytes\n", sizeof(header), bytes_read);
        // current_client -> clear_channel();
      }
      /*use ntohl to converts values from network byte order(big endian) to host byte order
      the conversion is needed because network format is big endian while esp32 runs on small endian.*/

      //or declare command_type as u_int32
      header.command_type = ntohl(header.command_type);
      header.command_id = ntohl(header.command_id);
      header.length = ntohl(header.length);
      header.crc_value = ntohl(header.crc_value);
      A_DBG("RECEIVED type %u id %u size %u CRC %04x", header.command_type, header.command_id, header.length, header.crc_value);

      //set a timeout limit for reading a packet's contents. readBytes has a builting timer (defaulting to 1000ms) can be changed using client.setTimeout()
      //only read the data if it follows the protocol defined maximum length
      if (header.length > CHUNK_SIZE) {
        A_ERR("Chunk size %u exceeded for received data. Skipping request %u", header.length, header.command_id);
        //alternatively try to disconnect and reconnect using client.stop(). send a -2?
        current_client -> clear_channel();
        send_ack(-1);
        continue;
      }

      char* req_contents = (char*)malloc(header.length);
      if (!req_contents) {
        A_ERR("Malloc fail for request contents allocation");
        send_ack(-1);
        continue;
      }
      current_client -> read_all(req_contents, header.length);

      Package_data data;
      data.header = header;
      //zero out contents to avoid pre existing junk data when reading binary data
      memset(data.contents, 0, sizeof(data.contents));
      memcpy(data.contents, req_contents, header.length);

      // Serial.printf("Received content %d, length: %d\n", data.cmd_id, data.length);
      A_DBG("%s\n", data.contents);
      // better way to convert to hex?

      // for (int i = 0; i < data.header.length; ++i) {
      //   printf("%02x", data.contents[i]);
      // }
      // printf("\n\n");

      //send request to queue to be processed
      if (data.header.command_type == CONFIRMATION_FLAG) {
        xStatus = xQueueSend(conf_queue, &data, portMAX_DELAY);
        if (xStatus != pdPASS) {
            vPrintString("receive_request_task Failed to send data to wifi_request_queue.\r\n");
        }
      } 
      else {
        xStatus = xQueueSend(wifi_request_queue, &data, portMAX_DELAY);
        if (xStatus != pdPASS) {
            vPrintString("receive_request_task Failed to send data to wifi_request_queue.\r\n");
        }
      }
      free(req_contents);
    }

    vTaskDelay(200 / portTICK_PERIOD_MS);
  }
}

/*This task handles (parses content and delegates execute functions) 
the received requests to avoid blocking the socket reader task. 
For the transfer related requests, a confirmation message 
is built and sent to proc the resending of corrupted packets 
if any are detected or to notify the server that it can send the next packet.

An acknowledgement message has the payload content set to the id of 
the incoming server request if the CRC32 check was successful or to 
the `-1` value otherwise.*/
void wifi_request_handling_task(void* params) {
  // UBaseType_t watermark = uxTaskGetStackHighWaterMark(NULL);
  // Serial.printf("\nwifi_request_task high water mark (BEGIN) : %u\n", watermark);
  Package_data data;
  BaseType_t xStatus;

  int ack = 0;
  while (1) {
    xStatus = xQueueReceive(wifi_request_queue, &data, portMAX_DELAY);
    ack = 0;
    if (xStatus == pdTRUE) {
      /*calculate crc value given received payload and compare 
      it to the crc the server reported in the header*/
      unsigned int expected_crc = crc_string(data.contents, data.header.length);

      /*The data packet is a transfer packet(upload or download).
      Check its integrity (using CRC32) and send the proper acknowledgment message.*/
      if (expected_crc != data.header.crc_value) {
        A_WRN("CRC32 check failed! Skipping packet processing");
        ack = -1;
        send_ack(ack);
        continue;
      } else {
        A_DBG("CRC32 check %04x successful! processing packet\n", expected_crc);
      }
      //successful CRC confirmation of packet
      ack = data.header.command_id;

      if (data.header.command_type == START_DOWNLOAD
          || data.header.command_type == FILE_TRANSFER || data.header.command_type == END_DOWNLOAD) {

        int result = 1;
        result = handle_download(&data);

        if (result != 1) {
          ack = result;
        }
        // A_DBG("result of packet processing is: %d\n", result);
        /*The data packet is a macro command. Call the appropriate function.*/
      } else if (data.header.command_type == MACRO_COMMAND) {
        A_DBG("Tokenizing");
        hard_press(data.contents);
        ack = data.header.command_id;
      } else if (data.header.command_type == REDRAW_COMMAND) {
        A_DBG("Sending request to redraw screen");
        ack = data.header.command_id;
        
        //todo create function to instantiate and send ui_update struct
        UI_update update;
        update.type = REDRAW_COMMAND;
        update.status = 0;
        if (snprintf(update.message, sizeof(update.message), "redraw screen") < 0) {
          A_ERR("update message creation failed in send_connection_status");
        }

        xStatus = xQueueSend(ui_updates_queue, &update, portMAX_DELAY);
        if(xStatus != pdPASS){
          vPrintString("send_connection_status failed to send update to ui_updates_queue\r\n");
        }
      }
      // Serial.printf("[DEBUG] [wifi_request_handling] Sending ack value %d for message %u\n", ack, data.header.command_id);
      A_DBG("Sending ack value %d for message %u\n", ack, data.header.command_id);
      //seding confirmation
      send_ack(ack);

    } else {
      vPrintString("[ERROR] [wifi_request_handling] failed to receive data from wifi_request_queue. \r\n");
    }
    vTaskDelay(10 / portTICK_PERIOD_MS);
  }
}
