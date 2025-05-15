#include "Tasks.h"

static TaskHandle_t touch_task_handle = NULL;

/*Initialize the touch function, screen, display function, keyboard
and start the tasks.
TODO: block some tasks from running before internet connection or during transfers*/

void setup() {
  Serial.begin(115200);
  A_DBG("Debug mode is set to %d", DEBUG);
  pinMode(TOUCH_RST, OUTPUT);
  delay(100);
  digitalWrite(TOUCH_RST, LOW);
  delay(1000);
  digitalWrite(TOUCH_RST, HIGH);
  delay(1000);

  ledcSetup(PWM_CHANNEL, PWM_FREQ, pwm_resolution_bits);
  // ledcAttachPin(TFT_BL, PWM_CHANNEL);

  ledcWrite(PWM_CHANNEL, 1023);  // output PWM

  digitalWrite(TOUCH_RST, LOW);
  delay(1000);
  digitalWrite(TOUCH_RST, HIGH);
  delay(1000);
  touch_init();
  delay(300);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PWD);
  // Init Display
  gfx->begin();

  Keyboard.begin();
  USB.begin();

  SPI.begin(SD_SCK, SD_MISO, SD_MOSI);
  if (!sd.begin(SdSpiConfig(SD_CS, SHARED_SPI, SD_SCK_MHZ(50)))) {
    sd.initErrorHalt();
    A_ERR("ERROR: SD Mount Failed!");
    while(true)
    {
      gfx->fillScreen(WHITE);
      gfx->setTextSize(3);
      gfx->setTextColor(RED);
      gfx->setCursor(50, 180);
      gfx->println(F("ERROR: SD Mount Failed!"));
      delay(3000);
    }
  } else {
    /*Initializing mutexes*/
    xPrintMutex = xSemaphoreCreateMutex();
    if (xPrintMutex == NULL) {
      A_ERR("Failed to create print mutex!");
    }
    xButtonsMutex = xSemaphoreCreateMutex();
    
    if (xButtonsMutex == NULL) {
      A_ERR("Failed to create buttons mutex");
    }
    // xClientMutex = xSemaphoreCreateMutex();
    // if (xClientMutex == NULL){
    //   A_ERR("Failed to create xClientMutex mutex");
    // }
    xConnCheckMutex = xSemaphoreCreateMutex();
    if (xConnCheckMutex == NULL){
      A_ERR("Failed to create xConnCheckMutex mutex");
    }

    connection_event_group = xEventGroupCreate();
    if (!connection_event_group) {
      A_ERR("Failed to create event group");
    }

    sr_client = new SrClient(Serial);
    nw_client = new NwClient(wfc, connection_event_group);
    current_client = (BaseClient*) sr_client;

    if (!init_icons_from_config("/configs/btn_config.txt")) {
      A_ERR("Icon read failed");
    }

    A_DBG("Free heap is %u", ESP.getFreeHeap());

    /*Creating task queues. The queue takes event size as parameter 
    so it can manage the memory blocks allocated for each instance of the event itself*/
    send_queue = xQueueCreate(20, sizeof(Package_data));
    conf_queue = xQueueCreate(5, sizeof(Package_data));
    ui_updates_queue = xQueueCreate(10, sizeof(UI_update));
    wifi_request_queue = xQueueCreate(20, sizeof(Package_data));

    if (send_queue == NULL) {
      A_ERR("Failed to create send_queue");
    }

    if (conf_queue == NULL) {
      A_ERR("Failed to create conf_queue");
    }

    if (ui_updates_queue == NULL) {
      A_ERR("Failed to create ui_updates_queue");
    }

    if (wifi_request_queue == NULL) {
      A_ERR("Failed to create ui_updates_queue");
    }

    xTaskCreatePinnedToCore(
      touch_check_task,
      "touch_check",
      8192,
      NULL,
      1,
      &touch_task_handle,
      1);

    xTaskCreatePinnedToCore(
      update_screen_task,
      "update_screen_task",
      4096,
      NULL,
      1,
      NULL,
      1);

    xTaskCreatePinnedToCore(
      establish_connection_task,
      "establish_connection_task",
      4096,
      NULL,
      1,
      NULL,
      0);

    xTaskCreatePinnedToCore(
      send_request_task,
      "send_request_task",
      8192,
      NULL,
      1,
      NULL,
      1);

    xTaskCreatePinnedToCore(
      receive_request_task,
      "receive_request_task",
      8192,
      NULL,
      1,
      NULL,
      1);

    xTaskCreatePinnedToCore(
      wifi_request_handling_task,
      "wifi_request_handling_task",
      8192,
      NULL,
      1,
      NULL,
      1);
  }
}

//constants vs macros
void loop() {
  // if(configured_timestamp){
  //   update_timestamp();
  //   delay(1000);
  // }
}