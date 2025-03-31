#ifndef _UTILITIES_H_
#define _UTILITIES_H_

#include "config.h"
#include <stdio.h>
// #include <avr/pgmspace.h>

SdFat sd;
SdFile file_obj;
char* paths[SPRITE_COUNT];

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

QueueHandle_t send_queue;
SemaphoreHandle_t xPrintMutex = NULL;


struct Header_data{
  unsigned int command_type;
  unsigned int command_id;
  unsigned int length;
  unsigned int crc_value;
};

struct Package_data{
  Header_data header;
  char contents[CHUNK_SIZE];
}data;


unsigned int client_cmd_id = 0;

unsigned long crc_update(unsigned long crc, byte data)
{
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
unsigned long crc_string(const char *s, size_t length) {
  unsigned long crc = ~0L;          // initialize with all bits set
  for (size_t i = 0; i < length; ++i) {
    crc = crc_update(crc, s[i]);    // process each byte
  }
  return ~crc;                      // final complement of the CRC
}

/*Create the file and the path to it if it doesn't exist. 
Finds the last `/` character to split filename from directory path
Path must start with a `/` to denote the root directory of the SD card*/
bool get_file_obj(const char* filename){
  int slash_pos = -1;
  char* directory = NULL;
  //get the last slash in the path
  for(int i = strlen(filename) - 1; i >= 0; --i){
    if(filename[i] == '/'){
      slash_pos = i;
      break;
    }
  }
  //no slash found
  if(slash_pos == -1){
    Serial.println("Invalid filename");
    return false;
  }
  //get directory path
  if(slash_pos > 0){
    directory = strndup(filename, slash_pos);
    Serial.printf("Directory is %s\n", directory);
  }else{
    Serial.println("Requested directory is root");
  }
  //create directory if it doesn't exist
  Serial.printf("Moving onto directory creation\n");
  if(!sd.exists(directory)){
    Serial.println("Parent dir does not exist. Creating it");
    if(!sd.mkdir(directory)){
      Serial.println("Failed to create directory");
      return false;
    }else{
      Serial.println("Successfully created directory");
    }
  }else{
    Serial.println("Directory already exists");
  }
  //opening or creating file
  Serial.printf("Attempting to open or create %s\n", filename);
  if(sd.exists(filename)){
    Serial.println("File already exists");
  }
  /*open file in approapriate mode (append will be called 
  in case the writing process fails mid way)*/


  if(!file_obj.open(filename, O_WRITE | O_CREAT | O_TRUNC)){
    Serial.println("Error opening or creating file");
    return false;
  }
  Serial.println("File opened successfully");
  if(directory){
    free(directory);
  }
  return true;
}

/*thread safe logging function
TODO:alternative mutexes for tasks that also use mutexes and call this function?*/
void vPrintString(const char *pString, bool debug = true){
  if(debug){
    //created mutex if it doesn't exist
    if(xPrintMutex == NULL){
      // xPrintMutex = xSemaphoreCreateMutex();
      Serial.printf("xPrintMutex hasn't been initialized\n");
      return;
    }
    //Perform a blocking wait to acquire mutex
    if(xSemaphoreTake(xPrintMutex, portMAX_DELAY) == pdTRUE){
      Serial.printf("%s", pString);
      //Release mutex
      xSemaphoreGive(xPrintMutex);
    }
  }
}
/*logging function that sends log messages to server
for debugging when connected to USB-native port (Serial not available)*/
void log(char* message){
  BaseType_t xStatus;

  Header_data header = {LOG_MESSAGE, 0, strlen(message), 0};
  Package_data data;
  data.header = header;
  strcpy(data.contents, message);

  xStatus = xQueueSend(send_queue, &data, portMAX_DELAY);
  if(xStatus != pdPASS){
    vPrintString("log failed to send data to send_queue.\r\n");
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
void hard_press(char* sequence){
  //first split the string by '+' using thread safe strtok
  char* save_ptr = sequence;
  char* token;

  token = strtok_r(sequence, "+", &save_ptr);
  char* log_msg = (char*)malloc(BUFFER_SIZE);
  if(log_msg == NULL){
    Serial.println("log_msg allocation failed");
  }

  while(token){
    //get command type
    char event = token[0];
    //char* pEnd;
    // printf("%s\n", token);
    
    unsigned long long int code = 0;
    if(strlen(token) > 1){
      //convert string key value to decimal value
      code = strtoull(token+1, NULL, 10);
      if(code == 0L){
        Serial.println("stroull failed for token conversion");
      }
    }
    //perform the appropriate action given the command type
    switch(event){
      case 'u':{
        char c = code;
        if(code >= 128){
          Keyboard.releaseRaw(code);
        }else{
          Keyboard.release(code);
        }

        sprintf(log_msg, "key_up selected for %c\n", c);
        // log(log_msg);
        break;
      } 
      case 'd':{
        char c = code;
        if(code >= 128){
          Keyboard.pressRaw(code);
        }else{
          Keyboard.press(code);
        }

        sprintf(log_msg, "key_down selected for %c\n", c);
        // log(log_msg);
        break;
      }
      case 'w':{
        delay(code);

        sprintf(log_msg, "delay selected for %ld\n", code);
        // log(log_msg);
        break;
      }
      case 'r':{
        Keyboard.releaseAll();

        sprintf(log_msg, "release all selected\n");
        // log(log_msg);
        break;
      }
      case 'p':{
        Keyboard.printf(token+1);
        sprintf(log_msg, "print selected\n");
        break;
      }
    }
    Serial.print(log_msg);
    token = strtok_r(NULL, "+", &save_ptr);
  }
  free(log_msg);
}

void init_paths(char* filename){
  const int max_line_size = 100;
  char line[max_line_size];
  int ln = 0;
  size_t n = 0;

  if(!sd.exists(filename)){
    Serial.println("File does not exist");
    return;
  }
  SdFile file;
  if(!file.open(filename, O_READ)){
    Serial.printf("Failed to open file in init_paths\n");
  }
  while ((n = file.fgets(line, sizeof(line))) > 0) {
    if(ln > SPRITE_COUNT){
      break;
    } 
    // Print line number.
    // Serial.print(ln);
    // Serial.print(": ");
    // Serial.print(line);
    if (line[n - 1] != '\n') {
      // Line is too long or last line is missing nl.
      line[n-1] = '\0';
      Serial.println(F(" <-- missing nl"));
      break;
    }
    paths[ln++] = strndup(line, n);
    if(paths[ln-1][n] != '\0'){
      Serial.printf("failed append of NULL\n");
    }
  }
}

void access_path(int icon_index){
  Keyboard.pressRaw(0xE3);
  Keyboard.pressRaw(HID_KEY_R);
  delay(500);

  Keyboard.releaseRaw(HID_KEY_GUI_LEFT);
  Keyboard.releaseRaw(HID_KEY_R);

  Keyboard.printf(paths[icon_index]);
  Keyboard.press(KEY_RETURN);
  delay(100);
  Keyboard.releaseAll();
}

const int MIN_DEBUG_LEVEL = 1;

void debug_print(const char* func_name, int debug_lvl, const char* fmt, ...){
  if(debug_lvl >= MIN_DEBUG_LEVEL){

    const char* level = NULL;
    switch(debug_lvl) {
      case 1:
          level = "DEBUG";
          break;
      case 2:
          level = "WARNING";
          break;
      case 3:
          level = "ERROR";
          break;
      default:
          level = "INFO";
          break;
    }
    Serial.printf("[%s] [%s] ", func_name, level);
    va_list argList;
    va_start(argList, fmt);
    vprintf(fmt, argList);
    va_end(argList);

    printf("\n");
  }
}

bool configured_timestamp = false;
struct tm time_info;

void configure_timestamp(){
  if(WiFi.status() != WL_CONNECTED){
    Serial.printf("Not connected to network. Failed to fetch current time\n");
  }

  const char* ntpServer = "pool.ntp.org";
  const long  gmtOffset_sec = 0;
  const int   daylightOffset_sec = 3600;

  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);

  Serial.printf("Updated time info\n");

}

const int timestamp_size = 30;
char current_timestamp[timestamp_size];

bool update_timestamp(){
  if(!getLocalTime(&time_info)){
    Serial.println("Failed to update time");
    return false;
  }
  // Serial.println(&timeinfo, "%A, %B %d %Y %H:%M:%S");
  if(!strftime(current_timestamp , timestamp_size, "%m-%d %H:%M:%S", &time_info)){
    Serial.printf("Failed to write time\n");
    return true;
  }else{
    Serial.printf("Succesfully wrote time %s\n", current_timestamp);
    return false;
  }
}

#define A_DBG(fmt, ...) { printf("[%s:%d]: " fmt "\n", __func__, __LINE__ __VA_OPT__(,) __VA_ARGS__); }

#define A_ERR(fmt, ...) A_DBG("[ERROR] " fmt __VA_OPT__(,) __VA_ARGS__)
#define A_WRN(fmt, ...) A_DBG("[WARNING] " fmt __VA_OPT__(,) __VA_ARGS__)
#endif