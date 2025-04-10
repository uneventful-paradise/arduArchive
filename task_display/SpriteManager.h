#ifndef _SPRITE_MANAGER_H
#define _SPRITE_MANAGER_H

#include "Sprite.h"

class SpriteManager {
private:
    Sprite** buttons;
    unsigned int btn_per_page;
    unsigned int btn_per_row;
    unsigned int btn_capacity;
    unsigned int btn_offset;
    unsigned int btn_count;
public:
    SpriteManager(const unsigned int BTN_PER_PAGE, const unsigned int BNT_PER_ROW, const unsigned int BTN_OFFSET);
    Sprite* add_button(int id, char* filename);
    bool update_button(int id, char* filename);
    bool delete_button(int id);
    ~SpriteManager();

    int getCapacity();
    int getCount();
    Sprite** getButtons();
};
#endif