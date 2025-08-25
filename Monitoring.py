import ADBSM1818 as BMS
import ADC
import can
from read_temp import temp
from read_temp import volt

import gpiozero
import time
import datetime

import os.path
import py7zr

PATH = "/usr/share/AMS/"
NO_PROBLEM_PIN = 5  # GPIO5

NO_PROBLEM_OUTPUT = gpiozero.LED(NO_PROBLEM_PIN)
# Selection du PIN pour la sortie du SCS

MAX_CELL = 13 # Nombre de cellules

MAX_MUX_PIN = 16  # Nombre de thermistors

READ_ENABLE =False # Affichage dans la console

MODE = "DISCHARGE"  # DISCHARGE, CHARGE or STANDBY

OVERVOLTAGE = 7  # V
UNDERVOLTAGE = 1  # V
NOMINAL_VOLTAGE = 230 # V

CHARGE_MAX_T = 47.5  # °C
DISCHARGE_MAX_T = 57.5 #57.5  # °C

MAX_DISCHARGE_CURRENT = 95  # A
MAX_CHARGE_CURRENT = 25 # A

LOW_WRITE_TIME = 10  # Temps d'écriture entre chaque donnée (en s) pour le LOW WRITE

CANID = 0x17
CHARGER_CANID = 0x1806E5F4

n = 0

### Functions


def write_data():  # Fonction qui convertie les données en données binaires et les écrit dans les fichiers data.bin et actualdata.bin
    if(ADC.VALUE <= 0):
        data_raw = int(TIME * 1e8).to_bytes(8) + (0).to_bytes(2)
    else:
        data_raw = int(TIME * 1e8).to_bytes(8) + ADC.VALUE.to_bytes(2)
    for k in range(BMS.TOTAL_IC):
        for i in range(MAX_CELL):
            data_raw += BMS.config.BMS_IC[k].cells.c_codes[i].to_bytes(2)
        for j in range(MAX_MUX_PIN):
            data_raw += BMS.config.BMS_IC[k].temp[j].to_bytes(2)
    data_raw += BMS.bin2int(NO_PROBLEM).to_bytes(len(NO_PROBLEM)//8)
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


def calc_temp():  # Calcul sur les données de températures (renvoie moyenne, max, indice du max, min, indice du min)
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
        for i in range(MAX_CELL):
            volt = BMS.config.BMS_IC[k].cells.c_codes[i] * 0.0001
            sum += volt
            if volt <= min:
                indicmin = [k + 1, i + 1]
                min = volt
            if volt >= max:
                indicmax = [k + 1, i + 1]
                max = volt
    return (sum, sum / (BMS.TOTAL_IC * MAX_CELL), max, indicmax, min, indicmin)


def send_charging_CAN():
    voltage_charge = NOMINAL_VOLTAGE
    current_charge = MAX_CHARGE_CURRENT
    voltage_charge_bin = (int(voltage_charge*10)) #O.1V/bit
    current_charge_bin = (int(current_charge*10)) #0.1A/bit
    BYTE1 = (voltage_charge_bin >> 8) & 0xFF # Voltage High byte
    BYTE2 = voltage_charge_bin & 0xFF # Voltage Low byte
    BYTE3 = (current_charge_bin >> 8) & 0xFF # Current high byte
    BYTE4 = current_charge_bin & 0xFF
    BYTE5 = int(0x00) # Start charging
    BYTE6 = int(0x00) # Charging mode
    with can.Bus(channel="can1", interface="socketcan") as bus:
        msg = can.Message(
            arbitration_id=CHARGER_CANID,
            data=[
                BYTE1,
                BYTE2,
                BYTE3,
                BYTE4,
                BYTE5,
                BYTE6
            ],
        )
        try:
            bus.send(msg)
        except Exception as err:
            print("Message CAN non envoyé :")
            print(f"{type(err).__name__} was raised: {err}")

def send_data_CAN():  # Envoi des données au VCU via CAN
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
                n,  # for test purpose only
            ],
        )
        try:
            bus.send(msg)
        except Exception as err:
            print("Message CAN non envoyé :")
            print(f"{type(err).__name__} was raised: {err}")

def open_wire():
    return BMS.open_wire_check(MAX_CELL)

if __name__ == "__main__":
    if os.path.isfile(PATH + "data/data.bin"):
        update_archive()

    BMS.init()  # On initialise les variables du BMS
    ADC.init()  # On initialise les variables de l'ADC

    BMS.reset_mux(READ_ENABLE)
    BMS.clear_all_DSC(READ_ENABLE)  # On efface les DSC
    BMS.clear_all_mes(READ_ENABLE)

    BMS.write_read_cfg(READ_ENABLE)  # On écrit la config actuelle dans le BMS
    BMS.write_read_cfgb(READ_ENABLE)

    tps = time.time()  # On initialise le timer

    ACTIVE = True  # On active la boucle
    MUX_PIN = 1  # On commence par traiter le capteur de température au PIN 1
    NO_PROBLEM = [0] * (64 * BMS.TOTAL_IC)
    # Création d'un code d'erreur en cas d'interruption
    NO_PROBLEM_OUTPUT.on()  # On ferme le SDC

    TIMER = time.time()
    
    for i in range(MAX_MUX_PIN):
        time1 = time.time()
        BMS.select_mux_pin(i+1,READ_ENABLE)
        time2 = time.time()
        BMS.test_start_GPIO_mes(READ_ENABLE)
        time3 = time.time()
        BMS.read_GPIO_v(READ_ENABLE)
        time4 = time.time()
        store_temp(i - 1)
    TIME = time.time()
    write_data()
    pbnow = 0
    thermistor = 1
    print("Nombre bms : " + str(BMS.TOTAL_IC))
    while ACTIVE:
        #try:
            pbnow=0
            TIME = time.time()
            send_data_CAN()
            #BMS.select_mux_pin(MUX_PIN,READ_ENABLE)  # On sélectionne le capteur de température

            openCircuit = open_wire()
            if(openCircuit):
                print("Circuit ouvert")
                NO_PROBLEM_OUTPUT.off()
                pbnow =1

            BMS.test_start_cell_mes()  # On démarre la mesure des cellules et GPIO1 et 2
            
            BMS.read_cell_v(READ_ENABLE)
            #BMS.read_GPIO_v(READ_ENABLE)
            #store_temp(MUX_PIN - 1)
            #if MUX_PIN < MAX_MUX_PIN:
                # On change de capteur de température à chaque itération
            #    MUX_PIN += 1
            #else:
            #    MUX_PIN = 1
            if thermistor==1:
                for i in range(MAX_MUX_PIN//2):
                    BMS.select_mux_pin(i+1,READ_ENABLE)
                    BMS.test_start_GPIO_mes(READ_ENABLE)
                    BMS.read_GPIO_v(READ_ENABLE)
                    store_temp(i - 1)
                thermistor=0
            else:
                for i in range(MAX_MUX_PIN//2,MAX_MUX_PIN):
                    BMS.select_mux_pin(i+1,READ_ENABLE)
                    BMS.test_start_GPIO_mes(READ_ENABLE)
                    BMS.read_GPIO_v(READ_ENABLE)
                    store_temp(i - 1)
                thermistor=1

            ADC.read_value()

            if MODE == "DISCHARGE":
                write_data()
                if ADC.convert_current(ADC.VALUE) <= 0:
                    NO_PROBLEM [1] = 1
                    print("Current sensor disconnected")
                    NO_PROBLEM_OUTPUT.off()
                    pbnow =1
                if ADC.convert_current(ADC.VALUE) >= MAX_DISCHARGE_CURRENT and ADC.convert_current(ADC.VALUE) >= 0:
                    NO_PROBLEM[1] = 1
                    print("Current error")
                    NO_PROBLEM_OUTPUT.off()
                    pbnow =1
                for current_ic in range(BMS.TOTAL_IC):
                    for cell in range(MAX_CELL):
                        # On teste pour voir s'il y a des problemes d'over/undervoltage et on modifie le code d'erreur en conséquence
                        if (BMS.config.BMS_IC[current_ic].cells.c_codes[cell] * 0.0001>= OVERVOLTAGE   ):
                            NO_PROBLEM[current_ic * 64 + cell + 2] = 1
                            print("Overvoltage")
                            NO_PROBLEM_OUTPUT.off()
                            pbnow =1
                        elif (BMS.config.BMS_IC[current_ic].cells.c_codes[cell] * 0.0001<= UNDERVOLTAGE):
                            NO_PROBLEM[current_ic * 64 + cell + 2] = 1
                            print("Undervoltage")
                            NO_PROBLEM_OUTPUT.off()
                            pbnow =1
                    for MUX_PIN in range(MAX_MUX_PIN):
                        MUX_PIN+=1
                        if (temp(BMS.config.BMS_IC[current_ic].temp[MUX_PIN-1]*0.0001)>= DISCHARGE_MAX_T and BMS.config.BMS_IC[current_ic].temp[MUX_PIN-1]!=0):

                            NO_PROBLEM[current_ic * 64 + 16 + 2 + MUX_PIN-1] = 1
                            print("Too hot")
                            NO_PROBLEM_OUTPUT.off()
                            pbnow =1
                        if(BMS.config.BMS_IC[current_ic].temp[MUX_PIN-1]==0):
                            print("Thermistance "+ str(MUX_PIN) + " 0V")
                        if((BMS.config.BMS_IC[current_ic].temp[MUX_PIN-1])>29000 and MUX_PIN >=9):
                            print("Temp sensor disconnected")
                            NO_PROBLEM[current_ic * 64 + 16 + 2 + MUX_PIN-1] = 1
                            pbnow =1
                            NO_PROBLEM_OUTPUT.off()
                    print(time.time()-TIME)
                    if not pbnow:
                        NO_PROBLEM_OUTPUT.on()

            elif MODE == "CHARGE":
                write_data()
                if ADC.convert_current(ADC.VALUE) >= MAX_CHARGE_CURRENT:
                    NO_PROBLEM[1] = 1
                    NO_PROBLEM_OUTPUT.off()
                for current_ic in range(BMS.TOTAL_IC):
                    for cell in range(MAX_CELL):
                        if (
                            BMS.config.BMS_IC[current_ic].cells.c_codes[cell] * 0.0001
                            >= OVERVOLTAGE
                        ):
                            NO_PROBLEM[current_ic * 64 + cell + 2] = 1
                            NO_PROBLEM_OUTPUT.off()
                    for temp_v in range(MAX_MUX_PIN):
                        if temp(BMS.config.BMS_IC[current_ic].temp[temp_v]) >= CHARGE_MAX_T:
                            NO_PROBLEM[current_ic * 64 + 16 + temp_v + 2] = 1
                            NO_PROBLEM_OUTPUT.off()
            else:
                if TIME - TIMER > LOW_WRITE_TIME:
                    # Dans le cas ou on veut juste monitorer les valeurs, sur de longues durées
                    write_data()
                    TIMER = TIME
        #except:
        #    ACTIVE = False
        #    print("Sortie boucle")
        #    NO_PROBLEM[0] = 1
        #    NO_PROBLEM_OUTPUT.off()
