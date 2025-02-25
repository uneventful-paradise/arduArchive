#include "Button.h"

Button::Button()
{
    this->x = 0;
    this->y = 0;
    this->w = 0;
    this->h = 0;
    this->text = "";
    this->textSize = DEFAULT_TEXT_SIZE;
    this->value = UNABLE;
}


Button::Button(int x, int y, int w, int h, String text, int value, int textSize)
{
    this->x = x;
    this->y = y;
    this->w = w;
    this->h = h;
    this->text = text;
    this->textSize = textSize;
    this->value = value;
}

Button::Button(Arduino_RPi_DPI_RGBPanel * gfx){
  this->gfx = gfx;
}

void Button::set(int x, int y, int w, int h, String text, int value, int textSize)
{
    this->x = x;
    this->y = y;
    this->w = w;
    this->h = h;
    this->text = text;
    this->textSize = textSize;
    this->value = value;
}

void Button::getFoDraw(int *x, int *y, int *w, int *h, String *text, int *textSize)
{
    *x = this->x;
    *y = this->y;
    *w = this->w;
    *h = this->h;
    *text = this->text;
    *textSize = this->textSize;
}

int Button::checkTouch(int x, int y)
{
    if (value == UNABLE)
    {
        return UNABLE;
    }
    else if (x > this->x && x < this->x + this->w && y > this->y && y < this->y + this->h)
    {
        return this->value;
    }
    else
        return UNABLE;
}

void Button::setText(String t)
{
    this->text = t;
}

String Button::getText()
{
    return this->text;
}
//? this->attr
void Button::setPath(String p){
  this->path = p;
}

String Button::getPath(){
  return this->path;
}

void Button::setValue(int v)
{
    this->value = v;
}

int Button::getValue()
{
    return this->value;
}

void Button::setTextSize(int textSize)
{
    this->textSize = textSize;
}

void Button::setFilename(char* filename){
  this->filename = filename;
}

char* Button::getFilename(){
  return this->filename;
}

void Button::setGFX(Arduino_RPi_DPI_RGBPanel * gfx){
  this -> gfx = gfx;
}

void Button::draw(JPEG_DRAW_CALLBACK *jpegDrawCallback){

  jpegDraw(this->filename, jpegDrawCallback, true /* useBigEndian */,
          this-> x /* x */, this->y /* y */, this->gfx->width() /* widthLimit */, this->gfx->height() /* heightLimit */);
}