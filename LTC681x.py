import time
import spidev

from typing import List


class CV:
    """
    Cell Voltage data structure.
    """

    def __init__(self):
        self.c_codes: List[int] = [0] * 18  # Cell Voltage Codes
        self.pec_match: List[int] = [
            0
        ] * 6  # If a PEC error was detected during most recent read cmd


class AX:
    """
    AUX Reg Voltage Data structure.
    """

    def __init__(self):
        self.a_codes: List[int] = [0] * 9  # Aux Voltage Codes
        self.pec_match: List[int] = [
            0
        ] * 4  # If a PEC error was detected during most recent read cmd


class ST:
    """
    Status Reg data structure.
    """

    def __init__(self):
        self.stat_codes: List[int] = [0] * 4  # Status codes
        self.flags: List[int] = [0] * 3  # Byte array that contains the uv/ov flag data
        self.mux_fail: List[int] = [0] * 1  # Mux self test status flag
        self.thsd: List[int] = [0] * 1  # Thermal shutdown status
        self.pec_match: List[int] = [
            0
        ] * 2  # If a PEC error was detected during most recent read cmd


class ICRegister:
    """
    IC register structure.
    """

    def __init__(self):
        self.tx_data: List[int] = [0] * 6  # Stores data to be transmitted
        self.rx_data: List[int] = [0] * 8  # Stores received data
        self.rx_pec_match: int = (
            0  # If a PEC error was detected during most recent read cmd
        )


class PECCounter:
    """
    PEC error counter structure.
    """

    def __init__(self):
        self.pec_count: int = 0  # Overall PEC error count
        self.cfgr_pec: int = 0  # Configuration register data PEC error count
        self.cell_pec: List[int] = [0] * 6  # Cell voltage register data PEC error count
        self.aux_pec: List[int] = [0] * 4  # Aux register data PEC error count
        self.stat_pec: List[int] = [0] * 2  # Status register data PEC error count


class RegisterCfg:
    """
    Register configuration structure.
    """

    def __init__(self):
        self.cell_channels: int = 0  # Number of Cell channels
        self.stat_channels: int = 0  # Number of Stat channels
        self.aux_channels: int = 0  # Number of Aux channels
        self.num_cv_reg: int = 0  # Number of Cell voltage register
        self.num_gpio_reg: int = 0  # Number of Aux register
        self.num_stat_reg: int = 0  # Number of Status register


class CellASIC:
    """
    Cell variable structure.
    """

    def __init__(self):
        self.config = ICRegister()
        self.configb = ICRegister()
        self.cells = CV()
        self.aux = AX()
        self.stat = ST()
        self.com = ICRegister()
        self.pwm = ICRegister()
        self.pwmb = ICRegister()
        self.sctrl = ICRegister()
        self.sctrlb = ICRegister()
        self.sid: List[int] = [0] * 6
        self.isospi_reverse: bool = False
        self.crc_count = PECCounter()
        self.ic_reg = RegisterCfg()
        self.system_open_wire: int = 0


spi = spidev.SpiDev()

CELL = 1
AUX = 2
STAT = 3
CFGR = 0
CFGRB = 4
NUM_RX_BYT = 8

CMD = {
    "STCOMM": [1, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1],
    "RDCOMM": [1, 1, 1, 0, 0, 1, 0, 0, 0, 1, 0],
    "WRCGFA": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    "WRCFGB": [0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0],
    "RDCFGA": [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
    "RDCFGB": [0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0],
    "RDCVA": [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
    "RDCVB": [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0],
    "RDCVC": [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    "RDCVD": [0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0],
    "RDCVE": [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
    "RDCVF": [0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1],
    "RDAUXA": [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0],
    "RDAUXB": [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0],
    "RDAUXC": [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1],
    "RDAUXD": [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
    "RDSTATA": [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
    "RDSTATB": [0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0],
    "WRSCTRL": [0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0],
    "WRPWM": [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    "WRPSB": [0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0],
    "RDSCTRL": [0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0],
    "RDPWM": [0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0],
    "RDPSB": [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0],
    "STSCTRL": [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1],
    "CLRSCTRL": [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0],
    "CLRCELL": [1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1],
    "CLRAUX": [1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0],
    "CLRSTAT": [1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1],
    "PLADC": [1, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0],
    "DIAGN": [1, 1, 1, 0, 0, 0, 1, 0, 1, 0, 1],
}


def bin2int(binval: List[bool]):
    st = ""
    for x in binval:
        st += str(x)
    return int(st, 2)


def int2bin(intval: int):
    binst = bin(intval)
    nb0 = 8 - len(binst) + 2
    res = [0] * nb0
    binst = binst[2:]
    for k in range(len(binst)):
        res.append(int(binst[k]))
    return res


def create_bin_for_pec(data):
    res = []
    for x in data:
        res += int2bin(x)
    return res


def pec15_calc(nb_byte: int, data: List[bool]):
    bindata = create_bin_for_pec(data[:nb_byte])
    return calcul_PEC(bindata)


def XOR(a, b):
    """Simple fonction XOR"""
    if a != b:
        return 1
    else:
        return 0


def calcul_PEC(Din: list):
    """Calcul du PEC pour le mot binaire Din"""
    PEC = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0][::-1]
    for bit in Din:
        IN0 = XOR(bit, PEC[14])
        IN3 = XOR(IN0, PEC[2])
        IN4 = XOR(IN0, PEC[3])
        IN7 = XOR(IN0, PEC[6])
        IN8 = XOR(IN0, PEC[7])
        IN10 = XOR(IN0, PEC[9])
        IN14 = XOR(IN0, PEC[13])

        PEC[14] = IN14
        PEC[13] = PEC[12]
        PEC[12] = PEC[11]
        PEC[11] = PEC[10]
        PEC[10] = IN10
        PEC[9] = PEC[8]
        PEC[8] = IN8
        PEC[7] = IN7
        PEC[6] = PEC[5]
        PEC[5] = PEC[4]
        PEC[4] = IN4
        PEC[3] = IN3
        PEC[2] = PEC[1]
        PEC[1] = PEC[0]
        PEC[0] = IN0
    res = [0] + PEC
    return res[::-1]


def wakeup_idle(total_ic: int):
    """Wake isoSPI up from IDlE state and enters the READY state"""
    for _ in range(total_ic):
        spi.writebytes(0xFF)


def wakeup_sleep(total_ic: int, f_hz: int):
    """Generic wakeup command to wake the LTC681x from sleep state"""
    for _ in range(total_ic):
        spi.writebytes([0, 0, 0, 0, 0, 0, 0, 0] * 300 * 1e-6 * f_hz)
        time.sleep(10e-6)


def cmd_68(cmd: List[bool]):
    """Generic function to write 68xx commands.\n
    Function calculates PEC for cmd data."""
    cmdbit = [0, 0, 0, 0, 0] + cmd[:3] + cmd[3:]
    pec = calcul_PEC(cmdbit)
    word = [
        bin2int(cmdbit[:8]),
        bin2int(cmdbit[8:]),
        bin2int(pec[:8]),
        bin2int(pec[8:]),
    ]
    spi.writebytes(word)


def write_68(
    total_ic: int,
    cmd: List[bool],
    data: List[int],
):
    """Generic function to write 68xx commands and write payload data. \n
    Function calculates PEC for cmd data and the data to be transmitted."""
    BYTES_IN_REG = 6

    cmdbit = [0, 0, 0, 0, 0] + cmd[:3] + cmd[3:]
    pec = calcul_PEC(cmdbit)
    word = [0] * (4 + 8 * total_ic)
    word[0] = bin2int(cmdbit[:8])
    word[1] = bin2int(cmdbit[8:])
    word[2] = bin2int(pec[:8])
    word[3] = bin2int(pec[8:])

    cmd_index = 4
    for current_ic in range(1, total_ic + 1)[::-1]:
        # Executes for each LTC681x, this loops starts with the last IC on the stack.
        for current_byte in range(BYTES_IN_REG):
            # The first configuration written is received by the last IC in the daisy chain
            word[cmd_index] = data[((current_ic - 1) * 6) + current_byte]
            cmd_index += 1

        data_pec = pec15_calc(BYTES_IN_REG, data[((current_ic - 1) * 6) :])
        word[cmd_index] = bin2int(data_pec[8:])
        word[cmd_index + 1] = bin2int(data_pec[:8])

        cmd_index += 2

    spi.writebytes(word)


def read_68(cmd: List[bool], total_ic: int):
    """Generic function to write 68xx commands and read data. \n
    Function calculated PEC for cmd data"""

    BYTES_IN_REG = 8
    pec_error = 0

    cmdbit = [0, 0, 0, 0, 0] + cmd[:3] + cmd[3:]
    pec = calcul_PEC(cmdbit)
    word = [0] * (4 + 8 * total_ic)
    word[0] = bin2int(cmdbit[:8])
    word[1] = bin2int(cmdbit[8:])
    word[2] = bin2int(pec[:8])
    word[3] = bin2int(pec[8:])

    spi.writebytes(word)
    data = spi.readbytes(BYTES_IN_REG * total_ic)
    res = [0] * len(data)

    for current_ic in range(total_ic):
        for current_byte in range(BYTES_IN_REG):
            res[(current_ic * 8) + current_byte] = data[
                current_byte + (current_ic * BYTES_IN_REG)
            ]

    received_pec = int2bin(res[(current_ic * 8) + 6]) + int2bin(
        res[(current_ic * 8) + 7]
    )
    bindata = create_bin_for_pec(
        data[(current_ic - 1) * 6 : (current_ic - 1) * 6 + BYTES_IN_REG - 2]
    )
    data_pec = calcul_PEC(bindata)
    if received_pec != data_pec:
        pec_error = -1

    return data, pec_error


def LTC681x_wrcfg(total_ic: int, ic: List["CellASIC"]):
    """
    Write the LTC681x CFGRA.

    :param total_ic: The number of ICs being written to.
    :param ic: A list of CellASIC objects that contain the configuration data to be written.
    """
    cmd = CMD["WRCGFA"]
    write_buffer = [0] * 256
    write_count = 0

    for current_ic in range(total_ic):
        if not ic.isospi_reverse:
            c_ic = current_ic
        else:
            c_ic = total_ic - current_ic - 1

        for data in range(6):
            write_buffer[write_count] = ic[c_ic].config.tx_data[data]
            write_count += 1

    write_68(total_ic, cmd, write_buffer)


def LTC681x_wrcfgb(total_ic: int, ic: List["CellASIC"]):
    """
    Write the LTC681x CFGRB.

    :param total_ic: The number of ICs being written to.
    :param ic: A list of CellASIC objects that contain the configuration data to be written.
    """
    cmd = CMD["WRCGFB"]
    write_buffer = [0] * 256
    write_count = 0

    for current_ic in range(total_ic):
        if not ic.isospi_reverse:
            c_ic = current_ic
        else:
            c_ic = total_ic - current_ic - 1

        for data in range(6):
            write_buffer[write_count] = ic[c_ic].configb.tx_data[data]
            write_count += 1

    write_68(total_ic, cmd, write_buffer)


def LTC681x_rdcfg(total_ic: int, ic: List["CellASIC"]) -> int:
    """
    Read the LTC681x CFGA.

    :param total_ic: Number of ICs in the system.
    :param ic: A list of CellASIC objects where the function stores the read configuration data.
    :return: PEC error status.
    """
    cmd = CMD["RDCFGA"]
    read_buffer = [0] * 256
    pec_error = 0

    read_buffer, pec_error = read_68(total_ic, cmd)

    for current_ic in range(total_ic):
        if not ic.isospi_reverse:
            c_ic = current_ic
        else:
            c_ic = total_ic - current_ic - 1

        for byte in range(8):
            ic[c_ic].config.rx_data[byte] = read_buffer[byte + (8 * current_ic)]

        calc_pec = pec15_calc(6, read_buffer[8 * current_ic :])
        data_pec = read_buffer[7 + (8 * current_ic)] | (
            read_buffer[6 + (8 * current_ic)] << 8
        )
        if calc_pec != data_pec:
            ic[c_ic].config.rx_pec_match = 1
        else:
            ic[c_ic].config.rx_pec_match = 0

    LTC681x_check_pec(total_ic, CFGR, ic)

    return pec_error


def LTC681x_rdcfgb(total_ic: int, ic: List["CellASIC"]) -> int:
    """
    Read the LTC681x CFGB.

    :param total_ic: Number of ICs in the system.
    :param ic: A list of CellASIC objects where the function stores the read configuration data.
    :return: PEC error status.
    """
    cmd = CMD["RDCFGB"]
    read_buffer = [0] * 256
    pec_error = 0

    read_buffer, pec_error = read_68(total_ic, cmd)

    for current_ic in range(total_ic):
        if not ic.isospi_reverse:
            c_ic = current_ic
        else:
            c_ic = total_ic - current_ic - 1

        for byte in range(8):
            ic[c_ic].configb.rx_data[byte] = read_buffer[byte + (8 * current_ic)]

        calc_pec = pec15_calc(6, read_buffer[8 * current_ic :])
        data_pec = read_buffer[7 + (8 * current_ic)] | (
            read_buffer[6 + (8 * current_ic)] << 8
        )
        if calc_pec != data_pec:
            ic[c_ic].configb.rx_pec_match = 1
        else:
            ic[c_ic].configb.rx_pec_match = 0

    LTC681x_check_pec(total_ic, CFGRB, ic)

    return pec_error


def LTC681x_check_pec(total_ic: int, reg: int, ic: List["CellASIC"]):
    """
    Helper function that increments PEC counters.

    :param total_ic: Number of ICs in the system.
    :param reg: Type of Register.
    :param ic: A list of CellASIC objects that store the data.
    """
    if reg == CFGR:
        for current_ic in range(total_ic):
            ic[current_ic].crc_count.pec_count += ic[current_ic].config.rx_pec_match
            ic[current_ic].crc_count.cfgr_pec += ic[current_ic].config.rx_pec_match
    elif reg == CFGRB:
        for current_ic in range(total_ic):
            ic[current_ic].crc_count.pec_count += ic[current_ic].configb.rx_pec_match
            ic[current_ic].crc_count.cfgr_pec += ic[current_ic].configb.rx_pec_match
    elif reg == CELL:
        for current_ic in range(total_ic):
            for i in range(ic[0].ic_reg.num_cv_reg):
                ic[current_ic].crc_count.pec_count += ic[current_ic].cells.pec_match[i]
                ic[current_ic].crc_count.cell_pec[i] += ic[current_ic].cells.pec_match[
                    i
                ]
    elif reg == AUX:
        for current_ic in range(total_ic):
            for i in range(ic[0].ic_reg.num_gpio_reg):
                ic[current_ic].crc_count.pec_count += ic[current_ic].aux.pec_match[i]
                ic[current_ic].crc_count.aux_pec[i] += ic[current_ic].aux.pec_match[i]
    elif reg == STAT:
        for current_ic in range(total_ic):
            for i in range(ic[0].ic_reg.num_stat_reg - 1):
                ic[current_ic].crc_count.pec_count += ic[current_ic].stat.pec_match[i]
                ic[current_ic].crc_count.stat_pec[i] += ic[current_ic].stat.pec_match[i]


def LTC681x_adcv(MD: int, DCP: int, CH: int):
    """
    Starts ADC conversion for cell voltage.

    :param MD: ADC Mode.
    :param DCP: Discharge Permit.
    :param CH: Cell Channels to be measured.
    """
    cmd = [0, 0]
    md_bits = (MD & 0x02) >> 1
    cmd[0] = md_bits + 0x02
    md_bits = (MD & 0x01) << 7
    cmd[1] = md_bits + 0x60 + (DCP << 4) + CH

    cmd_68(int2bin(cmd[0]) + int2bin(cmd[1]))


def LTC681x_adax(MD: int, CHG: int):
    """
    Start ADC Conversion for GPIO and Vref2.

    :param MD: ADC Mode.
    :param CHG: GPIO Channels to be measured.
    """
    cmd = [0, 0]
    md_bits = (MD & 0x02) >> 1
    cmd[0] = md_bits + 0x04
    md_bits = (MD & 0x01) << 7
    cmd[1] = md_bits + 0x60 + CHG

    cmd_68(int2bin(cmd[0]) + int2bin(cmd[1]))


def LTC681x_adstat(MD: int, CHST: int):
    """
    Start ADC Conversion for Status.

    :param MD: ADC Mode.
    :param CHST: Stat Channels to be measured.
    """
    cmd = [0, 0]
    md_bits = (MD & 0x02) >> 1
    cmd[0] = md_bits + 0x04
    md_bits = (MD & 0x01) << 7
    cmd[1] = md_bits + 0x68 + CHST

    cmd_68(int2bin(cmd[0]) + int2bin(cmd[1]))


def LTC681x_adcvsc(MD: int, DCP: int):
    """
    Starts cell voltage and SOC conversion.

    :param MD: ADC Mode.
    :param DCP: Discharge Permit.
    """
    cmd = [0, 0]
    md_bits = (MD & 0x02) >> 1
    cmd[0] = md_bits | 0x04
    md_bits = (MD & 0x01) << 7
    cmd[1] = md_bits | 0x60 | (DCP << 4) | 0x07

    cmd_68(int2bin(cmd[0]) + int2bin(cmd[1]))


def LTC681x_adcvax(MD: int, DCP: int):
    """
    Starts cell voltage and GPIO 1&2 conversion.

    :param MD: ADC Mode.
    :param DCP: Discharge Permit.
    """
    cmd = [0, 0]
    md_bits = (MD & 0x02) >> 1
    cmd[0] = md_bits | 0x04
    md_bits = (MD & 0x01) << 7
    cmd[1] = md_bits | ((DCP & 0x01) << 4) + 0x6F

    cmd_68(int2bin(cmd[0]) + int2bin(cmd[1]))


def LTC681x_rdcv(reg: int, total_ic: int, ic: List[CellASIC]) -> int:
    """
    Reads and parses the LTC681x cell voltage registers.
    The function is used to read the parsed Cell voltages codes of the LTC681x.
    This function will send the requested read commands, parse the data,
    and store the cell voltages in c_codes variable.

    :param reg: Controls which cell voltage register is read back.
    :param total_ic: The number of ICs in the system.
    :param ic: Array of the parsed cell codes.
    :return: PEC error count.
    """
    pec_error = 0
    c_ic = 0

    if reg == 0:
        for cell_reg in range(1, ic[0].ic_reg.num_cv_reg + 1):
            cell_data=LTC681x_rdcv_reg(cell_reg, total_ic)
            for current_ic in range(total_ic):
                if not ic[current_ic].isospi_reverse:
                    c_ic = current_ic
                else:
                    c_ic = total_ic - current_ic - 1

                pec_error += parse_cells(
                    current_ic,
                    cell_reg,
                    cell_data,
                    ic[c_ic].cells.c_codes,
                    ic[c_ic].cells.pec_match,
                )
    else:
        LTC681x_rdcv_reg(reg, total_ic, cell_data)
        for current_ic in range(total_ic):
            if not ic[current_ic].isospi_reverse:
                c_ic = current_ic
            else:
                c_ic = total_ic - current_ic - 1

            pec_error += parse_cells(
                current_ic,
                reg,
                cell_data[8 * c_ic :],
                ic[c_ic].cells.c_codes,
                ic[c_ic].cells.pec_match,
            )

    LTC681x_check_pec(total_ic, CELL, ic)

    return pec_error


def LTC681x_rdaux(reg: int, total_ic: int, ic: List[CellASIC]) -> int:
    """
    The function is used to read the parsed GPIO codes of the LTC681x.
    This function will send the requested read commands, parse the data,
    and store the gpio voltages in a_codes variable.

    :param reg: Determines which GPIO voltage register is read back.
    :param total_ic: The number of ICs in the system.
    :param ic: A two dimensional array of the gpio voltage codes.
    :return: PEC error count.
    """
    pec_error = 0
    c_ic = 0

    if reg == 0:
        for gpio_reg in range(1, ic[0].ic_reg.num_gpio_reg + 1):
            data=LTC681x_rdaux_reg(gpio_reg, total_ic)
            for current_ic in range(total_ic):
                if not ic[current_ic].isospi_reverse:
                    c_ic = current_ic
                else:
                    c_ic = total_ic - current_ic - 1

                pec_error += parse_cells(
                    current_ic,
                    gpio_reg,
                    data,
                    ic[c_ic].aux.a_codes,
                    ic[c_ic].aux.pec_match,
                )
    else:
        LTC681x_rdaux_reg(reg, total_ic, data)
        for current_ic in range(total_ic):
            if not ic[current_ic].isospi_reverse:
                c_ic = current_ic
            else:
                c_ic = total_ic - current_ic - 1

            pec_error += parse_cells(
                current_ic, reg, data, ic[c_ic].aux.a_codes, ic[c_ic].aux.pec_match
            )

    LTC681x_check_pec(total_ic, AUX, ic)

    return pec_error


def LTC681x_rdaux_reg(reg: int, total_ic: int):
    """
    The function reads a single GPIO voltage register and stores the read data
    in the *data point as a byte array. This function is rarely used outside of
    the LTC681x_rdaux() command.

    :param reg: Determines which GPIO voltage register is read back.
    :param total_ic: The number of ICs in the system.
    """
    REG_LEN = 8  # Number of bytes in the register + 2 bytes for the PEC

    if reg == 1:  # Read back auxiliary group A
        cmd_68(CMD["RDAUXA"])
    elif reg == 2:  # Read back auxiliary group B
        cmd_68(CMD["RDAUXB"])
    elif reg == 3:  # Read back auxiliary group C
        cmd_68(CMD["RDAUXC"])
    elif reg == 4:  # Read back auxiliary group D
        cmd_68(CMD["RDAUXD"])
    else:  # Read back auxiliary group A
        cmd_68(CMD["RDAUXA"])

    data = spi.readbytes(REG_LEN * total_ic)
    return data

def LTC681x_rdcv_reg(reg: int, total_ic: int):
    """
    Writes the command and reads the raw cell voltage register data.
    
    :param reg: Determines which cell voltage register is read back.
    :param total_ic: The number of ICs in the system.
    """
    REG_LEN = 8  # Number of bytes in each ICs register + 2 bytes for the PEC

    if reg == 1:  # 1: RDCVA
        cmd_68(CMD["RDCVA"])
    elif reg == 2:  # 2: RDCVB
        cmd_68(CMD["RDCVB"])
    elif reg == 3:  # 3: RDCVC
        cmd_68(CMD["RDCVC"])
    elif reg == 4:  # 4: RDCVD
        cmd_68(CMD["RDCVD"])
    elif reg == 5:  # 5: RDCVE
        cmd_68(CMD["RDCVE"])
    elif reg == 6:  # 6: RDCVF
        cmd_68(CMD["RDCVF"])
    else:
        cmd_68(CMD["RDCVA"])

    data=spi.readbytes(REG_LEN * total_ic)
    return data
