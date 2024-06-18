import LTC6811 as BMS
import ADC
import CAN

import csv

import gpiod

import datetime

NO_PROBLEM_PIN = 29  # GPIO5

chip = gpiod.Chip("gpiochip4")

NO_PROBLEM_OUTPUT = chip.get_line(NO_PROBLEM_PIN)

NO_PROBLEM_OUTPUT.request(consumer="NO_PROBLEM_OUTPUT", type=gpiod.LINE_REQ_DIR_OUT)

file = open("data.csv")
csvreader = csv.reader(file)
header = []
header = next(csvreader)

BMS.init()
ADC.init()
CAN.init()

ACTIVE = True
MUX_PIN = 0

MAX_MUX_PIN = 12  # Nombre de thermistors

NO_PROBLEM_OUTPUT.set_value(1)

while ACTIVE:
    try:
        BMS.write_read_cfg()
        BMS.start_cell_mes()
        BMS.start_GPIO_mes()
        BMS.read_cell_v()
        if MUX_PIN <= MAX_MUX_PIN:
            MUX_PIN += 1
        else:
            MUX_PIN = 1
        BMS.read_GPIO_v()
        ADC.read_value()
    except:
        ACTIVE = False
        NO_PROBLEM_OUTPUT.set_value(0)
        print("Erreur détectée - ouverture SDC")


def generate_data_file():
    header = ["Date", "Current"]
    for k in range(LTC6811.TOTAL_IC):
        for i in range(12):
            header.append("BMS" + str(k + 1) + " - Cell" + str(i + 1))
        for j in range(MAX_MUX_PIN):
            header.append("BMS" + str(k + 1) + " - Temp" + str(j + 1))
    with open("data.csv", "w+", newline="") as file:
        writer = csv.writer(file)

        writer.writerow(header)


def write_data():
    data_row = [str(datetime.datetime.now()), str(ADC.VALUE)]
    for k in range(LTC6811.TOTAL_IC):
        for i in range(12):
            data_row.append("{config.BMS_IC[k].cells.c_codes[i] * 0.0001:.4f}")
        for j in range(MAX_MUX_PIN):
            data_row.append("BMS" + str(k + 1) + " - Temp" + str(j + 1))
    with open("data.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(data_row)
