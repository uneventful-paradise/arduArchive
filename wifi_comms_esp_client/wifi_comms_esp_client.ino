// ESP32: send length header (uint32_t LE) + message bytes over Serial1
void setup() {
  Serial.begin(115200);       // for debugging
  Serial1.begin(115200, SERIAL_8N1, 16, 17);  // TX=16, RX=17 (adjust pins if needed)
}

void loop() {
  const char *msg = "Hello from ESP32!";
  uint32_t len = strlen(msg);                // message length in bytes

  // send length header (4 bytes, little-endian)
  Serial.write((uint8_t*)&len, sizeof(len));

  // send message payload
  Serial.write((const uint8_t*)msg, len);

  Serial1.printf("Sent message of length %d\n", len);
  delay(1000);
}
