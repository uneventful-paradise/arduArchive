#include "Tasks.h"

static TaskHandle_t touch_task_handle = NULL;

/*Initialize the touch function, screen, display function, keyboard
and start the tasks.
TODO: block some tasks from running before internet connection or during transfers*/

void setup() {
  Serial.begin(115200);

  Serial.printf("val of macro is %d", USE_DBG_MACROS);
  // DBG_FAIL_MACRO;

  pinMode(TOUCH_RST, OUTPUT);
  delay(100);
  digitalWrite(TOUCH_RST, LOW);
  delay(1000);
  digitalWrite(TOUCH_RST, HIGH);
  delay(1000);

  ledcSetup(PWM_CHANNEL, PWM_FREQ, pwm_resolution_bits);
  ledcAttachPin(TFT_BL, PWM_CHANNEL);

  ledcWrite(PWM_CHANNEL, 1023); // output PWM

  digitalWrite(TOUCH_RST, LOW);
  delay(1000);  
  digitalWrite(TOUCH_RST, HIGH);
  delay(1000);
  touch_init();
  delay(300);

  // Init Display
  gfx->begin();

  Keyboard.begin();
  USB.begin();

  SPI.begin(SD_SCK, SD_MISO, SD_MOSI);
  if (!SD.begin(SD_CS))
  {
    Serial.println(F("ERROR: SD Mount Failed!"));
    // while(1)
    {
      gfx->fillScreen(WHITE);
      gfx->setTextSize(3);
      gfx->setTextColor(RED);
      gfx->setCursor(50, 180);
      gfx->println(F("ERROR: SD Mount Failed!"));
      delay(3000);
    }
  }
  else
  {
    Serial.print("Free Heap before loading image: ");
    Serial.println(ESP.getFreeHeap());

    draw_main_screen(gfx);
    
    init_paths("/configs/path_config_2.txt");
    /*Initializing mutexes*/
     xPrintMutex = xSemaphoreCreateMutex();

    if (xPrintMutex == NULL) {
      Serial.println("Failed to create print mutex!");
    }
    /*Creating task queues. The queue takes event size as parameter 
    so it can manage the memory blocks allocated for each instance of the event itself*/
    selection_queue = xQueueCreate(10, sizeof(Touch_event));
    send_queue = xQueueCreate(20, sizeof(Package_data));
    ui_updates_queue = xQueueCreate(10, sizeof(UI_update));
    wifi_request_queue = xQueueCreate(20, sizeof(Package_data));
    
    if(selection_queue == NULL){
      Serial.println("Failed to create selection_queue");
    }
    if(send_queue == NULL){
      Serial.println("Failed to create send_queue");
    }
  
    if(ui_updates_queue == NULL){
      Serial.println("Failed to create ui_updates_queue");
    }

    if(wifi_request_queue == NULL){
      Serial.println("Failed to create ui_updates_queue");
    }

    xTaskCreatePinnedToCore(
      touch_check_task,
      "touch_check",
      4096,
      NULL,
      1,
      &touch_task_handle,
      1
    );

    xTaskCreatePinnedToCore(
      update_screen_task,
      "update_screen_task",
      4096,
      NULL,
      1,
      NULL,
      1
    );

    xTaskCreatePinnedToCore(
      handle_command,
      "handle_command",
      4096,
      NULL,
      1,
      NULL,
      1
    );

    xTaskCreatePinnedToCore(
      establish_connection_task,
      "establish_connection_task",
      4096, 
      NULL,
      1,
      NULL,
      0
    );

    xTaskCreatePinnedToCore(
      send_request_task,
      "send_request_task",
      8192,
      NULL,
      1,
      NULL,
      1
    );

    xTaskCreatePinnedToCore(
      receive_request_task,
      "receive_request_task",
      8192,
      NULL,
      1,
      NULL,
      1
    );

    xTaskCreatePinnedToCore(
      wifi_request_handling_task,
      "wifi_request_handling_task",
      8192,
      NULL,
      1,
      NULL,
      1
    );
    
  }
}

//interrupt upload if something goes wrong?
//constants vs macros
void loop() {
  
}