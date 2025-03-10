#ifndef _CONFIG_H_
#define _CONFIG_H_

#include <USB.h>
#include <USBHIDKeyboard.h>
#include <SPI.h>
#include <Wire.h>

#include <TAMC_GT911.h>
// #include "Tasks.h"
#include "Sprite.h"

#define WIFI_SSID           "DIGI-yWsT"
#define WIFI_PWD            "74F8ghZw"
#define SERVER_IP           "192.168.100.63"
#define PORT                65431
#define CHUNK_SIZE          2048
#define HEADER_SIZE         16
#define UPDATE_BUFFER_SIZE  256

#define MCCF  0     //MACRO COMMAND FLAG
#define SDCF  1     //START DOWNLOAD COMMAND FLAG
#define FTCF  2     //FILE TRANSFER COMMAND FLAG
#define EDCF  3     //END OF DOWNLOAD COMMAND FLAG
#define INTF  4     //INITIALIZATION FLAG (start of routine)
#define CFCF  5     //CONFIRMATION COMMAND FLAG

#define TOUCH_SDA     17
#define TOUCH_SCL     18
#define TOUCH_INT     -1
#define TOUCH_RST     38
#define TOUCH_WIDTH   800
#define TOUCH_HEIGHT  480

#define COLOR_BACKGROUND BLACK
#define COLOR_BUTTON BLACK
#define COLOR_BUTTON_P 0x4BAF
#define COLOR_TEXT WHITE
#define COLOR_LINE WHITE
#define COLOR_SHADOW 0x4BAF

#define BUTTON_POS_X 10
#define BUTTON_POS_Y 90

#define SPRITE_COUNT 10
#define BUTTON_DELAY 150
#define BUTTON_WIDTH 85
#define BUTTON_HEIGHT 85

#define VSCODE      "/jpg_icons/vscode.jpg"
#define CHROME      "/jpg_icons/chrome.jpg"
#define YOUTUBE     "/jpg_icons/youtube.jpg"
#define OBS         "/clap_icons/OBS.jpg"
#define OVERWATCH   "/clap_icons/Overwatch.jpg"
#define STEAM       "/clap_icons/Steam.jpg"
#define DISCORD     "/clap_icons/Discord.jpg"
#define TINDER      "/clap_icons/Tinder.jpg"
#define CC          "/clap_icons/Adobe_Creative_Cloud.jpg"
#define YT          "/clap_icons/Youtube.jpg"

#define PYCHARM_85      "/85px/1.jpg"
#define PYCHARM_85_B    "/85px/1b.jpg"
#define ADOBE_85        "/85px/2.jpg"
#define ADOBE_85_B      "/85px/2b.jpg"
#define WORD_85         "/85px/3.jpg"
#define WORD_85_B       "/85px/3B.jpg"
#define CALCULATOR_85   "/85px/4.jpg"
#define CALCULATOR_85_B "/85px/4b.jpg"
#define SPOTIFY_85      "/85px/5.jpg"
#define SPOTIFY_85_B    "/85px/5b.jpg"
#define STEAM_85        "/85px/9.jpg"
#define GIT_85          "/85px/6.jpg"
#define NOTEPAD_85      "/85px/10.jpg"
#define CHROME_85       "/85px/7.jpg"
#define YOUTUBE_85      "/85px/12.jpg"
#define VSCODE_85       "/85px/11.jpg"

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
#define PWM_FREQ 5000 // Hz
#define pwm_resolution_bits 10

#endif