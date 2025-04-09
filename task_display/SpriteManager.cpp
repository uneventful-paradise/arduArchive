#include "SpriteManager.h"

SpriteManager::SpriteManager(const unsigned int BTN_PER_PAGE, const unsigned int BNT_PER_ROW, const unsigned int BTN_OFFSET){
  this -> btn_per_page = BTN_PER_PAGE;
  this -> btn_per_row = BNT_PER_ROW;
  this -> btn_offset = BTN_OFFSET;

  this -> btn_count = 0;
  this -> btn_capacity = SPRITE_COUNT;
  this -> buttons = (Sprite**)malloc(this -> btn_capacity * sizeof(Sprite*));
  if (this -> buttons == NULL) {
    Serial.printf("Error at allocating buttons array\n");
  }

  for (int i = 0; i < this -> btn_capacity; ++i) {
    this -> buttons[i] = nullptr;
  }
}

Sprite* SpriteManager::add_button(int id, char* filename){
  if(id >= this -> btn_capacity){
    int old_size = this -> btn_capacity;
    int new_size = 2* old_size;

    this -> btn_capacity = new_size;
    Serial.printf("Updated buttons array to new size %d", new_size);
    
    Sprite** temp_buttons = (Sprite**)realloc(this->buttons, new_size * sizeof(Sprite*));
    if (temp_buttons == NULL) {
      Serial.printf("Realloc call for buttons array failed\n");
      return NULL;
    }
    Serial.printf("Resized array to %d\n", new_size);
    for(int i = old_size; i < new_size; ++i){
      this -> buttons[i] = NULL;
    }
    this -> buttons = temp_buttons;
  }

  Sprite* new_btn = new Sprite();
  this -> buttons[this -> btn_count++] = new_btn;

  int row = ( id % this -> btn_per_page) / this -> btn_per_row;
  int icon_x = (id % this -> btn_per_row) * 100 + this -> btn_offset;
  int icon_y = row * 100 + this -> btn_offset;

  new_btn -> set(icon_x, icon_y, BUTTON_WIDTH, BUTTON_HEIGHT, id);
  new_btn -> setFilename(filename);
  
  return new_btn;
}
//!UPDATE THESE TO SEARCH FOR THE ID IN THE LIST
bool SpriteManager::update_button(int id, char* filename){
  if (id < 0 || id >= this->btn_capacity || this->buttons[id] == nullptr) {
    return false;
  }
  this -> buttons[id] -> setFilename(filename);
  return true;
}

bool SpriteManager::delete_button(int id){
  if (id < 0 || id >= this->btn_capacity || this->buttons[id] == nullptr) {
    return false;
  }
  delete this -> buttons[id];
  this -> buttons[id] = nullptr;
  return true;
}

int SpriteManager::getCapacity(){
  return this -> btn_capacity;
}

Sprite** SpriteManager::getButtons(){
  return this -> buttons;
}

SpriteManager::~SpriteManager() {
  for (unsigned int i = 0; i < btn_capacity; ++i) {
      if (buttons[i] != nullptr) {
          delete buttons[i];
      }
  }
  free(buttons);
}