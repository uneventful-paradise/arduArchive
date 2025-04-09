#ifndef _TASKS_H_
#define _TASKS_H_
//TODO: set a higher priority for reader tasks?
//TODO: is yielding necessary when waiting upon xQeueuReceive

/*Setting xTicksToWait to portMAX_DELAY will 
cause the task to wait indefinitely (without timing out), 
provided INCLUDE_vTaskSuspend is set to 1 in FreeRTOSConfig.h.*/

#include "Display.h"
#include "WiFi_comms.h"

struct Touch_event {
  int x;
  int y;
  int buttonId;
};

QueueHandle_t selection_queue;
QueueHandle_t wifi_request_queue; 

EventGroupHandle_t connection_event_group;
#define WIFI_CONNECTED_BIT (1 << 0)
#define CLIENT_CONNECTED_BIT (1 << 1)

/*This taks's purpose is to listen to incoming touches, determine whether the touch has selected a valid icon
and send the selection information to the server via a Package_Data object.*/
void touch_check_task(void* params) {
  // BaseType_t watermark = uxTaskGetStackHighWaterMark(NULL);                    //checking for available stack
  // Serial.printf("touch_check_task stack high water mark: %u\n", watermark);

  BaseType_t xStatus;
  Sprite** buttons = sprite_manager.getButtons();
  while (true) {
    //screen has been touched
    if (get_pos() == 1) {
      for (int i = 0; i < sprite_manager.getCapacity(); i++) {
        int button_value = UNABLE;
        //checking if button is bound to command
        if ((button_value = buttons[i] -> checkTouch(pos[0], pos[1])) != UNABLE) {
          // Serial.printf("Pos is: %d, %d\n", pos[0], pos[1]);
          // Serial.printf("Value is: %d\n", button_value);

          //creating event and sending it to queue to trigger the touch_handle task
          Touch_event event = { pos[0], pos[1], button_value };
          //creating a data packet to send command information to server
          Package_data data;
          Header_data header;
          // Serial.printf("SENDING command for %s to server\n", paths[event.buttonId]);

          memset(data.contents, 0, sizeof(data.contents));
          if (snprintf(data.contents, sizeof(data.contents), "%d", button_value) < 0) {
            Serial.println("snprintf failed in touch_check_task");
            continue;
          }
          /*touches can only trigger macro commands
          cmd_id will be updated by sender task
          send button id as argument for the server to
          identify the corresponding actions
          */
          header.command_type = MACRO_COMMAND;
          header.command_id = 0;
          header.length = strlen(data.contents);
          header.crc_value = crc_string(data.contents, header.length);
          data.header = header;
          A_DBG("Selected value is %s\n", data.contents);

          xStatus = xQueueSend(selection_queue, &event, portMAX_DELAY);
          if (xStatus != pdPASS) {
            /*The send operation could not complete because the queue was full-
                this must be an error since xTicksToWait = portMAX_DELAY so the 
                task blocks indefinitely until there is enough space to write the data*/
            vPrintString("touch_check_task failed to send data to the selection_queue.\r\n");
          }

          xStatus = xQueueSend(send_queue, &data, portMAX_DELAY);
          if (xStatus != pdPASS) {
            vPrintString("touch_check_task failed to send data to the send_queue.\r\n");
          }
        }
      }
    }
    vTaskDelay(200 / portTICK_PERIOD_MS);
  }
}

//currently unused
void handle_command(void* params) {
  Touch_event event;
  while (true) {
    if (xQueueReceive(selection_queue, &event, portMAX_DELAY) == pdTRUE) {
      Serial.printf("Button with id %d has been selected\n", event.buttonId);
      //update display
      // access_path(event.buttonId);
    }
    // vTaskDelay(100/portTick_PERIOD_MS);    //do i need to delay or is this event driven?
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
  // Serial.printf("update_screen_tasl stack high water mark: %u\n", watermark);
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
      //file transfer related upload
      textWidth = strlen(update.message) * 20;
      textX = (screenWidth - textWidth) / 2;

      switch (update.type) {
        case START_DOWNLOAD:{
          A_DBG("case is start_download");
          clear_screen(gfx);
          draw_text(gfx, textX, textY, 3, WHITE, update.message);
  
          gfx->drawRect(barX, barY, barWidth, barHeight, WHITE);
          vTaskDelay(100 / portTICK_PERIOD_MS);
          break;
        }
        case FILE_TRANSFER:{
          //Transfer ongoing
          A_DBG("case is file_transfer");
          // gfx->fillRect(barX, barY, barWidth, barHeight, BLACK);
          // Calculate filled width based on update.arg (percentage 0 to 100)
          int filledWidth = (barWidth * update.status) / 100;
          gfx->fillRect(barX, barY, filledWidth, barHeight, WHITE);
          vTaskDelay(100 / portTICK_PERIOD_MS);
          break;
        }
        case END_DOWNLOAD: {
          A_DBG("case is end_download");
          draw_text(gfx, textX, textY + 100, 3, WHITE, update.message);
          vTaskDelay(500 / portTICK_PERIOD_MS);
          
          clear_screen(gfx);
          draw_main_screen(gfx);
          vTaskDelay(1000 / portTICK_PERIOD_MS);
          break;
        }
        case CONNECTION_CHECK: {
          // A_DBG("update message length is %d\n", strlen(update.message));
         
          if (update.status != 1) {
            A_DBG("case is connection lost");
            //TODO: add animation
            //connection dropped
            clear_screen(gfx);
            draw_text(gfx, textX, textY, 3, WHITE, update.message);
          } else if (update.status == 1) {
            A_DBG("case is connection gained");
            clear_screen(gfx);
            draw_text(gfx, textX, textY, 3, WHITE, update.message);
            vTaskDelay(500 / portTICK_PERIOD_MS);
            clear_screen(gfx);
            draw_main_screen(gfx);
          }
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

//TODO: block reading and writing tasks while not connected to WiFi or server.
/*
This task establishes and continuously monitors WiFi and server connection.
A device uses Station Mode to join a network that 
already exists.

During the setup phase of this function an initial network
connection is established. At this point a connection to
ntp server is creawted to fetch UTC timestamp and synchronize
local time with it.

To send conenction status updates to the GUI update task
the call to `send_connection_status` places an `ui_update`
object in the `ui_updates_queue` for the task to process. 
*/
void establish_connection_task(void* params) {

  int status =- 2;
  EventBits_t xEventGroupValue;

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PWD);

  //no WiFi connection established initially
  send_connection_status(status);
  
  //Initial connection attempt
  A_DBG("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    vTaskDelay(500 / portTICK_PERIOD_MS);
  }
  if (!configured_timestamp) {
    configure_timestamp();
    configured_timestamp = true;
  }
  A_DBG("WiFi Connected!");
  printWifiStatus();

  //Connecting to and monitoring connection to server and network.
  while (1) {
    xEventGroupValue = xEventGroupGetBits(connection_event_group);
    
    if (WiFi.status() != WL_CONNECTED) {
      if (xEventGroupValue & WIFI_CONNECTED_BIT) {
        //client was connected, therefore we lost connection
        xEventGroupClearBits(connection_event_group, WIFI_CONNECTED_BIT);
        status = -2;
        send_connection_status(status);
      }
      A_WRN("WiFi disconnected! Reconnecting...");
      WiFi.begin(WIFI_SSID, WIFI_PWD);
      continue;
    } else {
      if (!(xEventGroupValue & WIFI_CONNECTED_BIT)) {
        //client was not connected, therefore connection was established
        xEventGroupSetBits(connection_event_group, WIFI_CONNECTED_BIT);
        status = -1;
        send_connection_status(status);
        A_DBG("WiFi connected!");
      }
    }

    if (!client.connected()) {
      if (xEventGroupValue & CLIENT_CONNECTED_BIT) {
        xEventGroupClearBits(connection_event_group, CLIENT_CONNECTED_BIT);
        status = 0;
        send_connection_status(status);
      }
      A_WRN("Client disconnected! Reconnecting...");
      connect_to_server();
    }else{
      if (!(xEventGroupValue & CLIENT_CONNECTED_BIT)) {
        //client was not connected, therefore connection was established
        xEventGroupSetBits(connection_event_group, CLIENT_CONNECTED_BIT);
        status = 1;
        send_connection_status(status);
        A_DBG("Client connected!")
      }
    }
    vTaskDelay(100 / portTICK_PERIOD_MS);
  }
}

/*This task polls message requests from all other tasks and sends them to the server*/
void send_request_task(void* params) {
  // UBaseType_t watermark = uxTaskGetStackHighWaterMark(NULL);
  // Serial.printf("\nsend_request_task stack high water mark (BEGIN) : %u\n", watermark);

  BaseType_t xStatus;
  Touch_event event;
  Package_data data;

  EventBits_t xEventGroupValue;
  const EventBits_t xBitsToWaitFor = ( WIFI_CONNECTED_BIT | CLIENT_CONNECTED_BIT );
 
  while (true) {
    xEventGroupValue = xEventGroupWaitBits(
      /* The event group to read */
      connection_event_group,
      /* Bits to test */
      xBitsToWaitFor,
      /* Clear bits on exit if the
      unblock condition is met */
      pdFALSE,
      /* wait for all bits. 
      before proceeding to read */
      pdTRUE,
      /* Don't time out.*/
      portMAX_DELAY );
    //only attempt to send while client is connected otherwise go back to waiting/blocked state
    if (client.connected()) {
      xStatus = xQueueReceive(send_queue, &data, portMAX_DELAY);
      if (xStatus == pdPASS) {
        //send request to server
        data.header.command_id = client_cmd_id;
        send_request(&data);
      } else {
        vPrintString("[ERROR] [send_request_task] failed to receive from send_queue.\r\n");
      }

      // watermark = uxTaskGetStackHighWaterMark(NULL);
      // Serial.printf("\nsend_request_task stack high water mark (END) : %u\n", watermark);
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
  A_DBG("Acknowledge value is %s of size %d\n", data.contents, size);
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
  EventBits_t xEventGroupValue;
  const EventBits_t xBitsToWaitFor = ( WIFI_CONNECTED_BIT | CLIENT_CONNECTED_BIT );
    
  int read_threshold = HEADER_SIZE;
  size_t bytes_read = 0;

  while (true) {
    xEventGroupValue = xEventGroupWaitBits(
      /* The event group to read */
      connection_event_group,
      /* Bits to test */
      xBitsToWaitFor,
      /* Clear bits on exit if the
      unblock condition is met */
      pdFALSE,
      /* wait for all bits. 
      before proceeding to read */
      pdTRUE,
      /* Don't time out.*/
      portMAX_DELAY );
    //?((xEventGroupValue & (CONNECTED_TO_CLIENT | CONNECTED_TO_WIFI)) == (CONNECTED_TO_CLIENT | CONNECTED_TO_WIFI)) && 
    //TODO: can this busy loop be removed so that a touch isnt blocked by the read?
    if (client.available() >= read_threshold) {
      // A_WRN("passed threshold. waiting to read");
      //read and parse the header data. readbytes blocks until the specified number of bytes is available to read from the socket
      //we use ntohl because the data is sent in big-endian (networking standard) while the esp device operates in little-endian. ntohl converts integers to host byte order
      Header_data header;
      bytes_read = client.readBytes((char*)&header, sizeof(header));
      if (bytes_read != sizeof(header)) {
        Serial.printf("Error: Expected to read %u bytes but got %u bytes\n", sizeof(header), bytes_read);
        //how to delete junk from socket?
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
        //TODO: try to disconnect and reconnect? client.stop()
        A_WRN("emptying socket and requesting resend");
        while(client.available()){
          client.read();
        }
        send_ack(-1);
        continue;
      }

      char* req = (char*)malloc(header.length);
      if (!req) {
        A_ERR("Malloc fail for request contents allocation");
        send_ack(-1);
        continue;
      }
      client.readBytes(req, header.length);

      Package_data data;
      data.header = header;
      //zero out contents to avoid pre existing junk data when reading binary data
      memset(data.contents, 0, sizeof(data.contents));
      memcpy(data.contents, req, header.length);

      // Serial.printf("Received content %d, length: %d\n", data.cmd_id, data.length);
      // A_DBG("%s\n", data.contents);
      // better way to convert to hex?
      for (int i = 0; i < data.header.length; ++i) {
        printf("%02x", data.contents[i]);
      }
      printf("\n\n");

      // UBaseType_t watermark = uxTaskGetStackHighWaterMark(NULL);
      // Serial.printf("\nreceive_request_task stack high water mark (MID) : %u\n", watermark);

      //send request to queue to be processed
      xStatus = xQueueSend(wifi_request_queue, &data, portMAX_DELAY);
      if (xStatus != pdPASS) {
        vPrintString("receive_request_task Failed to send data to wifi_request_queue.\r\n");
      }
      free(req);
      // watermark = uxTaskGetStackHighWaterMark(NULL);
      // Serial.printf("\nreceive_request_task stack high water mark (END) : %u\n", watermark);
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

      // watermark = uxTaskGetStackHighWaterMark(NULL);
      // Serial.printf("\nwifi_request_task high water mark (MID) : %u\n", watermark);

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
      }
      // Serial.printf("[DEBUG] [wifi_request_handling] Sending ack value %d for message %u\n", ack, data.header.command_id);
      A_DBG("Sending ack value %d for message %u\n", ack, data.header.command_id);
      //seding confirmation
      send_ack(ack);

      // watermark = uxTaskGetStackHighWaterMark(NULL);
      // Serial.printf("\nwifi_request_task high water mark (END) : %u\n", watermark);
    } else {
      vPrintString("[ERROR] [wifi_request_handling] failed to receive data from wifi_request_queue. \r\n");
    }
    vTaskDelay(10 / portTICK_PERIOD_MS);
  }
}
#endif