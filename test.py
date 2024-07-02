import LTC6811
import time
import spidev

LTC6811.init()
while True:
    LTC6811.write_read_cfg()
    print(LTC6811.spi_write_read([0, 50, 100, 150], 6))
    time.sleep(0.1)

# spi = spidev.SpiDev()
# MAX_SPEED_HZ = 1000000  # Fréquence max et par défaut du bus SPI

# # We only have SPI bus 0 available to us on the Pi
# bus = 0

# # Device is the chip select pin. Set to 0 or 1, depending on the connections
# device = 0

# # Open a connection to a specific bus and device (chip select pin)
# spi.open(bus, device)

# # Set SPI speed and mode
# spi.max_speed_hz = MAX_SPEED_HZ
# spi.mode = 3
# import gpiozero

# led = gpiozero.LED(5)

# LTC6811.init()
# while True:
#     # LTC6811.write_read_cfg()
#     print(LTC6811.spi.xfer3([19] * 100))
#     # time.sleep(0.001)
#     # print(LTC6811.spi.readbytes(1000))
#     # led.on()
#     time.sleep(0.1)
#     # led.off()
#     # time.sleep(0.01)
