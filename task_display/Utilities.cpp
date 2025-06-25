
#include "config.h"
#include "Utilities.h"
#include <stdio.h>
// #include <avr/pgmspace.h>

SdFat sd;
SdFile file_obj;

/*lookup table used in computing crc value
more time efficient compared to a polynomoial version with no lookup.
table is stored in flash memory to save RAM.*/
const uint32_t PROGMEM crc_table[16] = {
  0x00000000, 0x1db71064, 0x3b6e20c8, 0x26d930ac,
  0x76dc4190, 0x6b6b51f4, 0x4db26158, 0x5005713c,
  0xedb88320, 0xf00f9344, 0xd6d6a3e8, 0xcb61b38c,
  0x9b64c2b0, 0x86d3d2d4, 0xa00ae278, 0xbdbdf21c
};

USBHIDKeyboard Keyboard;
USBHIDMouse Mouse;
USBHIDConsumerControl Consumer;

QueueHandle_t send_queue;
QueueHandle_t conf_queue;
SemaphoreHandle_t xPrintMutex = NULL;
SemaphoreHandle_t xButtonsMutex = NULL;
// SemaphoreHandle_t xClientMutex = NULL;
SemaphoreHandle_t xConnEventGrpMutex = NULL;
SemaphoreHandle_t xConnCheckMutex = NULL;
SemaphoreHandle_t xTouchSemaphore = NULL;
QueueHandle_t ui_updates_queue;

TimerHandle_t clock_timer, inactivity_timer;
const int timestamp_size = 30;
char current_timestamp[timestamp_size];
bool configured_timestamp = false;
struct tm time_info;

unsigned int client_cmd_id = 0;

void start_activity()
{
  BaseType_t xStatus = xSemaphoreTake(xTouchSemaphore, pdMS_TO_TICKS(100));
  if (xStatus != pdTRUE) {
    A_WRN("Failed to take touch semaphore");
  }
  xTimerStop(inactivity_timer, 0);
  xTimerStop(clock_timer, 0);
}

void end_activity()
{
  BaseType_t xStatus = xSemaphoreGive(xTouchSemaphore);
  if (xStatus != pdTRUE) {
    A_WRN("Failed to give touch semaphore");
  }
  xTimerReset(inactivity_timer, 0);
}

void note_activity()
{
  A_DBG("Reset inactivity timer");
  xTimerReset(inactivity_timer, 0);
  xTimerStop(clock_timer, 0);
}

bool reset_inactivity(){
  UI_update update;
  BaseType_t xStatus;
  if (xTimerIsTimerActive(clock_timer) != pdFALSE) {
      note_activity();
      update.type = TIME_UPDATE;
      //status to signal that main screen should be redrawn
      update.status = 1;
      strcpy(update.message, "Touch detected.");
      xStatus = xQueueSend(ui_updates_queue, &update, portMAX_DELAY);
      if(xStatus != pdPASS){
        A_ERR("Failed to send time in ui queue");
      }
      return true;
    }
  // reset inactivity timer on touch
  xTimerReset(inactivity_timer, 0);
  return false;
}

void clock_callback(TimerHandle_t xTimer)
{
    BaseType_t xStatus;
    if (update_timestamp()){
        // A_DBG("Updated timestamp to %s", current_timestamp);
        UI_update update;
        update.type = TIME_UPDATE;
        update.status = 0;
        strcpy(update.message, current_timestamp);
        xStatus = xQueueSend(ui_updates_queue, &update, portMAX_DELAY);
        if (xStatus != pdPASS){
            A_ERR("Failed to send time in ui queue");
        }
    }
}

void inactivity_callback(TimerHandle_t xTimer){
  //inactivity detected. start clock timer to send ui updates
  A_DBG("Entering inactivity");
  xTimerStart(clock_timer, 0);
}

unsigned long crc_update(unsigned long crc, byte data) {
  byte tbl_idx;
  tbl_idx = crc ^ (data >> (0 * 4));
  crc = pgm_read_dword_near(crc_table + (tbl_idx & 0x0f)) ^ (crc >> 4);
  tbl_idx = crc ^ (data >> (1 * 4));
  crc = pgm_read_dword_near(crc_table + (tbl_idx & 0x0f)) ^ (crc >> 4);
  return crc;
}

/*Caculate CRC32 value of a known length bitstring 
(binary data cannot be NULL terminated so we rely on the string length
for string traversal).*/
unsigned long crc_string(const char* s, size_t length) {
  unsigned long crc = ~0L;  // initialize with all bits set
  for (size_t i = 0; i < length; ++i) {
    crc = crc_update(crc, s[i]);  // process each byte
  }
  return ~crc;  // final complement of the CRC
}

/*Create the file and the path to it if it doesn't exist. 
Finds the last `/` character to split filename from directory path
Path must start with a `/` to denote the root directory of the SD card*/
bool get_file_obj(const char* filename) {
  int slash_pos = -1;
  char* directory = NULL;
  //get the last slash in the path
  for (int i = strlen(filename) - 1; i >= 0; --i) {
    if (filename[i] == '/') {
      slash_pos = i;
      break;
    }
  }
  //no slash found
  if (slash_pos == -1) {
    A_ERR("Invalid filename");
    return false;
  }
  //get directory path
  if (slash_pos > 0) {
    directory = strndup(filename, slash_pos);
    A_DBG("Directory is %s\n", directory);
  } else {
    A_DBG("Requested directory is root");
  }
  //create directory if it doesn't exist
  A_DBG("Moving onto directory creation\n");
  if (!sd.exists(directory)) {
    A_DBG("Parent dir does not exist. Creating it");
    if (!sd.mkdir(directory)) {
      A_ERR("Failed to create directory");
      return false;
    } else {
      A_DBG("Successfully created directory");
    }
  } else {
    A_DBG("Directory already exists");
  }
  //opening or creating file
  A_DBG("Attempting to open or create %s\n", filename);
  if (sd.exists(filename)) {
    A_DBG("File already exists");
  }
  /*open file in approapriate mode (append will be called 
  in case the writing process fails mid way)*/


  if (!file_obj.open(filename, O_RDWR | O_CREAT | O_TRUNC)) {
    A_ERR("Error opening or creating file");
    return false;
  }
  A_DBG("File opened successfully");
  if (directory) {
    free(directory);
  }
  return true;
}

/*thread safe logging function
TODO:alternative mutexes for tasks that also use mutexes and call this function?*/
void vPrintString(const char* pString, bool debug) {
  if (debug) {
    //created mutex if it doesn't exist
    if (xPrintMutex == NULL) {
      // xPrintMutex = xSemaphoreCreateMutex();
      A_ERR("xPrintMutex hasn't been initialized\n");
      return;
    }
    //Perform a blocking wait to acquire mutex
    if (xSemaphoreTake(xPrintMutex, portMAX_DELAY) == pdTRUE) {
      A_DBG("%s", pString);
      //Release mutex
      xSemaphoreGive(xPrintMutex);
    }
  }
}


/*Uses USBHIDKeyboard library to emulate harware level key presses.
The sequence argument is composed of a series of commands separated 
by the `+` character that can be any of the following:

wNUMERICAL_VALUE  - wait for `NUMERICAL_VALUE` miliseconds. essentially a delay
dKEY_VALUE        - press down the key represented in decimal value by `KEY_VALUE`
uKEY_VALUE        - release the key represented in decimal value by `KEY_VALUE`
r                 - release all pressed keys
pVALUE            - print VALUE string

Keyboard modifiers (special keys like ALT, ESCAPE etc.) need to be handled by the 
Raw variation of the library function.
*/
void hard_press(char* sequence) {
  //first split the string by '+' using thread safe strtok
  char* save_ptr = NULL;
  char* token = NULL;
  char cmd_prefix[3];

  token = strtok_r(sequence, "+", &save_ptr);

  while (token) {
    //get command type. prefix has a fixed length of 2 characters
    strncpy(cmd_prefix, token, 2);
    cmd_prefix[2] = '\0';  // null-terminate the string
    A_DBG("Event is %s\n", cmd_prefix);
    //char* pEnd;

    unsigned long int code = 0;
    if (strlen(token) > 2) {
      //convert string key value to decimal value
      code = strtoul(token + 2, NULL, 10);
      if (code == 0L) {
        A_ERR("stroull failed for token %s conversion", token);
      } else {
        A_DBG("Token is %s Code value is %lu\n", token, code);
      }
    }
    //perform the appropriate action given the command type
    if (!strcmp(cmd_prefix, "ku")) {
      char c = code;
      Keyboard.release(code);
      A_DBG("regular key_up selected for char %c\n", c);
    }
    else if (!strcmp(cmd_prefix, "kd")) {
      char c = code;
      Keyboard.press(code);
      A_DBG("regular key_down selected for char %c\n", c);
    }
    else if (!strcmp(cmd_prefix, "su")) {
      char c = code;
      Keyboard.releaseRaw(code);
      A_DBG("special key_up selected for code %lu\n", code);
    }
    else if (!strcmp(cmd_prefix, "sd")) {
      char c = code;
      Keyboard.pressRaw(code);
      A_DBG("special key_down selected for code %lu\n", code);
    }
    else if (!strcmp(cmd_prefix, "cu")) {
      Consumer.release();
      A_DBG("mouse button up selected for code %lu\n", code);
    } 
    else if (!strcmp(cmd_prefix, "cd")) {
      Consumer.press(code);
      A_DBG("mouse button down selected for code %lu\n", code);
    }
    else if (!strcmp(cmd_prefix, "mm")) {
      int x = 0, y = 0;
      if (sscanf(token, "mm(%d,%d)", &x, &y) == 2) {
        A_DBG("Mouse move to coords x = %d, y = %d\n", x, y);
        x*=3, y*=3; //scale the mouse movement to a more usable value
        while (x || y) {
          int partial_move_x = x > 127 ? 127 : (x < -127 ? -127 : x);
          int partial_move_y = y > 127 ? 127 : (y < -127 ? -127 : y);
          Mouse.move(partial_move_x, partial_move_y);
          x -= partial_move_x;
          y -= partial_move_y;
        }
      } else {
        A_ERR("Failed to parse mouse move coordinates from %s", token);
      }
    } 
    else if (!strcmp(cmd_prefix, "wt")) {
      delay(code);
      A_DBG("delay selected for %lu ms\n", code);
    } 
    else if (!strcmp(cmd_prefix, "ra")) {
      Keyboard.releaseAll();
      A_DBG("release all selected\n");
    } 
    else if (!strcmp(cmd_prefix, "pt")) {
      Keyboard.printf(token + 2);

      A_DBG("print selected\n");
    } 
    else {
      A_WRN("Unknown command prefix: %s", cmd_prefix);
    }

    token = strtok_r(NULL, "+", &save_ptr);
  }
}

bool configure_timestamp(){
  if(WiFi.status() != WL_CONNECTED){
    A_WRN("Not connected to network. Failed to fetch current time\n");
    return false;
  }

  const char* ntpServer = "pool.ntp.org";
  const long  gmtOffset_sec = 2 * 3600; // GMT+2 offset in seconds
  const int   daylightOffset_sec = 3600;

  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);

  A_DBG("Fetched time from ntp\n");
  return true;
}

bool update_timestamp(){
  if(!configured_timestamp){
    if(configure_timestamp()){
      configured_timestamp = true;
    }else{
      return false;
    }
  }

  if(!getLocalTime(&time_info)){
    A_WRN("Failed to update time");
    return false;
  }
  // Serial.println(&timeinfo, "%A, %B %d %Y %H:%M:%S");
  if(!strftime(current_timestamp , timestamp_size, "%H:%M:%S %b-%d ", &time_info)){
    A_DBG("Failed to write time\n");
    return false;
  }
  return true;
}

/*Send an update struct instance to the ui_updates_queue
for the update task to process and display*/
void send_connection_status(int change){
  //change is defined as 1 if !connected -> connected and -1 otherwise
  BaseType_t xStatus;
  UI_update update;
  char* temp_text;
  switch(change){
    case -3:{
      temp_text = "Atempting reconnection.";
      break;
    }
    case -2:{
      temp_text = "Awaiting network connection.";
      break;
    }
    case -1:{
      temp_text = "Network Connected.";
      break;
    }
    case 0:{
      temp_text = "Awaiting server connection.";
      break;
    }
    case 1:{
      temp_text = "Server Connected.";
      break;
    }
    default:{
      temp_text = "Uknown connection case";
      A_ERR("ERROR invalid status value in send_connection_status\n");
      break;
    }
  }

  if(snprintf(update.message, sizeof(update.message), "%s", temp_text) < 0){
    A_ERR("update message creation failed in send_connection_status\n");
  }  

  update.type = CONNECTION_CHECK;
  update.status = change;

  xStatus = xQueueSend(ui_updates_queue, &update, portMAX_DELAY);
  if(xStatus != pdPASS){
    vPrintString("send_connection_status failed to send update to ui_updates_queue\r\n");
  }
}
