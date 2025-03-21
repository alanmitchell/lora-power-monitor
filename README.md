# lora-power-monitor
Electric Power Sensor that transmits measurements via LoRaWAN.

Sensor is designed to be easily installed, as it uses a UL-listed AC/AC 5VAC plug-in power adapter to sense the AC voltage of the device being measured.  (If the device being measured uses 240VAC, reported power measurements need to be multiplied by 2.)  The AC current of the device being measured is sensed via a clamp-on Current Transformer (CT).  Loads up to 20 Amps can be measured with the parts specified.  Changing the burden resistor on the CT would allow measurement of higher current levels.

An Adafruit SAMD21 QT Py microcontroller is used for all computing tasks and taking measurement samples of the AC voltage and current. A SEEED Studio Lora-E5 LoRaWAN module handles all the LoRaWAN protocol and radio transceiver tasks.  The E5 needs to be configured to work on the US Things Network frequency
band.  Configuration is done by a separate GitHub project: https://github.com/alanmitchell/e5-lora-config .

CircuitPython 7.3.3 is the programming language (a serial bug was found in 
CircuitPython 8.0).

The QT Py is programmed in CircuitPython, and the main code file is `code.py`.
Most supporting code is in the `lib` folder, which is compiled to `.mpy` files
before being transferred to the microcontroller. Transfer of the code and default
calibration file to the microcontroller is done through the `deploy` bash script.
Initial configuration of the Lora-E5 module is done with a PC through a USB-to-TTL converter; the `tools/init_config.py` Python script does the configuration, and records LoRaWAN keys and IDs into a `tools/keys.csv` file.  Calibration of the unit
is accomplished through the `tools/calibrate_unit.py` script.

The sensor can be operated in two modes, as controlled by the config.py file:

* A detailed mode where a reading is transmitted when significant changes in power consumption occur.  In this mode, readings are not evenly spaced in the time.  
* A fixed interval mode, where average power readings for fixed length intervals are transmitted.

See rough [Design Notes Here](https://docs.google.com/document/d/1PNGpCO27ZZ14owpZriBHVxIDtBDqJXV66IEywvQ59-c/edit?usp=sharing).
