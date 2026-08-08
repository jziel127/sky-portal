#include <Servo.h>
#include <EEPROM.h>

// --- PCB PIN DEFINITIONS ---
const int PIN_PHOTON       = 9;   // J5 Header
const int PIN_COLOR_RATIO  = 10;  // J8 Header
const int PIN_POWER_SWITCH = 11;  // J9 Header

// --- EEPROM ADDRESSES ---
const int ADDR_PHOTON       = 0;
const int ADDR_COLOR_RATIO  = 2;
const int ADDR_POWER_SWITCH = 4;
const int ADDR_MAGIC        = 6;  // Marker to check if EEPROM is initialized
const uint16_t EEPROM_MAGIC = 0xABCD;

// --- SERVO OBJECTS & STATE ---
Servo photonServo;
Servo colorRatioServo;
Servo powerServo;

int targetPhoton     = 0;   // 0 (Max Red) to 180 (White)
int targetColorRatio = 0;   // 0 (Low) to 180 (High)
int targetPower      = 0;   // 0 (OFF) to 180 (ON)

int currentPhoton     = 0;
int currentColorRatio = 0;
int currentPower      = 0;

// --- HELPER: SMOOTH MOTION ENGINE ---
// Moves servos incrementally to eliminate harsh mechanical snaps and current spikes
void moveServosSmoothly() {
  bool moving = true;
  while (moving) {
    moving = false;

    // Photon Knob
    if (currentPhoton < targetPhoton) { currentPhoton++; moving = true; }
    else if (currentPhoton > targetPhoton) { currentPhoton--; moving = true; }
    photonServo.write(currentPhoton);

    // Color Ratio Knob
    if (currentColorRatio < targetColorRatio) { currentColorRatio++; moving = true; }
    else if (currentColorRatio > targetColorRatio) { currentColorRatio--; moving = true; }
    colorRatioServo.write(currentColorRatio);

    // Light Power Switch
    if (currentPower < targetPower) { currentPower++; moving = true; }
    else if (currentPower > targetPower) { currentPower--; moving = true; }
    powerServo.write(currentPower);

    delay(10); // Adjust step speed (lower = faster movement)
  }
}

// --- HELPER: SAVE STATE TO EEPROM ---
void saveState() {
  EEPROM.put(ADDR_PHOTON, targetPhoton);
  EEPROM.put(ADDR_COLOR_RATIO, targetColorRatio);
  EEPROM.put(ADDR_POWER_SWITCH, targetPower);
  EEPROM.put(ADDR_MAGIC, EEPROM_MAGIC);
}

// --- HELPER: LOAD STATE FROM EEPROM ---
void loadState() {
  uint16_t magic;
  EEPROM.get(ADDR_MAGIC, magic);

  if (magic == EEPROM_MAGIC) {
    EEPROM.get(ADDR_PHOTON, targetPhoton);
    EEPROM.get(ADDR_COLOR_RATIO, targetColorRatio);
    EEPROM.get(ADDR_POWER_SWITCH, targetPower);

    // Sanity bounds check
    targetPhoton     = constrain(targetPhoton, 0, 180);
    targetColorRatio = constrain(targetColorRatio, 0, 180);
    targetPower      = constrain(targetPower, 0, 180);
  } else {
    // Default values if first boot
    targetPhoton     = 0;   // High Red
    targetColorRatio = 0;   // Low Photon
    targetPower      = 0;   // OFF
    saveState();
  }

  currentPhoton     = targetPhoton;
  currentColorRatio = targetColorRatio;
  currentPower      = targetPower;
}

// --- TELEMETRY & STATUS PRINT ---
void printStatus() {
  Serial.println(F("\n--- SKYPORTAL SYSTEM STATUS ---"));
  
  Serial.print(F("Power Switch (D11): "));
  Serial.print(targetPower);
  Serial.println(targetPower >= 90 ? F("° [ON]") : F("° [OFF]"));

  Serial.print(F("Photon Knob  (D9) : "));
  Serial.print(targetPhoton);
  Serial.println(F("° (0=Red, 180=White)"));

  Serial.print(F("Color Ratio  (D10): "));
  Serial.print(targetColorRatio);
  Serial.println(F("° (0=Low, 180=High)"));
  
  Serial.println(F("-------------------------------\n"));
}

void printHelp() {
  Serial.println(F("=== SKYPORTAL CONTROL COMMANDS ==="));
  Serial.println(F("  PWR <0 or 180>     -> Toggle Power Switch (0=OFF, 180=ON)"));
  Serial.println(F("  PHO <0-180>        -> Set Photon Knob Angle"));
  Serial.println(F("  COL <0-180>        -> Set Color Ratio Knob Angle"));
  Serial.println(F("  SET <pwr> <pho> <col> -> Set all 3 parameters at once"));
  Serial.println(F("  STATUS             -> Display system state"));
  Serial.println(F("=================================="));
}

void setup() {
  Serial.begin(9600);
  delay(500);

  // 1. Load persisted state from non-volatile memory
  loadState();

  // 2. Pre-set servo positions BEFORE attaching to prevent startup snap
  photonServo.write(currentPhoton);
  colorRatioServo.write(currentColorRatio);
  powerServo.write(currentPower);

  // 3. Attach hardware PWM pins
  photonServo.attach(PIN_PHOTON);
  colorRatioServo.attach(PIN_COLOR_RATIO);
  powerServo.attach(PIN_POWER_SWITCH);

  Serial.println(F("SkyPortal Prototype Online. Memory restored."));
  printStatus();
  printHelp();
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    input.toUpperCase();

    if (input == "STATUS") {
      printStatus();
    } 
    else if (input.startsWith("PWR ")) {
      int val = input.substring(4).toInt();
      targetPower = (val >= 90) ? 180 : 0;
      moveServosSmoothly();
      saveState();
      printStatus();
    } 
    else if (input.startsWith("PHO ")) {
      int val = input.substring(4).toInt();
      targetPhoton = constrain(val, 0, 180);
      moveServosSmoothly();
      saveState();
      printStatus();
    } 
    else if (input.startsWith("COL ")) {
      int val = input.substring(4).toInt();
      targetColorRatio = constrain(val, 0, 180);
      moveServosSmoothly();
      saveState();
      printStatus();
    }
    else if (input.startsWith("SET ")) {
      // Parse multi-argument command: SET <pwr> <pho> <col>
      int space1 = input.indexOf(' ', 4);
      int space2 = input.indexOf(' ', space1 + 1);
      
      if (space1 > 0 && space2 > 0) {
        int pwr = input.substring(4, space1).toInt();
        int pho = input.substring(space1 + 1, space2).toInt();
        int col = input.substring(space2 + 1).toInt();

        targetPower      = (pwr >= 90) ? 180 : 0;
        targetPhoton     = constrain(pho, 0, 180);
        targetColorRatio = constrain(col, 0, 180);

        moveServosSmoothly();
        saveState();
        printStatus();
      }
    } 
    else {
      printHelp();
    }
  }
}