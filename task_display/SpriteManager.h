#ifndef _SPRITE_MANAGER_H
#define _SPRITE_MANAGER_H

#include "Sprite.h"

class SpriteManager {
private:
    Sprite** buttons;
    Sprite* navigation_buttons[NAV_BTN_COUNT];
    Arduino_RPi_DPI_RGBPanel* gfx;

    unsigned int btn_per_page;
    unsigned int btn_per_row;
    unsigned int max_capacity;

    unsigned int btn_capacity;
    unsigned int btn_offset;
    unsigned int btn_count;

    unsigned int current_page;
    unsigned int max_page;
public:
    SpriteManager(Arduino_RPi_DPI_RGBPanel* GFX,
        const unsigned int DEFAULT_BTN, 
        const unsigned int MAX_BTN, 
        unsigned int BTN_PER_PAGE, 
        const unsigned int BNT_PER_ROW, 
        const unsigned int BTN_OFFSET);

    Sprite* add_button(int id, char* filename);
    bool update_button(int id, char* filename);
    bool delete_button(int id);
    void clear_buttons();
    void switchPage(int code);
    ~SpriteManager();

    int getCurrentPage();
    void setCurrentPage(int value);
    int getMaxPage();
    void setMaxPage(int value);
    int getCapacity();
    int getCount();
    int getMaxBtns();
    Sprite** getButtons();
    Sprite** getNavButtons();
};
#endif