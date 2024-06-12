from LTC681x import *


def bin2hex(bin):
    n = bin2int(bin)
    return hex(n)


def hex2bin(hex):
    binst = bin(int(hex, 16))
    nb0 = 8 - len(binst) + 2
    res = [0] * nb0
    for x in binst[2:]:
        res.append(int(x))
    return res


##Additional specific functions


def LTC6811_init_reg_limits(
    total_ic: int,  # The number of ICs in the system
    ic: List[CellASIC],  # A two dimensional array where data will be written
) -> None:
    """
    Initialize the Register limits.

    Parameters:
        total_ic (int): The number of ICs in the system.
        ic (List[cell_asic]): A two dimensional array where data will be written.
    """
    for cic in range(total_ic):
        ic[cic].ic_reg.cell_channels = 12
        ic[cic].ic_reg.stat_channels = 4
        ic[cic].ic_reg.aux_channels = 6
        ic[cic].ic_reg.num_cv_reg = 4
        ic[cic].ic_reg.num_gpio_reg = 2
        ic[cic].ic_reg.num_stat_reg = 3


def LTC6811_set_discharge(Cell: int, total_ic: int, ic: List["CellASIC"]) -> None:
    """
    Helper function to set discharge bit in CFG register.

    Args:
        Cell (int): The cell to be discharged.
        total_ic (int): Number of ICs in the system.
        ic (List[CellASIC]): A list of CellASIC objects storing the data.
    """
    for i in range(total_ic):
        if 0 < Cell < 9:
            ic[i].config.tx_data[4] |= 1 << (Cell - 1)
        elif 9 <= Cell < 13:
            ic[i].config.tx_data[5] |= 1 << (Cell - 9)
        else:
            break


##Paramètres
TOTAL_IC = 1  # nombre de BMS en daisy chain

ENABLED = 1
DISABLED = 0
DATALOG_ENABLED = 1
DATALOG_DISABLED = 0

###################################################################
# Setup Variables
# The following variables can be modified to configure the software.
###################################################################

# ADC Command Configurations. See LTC681x.h for options.
ADC_OPT = ADC_OPT_DISABLED  # ADC Mode option bit
ADC_CONVERSION_MODE = MD_7KHZ_3KHZ  # ADC Mode
ADC_DCP = DCP_ENABLED  # Discharge Permitted
CELL_CH_TO_CONVERT = CELL_CH_ALL  # Channel Selection for ADC conversion
AUX_CH_TO_CONVERT = AUX_CH_ALL  # Channel Selection for ADC conversion
STAT_CH_TO_CONVERT = STAT_CH_ALL  # Channel Selection for ADC conversion
SEL_ALL_REG = REG_ALL  # Register Selection
SEL_REG_A = REG_1  # Register Selection
SEL_REG_B = REG_2  # Register Selection

MEASUREMENT_LOOP_TIME = 500  # Loop Time in milliseconds (ms)

# Under Voltage and Over Voltage Thresholds
OV_THRESHOLD = 41000  # Over voltage threshold ADC Code. LSB = 0.0001 ---(4.1V)
UV_THRESHOLD = 30000  # Under voltage threshold ADC Code. LSB = 0.0001 ---(3V)

# Loop Measurement Setup. These Variables are ENABLED or DISABLED. Remember ALL CAPS
WRITE_CONFIG = DISABLED  # This is to ENABLE or DISABLE writing into to configuration registers in a continuous loop
READ_CONFIG = DISABLED  # This is to ENABLE or DISABLE reading the configuration registers in a continuous loop
MEASURE_CELL = ENABLED  # This is to ENABLE or DISABLE measuring the cell voltages in a continuous loop
MEASURE_AUX = DISABLED  # This is to ENABLE or DISABLE reading the auxiliary registers in a continuous loop
MEASURE_STAT = DISABLED  # This is to ENABLE or DISABLE reading the status registers in a continuous loop
PRINT_PEC = DISABLED  # This is to ENABLE or DISABLE printing the PEC Error Count in a continuous loop
#####################################
# END SETUP
#####################################

########################################################
# Global Battery Variables received from 681x commands.
# These variables store the results from the LTC6811
# register reads and the array lengths must be based
# on the number of ICs on the stack
########################################################
BMS_IC = [CellASIC()] * TOTAL_IC

####################################################
# Set the configuration bits.
# Refer to the Configuration Register Group from data sheet.
####################################################
REFON = True  # Reference Powered Up Bit
ADCOPT = False  # ADC Mode option bit
GPIOBITS_A = [False, False, True, True, True]  # GPIO Pin Control // Gpio 1,2,3,4,5
UV = UV_THRESHOLD  # Under-voltage Comparison Voltage
OV = OV_THRESHOLD  # Over-voltage Comparison Voltage
DCCBITS_A = [False] * 12  # Discharge cell switch // Dcc 1,2,3,4,5,6,7,8,9,10,11,12
DCTOBITS = [
    True,
    False,
    True,
    False,
]  # Discharge time value // Dcto 0,1,2,3 // Programmed for 4 min
# Ensure that Dcto bits are set according to the required discharge time. Refer to the data sheet

MAX_SPEED_HZ = 2000000  # Fréquence max et par défaut du bus SPI

if __name__ == "__main__":

    # We only have SPI bus 0 available to us on the Pi
    bus = 0

    # Device is the chip select pin. Set to 0 or 1, depending on the connections
    device = 0

    # Open a connection to a specific bus and device (chip select pin)
    spi.open(bus, device)

    # Set SPI speed and mode
    spi.max_speed_hz = MAX_SPEED_HZ
    spi.mode = 3

    ##Initialisation

    LTC681x_init_cfg(TOTAL_IC, BMS_IC)
    for current_ic in range(TOTAL_IC):
        LTC681x_set_cfgr(
            current_ic, BMS_IC, REFON, ADCOPT, GPIOBITS_A, DCCBITS_A, DCTOBITS, UV, OV
        )
    LTC681x_reset_crc_count(TOTAL_IC, BMS_IC)
    LTC6811_init_reg_limits(TOTAL_IC, BMS_IC)

### Fonctions utiles :


def write_read_cfg():
    """Write and Read Configuration Register"""
    wakeup_sleep(TOTAL_IC)
    LTC681x_wrcfg(TOTAL_IC, BMS_IC)  # Write into Configuration Register
    print_wrconfig()
    wakeup_idle(TOTAL_IC)
    error = LTC681x_rdcfg(TOTAL_IC, BMS_IC)  # Read Configuration Register
    check_error(error)
    print_rxconfig()


def read_cfg():
    """Read Configuration Register"""
    wakeup_sleep(TOTAL_IC)
    error = LTC681x_rdcfg(TOTAL_IC, BMS_IC)
    check_error(error)
    print_rxconfig()


def start_cell_mes():
    """Start Cell ADC Measurement"""
    wakeup_sleep(TOTAL_IC)
    LTC681x_adcv(ADC_CONVERSION_MODE, ADC_DCP, CELL_CH_TO_CONVERT)
    conv_time = LTC681x_pollAdc()
    print_conv_time(conv_time)


def read_cell_v():
    """Read Cell Voltage Registers"""
    wakeup_sleep(TOTAL_IC)
    error = LTC681x_rdcv(SEL_ALL_REG, TOTAL_IC, BMS_IC)
    # Set to read back all cell voltage registers
    check_error(error)
    print_cells(DATALOG_DISABLED)


def start_GPIO_mes():
    """Start GPIO ADC Measurement"""
    wakeup_sleep(TOTAL_IC)
    LTC681x_adax(ADC_CONVERSION_MODE, AUX_CH_TO_CONVERT)
    conv_time = LTC681x_pollAdc()
    print_conv_time(conv_time)


def enable_DSC(pin: int):
    """Enable a discharge transistor
    cell : the cell to discharge"""
    wakeup_sleep(TOTAL_IC)
    LTC6811_set_discharge(pin, TOTAL_IC, BMS_IC)
    LTC681x_wrcfg(TOTAL_IC, BMS_IC)
    print_wrconfig()
    wakeup_idle(TOTAL_IC)
    error = LTC681x_rdcfg(TOTAL_IC, BMS_IC)
    check_error(error)
    print_rxconfig()


def clear_all_DSC():
    """Clear all discharge transistors"""
    wakeup_sleep(TOTAL_IC)
    LTC681x_clear_discharge(TOTAL_IC, BMS_IC)
    LTC681x_wrcfg(TOTAL_IC, BMS_IC)
    print_wrconfig()
    wakeup_idle(TOTAL_IC)
    error = LTC681x_rdcfg(TOTAL_IC, BMS_IC)
    check_error(error)
    print_rxconfig()


### Fonctions d'affichage :
def print_conv_time(conv_time: int) -> None:
    """
    Function to print the Conversion Time.

    Args:
        conv_time (int): The conversion time to be printed.
    """
    m_factor = 1000  # to print in ms

    print("Conversion completed in:", "{:.1f}".format(conv_time / m_factor), "ms\n")


def check_error(error: int) -> None:
    """
    Function to check error flag and print PEC error message.

    Args:
        error (int): The error flag to be checked.
    """
    if error == -1:
        print("A PEC error was detected in the received data")


def print_wrconfig():
    print()
    print("Written Configuration: ")
    for current_ic in range(TOTAL_IC):
        string = "CFGA IC " + str(current_ic + 1) + " : "
        string += "[" + str(BMS_IC[current_ic].config.tx_data[0])
        for i in range(1, 6):
            string += ", " + str(BMS_IC[current_ic].config.tx_data[i])
        print(string + "]")
        pec = pec15_calc(6, BMS_IC[current_ic].config.tx_data)
        print("Calculated PEC: ({},{})".format(pec[0], pec[1]))
    print()


def print_rxconfig():
    print()
    print("Received Configuration ")
    for current_ic in range(TOTAL_IC):
        string = "CFGA IC " + str(current_ic + 1) + " : "
        string += "[" + str(BMS_IC[current_ic].config.rx_data[0])
        for i in range(1, 6):
            string += ", " + str(BMS_IC[current_ic].config.rx_data[i])
        print(string + "]")
        print(
            "Calculated PEC: ({},{})".format(
                BMS_IC[current_ic].config.rx_data[6],
                BMS_IC[current_ic].config.rx_data[7],
            )
        )
    print()


def print_cells(datalog_en: int) -> None:
    """
    Prints cell voltage to the console.

    Args:
        datalog_en (int): Data logging enable flag.
    """
    print()
    for current_ic in range(TOTAL_IC):
        if datalog_en == 0:
            print(f" IC {current_ic + 1} : ", end="")
            print(
                f" C1: {BMS_IC[current_ic].cells.c_codes[0] * 0.0001:.4f}",
                end="",
            )
            for i in range(1, BMS_IC[0].ic_reg.cell_channels):
                print(
                    f", C{i + 1}: {BMS_IC[current_ic].cells.c_codes[i] * 0.0001:.4f}",
                    end="",
                )
            print()
        else:
            print(" Cells :", end="")
            print(f"{BMS_IC[current_ic].cells.c_codes[0] * 0.0001:.4f},", end="")
            for i in range(1, BMS_IC[0].ic_reg.cell_channels):
                print(f"{BMS_IC[current_ic].cells.c_codes[i] * 0.0001:.4f},", end="")
    print()
