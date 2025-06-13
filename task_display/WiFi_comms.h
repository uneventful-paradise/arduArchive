#ifndef _WIFI_H_
#define _WIFI_H_

#include "NwClient.h"
#include "SrClient.h"

extern WiFiClient wfc;
extern bool wifi_init;

void printWifiStatus();

void send_request(Package_data* data, BaseClient* bc);

int handle_download(Package_data* pd);

void initialize_wifi_logging();

#endif