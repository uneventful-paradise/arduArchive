#ifndef _DISPLAY_H_
#define _DISPLAY_H_

#include "config.h"
#include "Sprite.h"
// #include <TAMC_GT911.h>

struct TouchEvent{
  int x;
  int y;
  int buttonId;
};

int touch_last_x = 0, touch_last_y = 0;
int pos[2] = {0, 0};
Sprite* sprites[SPRITE_COUNT];
char* icons[SPRITE_COUNT] = {NOTEPAD_85, CHROME_85, YOUTUBE_85, SPOTIFY_85, ADOBE_85, PYCHARM_85, VSCODE_85, STEAM_85, GIT_85, NOTEPAD_85};
char* paths[SPRITE_COUNT];

QueueHandle_t touchQueue;

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

void touch_init(void)
{
  Wire.begin(TOUCH_SDA, TOUCH_SCL);
  ts.begin();
  ts.setRotation(TOUCH_ROTATION);
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


void touch_check_task(void* params){
  while(true){
    if (get_pos() == 1){                                                        //screen has been touched
      for (int i = 0; i < SPRITE_COUNT; i++){
        int button_value = UNABLE;
        if ((button_value = sprites[i]->checkTouch(pos[0], pos[1])) != UNABLE){ //checking if button is bound to command
          Serial.printf("Pos is :%d,%d\n", pos[0], pos[1]);
          Serial.printf("Value is :%d\n", button_value);

          TouchEvent event = {pos[0], pos[1], button_value};                    //creating event and sending it to queue to trigger the toiuch_handle task
          xQueueSend(touchQueue, &event, portMAX_DELAY);
        }
      }
    }
    vTaskDelay(200/portTICK_PERIOD_MS);
  }
}


#endif