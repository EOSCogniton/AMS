from ADBSM1818 import TOTAL_IC
from Monitoring import MAX_MUX_PIN
from Monitoring import MAX_CELL
from read_temp import temp
from ADC import convert_current

import datetime

filepath = "/usr/share/AMS/data/actualdata.bin"

file = open(filepath, "rb")

chunksize = 8 + 2 + (MAX_CELL + MAX_MUX_PIN) * 2 * TOTAL_IC

data_raw = []

while True:
    chunk = file.read(chunksize)
    data_raw.append(chunk)
    if not chunk:
        break

data = []

for raw in data_raw:
    mes = []
    mes.append(datetime.datetime.fromtimestamp(int.from_bytes(raw[0:8]) / 1e8))
    mes.append(round(convert_current(int.from_bytes(raw[8:10])), 2))
    for current_bms in range(TOTAL_IC):
        for cell in range(MAX_CELL):
            indic = (current_bms * (MAX_CELL + MAX_MUX_PIN) + cell + 1) * 2 + 8
            mes.append(round(int.from_bytes(raw[indic : indic + 2]) * 0.0001, 4))
        for temp_n in range(MAX_MUX_PIN):
            indic = (current_bms * (MAX_CELL + MAX_MUX_PIN) + MAX_CELL + temp_n + 1) * 2 + 8
            mes.append(
                round(float(temp(int.from_bytes(raw[indic : indic + 2]) * 0.0001)), 4)
            )
    data.append(mes)


def print_data(n: int):
    line = data[n]
    print(len(line))
    print("Date :", line[0])
    print("Courant (A) :", line[1])
    for i in range(TOTAL_IC):
        print("BMS " + str(i + 1))
        strcell = ""
        for k in range(MAX_CELL):
            strcell += "C" + str(k + 1) + ": " + str(line[k + 2]) + ", "
        print("Cellules (V) : " + strcell[:-2])
        strtemp = ""
        for k in range(MAX_MUX_PIN):
            strtemp += "T" + str(k + 1) + ": " + str(line[k + MAX_CELL + 2]) + ", "
        print("Températures (°C) : " + strtemp[:-2])
    print()


for i in range(len(data)-2):
    print_data(i)
