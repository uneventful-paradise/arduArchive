#include "SpriteManager.h"

SpriteManager::SpriteManager(Arduino_RPi_DPI_RGBPanel* GFX, const unsigned int DEFAULT_BTN, const unsigned int MAX_BTNS, const unsigned int BTN_PER_PAGE, const unsigned int BNT_PER_ROW, const unsigned int BTN_OFFSET){
  A_DBG("constructing sprite manager");
  this -> gfx = GFX;
  this -> btn_per_page = BTN_PER_PAGE;
  this -> btn_per_row = BNT_PER_ROW;
  this -> btn_offset = BTN_OFFSET;
  this -> max_capacity = MAX_BTNS;

  this -> btn_count = 0;
  this -> btn_capacity = DEFAULT_BTN;
  this -> buttons = (Sprite**)malloc(this -> btn_capacity * sizeof(Sprite*));

  this -> current_page = 0;
  this -> max_page = 0;

  if (this -> buttons == NULL) {
    A_ERR("Error at allocating buttons array");
  }

  for (int i = 0; i < this -> btn_capacity; ++i) {
    this -> buttons[i] = nullptr;
  }

  //!create function for init nav_buttons
  Sprite* btn_next = new Sprite();
  btn_next -> set(600, 400, BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_NEXT);
  btn_next -> setFilename("/85px/next.jpg");
  btn_next -> setGFX(this -> gfx);

  Sprite* btn_prev = new Sprite();
  btn_prev -> set(500, 400, BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_PREV);
  btn_prev -> setFilename("/85px/prev.jpg");
  btn_prev -> setGFX(this -> gfx);

  Sprite* btn_swap = new Sprite();
  btn_swap -> set(700, 400, BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_SWAP);
  btn_swap -> setFilename("/85px/prev.jpg");
  btn_swap -> setGFX(this -> gfx);

  navigation_buttons[0] = btn_prev;
  navigation_buttons[1] = btn_next;
  navigation_buttons[2] = btn_swap;
  A_DBG("sprite manager construction complete");
}

Sprite* SpriteManager::add_button(int id, char* filename){
  A_DBG("Adding button %d to array", id);
  
  if (this -> btn_count > this -> max_capacity) {
    A_ERR("Button limit reached!");
    return NULL;
  }
  
  int page = id / this -> btn_per_page;
  if(page >= max_page) {
    max_page = page;
  }

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
    this -> buttons = temp_buttons;

    //setting new, random, uninitialized memory blocks to null
    A_DBG("Resized array to %d", new_size);
    for(int i = old_size; i < new_size; ++i){
      // A_DBG("setting %d to nullptr", i);
      this -> buttons[i] = nullptr;
    }
  }

  Sprite* new_btn = new Sprite();
  this -> buttons[this -> btn_count++] = new_btn;
  A_DBG("Adding button of id %d and icon %s on position %d", id, filename, (this -> btn_count - 1));

  int row = (id % this -> btn_per_page) / this -> btn_per_row;
  int icon_x = (id % this -> btn_per_row) * 100 + this -> btn_offset;
  int icon_y = row * 100 + this -> btn_offset;

  new_btn -> set(icon_x, icon_y, BUTTON_WIDTH, BUTTON_HEIGHT, id);
  new_btn -> setFilename(filename);
  new_btn -> setGFX(gfx);
  
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
//works for a small number of buttons.
void SpriteManager::clear_buttons(){
  for (int i = 0; i < this -> btn_count; ++i) {
    delete this -> buttons[i];
    this -> buttons[i] = nullptr;
    A_DBG("deleted btn on pos %d", i);
  }
  this -> btn_count = 0;
}

void SpriteManager::switchPage(int code){
  if (code == BUTTON_NEXT) {
    if (this -> current_page == this -> max_page){
      this -> current_page = 0;
    }else{
      this -> current_page += 1; //++?
    }
  }else if (code == BUTTON_PREV) {
    if (this -> current_page == 0){
      this -> current_page = this -> max_page;
    }else{
      this -> current_page -= 1;
    }
  }
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

Sprite** SpriteManager::getNavButtons(){
  return this -> navigation_buttons;
}

SpriteManager::~SpriteManager() {
  for (unsigned int i = 0; i < btn_capacity; ++i) {
      if (buttons[i] != nullptr) {
          delete buttons[i];
      }
  }
  free(buttons);
}

int SpriteManager::getCurrentPage(){
  return this -> current_page;
}

void SpriteManager::setCurrentPage(int value){
  this -> current_page = value;
}

int SpriteManager::getMaxPage(){
  return this -> max_page;
}

void SpriteManager::setMaxPage(int value){
  this -> max_page = value;
}