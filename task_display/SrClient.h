#ifndef _SR_CLIENT_H_
#define _SR_CLIENT_H_
#include "BaseClient.h"

class SrClient : public BaseClient{
private:
    Stream& serial;
    // bool last_connected = false;
    int status = 0;
    // SemaphoreHandle_t conn_lock;
public:
    // NwClient(Stream* ser, SemaphoreHandle_t lock);
    SrClient(Stream& ser);
    virtual ~SrClient() override;
    virtual void initiate_connection() override;
    void connect_to_server();
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