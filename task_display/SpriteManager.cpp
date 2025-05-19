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
  this -> folder_page = 0;
  this -> max_page = 0;

  this -> x_limit = BNT_PER_ROW * (BUTTON_WIDTH + BTN_OFFSET) + BTN_OFFSET;
  this -> y_limit = BTN_PER_PAGE/BNT_PER_ROW * (BUTTON_HEIGHT + BTN_OFFSET) + BTN_OFFSET;

  if (this -> buttons == NULL) {
    A_ERR("Error at allocating buttons array");
  }

  for (int i = 0; i < this -> btn_capacity; ++i) {
    this -> buttons[i] = nullptr;
  }

  //!create function for init nav_buttons
  Sprite* btn_next = new Sprite();
  btn_next -> set(250, 400, BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_NEXT);
  btn_next -> setIconPath("/85px/next.jpg");
  btn_next -> setGFX(this -> gfx);

  Sprite* btn_prev = new Sprite();
  btn_prev -> set(350, 400, BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_PREV);
  btn_prev -> setIconPath("/85px/prev.jpg");
  btn_prev -> setGFX(this -> gfx);

  Sprite* btn_swap = new Sprite();
  btn_swap -> set(450, 400, BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_SWAP);
  btn_swap -> setIconPath("/85px/swap.jpg");
  btn_swap -> setGFX(this -> gfx);

  navigation_buttons[0] = btn_prev;
  navigation_buttons[1] = btn_next;
  navigation_buttons[2] = btn_swap;

   for (int i = 0; i < MAX_FOLDER_SIZE; ++i) {
    this -> folder_buttons[i] = nullptr;
  }
  A_DBG("sprite manager construction complete");
}

int SpriteManager::get_id_by_coords(int x, int y){
  if (x > this -> x_limit     ||
      x < this -> btn_offset  ||
      y > this -> y_limit     ||
      y < this -> btn_offset) {
    return UNABLE;
  }
  //shouldnt i add btn offset here?
  int col = (x ) / (BUTTON_WIDTH + this -> btn_offset);
  int row = (y ) / (BUTTON_HEIGHT + this -> btn_offset);

  if (col < 0 || col >= btn_per_row) {
    return UNABLE;
  }

  int rows_per_page = this -> btn_per_page / this -> btn_per_row;
  if (row < 0 || row >= rows_per_page) {
    return UNABLE;
  }
  int final_id = (row * this -> btn_per_row + col);
  if (!this->folder_page) {
    final_id += (this -> btn_per_page * this -> current_page);
  }

  A_DBG("Calculated id is %d", final_id);
  if (final_id < 0 || final_id >= this -> btn_capacity) {
    return UNABLE;
  }
  // A_DBG("touch at (%d,%d) translates to col=%d, row=%d → id=%d", x, y, col, row, final_id);
  return final_id;
}

Sprite* SpriteManager::add_button(int id, char* filename, bool folder_flag){
  A_DBG("Adding button %d to array", id);
  
  if (this -> btn_count >= this -> max_capacity) {
    A_ERR("Button limit reached!");
    return NULL;
  }

  if (id >= this -> max_capacity) {
    A_ERR("Button limit reached!");
    return NULL;
  }
  
  int page = id / this -> btn_per_page;
  if(page >= max_page) {
    max_page = page;
  }

  if(id >= this -> btn_capacity){
    A_DBG("Reached buttons array size limit!");

    int old_size = this -> btn_capacity;
    int new_size = 2 * old_size;
    if (new_size > this -> max_capacity) {
      new_size = this -> max_capacity;
    }
    if (id >= new_size){
      A_DBG("Size increase was not enough");
      new_size = id + 1;
    }

    A_DBG("Updating buttons array to new size %d", new_size);
    
    Sprite** temp_buttons = (Sprite**)realloc(this->buttons, new_size * sizeof(Sprite*));
    if (temp_buttons == NULL) {
      A_ERR("Realloc call for buttons array failed");
      return NULL;
    }

    this -> buttons = temp_buttons;
    this -> btn_capacity = new_size;
    A_DBG("Resized array to %d", new_size);
    
    //setting new, random, uninitialized memory blocks to null
    for(int i = old_size; i < this -> btn_capacity; ++i){
      // A_DBG("setting %d to nullptr", i);
      this -> buttons[i] = nullptr;
    }
  }

  Sprite* new_btn = new Sprite();

  if (this->buttons[id] == nullptr) {
    this->btn_count++;
  } else {
    A_DBG("Deleting button for replacement");
    delete this -> buttons[id];
    this -> buttons[id] = nullptr;
  }

  this -> buttons[id] = new_btn;
  A_DBG("Adding button of id %d and icon %s on position %d", id, filename, id);

  int row = (id % this -> btn_per_page) / this -> btn_per_row;
  int icon_x = (id % this -> btn_per_row) * (BUTTON_WIDTH + this -> btn_offset) + this -> btn_offset;
  int icon_y = row *(BUTTON_HEIGHT + this -> btn_offset) + this -> btn_offset;

  new_btn -> set(icon_x, icon_y, BUTTON_WIDTH, BUTTON_HEIGHT, id, folder_flag);
  // A_DBG("Set button %d to (%d, %d)", id, icon_x, icon_y);
  new_btn -> setIconPath(filename);
  new_btn -> setGFX(gfx);
  
  A_DBG("Succesfully added button\n");
  return new_btn;
}

//folders have a hard button limit. id = 100*folder_button_id + button_id
Sprite* SpriteManager::add_folder_button(int id, char* filename){
  int adjusted_id = id%100;
  A_DBG("Adding button %d to folder array", adjusted_id);

  Sprite* new_btn = new Sprite();
  //replace button if it takes up requested space
  if (this->folder_buttons[adjusted_id] != nullptr) {
    A_DBG("Deleting button for replacement");
    delete this -> folder_buttons[adjusted_id];
    this -> folder_buttons[adjusted_id] = nullptr;
  }
  this -> folder_buttons[adjusted_id] = new_btn;
  A_DBG("Adding button of id %d and icon %s on position %d", id, filename, adjusted_id);

  int row = (id % this -> btn_per_page) / this -> btn_per_row;
  int icon_x = (id % this -> btn_per_row) * (BUTTON_WIDTH + this -> btn_offset) + this -> btn_offset;
  int icon_y = row *(BUTTON_HEIGHT + this -> btn_offset) + this -> btn_offset;
  //create folder button
  new_btn -> set(icon_x, icon_y, BUTTON_WIDTH, BUTTON_HEIGHT, adjusted_id);
  new_btn -> setIconPath(filename);
  new_btn -> setGFX(gfx);
  
  A_DBG("Succesfully added button\n");
  return new_btn;
}

//!UPDATE THESE TO SEARCH FOR THE ID IN THE LIST
bool SpriteManager::update_button(int id, char* filename){
  if (id < 0 || id >= this->btn_capacity || this->buttons[id] == nullptr) {
    return false;
  }
  this -> buttons[id] -> setIconPath(filename);
  return true;
}

bool SpriteManager::delete_button(int id){
  if (id < 0 || id >= this -> btn_capacity) {
    return false;
  }

  if((this -> buttons[id] != nullptr)){
    delete this -> buttons[id];
    this -> buttons[id] = nullptr;
    this -> btn_count -= 1;
    return true;
  }

  return false;
}

/*
    int max_id = -1;
    for (int i = this -> btn_capacity - 1; i >= 0; --i) {
      if (this -> buttons[i] != nullptr){
        max_id = i;
        break;
      }
    }

    A_DBG("Max btn is %d", max_id);

    if ((max_id != -1) && (max_id <= ((this->btn_capacity / 2) - 1))){
      int new_size = this -> btn_capacity / 2;
      Sprite** temp_buttons = (Sprite**)realloc(this->buttons, new_size * sizeof(Sprite*));
      if (temp_buttons == NULL) {
        A_ERR("Realloc call for buttons array failed");
        return NULL;
      }
      this -> buttons = temp_buttons;
    }
*/

//works for a small number of buttons. when to resize?
void SpriteManager::clear_buttons(){
  for (int i = 0; i < this -> btn_capacity; ++i) {
    if (this -> buttons[i] != nullptr){
      delete this -> buttons[i];
      this -> buttons[i] = nullptr;
      A_DBG("deleted btn on pos %d", i);
    }
  }
  this -> btn_count = 0;
}

void SpriteManager::clear_folder_buttons(){
  for (int i = 0; i < MAX_FOLDER_SIZE; ++i) {
    if (this -> folder_buttons[i] != nullptr){
      delete this -> folder_buttons[i];
      this -> folder_buttons[i] = nullptr;
      A_DBG("deleted folder button on pos %d", i);
    }
  }
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

unsigned int SpriteManager::getFolderPage(){
  return this -> folder_page;
}

void SpriteManager::setFolderPage(unsigned int value){
  this -> folder_page = value;
}

Sprite** SpriteManager::getFolderButtons(){
  return this -> folder_buttons;
}