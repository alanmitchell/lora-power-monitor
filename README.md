# lora-power-monitor
Electric Power Sensor that transmits measurements via LoRaWAN.

Sensor is designed to be easily installed, as it uses a UL-listed AC/AC 5VAC plug-in power adapter to sense the AC voltage of the device being measured.  (If the device being measured used 240VAC, reported power measurements need to be multiplied by 2.)  The AC current of the device being measured is sensed via a clamp-on Current Transformer (CT).  Loads up to 20 Amps can be measured with the parts specified.  Changing the burden resistor on the CT would allow measuremnt of higher current levels.

An Adafruit SAMD21 QT Py microcontroller is used for all computing tasks and taking measurement samples of the AC voltage and current. A SEEED Studio Lora-E5 LoRaWAN module handles all the LoRaWAN protocol and radio transceiver tasks.

The QT Py is programmed in CircuitPython, and all of the code is in the `main.py` module.  Initial configuration of the Lora-E5 module is done with a PC through a USB-to-TTL converter; the `init_config.py` Python script does the configuration, and records LoRaWAN keys and IDs into a `keys.csv` file.

The sensor transmits readings when significant changes in power consumption occur.  So readings are not evenly spaced in the time.  If average power use is desired, proper time-weighted averaging must be applied.

See rough [Design Notes Here](https://docs.google.com/document/d/1PNGpCO27ZZ14owpZriBHVxIDtBDqJXV66IEywvQ59-c/edit?usp=sharing).
