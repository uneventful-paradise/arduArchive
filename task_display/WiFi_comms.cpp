#include "WiFi_comms.h"

WiFiClient wfc;

void printWifiStatus() {
  A_DBG("wifi status?");
  // A_DBG("\nSSID: ");
  // A_DBG(WiFi.SSID());

  // A_DBG("IP Address: ");
  // A_DBG(WiFi.localIP());

  // A_DBG("Signal strength (RSSI): ");
  // A_DBG(WiFi.RSSI());
  // A_DBG(" dBm");
}
/*Send the package of data to the server.
Convert data to network format (big endian by default) and
send it as a bytes array in a loop to make sure that it is
completely written on the socket.

TODO: change structure of Package_data to dynamically allocated contents
to avoid sending unnecessary data around.*/
void send_request(Package_data* data, BaseClient* bc) {
  // Serial.printf("Got data type %u id %u len %u CRC %04x \n%s\n", cmd_type, cmd_id, req_len, crc_value, req);
  unsigned int packet_id = data->header.command_id;
  unsigned int packet_len = data->header.length;
  // Serial.printf("\nSending type %u id %u len %u CRC %04x\n%s\n",
  //               data->header.command_type,
  //               data->header.command_id,
  //               data->header.length,
  //               data->header.crc_value,
  //               data->contents);
  A_DBG("Sending type %u id %u len %u CRC %04x\n%s\n",
        data->header.command_type,
        data->header.command_id,
        data->header.length,
        data->header.crc_value,
        data->contents);

  //Convert data to big endian (network byte order) before sending (network standard).
  data->header.command_type = htonl(data->header.command_type);
  data->header.command_id = htonl(data->header.command_id);
  data->header.length = htonl(data->header.length);
  data->header.crc_value = htonl(data->header.crc_value);
  // Serial.printf("Send type %u id %u len %u CRC %04x \n%s\n", cmd_type, cmd_id, req_len, crc_value, req);

  //Calculate total packet size
  // Serial.printf("Size of contents is: %d\n", packet_len);
  // A_DBG("Size of contents is: %d\n", packet_len);
  unsigned int packet_size = HEADER_SIZE + packet_len;

  size_t bytes_sent = 0;
  //Loop to send all the data in the packet (TCP can fail to send all the bytes in a single send call).
  //Casting data to char/byte to clarify we are sending raw bytes
  
  while (bytes_sent < packet_size) {
    int sent = bc -> write_all(((uint8_t*)data) + bytes_sent, packet_size - bytes_sent);
    if (sent > 0) {
      bytes_sent += sent;  // move forward in the buffer
    } else {
      // Serial.printf("Send %d failed at byte %d. Retrying...\n", packet_id, bytes_sent);
      A_ERR("Send %d failed at byte %d. Retrying...\n", packet_id, bytes_sent);
      delay(10);
    }
  }
  // Serial.printf("Send of id %u successful!\n", packet_id);
  A_DBG("Send of id %u successful!\n", packet_id);
  //increment client request id for next packet
  client_cmd_id++;
}

/*Manage download process. This function uses a global File handle to 
handle writing received content on the SD card. The `file_obj` is a global
file handled initialized with null (value of File() default constructor).

Download data packets are handled based on the `command_type` argument:

Upon a "START_DOWNLOAD" request the file is created (or opened) and its handle is assigned to `file_obj`.
This first request contains the client sided filename and 
total file size (necessary for the progress bar calculation).

The following FILE_SIZE/CHUNK packets are data transfer packets and will be written to the 
newly created file.

Finally, the "END_DOWNLOAD" request signalizes that EOF has been read on the server side. 
The file is closed and the `file_obj` object is reasigned NULL. So, `file_obj` is NULL as
long as no file transfer is ongoing.
*/
unsigned int final_file_size = 0;  //unsigned long int
unsigned int current_file_size = 0;
float download_percentage = 0;
char* current_filename;

int handle_download(Package_data* pd) {
  UI_update update;
  BaseType_t xStatus;

  /*In the START_DOWNLOAD packet there are sent
  the client side filename and final file size separated by a space*/
  // Serial.printf("Header command type is %u\n", pd->header.command_type);
  if (pd->header.command_type == START_DOWNLOAD) {

    //parsing the contents to get filename and filesize
    //request has form "filename filesize"
    char* copied_contents = strndup(pd->contents, pd->header.length);
    char* save_ptr = copied_contents;
    char* token;

    token = strtok_r(copied_contents, " ", &save_ptr);
    current_filename = strdup(token);

    token = strtok_r(NULL, " ", &save_ptr);
    /*use stroull to convert string to unsigned 
    long long int value. Number value in string is base 10*/
    final_file_size = strtoull(token, NULL, 10);
    if (final_file_size == 0L) {
      // Serial.println("strtoull failed in handle download");
      A_ERR("strtoull failed in handle download");
      free(copied_contents);
      return -2;
    }
    /*now that the filename and file size have been copied/calculated
    we free the copied contents of the data packet*/
    free(copied_contents);

    //open the file and initiate the transfer
    if (!get_file_obj(current_filename)) {
      return -2;
    }
    current_file_size = 0;
    // Serial.printf("INITIATED DOWNLOAD. Final size will be %d\n", final_file_size);
    A_DBG("INITIATED DOWNLOAD. Final size will be %d\n", final_file_size);

    /*Send an update to screen*/
    update.type = START_DOWNLOAD;
    update.status = 0;
    if (sprintf(update.message, "Starting download") < 0) {
      // Serial.println("Update message creation failed");
      A_ERR("Update message creation failed");
    }
    //checking that the file has been created/opened without errors.
    if (file_obj) {
      //sending update to queue for the update function to receive and execute
      xStatus = xQueueSend(ui_updates_queue, &update, portMAX_DELAY);
      if (xStatus != pdPASS) {
        vPrintString("handle_download failed to send download start data to ui_updates_queue.\r\n");
      }
    } else {
      // Serial.println("Invalid download file");
      A_ERR("Invalid download file");
      return -2;
    }
    // Serial.printf("passing to next packet\n");
    return 1;
  } else if (pd->header.command_type == END_DOWNLOAD) {
    //EOF read on server side. Ending download.
    //init file to null?
    // Serial.println("EOF reached. Ending download.");
    A_DBG("EOF reached. Ending download.");
    file_obj.flush();
    file_obj.close();
    //resetting file obj to evaluate to false once the download is complete
    if (current_file_size != final_file_size) {
      // Serial.println("ERROR: Total written does not match target value");
      A_ERR("Total written %d does not match target value", current_file_size);
    } else {
      // Serial.printf("DOWNLOAD FINISHED. Wrote %d bytes\n", final_file_size);
      A_DBG("DOWNLOAD FINISHED. Wrote %d bytes\n", final_file_size);
    }
    final_file_size = 0;
    current_file_size = 0;
    //free filename to be used by next START_DOWNLOAD command
    free(current_filename);

    update.type = END_DOWNLOAD;
    update.status = 100;
    if (sprintf(update.message, "Download finished") < 0) {
      // Serial.println("Update message creation failed");
      A_ERR("Update message creation failed");
    }

    xStatus = xQueueSend(ui_updates_queue, &update, portMAX_DELAY);
    if (xStatus != pdPASS) {
      vPrintString("handle_download failed to send end of download data to ui_updates_queue.\r\n");
    }
    return 1;
  } else if (pd->header.command_type == FILE_TRANSFER) {
    //transfer packet contains file data

    if (file_obj) {
      //getting file cursor pointer position
      // unsigned long position = file_obj.position();
      // Serial.printf("Before write cursor was at %lu\n", position);

      size_t total_written = 0;
      const unsigned int max_retries = 10;
      unsigned int retry_counter = 0;
      bool fatal_error = false;

      total_written = file_obj.write((uint8_t*)pd->contents, pd->header.length);
      if (total_written != pd->header.length) {
        // Serial.printf("ERROR: partial write of %d bytes for packet %u\n", total_written, pd->header.command_id);
        A_ERR("Wrote %d of %d bytes for packet %u. Error code %d\n", total_written, pd->header.length, pd->header.command_id, file_obj.getError());
      } else {
        A_DBG("Correctly wrote %d bytes to file\n", total_written);
      }
      //write successful

      //TODO: decide on whether to flush after every write or let flush be called automatically
      file_obj.flush();
      // position = file_obj.position();
      // Serial.printf("After write cursor was at %lu\n", position);

      // Serial.printf("Current progress %f\n", download_percentage);
      A_DBG("Current progress %f\n", download_percentage);

      // current_file_size += pd.length;
      current_file_size += total_written;
      download_percentage = round(((float)current_file_size / (float)final_file_size) * 100);

      update.type = FILE_TRANSFER;
      update.status = download_percentage;
      if (sprintf(update.message, "Download %f complete", download_percentage) < 0) {
        // Serial.println("Update message creation failed");
        A_ERR("Update message creation failed");
      }

      xStatus = xQueueSend(ui_updates_queue, &update, portMAX_DELAY);
      if (xStatus != pdPASS) {
        vPrintString("handle_download failed to send file trasnfer data to ui_updates_queue.\r\n");
      }

      return 1;
    } else {
      // Serial.println("Target file for upload is invalid");
      A_ERR("Target file for upload is invalid");
    }
  }
  // Serial.printf("package type does not match download format\n");
  A_ERR("package type does not match download format\n");
  return 0;
}
