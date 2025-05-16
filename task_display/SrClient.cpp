#include "SrClient.h"

SrClient::SrClient(Stream& ser) : serial(ser) {}

SrClient::~SrClient(){
    A_DBG("Destroying serial client");
}
// wait for serial port to connect. Needed for native USB
// serial.begin has already been called in .ino . maybe end and begin?
void SrClient::initiate_connection(){
    this -> status = 0;
    send_connection_status(this -> status);
    BaseType_t xStatus;
    const TickType_t xTicksToWait = pdMS_TO_TICKS(2000);
    Package_data pd;
    while(true){
        this->serial.printf("\nserial_start\n");
        xStatus = xQueueReceive(conf_queue, &pd, xTicksToWait);
        if(xStatus != pdFAIL){
            break;
        }
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
    delay(1000);
    this->status = 1;
    send_connection_status(this -> status);
}
//does nothing, serial is always connected? could send pings periodically
void SrClient::wait_on_connection(){

}

void SrClient::check_connection(){
    
}

int SrClient::get_available(){
    return this -> serial.available();
}

int SrClient::read_one(){
    return this -> serial.read();
}

void SrClient::clear_channel(){
    A_WRN("emptying socket and requesting resend");
    while (this -> get_available()) {
      this -> serial.read();
    }
}
size_t SrClient::read_all(char* buffer, size_t req_len){
    // this -> serial.readBytes(buffer, req_len);
    unsigned int packets = 0;
    size_t avail;
    size_t total = 0;
    A_DBG("Trying to read %d bytes", req_len);
    while (total < req_len) {
        int avail = this -> serial.available();
        // A_DBG("Currently %d on serial", curr_available);
        if (avail > 0) {
            size_t to_read = req_len - total;
            if (to_read > avail) {
                to_read = avail;
            }

            size_t read = serial.readBytes(buffer + total, to_read);

            if (read <= 0) {
                A_ERR("No available data");
            }else if (read != to_read){
                A_WRN("Incomplete packet");
            }
            total += to_read;
            packets++;
        } else {
            vTaskDelay(pdMS_TO_TICKS(1));
        }
    }
    A_DBG("Finished reading %d in %d packs", total, packets);
    return total;
}

size_t SrClient::write_all(const uint8_t* data, size_t length){
    size_t sent = this -> serial.write(data, length);
    this -> serial.flush();
    return sent;
}

void SrClient::close(){
    A_DBG("Closing serial client");
    // this -> serial.end(); //!stream doesnt have end
}