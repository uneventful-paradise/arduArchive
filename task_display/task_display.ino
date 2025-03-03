#include "Tasks.h"

static TaskHandle_t touch_task_handle = NULL;

USBHIDKeyboard Keyboard;

int icon_x = 0, icon_y = 0;

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

static int jpegDrawCallback(JPEGDRAW *pDraw)
{
  // Serial.printf("Draw pos = %d,%d. size = %d x %d\n", pDraw->x, pDraw->y, pDraw->iWidth, pDraw->iHeight);
  gfx->draw16bitBeRGBBitmap(pDraw->x, pDraw->y, pDraw->pPixels, pDraw->iWidth, pDraw->iHeight);
  return 1;
}

void drawLog(const char* filename, int x, int y){
  Serial.printf("Drawing image %s at x = %d, y = %d\n", filename, x, y);
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


    for(int i = 0; i < SPRITE_COUNT; ++i){ //define loadIcon()
      if(icon_x + 85 > gfx->width()){
        icon_y += 100;
        icon_x = 0;
      }
      // Serial.println("printing paths");
      sprites[i] = new Sprite();
      sprites[i]->set(icon_x, icon_y, BUTTON_WIDTH, BUTTON_HEIGHT, "", i, 0);
      sprites[i]->setFilename(icons[i]);
      sprites[i]->setPath(paths[i]);
      // Serial.println(paths[i]);
      sprites[i]->setGFX(gfx);
      sprites[i]->draw(jpegDrawCallback);
      icon_x += 100;

    }

    init_paths("/configs/path_config_2.txt");
    //https://www.esp32.com/viewtopic.php?t=2663
    //https://www.freertos.org/Documentation/02-Kernel/04-API-references/01-Task-creation/01-xTaskCreate

    //creating task queue. the queue takes event size as parameter so it can manage the memory blocks allocated for each instance of the event
    selection_queue = xQueueCreate(10, sizeof(TouchEvent));
    macro_queue = xQueueCreate(10, sizeof(TouchEvent));
    if(selection_queue == NULL){
      Serial.println("Failed to create selection_queue");
    }
    if(macro_queue == NULL){
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
      handle_command,
      "handle_command",
      4096,
      NULL,
      1,
      NULL,
      1
    );
    xTaskCreatePinnedToCore(
      wifi_comms_task,
      "wifi_comms_task",
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
