#ifndef _Button_H_
#define _Button_H_
#include <SD.h>
#include <arduino.h>
#include <Arduino_GFX_Library.h>
#include "JpegFunc.h"

#define UNABLE -1
#define ENABLE 1
#define DEFAULT_TEXT_SIZE 2

//define a button class
class Button
{
private:
  //Button Position
  int x;
  int y;
  int w;
  int h;

  //Button text
  String path;
  char* filename;
  String text;
  int textSize;
  Arduino_RPi_DPI_RGBPanel * gfx;

  //Button value, default value = -1 is untouchable
  int value;

public:
  Button();
  Button(int x, int y, int w, int h, String text, int value, int textSize = DEFAULT_TEXT_SIZE);
  Button(Arduino_RPi_DPI_RGBPanel * gfx);

  void set(int x, int y, int w, int h, String text, int value, int textSize = DEFAULT_TEXT_SIZE);
  void getFoDraw(int *x, int *y, int *w, int *h, String *text, int *textSize);

  void setText(String t);
  String getText();
  void setPath(String path);
  String getPath();
  void setValue(int v);
  int getValue();
  char* getFilename();
  void setFilename(char* filename);
  void setTextSize(int textSize);
  int checkTouch(int x, int y);
  void setGFX(Arduino_RPi_DPI_RGBPanel * gfx);

  void draw(JPEG_DRAW_CALLBACK *jpegDrawCallback);
};

#endif