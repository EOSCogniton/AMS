import time
import spidev

# We only have SPI bus 0 available to us on the Pi
bus = 0

#Device is the chip select pin. Set to 0 or 1, depending on the connections
device = 1

# Enable SPI
spi = spidev.SpiDev()

# Set SPI speed and mode
spi.max_speed_hz = 1e6
spi.mode = 0

def XOR (a, b):
    if a != b:
        return 1
    else:
        return 0

def calcul_PEC(Din):
    PEC = [0,0,0,0,0,0,0,0,0,0,1,0,0,0,0]
    for bit in Din:
        IN0 = XOR(bit,PEC[14])
        IN3 = XOR(IN0,PEC[2])
        IN4 = XOR(IN0,PEC[3])
        IN7 = XOR(IN0,PEC[6])
        IN8 = XOR(IN0,PEC[7])
        IN10 = XOR(IN0,PEC[9])
        IN14 = XOR(IN0,PEC[13])

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
    return PEC

def list_binary2int(bin):
    st=""
    for x in bin:
        st+=str(x)
    return int(st,2)

CMD = {"STCOMM": [1, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1],"RDCOMM": [1, 1, 1, 0, 0, 1, 0, 0, 0, 1, 0 ]}

def list_binary2hex(bin):
    n=list_binary2int(bin)
    return hex(n)

def CMDbyte(cmd):
    cmdbin=CMD[cmd]
    return cmdbin[8:][::-1]+[0,0,0,0,0]+cmdbin[:8][::1]

def exchange_poll(cmd):
    msgbin=CMDbyte(cmd)
    PECbin=calcul_PEC(msgbin)
    return spi.xfer2([list_binary2hex(msgbin),list_binary2hex(PECbin)])

if __name__ == "__main__":
    console.log(exchange_poll("STCOMM"))
    console.log(exchange_poll("RDCOMM"))
