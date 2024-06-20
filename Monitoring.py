import LTC6811 as BMS
import ADC
import CAN
from read_temp import temp

import gpiod
import time
import datetime

import os.path

NO_PROBLEM_PIN = 29  # GPIO5

chip = gpiod.Chip("gpiochip4")

NO_PROBLEM_OUTPUT = chip.get_line(NO_PROBLEM_PIN)

NO_PROBLEM_OUTPUT.request(consumer="NO_PROBLEM_OUTPUT", type=gpiod.LINE_REQ_DIR_OUT)

MAX_MUX_PIN = 12  # Nombre de thermistors

READ_ENABLE = False  # Affichage dans la console

MODE = "DISCHARGE"  # DISCHARGE, CHARGE or STANDBY

OVERVOLTAGE = 4.18  # V
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
    with open("data.bin", "ab") as file:
        # data=bytearray(data_row)
        file.write(data_raw)


def store_temp(sensor: int):
    global BMS
    for k in range(BMS.TOTAL_IC):
        BMS.config.BMS_IC[k].temp[sensor] = BMS.config.BMS_IC[k].aux.a_codes[0]
        # Les capteurs de temp sont sur le GPIO1 (a_codes[0])


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


def print_error(error: str):
    print(error)
    with open("error.txt", "a") as f:
        f.write(
            "Date : "
            + str(datetime.datetime.fromtimestamp(TIME))
            + " - "
            + error
            + "\n"
        )


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
            TIME = time.time()
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
                    NO_PROBLEM_OUTPUT.set_value(0)
                    print_error("Courant en limite de fusible - ouverture SDC")
                for current_ic in range(BMS.TOTAL_IC):
                    for cell in range(12):
                        if (
                            BMS.config.BMS_IC[current_ic].cells.c_codes[cell] * 0.0001
                            >= OVERVOLTAGE
                        ):
                            NO_PROBLEM_OUTPUT.set_value(0)
                            print_error(
                                "SURTENSION pour la cellule {} du BMS {} - ouverture SDC".format(
                                    cell + 1, current_ic + 1
                                )
                            )
                        elif (
                            BMS.config.BMS_IC[current_ic].cells.c_codes[cell] * 0.0001
                            <= UNDERVOLTAGE
                        ):
                            NO_PROBLEM_OUTPUT.set_value(0)
                            print_error(
                                "Cellule {} du BMS {} déchargée - ouverture SDC".format(
                                    cell + 1, current_ic + 1
                                )
                            )
                    for temp_v in range(MAX_MUX_PIN):
                        if (
                            temp(BMS.config.BMS_IC[current_ic].temp[temp_v])
                            >= DISCHARGE_MAX_T
                        ):
                            NO_PROBLEM_OUTPUT.set_value(0)
                            print_error(
                                "Température de la cellule {} du BMS {} trop élevée - ouverture SDC".format(
                                    temp_v + 1, current_ic + 1
                                )
                            )
            elif MODE == "CHARGE":
                write_data()
                if ADC.convert_current(ADC.VALUE) >= MAX_DISCHARGE_CURRENT:
                    NO_PROBLEM_OUTPUT.set_value(0)
                    print_error("Courant en limite de fusible - ouverture SDC")
                for current_ic in range(BMS.TOTAL_IC):
                    for cell in range(12):
                        if (
                            BMS.config.BMS_IC[current_ic].cells.c_codes[cell] * 0.0001
                            >= OVERVOLTAGE
                        ):
                            NO_PROBLEM_OUTPUT.set_value(0)
                            print_error(
                                "SURTENSION pour la cellule {} du BMS {} - ouverture SDC".format(
                                    cell + 1, current_ic + 1
                                )
                            )
                    for temp_v in range(MAX_MUX_PIN):
                        if (
                            temp(BMS.config.BMS_IC[current_ic].temp[temp_v])
                            >= CHARGE_MAX_T
                        ):
                            NO_PROBLEM_OUTPUT.set_value(0)
                            print_error(
                                "Température de la cellule {} du BMS {} trop élevée - ouverture SDC".format(
                                    temp_v + 1, current_ic + 1
                                )
                            )
            else:
                if TIME - TIMER > LOW_WRITE_TIME:
                    write_data()
                    TIMER = TIME
        except:
            ACTIVE = False
            NO_PROBLEM_OUTPUT.set_value(0)
            print_error("Erreur dans l'éxécution PYTHON - ouverture SDC")
