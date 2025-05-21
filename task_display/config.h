#ifndef _CONFIG_H_
#define _CONFIG_H_

#include <USB.h>
// #include <SD.h>
#include "JpegFunc.h"
#include <USBHIDKeyboard.h>
#include <SPI.h>
#include <Wire.h>

#include <TAMC_GT911.h>
// #include "Tasks.h"
#include <WiFi.h>
#include "time.h"

#define BASE_CONFIG_PATH "/configs/btn_config.txt"
#define WIFI_SSID "DIGI-yWsT"
#define WIFI_PWD "74F8ghZw"
// #define WIFI_SSID "testesp32"
// #define WIFI_PWD "javabanana"
#define SERVER_IP "192.168.100.63"
#define PORT 65432
#define CHUNK_SIZE 2048
#define HEADER_SIZE 16  //unsigned int cmd_type | unsigned int cmd_id | unsigned int length | unsigned int crc_value
#define BUFFER_SIZE 256

#define MACRO_COMMAND 0
#define START_DOWNLOAD 1
#define FILE_TRANSFER 2
#define END_DOWNLOAD 3
#define INITIALIZE_ROUTINE 4
#define CONFIRMATION_FLAG 5
#define REDRAW_COMMAND 6
#define CONNECTION_CHECK 7
#define CLIENT_SWAP 8
#define TIME_UPDATE 9

#define TOUCH_SDA 17
#define TOUCH_SCL 18
#define TOUCH_INT -1
#define TOUCH_RST 38
#define TOUCH_WIDTH 800
#define TOUCH_HEIGHT 480

#define COLOR_BACKGROUND BLACK
#define COLOR_BUTTON BLACK
#define COLOR_BUTTON_P 0x4BAF
#define COLOR_TEXT WHITE
#define COLOR_LINE WHITE
#define COLOR_SHADOW 0x4BAF

#define BUTTON_POS_X 10
#define BUTTON_POS_Y 90

#define INIT_SPRITE_COUNT 6
#define MAX_SPRITE_COUNT 64
#define BUTTONS_PER_PAGE 15
#define BUTTONS_PER_ROW 5
#define BUTTON_VERTICAL_OFFSET 20
#define BUTTON_HORIZONTAL_OFFSET 45
#define BUTTON_DELAY 150
#define BUTTON_WIDTH 100
#define BUTTON_HEIGHT 100
#define MAX_FOLDER_SIZE 15

#define NAV_BTN_COUNT 3
#define BUTTON_PREV 100
#define BUTTON_NEXT 101
#define BUTTON_SWAP 102
#define SR_CLIENT_MODE 0
#define NW_CLIENT_MODE 1

//micro SD card
#define SD_SCK 12
#define SD_MISO 13
#define SD_MOSI 11
#define SD_CS 10

//Setting display and touch variables

#define TOUCH_ROTATION ROTATION_INVERTED


#define TOUCH_MAP_X1 800
#define TOUCH_MAP_X2 0
#define TOUCH_MAP_Y1 480
#define TOUCH_MAP_Y2 0

#define GFX_BL 44
#define TFT_BL GFX_BL

#define PWM_CHANNEL 1
#define PWM_FREQ 5000  // Hz
#define pwm_resolution_bits 10

#define SPI_CLOCK SD_SCK_MHZ(12)

#if defined(HAS_TEENSY_SDIO)
#define SD_CONFIG SdioConfig(FIFO_SDIO)
#elif defined(RP_CLK_GPIO) && defined(RP_CMD_GPIO) && defined(RP_DAT0_GPIO)
// See the Rp2040SdioSetup example for RP2040/RP2350 boards.
#define SD_CONFIG SdioConfig(RP_CLK_GPIO, RP_CMD_GPIO, RP_DAT0_GPIO)
#elif ENABLE_DEDICATED_SPI
#define SD_CONFIG SdSpiConfig(SD_CS, DEDICATED_SPI, SPI_CLOCK)
#else  // HAS_TEENSY_SDIO
#define SD_CONFIG SdSpiConfig(SD_CS, SHARED_SPI, SPI_CLOCK)
#endif  // HAS_TEENSY_SDIO


#define DEBUG 1

#define A_DBG(fmt, ...) do { if (DEBUG) { printf("[%s:%d]: " fmt "\n", __func__, __LINE__  __VA_OPT__(, ) __VA_ARGS__); } } while (0)
// #define A_DBG(fmt, ...) { printf("[%s:%d]: " fmt "\n", __func__, __LINE__ __VA_OPT__(, ) __VA_ARGS__); }
// {update_timestamp(); printf("[%s:%s:%d]: " fmt "\n", current_timestamp, __func__, __LINE__ __VA_OPT__(, ) __VA_ARGS__);}

#define A_ERR(fmt, ...) A_DBG("[ERROR] " fmt __VA_OPT__(, ) __VA_ARGS__)
#define A_WRN(fmt, ...) A_DBG("[WARNING] " fmt __VA_OPT__(, ) __VA_ARGS__)

#endif