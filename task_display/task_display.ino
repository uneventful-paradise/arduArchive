#include "config.h"

// #include <TAMC_GT911.h>

Arduino_ESP32RGBPanel *bus = new Arduino_ESP32RGBPanel(
    GFX_NOT_DEFINED /* CS */, GFX_NOT_DEFINED /* SCK */, GFX_NOT_DEFINED /* SDA */,
    40 /* DE */, 41 /* VSYNC */, 39 /* HSYNC */, 42 /* PCLK */,
    45 /* R0 */, 48 /* R1 */, 47 /* R2 */, 21 /* R3 */, 14 /* R4 */,
    5 /* G0 */, 6 /* G1 */, 7 /* G2 */, 15 /* G3 */, 16 /* G4 */, 4 /* G5 */,
    8 /* B0 */, 3 /* B1 */, 46 /* B2 */, 9 /* B3 */, 1 /* B4 */
);

// Uncomment for ST7262 IPS LCD 800x480
Arduino_RPi_DPI_RGBPanel *gfx = new Arduino_RPi_DPI_RGBPanel(
    bus,
    800 /* width */, 0 /* hsync_polarity */, 8 /* hsync_front_porch */, 4 /* hsync_pulse_width */, 8 /* hsync_back_porch */,
    480 /* height */, 0 /* vsync_polarity */, 8 /* vsync_front_porch */, 4 /* vsync_pulse_width */, 8 /* vsync_back_porch */,
    1 /* pclk_active_neg */, 16000000 /* prefer_speed */, true /* auto_flush */);

TAMC_GT911 ts = TAMC_GT911(TOUCH_SDA, TOUCH_SCL, TOUCH_INT, TOUCH_RST, TOUCH_WIDTH, TOUCH_HEIGHT);

USBHIDKeyboard Keyboard;
int touch_last_x = 0, touch_last_y = 0;
int icon_x = 0, icon_y = 0;
int pos[2] = {0, 0};
Button* buttons[BUTTON_COUNT];
char* icons[BUTTON_COUNT] = {NOTEPAD_85, CHROME_85, YOUTUBE_85, SPOTIFY_85, ADOBE_85, PYCHARM_85, VSCODE_85, STEAM_85, GIT_85};
char* paths[BUTTON_COUNT];

void touch_init(void)
{
  Wire.begin(TOUCH_SDA, TOUCH_SCL);
  ts.begin();
  ts.setRotation(TOUCH_ROTATION);
}

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
    if(index > BUTTON_COUNT){
      break;
    }
    String s = file.readStringUntil('\n');
    paths[index++] = strdup(s.c_str());
  }
}

void access_path(int icon_index){
  Keyboard.pressRaw(0xE3);
  Keyboard.pressRaw(HID_KEY_R);

  Keyboard.releaseRaw(HID_KEY_GUI_LEFT);
  Keyboard.releaseRaw(HID_KEY_R);

  Keyboard.printf(paths[icon_index]);
  Keyboard.press(KEY_RETURN);
  Keyboard.releaseAll();
}

int get_pos()
{
    ts.read();

    if (ts.isTouched && pos[0] != ts.points[0].x && pos[1] != ts.points[0].y)
    {
        pos[0] = ts.points[0].x;
        pos[1] = ts.points[0].y;
        Serial.println("atins");

        Serial.print(",x = ");
        Serial.print(pos[0]);
        Serial.print(", y = ");
        Serial.print(pos[1]);
        Serial.println();

        ts.isTouched = false;

        return 1;
    }
    else
    {
        pos[0] = -1;
        pos[1] = -1;
        return 0;
    }
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


    for(int i = 0; i < BUTTON_COUNT; ++i){ //define loadIcon()
      if(icon_x + 85 > gfx->width()){
        icon_y += 100;
        icon_x = 0;
      }
      Serial.println("printing paths");
      buttons[i] = new Button();
      buttons[i]->set(icon_x, icon_y, 85, 85, "", i, 0);
      buttons[i]->setFilename(icons[i]);
      buttons[i]->setPath(paths[i]);
      Serial.println(paths[i]);
      buttons[i]->setGFX(gfx);
      // buttons[i]->draw(jpegDrawCallback);
      icon_x += 100;

    }

    init_paths("/configs/path_config_2.txt");
    //https://www.esp32.com/viewtopic.php?t=2663
    //https://www.freertos.org/Documentation/02-Kernel/04-API-references/01-Task-creation/01-xTaskCreate
    xTaskCreatePinnedToCore(
      display_text_task,  //function that implemenets the task
      "display text",     //display name for task
      4096,               //stack size in words, not in bytes
      (void*)gfx,                //parameter passed into the task      
      3,                  //priority at which task is created        
      NULL,               //used to pass out the created task's handle
      1                  //core where the task shsould run
              );
            

    Task2_params t2p = {
      gfx,
      jpegDrawCallback,
      buttons,
      BUTTON_COUNT
    };

    xTaskCreatePinnedToCore(
      display_icon_task,  //function that implemenets the task
      "display icon",     //display name for task
      4096,               //stack size in words, not in bytes
      (void*)&t2p,                //parameter passed into the task      
      3,                  //priority at which task is created        
      NULL,               //used to pass out the created task's handle
      1                  //core where the task shsould run
              );
  }
}

void loop() {
  // put your main code here, to run repeatedly:
  // if (get_pos() == 1){
  //   for (int i = 0; i < BUTTON_COUNT; i++)
  //   {
  //       int button_value = UNABLE;
  //       if ((button_value = buttons[i]->checkTouch(pos[0], pos[1])) != UNABLE)
  //       {
  //         Serial.printf("Pos is :%d,%d\n", pos[0], pos[1]);
  //         Serial.printf("Value is :%d\n", button_value%6);
  //         Serial.printf("Text is :");
  //         Serial.println(paths[button_value]);
  //         access_path(button_value);
  //         delay(200);
  //     }
  //   }
  // }
}
