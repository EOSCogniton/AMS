import LTC6811 as BMS
import ADC
import can
from read_temp import temp

import gpiozero
import time
import datetime

import os.path
import py7zr

PATH = "/usr/share/AMS/"
NO_PROBLEM_PIN = 5  # GPIO5

NO_PROBLEM_OUTPUT = gpiozero.LED(NO_PROBLEM_PIN)
# Selection du PIN pour la sortie du SCS

MAX_MUX_PIN = 12  # Nombre de thermistors

READ_ENABLE = False  # Affichage dans la console

MODE = "DISCHARGE"  # DISCHARGE, CHARGE or STANDBY

OVERVOLTAGE = 7  # V
UNDERVOLTAGE = 2.55  # V

CHARGE_MAX_T = 47.5  # °C
DISCHARGE_MAX_T = 57.5  # °C

MAX_DISCHARGE_CURRENT = 95  # A

LOW_WRITE_TIME = 10  # Temps d'écriture entre chaque donnée (en s) pour le LOW WRITE

CANID = 0x17

n = 0

### Functions


def write_data():  # Fonction qui convertie les données en données binaires et les écrit dans les fichiers data.bin et actualdata.bin
    data_raw = int(TIME * 1e8).to_bytes(8) + ADC.VALUE.to_bytes(2)
    for k in range(BMS.TOTAL_IC):
        for i in range(12):
            data_raw += BMS.config.BMS_IC[k].cells.c_codes[i].to_bytes(2)
        for j in range(MAX_MUX_PIN):
            data_raw += BMS.config.BMS_IC[k].temp[j].to_bytes(2)
    data_raw += BMS.bin2int(NO_PROBLEM).to_bytes(5)
    with open(PATH + "data/data.bin", "ab") as fileab:
        # data=bytearray(data_row)
        fileab.write(data_raw)
    with open(PATH + "data/actualdata.bin", "wb") as filewb:
        filewb.write(data_raw)


def store_temp(sensor: int):  # Stockage des valeurs de températures
    global BMS
    for k in range(BMS.TOTAL_IC):
        BMS.config.BMS_IC[k].temp[sensor] = BMS.config.BMS_IC[k].aux.a_codes[0]
        # Les capteurs de temp sont sur le GPIO1 (a_codes[0])


def update_archive():  # Création d'archive comprimée à la date du jour
    with open(PATH + "data/data.bin", "rb") as f:
        datebin = f.read(8)
        date = datetime.datetime.fromtimestamp(int.from_bytes(datebin) / 1e8).date()
        written = False
        k = 1
        while not written:
            if os.path.isfile("data/" + str(date) + "-" + str(k) + ".7z"):
                k += 1
            else:
                with py7zr.SevenZipFile(
                    PATH + "data/" + str(date) + "-" + str(k) + ".7z", "w"
                ) as archive:
                    archive.writeall(PATH + "data/data.bin", "data.bin")
                os.remove(PATH + "data/data.bin")
                written = True


def calc_temp():  # Calcul sur les données de températures
    sum = 0
    min = 100
    max = -100
    indicmin = [1, 1]
    indicmax = [1, 1]
    for k in range(BMS.TOTAL_IC):
        for i in range(MAX_MUX_PIN):
            tempe = temp(BMS.config.BMS_IC[k].temp[i])
            sum += tempe
            if -50 < tempe <= min:
                indicmin = [k + 1, i + 1]
                min = tempe
            if 500 >= tempe >= max:
                indicmax = [k + 1, i + 1]
                max = tempe
    return (sum / (BMS.TOTAL_IC * MAX_MUX_PIN), max, indicmax, min, indicmin)


def calc_voltage():  # Calcul sur les données de tension
    sum = 0
    min = 100
    max = -100
    indicmin = [1, 1]
    indicmax = [1, 1]
    for k in range(BMS.TOTAL_IC):
        for i in range(12):
            volt = BMS.config.BMS_IC[k].cells.c_codes[i] * 0.0001
            sum += volt
            if volt <= min:
                indicmin = [k + 1, i + 1]
                min = volt
            if volt >= max:
                indicmax = [k + 1, i + 1]
                max = volt
    return (sum, sum / (BMS.TOTAL_IC * 12), max, indicmax, min, indicmin)


def send_data_CAN():  # Envoi des données via CAN
    global n
    tempe = calc_temp()
    volt = calc_voltage()
    tension = volt[0]
    tensionbin = BMS.int2bin(int(tension * 100))
    tempmax = tempe[1]
    tempmaxbin = BMS.int2bin(int(tempmax * 100))
    if len(tensionbin) <= 8:
        tensionbin = [0] * 8 + tensionbin
    if len(tempmaxbin) <= 8:
        tempmaxbin = [0] * 8 + tempmaxbin
    n += 1
    if n > 200:
        n = 0
    with can.Bus(channel="can0", interface="socketcan") as bus:
        msg = can.Message(
            arbitration_id=CANID,
            data=[
                BMS.bin2int(tensionbin[:8]),
                BMS.bin2int(tensionbin[8:]),
                BMS.bin2int(tempmaxbin[:8]),
                BMS.bin2int(tempmaxbin[8:]),
                n,
            ],
        )
        try:
            bus.send(msg)
        except:
            print("Message non envoyé")


if __name__ == "__main__":
    if os.path.isfile(PATH + "data/data.bin"):
        update_archive()

    BMS.init()  # On initialise les variables du BMS
    ADC.init()  # On initialise les variables de l'ADC

    BMS.write_read_cfg(READ_ENABLE)  # On écrit la config actuelle dans le BMS

    ACTIVE = True  # On active la boucle
    MUX_PIN = 0  # On commence par traiter le capteur de température au PIN 0
    NO_PROBLEM = [0] * (32 * BMS.TOTAL_IC)
    # Création d'un code d'erreur en cas d'interruption
    NO_PROBLEM_OUTPUT.on()  # On ferme le SDC

    TIMER = time.time()

    while ACTIVE:
        # try:
        TIME = time.time()
        send_data_CAN()
        BMS.start_cell_mes(READ_ENABLE)
        BMS.start_GPIO_mes(READ_ENABLE)
        BMS.read_cell_v(READ_ENABLE)
        if MUX_PIN <= MAX_MUX_PIN:
            # On change de capteur de température à chaque itération
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
                    # On teste pour voir s'il y a des problemes d'over/undervoltage et on modifie le code d'erreur en conséquence
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
                    # idem mais pour les températures
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
                    if temp(BMS.config.BMS_IC[current_ic].temp[temp_v]) >= CHARGE_MAX_T:
                        NO_PROBLEM[current_ic * 32 + 16 + temp_v + 2] = 1
                        NO_PROBLEM_OUTPUT.off()
        else:
            if TIME - TIMER > LOW_WRITE_TIME:
                # Dans le cas ou on veut juste monitorer les valeurs, sur de longues durées
                write_data()
                TIMER = TIME
        # except:
        #     ACTIVE = False
        #     NO_PROBLEM[0] = 1
        #     NO_PROBLEM_OUTPUT.off()
