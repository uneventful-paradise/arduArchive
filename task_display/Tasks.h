#ifndef _TASKS_H_
#define _TASKS_H_
//TODO: set a higher priority for reader tasks?
//TODO: is yielding necessary when waiting upon xQeueuReceive

//!check if continue and break in button loop optimizes page switching

#include "Display.h"
#include "WiFi_comms.h"

extern EventGroupHandle_t connection_event_group;
extern QueueHandle_t wifi_request_queue; 

extern SrClient* sr_client;
extern NwClient* nw_client;
extern BaseClient* current_client;

void protected_check_connection();

void touch_check_task(void* params);

void update_screen_task(void* params); 

void establish_connection_task(void* params);

void send_request_task(void* params);

void swap_client_type();

void send_ack(int ack);

void receive_request_task(void* params);

void wifi_request_handling_task(void* params);

#endif