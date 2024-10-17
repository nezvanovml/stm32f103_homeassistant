# stm32_homeassistant
Version: 1.0

Integration for Home Assistant.

Installation: clone this repo to config/custom_components/ of your instance of HA.

Supports:
* Relays (switches controlling relays)
* VirtualSwitches (virtual switches)
* ButtonBinarySensor (Button inputs on device)
* SimpleBinarySensor (Binary inputs on device)
* VirtualBinarySensor (virtual indicators)
* AnalogInSensor (Analog inputs on devcice, mapped to 0..100)
* TemperatureSensor (1Wire DS18B20 sensors on device)
