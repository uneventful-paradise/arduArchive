#ifndef _Sprite_H_
#define _Sprite_H_

#include "config.h"
#include <arduino.h>
#include <Arduino_GFX_Library.h>

#define UNABLE -1
#define ENABLE 1
#define DEFAULT_TEXT_SIZE 2

//define a button class
class Sprite {
private:
  //Button Position
  int x;
  int y;
  int w;
  int h;

  //Button text
  char *icon_path;
  bool is_folder;
  Arduino_RPi_DPI_RGBPanel *gfx;
  //Button id, default id = -1 is untouchable
  int id;

public:
  Sprite();
  Sprite(int x, int y, int w, int h, int id, bool is_folder = false);
  Sprite(Arduino_RPi_DPI_RGBPanel *gfx);

  void set(int x, int y, int w, int h, int id, bool is_folder = false);
  void getFoDraw(int *x, int *y, int *w, int *h);

  void setId(int v);
  int getId();
  bool getFolderState();
  void setFolderState(bool value);
  char* getIconPath();
  void setIconPath(char *icon_path);
  int checkTouch(int x, int y);
  void setGFX(Arduino_RPi_DPI_RGBPanel *gfx);
  int getWidth();
  int getHeight();

  void draw(JPEG_DRAW_CALLBACK *jpegDrawCallback);
  ~Sprite();
};

#endif