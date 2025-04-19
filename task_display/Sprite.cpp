#include "Sprite.h"

Sprite::Sprite() {
  this->x = 0;
  this->y = 0;
  this->w = 0;
  this->h = 0;
  this->id = UNABLE;
}


Sprite::Sprite(int x, int y, int w, int h, int id) {
  this->x = x;
  this->y = y;
  this->w = w;
  this->h = h;
  this->id = id;
}

Sprite::Sprite(Arduino_RPi_DPI_RGBPanel *gfx) {
  this->gfx = gfx;
}

void Sprite::set(int x, int y, int w, int h, int id) {
  this->x = x;
  this->y = y;
  this->w = w;
  this->h = h;
  this->id = id;
}

void Sprite::getFoDraw(int *x, int *y, int *w, int *h) {
  *x = this->x;
  *y = this->y;
  *w = this->w;
  *h = this->h;
}

int Sprite::checkTouch(int x, int y) {
  if (id == UNABLE) {
    return UNABLE;
  } else if (x > this->x && x < this->x + this->w && y > this->y && y < this->y + this->h) {
    return this->id;
  } else
    return UNABLE;
}

void Sprite::setId(int v) {
  this->id = v;
}

int Sprite::getId() {
  return this->id;
}

int Sprite::getWidth() {
  return this->w;
}

int Sprite::getHeight() {
  return this->h;
}

void Sprite::setFilename(char *filename) {
  this->filename = strdup(filename);
}

char *Sprite::getFilename() {
  return this->filename;
}

void Sprite::setGFX(Arduino_RPi_DPI_RGBPanel *gfx) {
  this->gfx = gfx;
}

void Sprite::draw(JPEG_DRAW_CALLBACK *jpegDrawCallback) {
  if (this -> filename == NULL) {
    A_ERR("filename not assigned for button %d\n", (this -> id));
    return;
  }

  jpegDraw(this->filename, jpegDrawCallback, true /* useBigEndian */,
           this->x /* x */, this->y /* y */, this->gfx->width() /* widthLimit */, this->gfx->height() /* heightLimit */);
}

//?swap to nullptr
Sprite::~Sprite(){
  if (this->filename != NULL) {
    free(this->filename);
  }
  this->filename = NULL;
}