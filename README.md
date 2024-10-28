### Erase flash
C:\Users\Drug\AppData\Local\Programs\Thonny\python.exe -u -m esptool --port COM11 --chip esp32c3 erase_flash
### Write firmware
C:\Users\Drug\AppData\Local\Programs\Thonny\python.exe -u -m esptool --port COM11 --baud 460800 --chip esp32c3 write_flash -z 0x0 ESP32_GENERIC_C3-20241025-v1.24.0.bin
### Connect to serial
C:\Users\Drug\AppData\Local\Programs\Thonny\python.exe -u -m serial.tools.miniterm COM11 115200