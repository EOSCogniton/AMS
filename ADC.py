### Code ce controle de l'ADC
# https://www.ti.com/lit/ds/symlink/ads1115-q1.pdf?ts=1718378770402

import smbus2
from typing import List

def bin2int(binval: List[bool]):
    st = ""
    for x in binval:
        st += str(x)
    return int(st, 2)

# I2C channel 0 is connected to the GPIO pins
channel = 0

ADR = [1, 0, 0, 1, 0, 0, 0]  # Adresse de l'ADC, avec le pin address mis au gnd
SELECT_CFG = [0, 0, 0, 0, 0, 0, 0, 1]
SELECT_CONV = [0, 0, 0, 0, 0, 0, 0, 0]
CHANNEL = {0: [1, 0, 0], 1: [1, 0, 1], 2: [1, 1, 0], 3: [1, 1, 1]}

# Initialize I2C (SMBus)
bus = smbus2.SMBus(channel)


def init(entry: int):

    bit1 = SELECT_CFG
    if not (0 <= entry <= 3):
        print("N° d'entrée invalide")
        return
    bit2 = [1] + CHANNEL[entry] + [0, 0, 0] + [0]
    # Premier bit : éteint ou allumé
    # 2-3-4 bit : sélection du channel d'entrée (possibilité de faire du différentiel, voir datasheet)
    # 5-6-7 bit : sélection de la tension max (ici 6V)
    # 8 bit : mode (conversion en continu ou one shot, ici en continu)
    bit3 = [1, 0, 0] + [0] + [0] + [0] + [1, 1]
    # 1-2-3 bit : Sélection du data rate
    # 4 bit : Mode de comparateur
    # 5 bit : Polarité de comparateur
    # 6 bit : Mode de trigger du comparateur
    # 7-8 bit : nombre de trigger nécessaire pour activer le alert/ready (non utilisé)
    initmsg = [bin2int(bit1),bin2int(bit2),bin2int(bit3)]


# Create a sawtooth wave 16 times
for i in range(0x10000):
    pass
    # Create our 12-bit number representing relative voltage
    voltage = i & 0xFFF

    # Shift everything left by 4 bits and separate bytes
    msg = (voltage & 0xFF0) >> 4
    msg = [msg, (msg & 0xF) << 4]

    # Write out I2C command: address, reg_write_dac, msg[0], msg[1]
    bus.write_i2c_block_data(address, reg_write_dac, msg)
