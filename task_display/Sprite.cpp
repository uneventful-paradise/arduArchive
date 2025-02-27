#include "Sprite.h"

Sprite::Sprite()
{
    this->x = 0;
    this->y = 0;
    this->w = 0;
    this->h = 0;
    this->text = "";
    this->textSize = DEFAULT_TEXT_SIZE;
    this->value = UNABLE;
}


Sprite::Sprite(int x, int y, int w, int h, String text, int value, int textSize)
{
    this->x = x;
    this->y = y;
    this->w = w;
    this->h = h;
    this->text = text;
    this->textSize = textSize;
    this->value = value;
}

Sprite::Sprite(Arduino_RPi_DPI_RGBPanel * gfx){
  this->gfx = gfx;
}

void Sprite::set(int x, int y, int w, int h, String text, int value, int textSize)
{
    this->x = x;
    this->y = y;
    this->w = w;
    this->h = h;
    this->text = text;
    this->textSize = textSize;
    this->value = value;
}

void Sprite::getFoDraw(int *x, int *y, int *w, int *h, String *text, int *textSize)
{
    *x = this->x;
    *y = this->y;
    *w = this->w;
    *h = this->h;
    *text = this->text;
    *textSize = this->textSize;
}

int Sprite::checkTouch(int x, int y)
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

void Sprite::setText(String t)
{
    this->text = t;
}

String Sprite::getText()
{
    return this->text;
}
//? this->attr
void Sprite::setPath(String p){
  this->path = p;
}

String Sprite::getPath(){
  return this->path;
}

void Sprite::setValue(int v)
{
    this->value = v;
}

int Sprite::getValue()
{
    return this->value;
}

int Sprite::getWidth()
{
    return this->w;
}

int Sprite::getHeight()
{
    return this->h;
}

void Sprite::setTextSize(int textSize)
{
    this->textSize = textSize;
}

void Sprite::setFilename(char* filename){
  this->filename = filename;
}

char* Sprite::getFilename(){
  return this->filename;
}

void Sprite::setGFX(Arduino_RPi_DPI_RGBPanel * gfx){
  this -> gfx = gfx;
}

void Sprite::draw(JPEG_DRAW_CALLBACK *jpegDrawCallback){

  jpegDraw(this->filename, jpegDrawCallback, true /* useBigEndian */,
          this-> x /* x */, this->y /* y */, this->gfx->width() /* widthLimit */, this->gfx->height() /* heightLimit */);
}