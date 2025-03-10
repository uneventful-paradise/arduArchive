#include "Tasks.h"

static TaskHandle_t touch_task_handle = NULL;

USBHIDKeyboard Keyboard;

void init_paths(char* filename){
  if(!SD.exists(filename)){
    Serial.println("File does not exist");
    return;
  }
  File file = SD.open(filename);
  if(!file){
    Serial.println("Could not open file");
    return;
  }
  int index = 0;
  while(file.available()){
    if(index > SPRITE_COUNT){
      break;
    }
    String s = file.readStringUntil('\n');
    paths[index++] = strdup(s.c_str());
  }
}

void access_path(int icon_index){
  Keyboard.pressRaw(0xE3);
  Keyboard.pressRaw(HID_KEY_R);
  delay(500);

  Keyboard.releaseRaw(HID_KEY_GUI_LEFT);
  Keyboard.releaseRaw(HID_KEY_R);

  Keyboard.printf(paths[icon_index]);
  Keyboard.press(KEY_RETURN);
  delay(100);
  Keyboard.releaseAll();
}


void setup() {
  Serial.begin(115200);

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

    draw_main_screen();
    
    init_paths("/configs/path_config_2.txt");
    //https://www.esp32.com/viewtopic.php?t=2663
    //https://www.freertos.org/Documentation/02-Kernel/04-API-references/01-Task-creation/01-xTaskCreate

    //creating task queue. the queue takes event size as parameter so it can manage the memory blocks allocated for each instance of the event
    selection_queue = xQueueCreate(10, sizeof(Touch_event));
    macro_queue = xQueueCreate(10, sizeof(Touch_event));
    ui_updates_queue = xQueueCreate(10, sizeof(UI_update));
    wifi_request_queue = xQueueCreate(20, sizeof(PackageData));
    
    if(selection_queue == NULL){
      Serial.println("Failed to create selection_queue");
    }
    if(macro_queue == NULL){
      Serial.println("Failed to create macro_queue");
    }
  
    if(ui_updates_queue == NULL){
      Serial.println("Failed to create macro_queue");
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
      4096, //was 8192 because of insufficient stack space durin upload
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
      handle_requests_task,
      "handle_requests_task",
      8192,
      NULL,
      1,
      NULL,
      1
    );
  }
}

void loop() {

}
