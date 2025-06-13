#ifndef _UTILITIES_H_
#define _UTILITIES_H_

// #include <avr/pgmspace.h>
#include "config.h"
#include <stdio.h>

extern SdFat sd;
extern SdFile file_obj;

extern USBHIDKeyboard Keyboard;
extern USBHIDMouse Mouse;
extern USBHIDConsumerControl Consumer;

extern QueueHandle_t send_queue;
extern QueueHandle_t conf_queue;
extern SemaphoreHandle_t xPrintMutex;
extern SemaphoreHandle_t xButtonsMutex;
extern SemaphoreHandle_t xConnEventGrpMutex;
extern SemaphoreHandle_t xConnCheckMutex;
extern SemaphoreHandle_t xTouchSemaphore;
extern TimerHandle_t clock_timer, inactivity_timer;

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

/*functions to toggle timer states.
start_acitivty and end_activity are used for processes whose duration 
is not easily determined whule note_activity is used for short (atomic like) operations*/
void start_activity();
void end_activity();
void note_activity();
bool reset_inactivity();

void clock_callback(TimerHandle_t xTimer);

void inactivity_callback(TimerHandle_t xTimer);

unsigned long crc_update(unsigned long crc, byte data);

unsigned long crc_string(const char* s, size_t length);

bool get_file_obj(const char* filename);

void vPrintString(const char* pString, bool debug = true);

void hard_press(char* sequence);

void send_connection_status(int change);

bool update_timestamp();

bool configure_timestamp();

#endif