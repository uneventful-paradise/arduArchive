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
enum SwipeType { SWIPE_START, SWIPE_TRACK, SWIPE_SUCCESS, SCREEN_PRESS, SWIPE_FAIL}; 

static int jpegDrawCallback(JPEGDRAW *pDraw);

void drawLog(const char *filename, int x, int y);

void touch_init(void);

int get_pos();

void draw_text(int text_x, int text_y, int text_size, int text_color, const char *text);

void clear_screen();

void draw_nav_btns();

void draw_folder_contents();

void draw_main_screen();

bool init_icons(const char* icon_directory);

bool init_icons_from_config(const char* config_path, bool is_dir = false);

bool swap_page(int page_code, unsigned int folder_page);

SwipeType track_swipe();

SwipeType execute_swipe(int sx, int sy, int ex, int ey, unsigned long st, unsigned long et);

void draw_time(char* time_string, int x, int y, int size = 2);

#endif