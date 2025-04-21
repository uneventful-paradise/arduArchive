#ifndef _UTILITIES_H_
#define _UTILITIES_H_

// #include <avr/pgmspace.h>
#include "config.h"
#include <stdio.h>

extern SdFat sd;
extern SdFile file_obj;


extern USBHIDKeyboard Keyboard;

extern QueueHandle_t send_queue;
extern QueueHandle_t conf_queue;
extern SemaphoreHandle_t xPrintMutex;
extern SemaphoreHandle_t xButtonsMutex;
extern SemaphoreHandle_t xClientMutex;
extern SemaphoreHandle_t xConnEventGrpMutex;

struct Header_data {
  unsigned int command_type;
  unsigned int command_id;
  unsigned int length;
  unsigned int crc_value;
};

struct Package_data {
  Header_data header;
  char contents[CHUNK_SIZE];
};

struct UI_update {
  unsigned int type;
  int status;
  char message[BUFFER_SIZE];
};

extern QueueHandle_t ui_updates_queue;

extern unsigned int client_cmd_id;

unsigned long crc_update(unsigned long crc, byte data);

unsigned long crc_string(const char* s, size_t length);

bool get_file_obj(const char* filename);

void vPrintString(const char* pString, bool debug = true);

void hard_press(char* sequence);

void send_connection_status(int change);


#endif