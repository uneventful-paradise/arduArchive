#ifndef _NW_CLIENT_H_
#define _NW_CLIENT_H_
#include "BaseClient.h"

#define WIFI_CONNECTED_BIT (1 << 0)
#define CLIENT_CONNECTED_BIT (1 << 1)

class NwClient : public BaseClient{
private:
    WiFiClient& client;
    EventGroupHandle_t connection_event_group;
    EventBits_t xEventGroupValue;
    int status =- 2;
    unsigned int retries = 0;
    unsigned int max_retries = 6;
    const EventBits_t xBitsToWaitFor = ( WIFI_CONNECTED_BIT | CLIENT_CONNECTED_BIT );
    // const TickType_t xTicksToWait = 100 / portTICK_PERIOD_MS;
public:
    NwClient(WiFiClient& wfc, EventGroupHandle_t evg);
    virtual ~NwClient() override;
    virtual void initiate_connection() override;
    void connect_to_server();
    void mark_connected();
    void mark_disconnected();
    virtual void wait_on_connection() override;
    virtual void check_connection() override;
    virtual int get_available() override;
    virtual int read_one() override;
    virtual void clear_channel() override;
    virtual size_t read_all(char* buffer, size_t req_len) override;
    virtual size_t write_all(const uint8_t* data, size_t length) override;
    virtual void close() override;
};
#endif