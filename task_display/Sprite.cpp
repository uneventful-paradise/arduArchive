#include "Sprite.h"

Sprite::Sprite() {
  this -> x = 0;
  this -> y = 0;
  this -> w = 0;
  this -> h = 0;
  this -> id = UNABLE;
  this -> icon_path = NULL;
  this -> is_folder = false;
}


Sprite::Sprite(int x, int y, int w, int h, int id, bool is_folder) {
  this->x = x;
  this->y = y;
  this->w = w;
  this->h = h;
  this->id = id;
  this -> icon_path = NULL;
  this -> is_folder = is_folder;
}

Sprite::Sprite(Arduino_RPi_DPI_RGBPanel *gfx) {
  this->gfx = gfx;
}

void Sprite::set(int x, int y, int w, int h, int id, bool is_folder) {
  this->x = x;
  this->y = y;
  this->w = w;
  this->h = h;
  this->id = id;
  this->is_folder = is_folder;
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

bool Sprite::getFolderState() {
  return this->is_folder;
}

void Sprite::setFolderState(bool value) {
  this->is_folder = value;
}

void Sprite::setIconPath(char *icon_path) {
  this->icon_path = strdup(icon_path);
}

char *Sprite::getIconPath() {
  return this->icon_path;
}

void Sprite::setGFX(Arduino_RPi_DPI_RGBPanel *gfx) {
  this->gfx = gfx;
}

void Sprite::draw(JPEG_DRAW_CALLBACK *jpegDrawCallback) {
  if (this -> icon_path == NULL) {
    A_ERR("filename not assigned for button %d\n", (this -> id));
    return;
  }

  jpegDraw(this->icon_path, jpegDrawCallback, true /* useBigEndian */,
           this->x /* x */, this->y /* y */, this->gfx->width() /* widthLimit */, this->gfx->height() /* heightLimit */);
  // A_DBG("Coords of button %d are (%d, %d)", this -> id, this -> x, this ->y);
}

//?swap to nullptr
Sprite::~Sprite(){
  if (this->icon_path != NULL) {
    free(this->icon_path);
  }
  this->icon_path = NULL;
}