import LTC6811 as BMS
import ADC
import CAN

import csv

import gpiod

NO_PROBLEM_PIN = 29 # GPIO5

chip = gpiod.Chip('gpiochip4')

NO_PROBLEM_OUTPUT = chip.get_line(NO_PROBLEM_PIN)

NO_PROBLEM_OUTPUT.request(consumer="NO_PROBLEM_OUTPUT",type=gpiod.LINE_REQ_DIR_OUT)

file = open('data.csv')
csvreader = csv.reader(file)
header = []
header = next(csvreader)

BMS.init()
ADC.init()
CAN.init()

ACTIVE = True
MUX_PIN = 0

MAX_MUX_PIN = 12 #Nombre de thermistors

NO_PROBLEM_OUTPUT.set_value(1)

while ACTIVE:
    try:
        BMS.write_read_cfg()
        BMS.start_cell_mes()
        BMS.start_GPIO_mes()
        BMS.read_cell_v()
        if MUX_PIN <= MAX_MUX_PIN:
            MUX_PIN+=1
        else:
            MUX_PIN=1
        BMS.read_GPIO_v()
        ADC.read_value()
    except:
        ACTIVE = False
        NO_PROBLEM_OUTPUT.set_value(0)
        print("Erreur détectée - ouverture SDC")

