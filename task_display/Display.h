#ifndef _DISPLAY_H_
#define _DISPLAY_H_

#include "utilities.h"
#include "Sprite.h"
// #include <TAMC_GT911.h>

int touch_last_x = 0, touch_last_y = 0;
int pos[2] = {0, 0};
Sprite* sprites[SPRITE_COUNT];
char* icons[SPRITE_COUNT] = {NOTEPAD_85, CHROME_85, YOUTUBE_85, SPOTIFY_85, ADOBE_85, PYCHARM_85, VSCODE_85, STEAM_85, GIT_85, NOTEPAD_85};

int icon_x = 0, icon_y = 0;

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


static int jpegDrawCallback(JPEGDRAW *pDraw)
{
  // Serial.printf("Draw pos = %d,%d. size = %d x %d\n", pDraw->x, pDraw->y, pDraw->iWidth, pDraw->iHeight);
  gfx->draw16bitBeRGBBitmap(pDraw->x, pDraw->y, pDraw->pPixels, pDraw->iWidth, pDraw->iHeight);
  return 1;
}

void drawLog(const char* filename, int x, int y){
  Serial.printf("Drawing image %s at x = %d, y = %d\n", filename, x, y);
}

void touch_init(void)
{
  Wire.begin(TOUCH_SDA, TOUCH_SCL);
  ts.begin();
  ts.setRotation(TOUCH_ROTATION);
}

/*Get coordinates of a touch. Updates x and y coordinates in the `pos` 
array for new touches alongside a return value of 1. Otherwise coords
are set to -1 and a value of 0 is returned. */
int get_pos()
{
    ts.read();

    if (ts.isTouched && pos[0] != ts.points[0].x && pos[1] != ts.points[0].y)
    {
      pos[0] = ts.points[0].x;
      pos[1] = ts.points[0].y;
      Serial.println("touched");

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

void draw_text(Arduino_RPi_DPI_RGBPanel *gfx, int text_x, int text_y, int text_size, int text_color, const char* text){
  gfx->setTextSize(text_size);
  gfx->setTextColor(text_color);
  gfx->setCursor(text_x, text_y);
  gfx->println(text);
}

void clear_screen(Arduino_RPi_DPI_RGBPanel *gfx){
  gfx->fillScreen(BLACK);
}
/*Draw main icon scene*/
void draw_main_screen(Arduino_RPi_DPI_RGBPanel *gfx){
  gfx->setCursor(0,0);
  icon_x = 0;
  icon_y = 0;
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
}

#endif