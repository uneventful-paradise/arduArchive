#include "Display.h"

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


void handle_command(void* params){
  TouchEvent event;
  while(true){
    if(xQueueReceive(touchQueue, &event, portMAX_DELAY) == pdTRUE){
      Serial.printf("Button with id %d has been selected and path is %s\n", event.buttonId, paths[event.buttonId]);
      //update display 
      access_path(event.buttonId);
    }
    // vTaskDelay(100/portTick_PERIOD_MS);    //do i need to delay or is this event driven?
  }
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
      Serial.println("printing paths");
      sprites[i] = new Sprite();
      sprites[i]->set(icon_x, icon_y, BUTTON_WIDTH, BUTTON_HEIGHT, "", i, 0);
      sprites[i]->setFilename(icons[i]);
      sprites[i]->setPath(paths[i]);
      Serial.println(paths[i]);
      sprites[i]->setGFX(gfx);
      sprites[i]->draw(jpegDrawCallback);
      icon_x += 100;

    }

    init_paths("/configs/path_config_2.txt");
    //https://www.esp32.com/viewtopic.php?t=2663
    //https://www.freertos.org/Documentation/02-Kernel/04-API-references/01-Task-creation/01-xTaskCreate

    //practice tasks
    //creating task queue. the queue takes event size as parameter so it can manage the memory blocks allocated for each instance of the event
    touchQueue = xQueueCreate(10, sizeof(TouchEvent));
    if(touchQueue == NULL){
      Serial.println("Failed to create touchQueue");
    }
    // xTaskCreatePinnedToCore(
    //   display_text_task,  //function that implemenets the task
    //   "display text",     //display name for task
    //   4096,               //stack size in words, not in bytes
    //   (void*)gfx,                //parameter passed into the task      
    //   3,                  //priority at which task is created        
    //   NULL,               //used to pass out the created task's handle
    //   1                  //core where the task shsould run
    //           );
            

    // Task2_params t2p = {
    //   gfx,
    //   jpegDrawCallback,
    //   buttons,
    //   BUTTON_COUNT
    // };

    // xTaskCreatePinnedToCore(
    //   display_icon_task,  //function that implemenets the task
    //   "display icon",     //display name for task
    //   4096,               //stack size in words, not in bytes
    //   (void*)&t2p,                //parameter passed into the task      
    //   3,                  //priority at which task is created        
    //   NULL,               //used to pass out the created task's handle
    //   1                  //core where the task shsould run
    //           );

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
  }
}

void loop() {

}
