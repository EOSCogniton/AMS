### Code ce controle de l'ADC
# https://www.ti.com/lit/ds/symlink/ads1115-q1.pdf?ts=1718378770402

import smbus2
from typing import List


def bin2int(binval: List[bool]):
    st = ""
    for x in binval:
        st += str(x)
    return int(st, 2)


def int2bin(nb: int):
    binst = bin(nb)
    nb0 = 8 - len(binst) + 2
    res = [0] * nb0
    for x in binst[2:]:
        res.append(int(x))
    return res


# I2C channel 0 is connected to the GPIO pins
I2C_CHANNEL = 1  # i2cdetect -y 1 to detect

ADR = [1, 0, 0, 1, 0, 0, 0]  # Adresse de l'ADC, avec le pin address mis au gnd
CONFIG_REG = [0, 0, 0, 0, 0, 0, 0, 1]
DATA_REG = [0, 0, 0, 0, 0, 0, 0, 0]
CHANNEL = {0: [1, 0, 0], 1: [1, 0, 1], 2: [1, 1, 0], 3: [1, 1, 1]}
FSR = 6.144  # V Full Scale rate (valeur maximale de tension)
RESISTOR = 47  # Ohm (Valeur de résistance en entrée de channel)
ENTRY = 3

# Initialize I2C (SMBus)
bus = smbus2.SMBus(I2C_CHANNEL)


def set_channel(entry: int):
    address = bin2int(ADR + [0])  # R/W bit to 0 to Write
    reg = bin2int(CONFIG_REG)
    if not (0 <= entry <= 3):
        print("N° d'entrée invalide")
        return
    bit1 = [1] + CHANNEL[entry] + [0, 0, 0] + [0]
    # Premier bit : éteint ou allumé
    # 2-3-4 bit : sélection du channel d'entrée (possibilité de faire du différentiel, voir datasheet)
    # 5-6-7 bit : sélection de la tension max (ici 6V)
    # 8 bit : mode (conversion en continu ou one shot, ici en continu)
    bit2 = [1, 0, 0] + [0] + [0] + [0] + [1, 1]
    # 1-2-3 bit : Sélection du data rate
    # 4 bit : Mode de comparateur
    # 5 bit : Polarité de comparateur
    # 6 bit : Mode de trigger du comparateur
    # 7-8 bit : nombre de trigger nécessaire pour activer le alert/ready (non utilisé)
    word = bin2int(bit1 + bit2)
    # bus.write_word_data(address, reg, word)


def enable_read():
    address = bin2int(ADR + [0])  # R/W bit high to read
    reg = DATA_REG
    # bus.write_byte(address, reg)


def read_value():
    global VALUE
    addr = bin2int(ADR + [1])
    msg = smbus2.i2c_msg.read(addr, 2)
    msg = [1, 2]
    msgbin = [int2bin(msg[0]), int2bin(msg[1])]
    # bus.i2c_rdwr(msg)
    VALUE = bin2int(msgbin[0][1:] + msgbin[1])


def convert_current(value: int):
    return value * FSR / (2**15) / RESISTOR


def init():
    global VALUE  # Registre dans lequel on stocke la valeur en tension
    VALUE = 0
    set_channel(ENTRY)
    enable_read()
    print("Valeur de tension initiale :", VALUE, " V")
    print("Valeur en courant : ", convert_current(VALUE), " A")


if __name__ == "__main__":
    init()
