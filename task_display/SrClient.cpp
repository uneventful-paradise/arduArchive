#include "SrClient.h"

SrClient::SrClient(Stream& ser) : serial(ser) {}

SrClient::~SrClient(){
    A_DBG("Destroying serial client");
}
// wait for serial port to connect. Needed for native USB
// serial.begin has already been called in .ino . maybe end and begin?
void SrClient::initiate_connection(){
    // this -> serial.flush();
    // this -> serial.begin(115200);
    // while (!(this->serial)) {
    //     vTaskDelay(500 / portTICK_PERIOD_MS); 
    // }

    send_connection_status(this -> status);
    this->serial.printf("\nserial_start\n");
}
//does nothing, serial is always conencted?
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
    A_DBG("Closing wifi client");
    // this -> serial.end(); //!stream doesnt have end
}