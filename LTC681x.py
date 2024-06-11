import time
import spidev

spi = spidev.SpiDev()

CMD = {"STCOMM": [1, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1],"RDCOMM": [1, 1, 1, 0, 0, 1, 0, 0, 0, 1, 0 ],"RDCFG": [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0]}

def bin2int(bin):
    st=""
    for x in bin:
        st+=str(x)
    return int(st,2)

def XOR (a, b):
    """Simple fonction XOR"""
    if a != b:
        return 1
    else:
        return 0
    
def calcul_PEC(Din:list):
    """Calcul du PEC pour le mot binaire Din"""
    PEC = [0,0,0,0,0,0,0,0,0,0,1,0,0,0,0][::-1]
    for bit in Din:
        IN0 = XOR(bit,PEC[14])
        IN3 = XOR(IN0,PEC[2])
        IN4 = XOR(IN0,PEC[3])
        IN7 = XOR(IN0,PEC[6])
        IN8 = XOR(IN0,PEC[7])
        IN10 = XOR(IN0,PEC[9])
        IN14 = XOR(IN0,PEC[13])

        PEC [14] = IN14
        PEC [13] = PEC [12]
        PEC [12] = PEC [11]
        PEC [11] = PEC [10]
        PEC [10] = IN10
        PEC [9] = PEC [8]
        PEC [8] = IN8
        PEC [7] = IN7
        PEC [6] = PEC [5]
        PEC [5] = PEC [4]
        PEC [4] = IN4
        PEC [3] = IN3
        PEC [2] = PEC [1]
        PEC [1] = PEC [0]
        PEC [0] = IN0
    res=[0]+PEC
    return res[::-1]

def wakeup_idle(nb_BMS:int):
    """Wake isoSPI up from IDlE state and enters the READY state"""
    for _ in range(nb_BMS):
        spi.writebytes(0xff)

def wakeup_sleep(nb_BMS:int,f_hz:int):
    """Generic wakeup command to wake the LTC681x from sleep state"""
    for _ in range(nb_BMS):
        spi.writebytes([0,0,0,0,0,0,0,0]*300*1e-6*f_hz)
        time.sleep(10e-6)

def cmd_68(cmd:str):
    """Generic function to write 68xx commands.\n
    Function calculates PEC for cmd data."""
    cmdbin=CMD[cmd]
    cmdbit=[0,0,0,0,0]+cmdbin[:3]+cmdbin[3:]
    pec=calcul_PEC(cmdbit)
    word=[bin2int(cmdbit[:8]),bin2int(cmdbit[8:]),bin2int(pec[:8]),bin2int(pec[8:])]
    spi.writebytes(word)

def write_68(cmd:str,data:list,nb_BMS:int):
    """Generic function to write 68xx commands and write payload data. \n
    Function calculates PEC for cmd data and the data to be transmitted."""
    BYTES_IN_REG = 6

    cmdbin=CMD[cmd]
    cmdbit=[0,0,0,0,0]+cmdbin[:3]+cmdbin[3:]
    pec=calcul_PEC(cmdbit)
    word = [0]*(4+8*nb_BMS)
    word[0]=bin2int(cmdbit[:8])
    word[1]=bin2int(cmdbit[8:])
    word[2]=bin2int(pec[:8])
    word[3]=bin2int(pec[8:])

    cmd_index = 4
    for current_BMS in range(nb_BMS)[::-1]: #Executes for each LTC681x, this loops starts with the last IC on the stack.
        for current_byte in range(BYTES_IN_REG): #The first configuration written is received by the last IC in the daisy chain
            word[4] = bin2int(data[((current_BMS-1)*6)+current_byte])
            cmd_index+=1

            data_pec=calcul_PEC(data[(current_BMS-1)*6])
            word[cmd_index]=bin2int(data_pec[8:])
            word[cmd_index+1]=bin2int(data_pec[:8])

            cmd_index+=2
    
    spi.writebytes(word)

def read_68():
    """Generic function to write 68xx commands and read data. \n
    Function calculated PEC for cmd data"""