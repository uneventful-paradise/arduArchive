#include "NwClient.h"

NwClient::NwClient(WiFiClient& wfc, EventGroupHandle_t evg) : client(wfc) {
    // this -> client = wfc;
    this -> connection_event_group = evg;
    A_DBG("Created wifi client");
}

NwClient::~NwClient(){
    A_DBG("Destroying wifi client");
}

void NwClient::wait_on_connection(){
    this -> xEventGroupValue = xEventGroupWaitBits(
        /* The event group to read */
        this -> connection_event_group,
        /* Bits to test */
        this -> xBitsToWaitFor,
        /* Clear bits on exit if the
        unblock condition is met */
        pdFALSE,
        /* wait for all bits. 
        before proceeding to read */
        pdTRUE,
        /* Don't time out.*/
        portMAX_DELAY );
    if ((this -> xEventGroupValue & (CLIENT_CONNECTED_BIT | WIFI_CONNECTED_BIT)) != (CLIENT_CONNECTED_BIT | WIFI_CONNECTED_BIT)) {
        // A_DBG("Network Client is connected and can proceed to perform I/O operation");
        A_WRN("Faulty read");
    }
}

void NwClient::initiate_connection(){
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PWD);
  //no WiFi connection established initially
  this -> status = -2;
  send_connection_status(this -> status);
  
  //Initial connection attempt
  A_DBG("Connecting to WiFi...");
//   wl_status_t res = WiFi.waitForConnectResult(20000);
  while (WiFi.status() != WL_CONNECTED) {
    A_WRN("WiFi disconnected! Reconnecting...");
    this->retries++;
    if ( this -> retries >= this -> max_retries) {
        A_DBG("Disconnecting from WiFi");
        WiFi.disconnect();
        this -> retries = 0;
        WiFi.begin(WIFI_SSID, WIFI_PWD);
    }
    Serial.print(".");
    vTaskDelay(1000 / portTICK_PERIOD_MS);
  }

  A_DBG("WiFi Connected!");
//   printWifiStatus();
}

void NwClient::connect_to_server(){
    A_DBG("Connecting to server...");
    if (!this->client.connect(SERVER_IP, PORT)) {
        A_WRN("Connection failed!");
        vTaskDelay(500);
    } else {
        A_DBG("Connected to server.");
    }
}

void NwClient::check_connection(){
    this -> xEventGroupValue = xEventGroupGetBits( this -> connection_event_group );

    if (WiFi.status() != WL_CONNECTED) {
        if ( this -> xEventGroupValue & WIFI_CONNECTED_BIT ) {
            //client was connected, therefore we lost connection
            xEventGroupClearBits(connection_event_group, WIFI_CONNECTED_BIT);
            this -> status = -2;
            send_connection_status( this -> status );
        }
        this->retries++;
        if ( this -> retries >= this -> max_retries) {
            A_DBG("Disconnecting from WiFi");
            WiFi.disconnect();
            this -> retries = 0;
        }
        A_WRN("WiFi disconnected! Reconnecting...");
        WiFi.begin(WIFI_SSID, WIFI_PWD);
        return;
    } else {
        if (!( this->xEventGroupValue & WIFI_CONNECTED_BIT )) {
            //client was not connected, therefore connection was established
            xEventGroupSetBits( this -> connection_event_group, WIFI_CONNECTED_BIT );
            this -> status = -1;
            send_connection_status( this -> status);
            A_DBG("WiFi connected!");
        }
    }

    if (!client.connected()) {
        if ( this -> xEventGroupValue & CLIENT_CONNECTED_BIT ) {
            xEventGroupClearBits( this -> connection_event_group, CLIENT_CONNECTED_BIT );
            this -> status = 0;
            send_connection_status(this -> status);
        }
        A_WRN("Client disconnected! Reconnecting...");
        connect_to_server();
    }else{
        if (!(this->xEventGroupValue & CLIENT_CONNECTED_BIT)) {
            //client was not connected, therefore connection was established
            xEventGroupSetBits( this -> connection_event_group, CLIENT_CONNECTED_BIT );
            this -> status = 1;
            send_connection_status( this -> status);
            A_DBG("Client connected!");
        }
    }
}

int NwClient::get_available(){
    return this -> client.available();
}

int NwClient::read_one(){
    return this -> client.read();
}

void NwClient::clear_channel(){
    A_WRN("emptying socket and requesting resend");
    while (this -> get_available()) {
      this -> read_one();
    }
}

size_t NwClient::read_all(char* buffer, size_t req_len){
    // A_DBG("Network Client reading");
    return this -> client.readBytes(buffer, req_len);
}
size_t NwClient::write_all(const uint8_t* data, size_t req_len){
    return this -> client.write(data, req_len);
}

void NwClient::close(){
    A_DBG("Closing wifi client");
    this -> client.stop();
    WiFi.disconnect();
}

void NwClient::mark_connected(){
    xEventGroupSetBits( 
        this -> connection_event_group, 
        WIFI_CONNECTED_BIT | CLIENT_CONNECTED_BIT
    );
}

void NwClient::mark_disconnected(){
    xEventGroupClearBits( 
        this -> connection_event_group, 
        WIFI_CONNECTED_BIT  | CLIENT_CONNECTED_BIT
    );
}