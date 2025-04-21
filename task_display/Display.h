#ifndef _DISPLAY_H_
#define _DISPLAY_H_

#include "SpriteManager.h"
#include "Utilities.h"
// #include <TAMC_GT911.h>

extern int touch_last_x,touch_last_y;
extern int pos[2];


extern int icon_x, icon_y;

extern Arduino_ESP32RGBPanel *bus;

// Uncomment for ST7262 IPS LCD 800x480
extern Arduino_RPi_DPI_RGBPanel *gfx;
extern TAMC_GT911 ts;
extern SpriteManager sprite_manager;

static int jpegDrawCallback(JPEGDRAW *pDraw);

void drawLog(const char *filename, int x, int y);

void touch_init(void);

int get_pos();

void draw_text(int text_x, int text_y, int text_size, int text_color, const char *text);

void clear_screen();

void draw_nav_btns();

void draw_main_screen();

bool init_icons(const char* icon_directory);

bool init_icons_from_config(const char* config_path);

#endif