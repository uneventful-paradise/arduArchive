// ESP32: send length header (uint32_t LE) + message bytes over Serial1
const unsigned int CHUNK_SIZE = 1024;
const unsigned int serial_buffer = 240;
char* buffer[CHUNK_SIZE];
void setup() {
  Serial.begin(115200);
}
unsigned int avail;
int packet = 0;
void loop() {
  int total = 0;
  while(total < CHUNK_SIZE){  //add timeout in case server dies?
    avail = Serial.available();
    if(avail == 0){
      // Serial.println("0 bytes available, skipping!");
      continue;
    }
    size_t to_read = CHUNK_SIZE - total;
    
    if(to_read > avail){
      to_read = avail;
    }
    size_t read = Serial.readBytes((uint8_t*)(buffer+total), to_read);
    
    if (read <= 0) {
      Serial.println("ERROR: no available data");
    }
    else if(read != to_read){
      Serial.printf("WARNING: partial read %d\n", packet);
    }
    
    total += read;
  }
  packet++;
  Serial.printf("Success packet %d:\n%s", packet, buffer);
  delay(200);
}
