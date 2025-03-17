#ifndef _UTILITIES_H_
#define _UTILITIES_H_

#include "config.h"
// #include <avr/pgmspace.h>

const uint32_t PROGMEM crc_table[16] = {
    0x00000000, 0x1db71064, 0x3b6e20c8, 0x26d930ac,
    0x76dc4190, 0x6b6b51f4, 0x4db26158, 0x5005713c,
    0xedb88320, 0xf00f9344, 0xd6d6a3e8, 0xcb61b38c,
    0x9b64c2b0, 0x86d3d2d4, 0xa00ae278, 0xbdbdf21c
};

USBHIDKeyboard Keyboard;

QueueHandle_t send_queue;

struct Package_data{
  int command_type;
  int command_id;
  int opt_arg;
  int length;
  unsigned int crc_value;
  char contents[CHUNK_SIZE];
}data;

File file_obj = File();

unsigned long crc_update(unsigned long crc, byte data)
{
    byte tbl_idx;
    tbl_idx = crc ^ (data >> (0 * 4));
    crc = pgm_read_dword_near(crc_table + (tbl_idx & 0x0f)) ^ (crc >> 4);
    tbl_idx = crc ^ (data >> (1 * 4));
    crc = pgm_read_dword_near(crc_table + (tbl_idx & 0x0f)) ^ (crc >> 4);
    return crc;
}

unsigned long crc_string(const char *s, size_t length) {
  unsigned long crc = ~0L;          // initialize with all bits set
  for (size_t i = 0; i < length; ++i) {
    crc = crc_update(crc, s[i]);    // process each byte
  }
  return ~crc;                      // final complement of the CRC
}
//create/open the file where we have to write the data
File get_file_obj(const char* filename){
  //way to check this?

  // if(!SD.begin(SD_CS)){
  //   Serial.println("Failed to open SD card");
  //   return File();
  // }

  //filename must start with '/'
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
  return file_obj;
}


void log(char* message){
  Package_data data;
  data.command_type = LGCF;
  data.command_id = 0;  
  data.opt_arg = 0;
  data.length = strlen(message);
  strcpy(data.contents, message);

  xQueueSend(send_queue, &data, portMAX_DELAY);
}

void hard_press(char* sequence){
  //sequence cointains dKEY_NAME + .... + wDELAY_TIME + .... +uKEY_NAME
  //first we split the string by '+' using thread safe strtok
  char* save_ptr = sequence;
  char* token;

  token = strtok_r(sequence, "+", &save_ptr);
  char* log_msg = (char*)malloc(BUFFER_SIZE);
  if(log_msg == NULL){
    Serial.println("log_msg allocation failed");
  }

  while(token){
    char event = token[0];
    //converting string to ascii code
    //char* pEnd;
    // printf("%s\n", token);
    
    unsigned long long int code = 0;
    if(strlen(token) > 1){
      code = strtoull(token+1, NULL, 10);
      if(code == 0L){
        Serial.println("stroull failed for token conversion");
      }
    }

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


#endif