import spidev
import time
import gpiod

chip = gpiod.Chip("gpiochip4")
cs_line = chip.get_line(24)
cs_line.request(consumer="CS", type=gpiod.LINE_REQ_DIR_OUT)

spi = spidev.SpiDev()
MAX_SPEED_HZ = 2000000  # Fréquence max et par défaut du bus SPI

# We only have SPI bus 0 available to us on the Pi
bus = 0

# Device is the chip select pin. Set to 0 or 1, depending on the connections
device = 0

# Open a connection to a specific bus and device (chip select pin)
spi.open(bus, device)

# Set SPI speed and mode
spi.max_speed_hz = MAX_SPEED_HZ
spi.mode = 3

while True:
    # cs_line.set_value(0)
    spi.xfer([1] * 10)
    time.sleep(0.01)
    # cs_line.set_value(1)
