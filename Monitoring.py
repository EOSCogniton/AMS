import LTC6811 as BMS
import ADC
import CAN
from read_temp import temp

import gpiozero
import time
import datetime

import os.path
import py7zr

NO_PROBLEM_PIN = 5  # GPIO5

NO_PROBLEM_OUTPUT = gpiozero.LED(NO_PROBLEM_PIN)

MAX_MUX_PIN = 12  # Nombre de thermistors

READ_ENABLE = True  # Affichage dans la console

MODE = "DISCHARGE"  # DISCHARGE, CHARGE or STANDBY

OVERVOLTAGE = 7  # V
UNDERVOLTAGE = 2.55  # V

CHARGE_MAX_T = 47.5  # °C
DISCHARGE_MAX_T = 57.5  # °C

MAX_DISCHARGE_CURRENT = 95  # A

LOW_WRITE_TIME = 10  # Temps d'écriture entre chaque donnée (en s) pour le LOW WRITE


### Functions


def write_data():
    data_raw = int(TIME * 1e8).to_bytes(8) + ADC.VALUE.to_bytes(2)
    for k in range(BMS.TOTAL_IC):
        for i in range(12):
            data_raw += BMS.config.BMS_IC[k].cells.c_codes[i].to_bytes(2)
        for j in range(MAX_MUX_PIN):
            data_raw += BMS.config.BMS_IC[k].temp[j].to_bytes(2)
    data_raw += BMS.bin2int(NO_PROBLEM).to_bytes(5)
    with open("data/data.bin", "ab") as fileab:
        # data=bytearray(data_row)
        fileab.write(data_raw)
    with open("data/actualdata.bin", "wb") as filewb:
        filewb.write(data_raw)


def store_temp(sensor: int):
    global BMS
    for k in range(BMS.TOTAL_IC):
        BMS.config.BMS_IC[k].temp[sensor] = BMS.config.BMS_IC[k].aux.a_codes[0]
        # Les capteurs de temp sont sur le GPIO1 (a_codes[0])


def update_archive():
    with open("data/data.bin", "rb") as f:
        datebin = f.read(8)
        date = datetime.datetime.fromtimestamp(int.from_bytes(datebin) / 1e8).date()
        written = False
        k = 1
        while not written:
            if os.path.isfile("data/" + str(date) + "-" + str(k) + ".7z"):
                k += 1
            else:
                with py7zr.SevenZipFile(
                    "data/" + str(date) + "-" + str(k) + ".7z", "w"
                ) as archive:
                    archive.writeall("data/data.bin", "data.bin")
                os.remove("data/data.bin")
                written = True


if __name__ == "__main__":
    if os.path.isfile("data/data.bin"):
        update_archive()

    BMS.init()
    ADC.init()
    CAN.init()

    BMS.write_read_cfg(READ_ENABLE)
    BMS.start_cell_mes(READ_ENABLE)
    BMS.start_GPIO_mes(READ_ENABLE)

    ACTIVE = True
    MUX_PIN = 0
    # generate_data_file()
    NO_PROBLEM = [0] * (32 * BMS.TOTAL_IC)
    # Création d'un code d'erreur en cas d'interruption
    NO_PROBLEM_OUTPUT.on()

    TIMER = time.time()

    while ACTIVE:
        try:
            TIME = time.time()
            BMS.start_cell_mes(READ_ENABLE)
            BMS.start_GPIO_mes(READ_ENABLE)
            BMS.read_cell_v(READ_ENABLE)
            if MUX_PIN <= MAX_MUX_PIN:
                MUX_PIN += 1
            else:
                MUX_PIN = 1
            BMS.read_GPIO_v(READ_ENABLE)
            store_temp(MUX_PIN - 1)
            ADC.read_value()
            if MODE == "DISCHARGE":
                write_data()
                if ADC.convert_current(ADC.VALUE) >= MAX_DISCHARGE_CURRENT:
                    NO_PROBLEM[1] = 1
                    NO_PROBLEM_OUTPUT.off()
                for current_ic in range(BMS.TOTAL_IC):
                    for cell in range(12):
                        if (
                            BMS.config.BMS_IC[current_ic].cells.c_codes[cell] * 0.0001
                            >= OVERVOLTAGE
                        ):
                            NO_PROBLEM[current_ic * 32 + cell + 2] = 1
                            NO_PROBLEM_OUTPUT.off()
                        elif (
                            BMS.config.BMS_IC[current_ic].cells.c_codes[cell] * 0.0001
                            <= UNDERVOLTAGE
                        ):
                            NO_PROBLEM[current_ic * 32 + cell + 2] = 1
                            NO_PROBLEM_OUTPUT.off()
                    for temp_v in range(MAX_MUX_PIN):
                        if (
                            temp(BMS.config.BMS_IC[current_ic].temp[temp_v])
                            >= DISCHARGE_MAX_T
                        ):
                            NO_PROBLEM[current_ic * 32 + 16 + 2 + temp_v] = 1
                            NO_PROBLEM_OUTPUT.off()
            elif MODE == "CHARGE":
                write_data()
                if ADC.convert_current(ADC.VALUE) >= MAX_DISCHARGE_CURRENT:
                    NO_PROBLEM[1] = 1
                    NO_PROBLEM_OUTPUT.off()
                for current_ic in range(BMS.TOTAL_IC):
                    for cell in range(12):
                        if (
                            BMS.config.BMS_IC[current_ic].cells.c_codes[cell] * 0.0001
                            >= OVERVOLTAGE
                        ):
                            NO_PROBLEM[current_ic * 32 + cell + 2] = 1
                            NO_PROBLEM_OUTPUT.off()
                    for temp_v in range(MAX_MUX_PIN):
                        if (
                            temp(BMS.config.BMS_IC[current_ic].temp[temp_v])
                            >= CHARGE_MAX_T
                        ):
                            NO_PROBLEM[current_ic * 32 + 16 + temp_v + 2] = 1
                            NO_PROBLEM_OUTPUT.off()
            else:
                if TIME - TIMER > LOW_WRITE_TIME:
                    write_data()
                    TIMER = TIME
        except:
            ACTIVE = False
            NO_PROBLEM[0] = 1
            NO_PROBLEM_OUTPUT.off()
