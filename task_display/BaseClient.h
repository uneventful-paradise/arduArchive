#ifndef _BASE_CLIENT_H_
#define _BASE_CLIENT_H_
#include "Utilities.h"

class BaseClient{
public:
    BaseClient(){};
    virtual ~BaseClient(){};
    virtual void initiate_connection() = 0;
    virtual void wait_on_connection() = 0;
    virtual void check_connection() = 0;
    virtual int get_available() = 0;
    //https://github.com/espressif/arduino-esp32/blob/f1223663dd122b605603c1e072a33f3a6935f451/libraries/Network/src/NetworkClient.cpp#L107
    virtual int read_one() = 0;
    virtual void clear_channel() = 0;
    virtual size_t read_all(char* buffer, size_t req_len) = 0;
    virtual size_t write_all(const uint8_t* data, size_t req_len) = 0;
    virtual void close() = 0;
};
#endif