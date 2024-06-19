import LTC6811 as BMS
import ADC
import CAN
from read_temp import temp

import csv
import gpiod
import time
import datetime

import os.path

NO_PROBLEM_PIN = 29  # GPIO5

chip = gpiod.Chip("gpiochip4")

NO_PROBLEM_OUTPUT = chip.get_line(NO_PROBLEM_PIN)

NO_PROBLEM_OUTPUT.request(consumer="NO_PROBLEM_OUTPUT", type=gpiod.LINE_REQ_DIR_OUT)

MAX_MUX_PIN = 12  # Nombre de thermistors

READ_ENABLE = True  # Affichage dans la console

LOW_WRITE = False  # Ecriture lente des données (ttes les 10s)


### Functions
def generate_data_file():
    header = ["Date", "Current"]
    for k in range(BMS.TOTAL_IC):
        for i in range(12):
            header.append("BMS" + str(k + 1) + " - Cell" + str(i + 1))
        for j in range(MAX_MUX_PIN):
            header.append("BMS" + str(k + 1) + " - Temp" + str(j + 1))
    with open("data.csv", "w+", newline="") as file:
        writer = csv.writer(file)

        writer.writerow(header)


def write_data():
    data_raw = int(time.time() * 1e8).to_bytes(8) + ADC.VALUE.to_bytes(2)
    for k in range(BMS.TOTAL_IC):
        for i in range(12):
            data_raw += BMS.config.BMS_IC[k].cells.c_codes[i].to_bytes(2)
        for j in range(MAX_MUX_PIN):
            data_raw += BMS.config.BMS_IC[k].temp[j].to_bytes(2)
    with open("data.bin", "ab") as file:
        # data=bytearray(data_row)
        file.write(data_raw)


def store_temp(sensor: int):
    global BMS
    for k in range(BMS.TOTAL_IC):
        BMS.config.BMS_IC[k].temp[sensor] = BMS.config.BMS_IC[k].aux.a_codes[
            0
        ]  # Les capteurs de temp sont sur le GPIO1 (a_codes[0])


def update_archive():
    with open("data.bin", "rb") as f:
        datebin = f.read(8)
        date = datetime.datetime.fromtimestamp(int.from_bytes(datebin) / 1e8).date()
        written = False
        k = 1
        while not written:
            if os.path.isfile("archive/" + str(date) + "-" + str(k) + ".bin"):
                k += 1
            else:
                os.rename("data.bin", "archive/" + str(date) + "-" + str(k) + ".bin")
                written = True


if __name__ == "__main__":
    if os.path.isfile("data.bin"):
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
    NO_PROBLEM_OUTPUT.set_value(1)

    TIMER = time.time()

    while ACTIVE:
        try:
            BMS.read_cell_v(READ_ENABLE)
            if MUX_PIN <= MAX_MUX_PIN:
                MUX_PIN += 1
            else:
                MUX_PIN = 1
            BMS.read_GPIO_v(READ_ENABLE)
            store_temp(MUX_PIN - 1)
            ADC.read_value()
            if LOW_WRITE == False:
                write_data()
            else:
                snap_time = time.time()
                if snap_time() - TIMER > 10:
                    write_data
                    TIMER = snap_time
        except:
            ACTIVE = False
            NO_PROBLEM_OUTPUT.set_value(0)
            print("Erreur détectée - ouverture SDC")
