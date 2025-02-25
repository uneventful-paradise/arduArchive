#include "Button.h"

struct Task2_params{
  Arduino_RPi_DPI_RGBPanel* gfx;
  JPEG_DRAW_CALLBACK *jpegDrawCallback;
  Button** buttons;
  int button_count;
};

static void display_text_task(void* params){
  // unsigned long long int start = millis();   //what is a good way to print every other second?
  Arduino_RPi_DPI_RGBPanel* gfx = (Arduino_RPi_DPI_RGBPanel *)params;
  gfx->fillRect(200, 160, 260, 160, WHITE);
  gfx->setCursor(220, 180);
  gfx->setTextSize(4);
  gfx->setTextColor(BLACK);
  gfx->println("Task 1 is displaying");

  for(;;){
    //waiting for event (touches?)
    
    Serial.println("Task 1 is running");
    vTaskDelay(1000 / portTICK_PERIOD_MS);
  }
  vTaskDelete(NULL);
}

static void display_icon_task(void* params){
  Task2_params t2p = *(Task2_params*)params;

  for(;;){
    //waiting for event (touches?)
    
    Serial.println("Task 2 is running");
    int rand_index = random(0, t2p.button_count);
    t2p.buttons[rand_index]->draw(t2p.jpegDrawCallback);
    vTaskDelay(1000 / portTICK_PERIOD_MS);
  }
  vTaskDelete(NULL);
}