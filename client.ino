#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>

#include <WebSocketsClient.h>
#include <Hash.h>

#include <Servo.h>
#include <Eventually.h>

ESP8266WiFiMulti WiFiMulti;
WebSocketsClient webSocket;

Servo servo1;

bool isServoDown;

#define USE_SERIAL Serial

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
	switch(type) {
		case WStype_DISCONNECTED:
			USE_SERIAL.printf("[WSc] Disconnected!\n");
			break;
		case WStype_CONNECTED: {
			USE_SERIAL.printf("[WSc] Connected to url: %s\n", payload);
			// send message to server when Connected
			// webSocket.sendTXT("Connected");
		}
			break;
		case WStype_TEXT:
			USE_SERIAL.printf("[WSc] get text: %s\n", payload);
			if (strcmp((char*) payload, "servodown") == 0) { // if payload == 'servodown'
				servoDown();
			}
			// send message to server
			// webSocket.sendTXT("message here");
			break;
		case WStype_BIN:
			USE_SERIAL.printf("[WSc] get binary length: %u\n", length);
			hexdump(payload, length);
			// send data to server
			// webSocket.sendBIN(payload, length);
			break;
    case WStype_PING:
      // pong will be send automatically
      USE_SERIAL.printf("[WSc] get ping\n");
      break;
    case WStype_PONG:
      // answer to a ping we send
      USE_SERIAL.printf("[WSc] get pong\n");
      break;
    }
}

void servoDown() {
	servo1.write(0);
	isServoDown = true;
	delay(500);
}

void servoUp() {
	servo1.write(90);
	isServoDown = false;
	delay(500);
}

void setup() {
	// USE_SERIAL.begin(921600);
	USE_SERIAL.begin(115200);

	//Serial.setDebugOutput(true);
	USE_SERIAL.setDebugOutput(true);

	USE_SERIAL.println();
	USE_SERIAL.println();
	USE_SERIAL.println();

	for(uint8_t t = 4; t > 0; t--) {
		USE_SERIAL.printf("[SETUP] BOOT WAIT %d...\n", t);
		USE_SERIAL.flush();
		delay(1000);
	}

	WiFi.setAutoConnect(true); // set this to False if WiFi details changed
	WiFiMulti.addAP("RM411-Arduino-2.4", "sbcps23201000");

	//WiFi.disconnect();
	while(WiFiMulti.run() != WL_CONNECTED) {
		delay(100);
	}

	// server address, port and URL
	webSocket.begin("192.168.1.2", 5000, "/");

	// event handler
	webSocket.onEvent(webSocketEvent);

	// try ever 3000 again if connection has failed
	webSocket.setReconnectInterval(3000);

	pinMode(A0, INPUT);
	servo1.attach(D2);
	servoDown();
}

void loop() {
	webSocket.loop();
	//webSocket.sendTXT("hit");
	int result = analogRead(A0);
	USE_SERIAL.printf("Sensor status: %d\n", result);
	if (result > 970 && isServoDown) {
		USE_SERIAL.printf("Sensor is Hit!\n");
		webSocket.sendTXT("Hit!");
		servoUp();
		// delay(1000);
		// servoDown();
	}
	delay(50);
}