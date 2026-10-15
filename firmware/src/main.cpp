
#include <Arduino.h>
#include <esp_system.h>
#include <esp_timer.h>

namespace {
constexpr char kFirmwareVersion[] = "0.2.0";
constexpr uint32_t kHeartbeatIntervalMs = 3000;
char deviceId[32];
char bootId[17];
uint64_t sequence = 0;
uint32_t lastHeartbeat = 0;

void sendMessage(const char* type) {
    // All fields are device diagnostics. There are no environmental sensors.
    const String chip = ESP.getChipModel();
    Serial.printf(
        "{\"protocol_version\":1,\"type\":\"%s\",\"device_id\":\"%s\","
        "\"chip_model\":\"%s\",\"firmware_version\":\"%s\","
        "\"boot_id\":\"%s\",\"uptime_ms\":%llu,\"sequence\":%llu}\n",
        type, deviceId, chip.c_str(), kFirmwareVersion, bootId,
        static_cast<unsigned long long>(esp_timer_get_time() / 1000),
        static_cast<unsigned long long>(sequence++));
}
}

void setup() {
    Serial.begin(115200);
    snprintf(deviceId, sizeof(deviceId), "esp32-%012llx",
             static_cast<unsigned long long>(ESP.getEfuseMac() & 0xFFFFFFFFFFFFULL));
    // Randomness identifies a boot; it never generates sensor readings.
    snprintf(bootId, sizeof(bootId), "%08lx%08lx",
             static_cast<unsigned long>(esp_random()),
             static_cast<unsigned long>(esp_random()));
    delay(250);
    sendMessage("hello");
    lastHeartbeat = millis();
}

void loop() {
    const uint32_t now = millis();
    if (static_cast<uint32_t>(now - lastHeartbeat) >= kHeartbeatIntervalMs) {
        lastHeartbeat = now;
        sendMessage("heartbeat");
    }
    delay(10);
}
