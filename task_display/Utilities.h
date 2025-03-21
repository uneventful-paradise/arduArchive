#ifndef _UTILITIES_H_
#define _UTILITIES_H_

#include "config.h"
// #include <avr/pgmspace.h>

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

struct Package_data{
  int command_type;
  int command_id;
  int opt_arg;
  int length;
  unsigned int crc_value;
  char contents[CHUNK_SIZE];
}data;

File file_obj = File();
char* paths[SPRITE_COUNT];

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
File get_file_obj(const char* filename){
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
    return File();
  }
  //get directory path
  if(slash_pos > 0){
    directory = strndup(filename, slash_pos);
    Serial.printf("Directory is %s\n", directory);
  }else{
    Serial.println("Requested directory is root");
  }
  //create directory if it doesn't exist
  if(!SD.exists(directory)){
    if(!SD.mkdir(directory)){
      Serial.println("Failed to create directory");
      return File();
    }else{
      Serial.println("Successfully created directory");
    }
  }else{
    Serial.println("Directory already exists");
  }
  //opening or creating file
  Serial.printf("Attempting to open or create %s\n", filename);
  if(SD.exists(filename)){
    Serial.println("File already exists");
  }
  file_obj = SD.open(filename, FILE_WRITE);
  if(!file_obj){
    Serial.println("Error opening or creating file");
    return File();
  }
  Serial.println("File opened successfully");
  free(directory);
  return file_obj;
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

  Package_data data;
  data.command_type = LGCF;
  data.command_id = 0;  
  data.opt_arg = 0;
  data.length = strlen(message);
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
  if(!SD.exists(filename)){
    Serial.println("File does not exist");
    return;
  }
  File file = SD.open(filename);
  if(!file){
    Serial.println("Could not open file");
    return;
  }
  int index = 0;
  while(file.available()){
    if(index > SPRITE_COUNT){
      break;
    }
    String s = file.readStringUntil('\n');
    paths[index++] = strdup(s.c_str());
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

#endif