#include "Display.h"
// #include <TAMC_GT911.h>

int touch_last_x = 0, touch_last_y = 0;
int pos[2] = { 0, 0 };


int icon_x = 0, icon_y = 0;

Arduino_ESP32RGBPanel *bus = new Arduino_ESP32RGBPanel(
  GFX_NOT_DEFINED /* CS */, GFX_NOT_DEFINED /* SCK */, GFX_NOT_DEFINED /* SDA */,
  40 /* DE */, 41 /* VSYNC */, 39 /* HSYNC */, 42 /* PCLK */,
  45 /* R0 */, 48 /* R1 */, 47 /* R2 */, 21 /* R3 */, 14 /* R4 */,
  5 /* G0 */, 6 /* G1 */, 7 /* G2 */, 15 /* G3 */, 16 /* G4 */, 4 /* G5 */,
  8 /* B0 */, 3 /* B1 */, 46 /* B2 */, 9 /* B3 */, 1 /* B4 */
);

// Uncomment for ST7262 IPS LCD 800x480
Arduino_RPi_DPI_RGBPanel *gfx = new Arduino_RPi_DPI_RGBPanel(
  bus,
  800 /* width */, 0 /* hsync_polarity */, 8 /* hsync_front_porch */, 4 /* hsync_pulse_width */, 8 /* hsync_back_porch */,
  480 /* height */, 0 /* vsync_polarity */, 8 /* vsync_front_porch */, 4 /* vsync_pulse_width */, 8 /* vsync_back_porch */,
  1 /* pclk_active_neg */, 16000000 /* prefer_speed */, true /* auto_flush */);

TAMC_GT911 ts = TAMC_GT911(TOUCH_SDA, TOUCH_SCL, TOUCH_INT, TOUCH_RST, TOUCH_WIDTH, TOUCH_HEIGHT);
SpriteManager sprite_manager = SpriteManager(gfx,
                                            INIT_SPRITE_COUNT, 
                                            MAX_SPRITE_COUNT,
                                            BUTTONS_PER_PAGE,
                                            BUTTONS_PER_ROW, 
                                            BUTTON_VERTICAL_OFFSET,
                                            BUTTON_HORIZONTAL_OFFSET);

static int jpegDrawCallback(JPEGDRAW *pDraw) {
  // Serial.printf("Draw pos = %d,%d. size = %d x %d\n", pDraw->x, pDraw->y, pDraw->iWidth, pDraw->iHeight);
  gfx->draw16bitBeRGBBitmap(pDraw->x, pDraw->y, pDraw->pPixels, pDraw->iWidth, pDraw->iHeight);
  return 1;
}

void drawLog(const char *filename, int x, int y) {
  A_DBG("Drawing image %s at x = %d, y = %d\n", filename, x, y);
}

void touch_init(void) {
  Wire.begin(TOUCH_SDA, TOUCH_SCL);
  ts.begin();
  ts.setRotation(TOUCH_ROTATION);
}

/*Get coordinates of a touch. Updates x and y coordinates in the `pos` 
array for new touches alongside a return value of 1. Otherwise coords
are set to -1 and a value of 0 is returned. */
int get_pos() {
  ts.read();

  if (ts.isTouched && pos[0] != ts.points[0].x && pos[1] != ts.points[0].y) {
    pos[0] = ts.points[0].x;
    pos[1] = ts.points[0].y;
    // Serial.println("touched");

    // Serial.print(",x = ");
    // Serial.print(pos[0]);
    // Serial.print(", y = ");
    // Serial.print(pos[1]);
    // Serial.println();

    ts.isTouched = false;

    return 1;
  } else {
    pos[0] = -1;
    pos[1] = -1;
    return 0;
  }
}

void draw_text(int text_x, int text_y, int text_size, int text_color, const char *text) {
  gfx->setTextSize(text_size);
  gfx->setTextColor(text_color);
  gfx->setCursor(text_x, text_y);
  gfx->println(text);
}

void clear_screen() {
  gfx->fillScreen(BLACK);
}

void draw_nav_btns(){
  Sprite** nav_btn = sprite_manager.getNavButtons();
  for(int i = 0; i < NAV_BTN_COUNT; ++i){ 
    if(nav_btn[i] != nullptr){
      int id = nav_btn[i] -> getId();
      char* fname = nav_btn[i] -> getIconPath();
  
      // A_DBG("Now drawing %d, of path %s\n", id, fname);
      nav_btn[i] -> draw(jpegDrawCallback);
    }
  }
}

/*Draw main icon scene*/
void draw_main_screen() {
  clear_screen();
  gfx->setCursor(0, 0);
  // draw_nav_btns();
  if (xButtonsMutex != NULL) {
    if (xSemaphoreTake(xButtonsMutex, portMAX_DELAY) != pdTRUE){
      A_ERR("Failed to take buttons mutex");
    }

    Sprite** buttons = sprite_manager.getButtons();
    
    int page = sprite_manager.getCurrentPage();
    int start_index = page * BUTTONS_PER_PAGE;
    int end_index = start_index + BUTTONS_PER_PAGE;
    if (end_index > sprite_manager.getCapacity()) {
      end_index = sprite_manager.getCapacity();
    }

    for(int i = start_index; i < end_index; ++i){ 
      if (buttons[i] != nullptr) {
        // int id = buttons[i] -> getId();
        // char* fname = buttons[i] -> getFilename();
    
        // // if(buttons[i] -> getId() / BUTTONS_PER_PAGE == page){
        //   // }
        // A_DBG("Now drawing %d, of path %s", id, fname);
        buttons[i] -> draw(jpegDrawCallback);
      }
    }

    if (xSemaphoreGive(xButtonsMutex) != pdTRUE) {
      A_ERR("Failed to give buttons mutex");
    }
  }
}
//todo: clear screen in draw_main_screen fn
void draw_folder_contents() {
  clear_screen();
  gfx->setCursor(0, 0);
  // draw_nav_btns();
  // A_DBG("Drawing folder contents");
  if (xButtonsMutex != NULL) {
    if (xSemaphoreTake(xButtonsMutex, portMAX_DELAY) != pdTRUE){
      A_ERR("Failed to take buttons mutex");
    }

    Sprite** folder_buttons = sprite_manager.getFolderButtons();
    // A_DBG("Folder page is %d", sprite_manager.getFolderPage());
    for(int i = 0; i < MAX_FOLDER_SIZE; ++i){ 
      if (folder_buttons[i] != nullptr) {
        // int id = folder_buttons[i] -> getId();
        // char* fname = folder_buttons[i] -> getIconPath();
        // A_DBG("Now drawing %d, of path %s", id, fname);
        folder_buttons[i] -> draw(jpegDrawCallback);
      }
    }

    if (xSemaphoreGive(xButtonsMutex) != pdTRUE) {
      A_ERR("Failed to give buttons mutex");
    }
  }
}

const unsigned int FILENAME_SIZE = 13;
/**
  * Initialize icon information.
  *
  * \param[in] icon_directory The path to the direcotry where icons are stored
  * icons follow a specific naming format: {icon_id}.jpg
  * \return False if an error was encountered, True otherwise
  */
bool init_icons(const char* icon_directory){
  unsigned icon_x = 0, icon_y = 0, row = 0;
  unsigned const int DIR_PATH_SIZE = strlen(icon_directory)+1;
  SdFile dir;
  if(!dir.open(icon_directory)){
    A_ERR("ERROR: failed to open directory for icon initialization\n");
    return false;
  }

  SdFile file;
  while (file.openNext(&dir, O_READ)) {
    char filename[FILENAME_SIZE], copy_filename[FILENAME_SIZE + DIR_PATH_SIZE]; 
    file.getName(filename, sizeof(filename));
    //The generated string has a length of at most n-1, leaving space for the additional terminating null character.
    //could also just use strlen(copy_filename)
    snprintf(copy_filename, strlen(filename) + DIR_PATH_SIZE + 1, "%s/%s", icon_directory, filename);
    A_DBG("Display filepath will be %s", copy_filename);

    // A_DBG("Currently processing %s\n", filename);
    //get pointer to the start of the extension to eliminate it
    char* terminator;
    if((terminator = strstr(filename, ".jpg")) != NULL){
      *terminator = '\0';
    }else{
      A_ERR("Icon file has wrong format\n");
      continue;
    }
    // A_DBG("After processing filename is %s\n", filename);

    int btn_id;
    char* pEnd;
    /* convert the string id into an int. 0 is a special case because of
    error return type of strtol.*/
    if ((btn_id = strtol(filename, &pEnd, 10)) == 0L && strcmp(filename, "0")){
      //TODO: check for out of limits?
      A_ERR("ERROR: strtol failed conversion\n");
      continue;
    }
    A_DBG("ID of this button will be %d", btn_id);

    Sprite* btn = sprite_manager.add_button(btn_id, copy_filename);
    if (btn == NULL){
      A_ERR("Button creation failed");
    }
    
    file.close();
  }
  dir.close();
  return true;
}


bool init_icons_from_config(const char* config_path, bool is_icon_folder){
  SdFile file;
  const int max_line_size = 100;
  char line[max_line_size], line_copy[max_line_size];
  size_t n = 0;
  unsigned int id = 0, folder_flag = 0;
  
  if (!sd.exists(config_path)) {
    A_ERR("File does not exist");
    return false;
  }

  if (!file.open(config_path, O_READ)) {
    A_ERR("Failed to open file");
    return false;
  }

  char* save_ptr = NULL;
  char* token;

  while ((n = file.fgets(line, sizeof(line))) > 0) {
    // Ensure we have at least one character.
    if (n < 1){
      A_WRN("Empty line");
      continue;
    }
  
    if (line[n - 1] == '\n') {
      //remove endlines
      line[n-1] = '\0';
    }
  
    // A_DBG("Line is %s", line);

    //get filename
    token = strtok_r(line, " ", &save_ptr);
    if(token == NULL){
      A_ERR("failed to extract picture path. Wrong line format");
      continue;
    }
    // A_DBG("filename is %s", token);
    strcpy(line_copy, token);
    //get the stringified id
    token = strtok_r(NULL, " ", &save_ptr);

    if (token == NULL) {
      A_ERR("failed to extract button id. Wrong line format");
      continue;
    }
    //convert string key value to decimal value
    id = strtol(token, NULL, 10);
    if (id == 0L && strcmp(token, "0")) {
      A_ERR("stroull failed for id token conversion");
      continue;
    }
    //get folder flag
    token = strtok_r(NULL, " ", &save_ptr);

    if (token == NULL) {
      A_ERR("failed to extract folder flag. Wrong line format");
      continue;
    }

    folder_flag = strtol(token, NULL, 10);
    if (folder_flag == 0L && strcmp(token, "0")) {
      A_ERR("stroull failed for dir flag token conversion");
      continue;
    }

    // A_DBG("filename is %s | id is %d | folder flag is %d", line_copy, id, folder_flag);

    if (xButtonsMutex != NULL) {
      if (xSemaphoreTake(xButtonsMutex, portMAX_DELAY) != pdTRUE){
        A_ERR("Failed to take buttons mutex");
      }

      Sprite* btn = nullptr;
      if (is_icon_folder) {
        // A_DBG("Adding folder button");
        btn = sprite_manager.add_folder_button(id, line_copy);
      }else{
        btn = sprite_manager.add_button(id, line_copy, folder_flag);
      }

      if (btn == nullptr){
        A_ERR("Button creation failed");
      }

      if (xSemaphoreGive(xButtonsMutex) != pdTRUE) {
        A_ERR("Failed to give buttons mutex");
      }
    }
  }
  // file.close();
  return true;
}

bool swap_page(int page_code, unsigned int folder_page){
  note_activity();
  if (folder_page > 0){
    A_DBG("User pressed a nav button in folder mode");
    sprite_manager.clear_folder_buttons();
    sprite_manager.setFolderPage(0);
    draw_main_screen();
    return false;
  }
  sprite_manager.switchPage(page_code);
  if (sprite_manager.getMaxPage() > 0) {
    draw_main_screen();
  }
  return true;
}

static bool prev_touched = false, touch_state = false;
static int start_x = -1, start_y = -1, end_x = -1, end_y = -1;
static unsigned long start_time;

SwipeType track_swipe() {
  BaseType_t xStatus = xSemaphoreTake(xTouchSemaphore, pdMS_TO_TICKS(100));
  if (xStatus != pdTRUE) {
    // A_WRN("Failed to take touch semaphore");
    return SWIPE_FAIL;
  }
  
  //track touch until break condition
  ts.read();
  touch_state = ts.isTouched;
  // A_DBG("Touch state is %d, prev_touched is %d", touch_state, prev_touched);
  //first touch of swipe
  xStatus = xSemaphoreGive(xTouchSemaphore);
  if (xStatus != pdTRUE) {
    A_WRN("Failed to give touch semaphore");
  }

  if (touch_state && !prev_touched) {
    prev_touched = true;
    start_x = ts.points[0].x;
    start_y = ts.points[0].y;
    start_time = millis();
    // A_DBG("Start of swipe at %d, %d, %lu", start_x, start_y, start_time);
    return SWIPE_START;
  } else if (touch_state && prev_touched) {
    end_x = ts.points[0].x;
    end_y = ts.points[0].y;
    return SWIPE_TRACK;
  } else if (!touch_state && prev_touched) {
    end_x = ts.points[0].x;
    end_y = ts.points[0].y;
    prev_touched = false;
    unsigned long end_time = millis();
    // A_DBG("Swipe ending at %d, %d, %lu", end_x, end_y, end_time);
    if (start_x != -1 && end_x != -1 && start_y != -1 && end_y != -1) {
      SwipeType result = execute_swipe(start_x, start_y, end_x, end_y, start_time, end_time);
      start_x = start_y = end_x = end_y = -1;
      return result;
    } else {
      A_ERR("Invalid coordinates for swipe");
    }
  }
  // vTaskDelay(pdMS_TO_TICKS(30));
  return SWIPE_FAIL;
}

SwipeType execute_swipe(int sx, int sy, int ex, int ey, unsigned long st, unsigned long et) {
  int dx = ex - sx, dy = ey - sy;
  unsigned long dt = et - st;
  if (dt < 100 || abs(dx) < 30) {
    pos[0] = ex;
    pos[1] = ey;
    A_DBG("Screen pressed at %d, %d", pos[0], pos[1]);
    return SwipeType::SCREEN_PRESS;
  }
  if (dt > 2000) {
    //invalidate slow swipe
    A_DBG("Swipe too slow, dt = %lu", dt);
    return SwipeType::SWIPE_FAIL;
  }
  //swipe up to change mode?
  unsigned int folder_page = sprite_manager.getFolderPage();
  if (dx > 0) {
    swap_page(BUTTON_PREV, folder_page);
    A_DBG("Swiped left");
    return SwipeType::SWIPE_SUCCESS;
  } else if (dx < 0) {
    swap_page(BUTTON_NEXT, folder_page);
    A_DBG("Swiped right");
    return SwipeType::SWIPE_SUCCESS;
  } else {
    A_WRN("bad delta for swipe");
  }
  return SwipeType::SWIPE_FAIL;
}

void draw_time(char *time_string, int x, int y, int size)
{
  char* save_ptr = NULL;
  char* token;
  token = strtok_r(time_string, " ", &save_ptr);
  if(token == NULL){
    A_ERR("failed to extract first time token.");
    return;
  }

  // int month_day_size = (size > 0 ? size - 1 : 1);
  // A_DBG("Drawing time at %d, %d with size %d", x, y, size);
  gfx -> setCursor(x, y);
  gfx -> setTextSize(size);
  gfx -> setTextColor(WHITE);
  gfx -> printf("%s ", token); // Print the first token (month-day)
  gfx -> setTextSize(2);
  int curs_x = gfx -> getCursorX();
  int curs_y = gfx -> getCursorY();
  gfx -> setCursor(curs_x, curs_y + 50); // Move cursor down for the next line
  token = strtok_r(NULL, " ", &save_ptr);
  gfx -> println(token);
}