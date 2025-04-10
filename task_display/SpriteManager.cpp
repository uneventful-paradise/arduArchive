#include "SpriteManager.h"

SpriteManager::SpriteManager(const unsigned int BTN_PER_PAGE, const unsigned int BNT_PER_ROW, const unsigned int BTN_OFFSET){
  A_DBG("constructing sprite manager");

  this -> btn_per_page = BTN_PER_PAGE;
  this -> btn_per_row = BNT_PER_ROW;
  this -> btn_offset = BTN_OFFSET;

  this -> btn_count = 0;
  this -> btn_capacity = SPRITE_COUNT;
  this -> buttons = (Sprite**)malloc(this -> btn_capacity * sizeof(Sprite*));
  if (this -> buttons == NULL) {
    A_ERR("Error at allocating buttons array");
  }

  for (int i = 0; i < this -> btn_capacity; ++i) {
    this -> buttons[i] = nullptr;
  }

  A_DBG("sprite manager construction complete");
}

Sprite* SpriteManager::add_button(int id, char* filename){
  A_DBG("Adding button %d to array", id);

  if(this -> btn_count >= this -> btn_capacity){
    A_DBG("Reached buttons array size limit!");

    int old_size = this -> btn_capacity;
    int new_size = 2 * old_size;

    this -> btn_capacity = new_size;
    A_DBG("Updated buttons array to new size %d", new_size);
    
    Sprite** temp_buttons = (Sprite**)realloc(this->buttons, new_size * sizeof(Sprite*));
    if (temp_buttons == NULL) {
      A_ERR("Realloc call for buttons array failed");
      return NULL;
    }
    A_DBG("Resized array to %d", new_size);
    // for(int i = old_size; i < new_size; ++i){
    //   A_DBG("setting %d to nullptr", i);
    //   this -> buttons[i] = nullptr;
    // }
    this -> buttons = temp_buttons;
    // return NULL;
  }

  Sprite* new_btn = new Sprite();
  int index = this -> btn_count;
  this -> buttons[index] = new_btn;
  this -> btn_count++;
  A_DBG("Adding button of id %d and icon %s on position %d", id, filename, index);

  int row = ( id % this -> btn_per_page) / this -> btn_per_row;
  int icon_x = (id % this -> btn_per_row) * 100 + this -> btn_offset;
  int icon_y = row * 100 + this -> btn_offset;

  new_btn -> set(icon_x, icon_y, BUTTON_WIDTH, BUTTON_HEIGHT, id);
  new_btn -> setFilename(filename);
  
  A_DBG("Succesfully added button\n");
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
//?hashmap?
bool SpriteManager::delete_button(int id){
  if (id < 0) {
    return false;
  }
  for (int i = 0; i < this -> btn_count; ++i) {
    if((this -> buttons[i] != nullptr) && (this -> buttons[i] -> getId() == id)){
      delete this -> buttons[i];
      this -> buttons[i] = nullptr;

      for (int j = i; j < this -> btn_count - 1; ++j) {
        this -> buttons[j] = this -> buttons[j + 1];
      }
      this -> buttons[this -> btn_count - 1] = nullptr;
      this -> btn_count -= 1;
      return true;
    }
  }
  return false;
}

int SpriteManager::getCapacity(){
  return this -> btn_capacity;
}

int SpriteManager::getCount(){
  return this -> btn_count;
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