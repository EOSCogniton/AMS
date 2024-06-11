import time
import spidev







def bin2hex(bin):
    n=bin2int(bin)
    return hex(n)

def hex2bin(hex):
    binst=bin(int(hex,16))
    nb0=8-len(binst)+2
    res=[0]*nb0
    for x in binst[2:]:
        res.append(int(x))
    return res

def int2bin(int):
    binst=bin(int)
    nb0=8-len(binst)+2
    res=[0]*nb0
    for x in binst[2:]:
        res.append(int(x))
    return res

    
def exchange_poll(cmd):
    msgbin=CMDbyte(cmd)
    PECbin=calcul_PEC(msgbin)
    return spi.xfer([bin2int(msgbin),bin2int(PECbin)])

def send_only(cmd):
    msgbin=CMDbyte(cmd)
    PECbin=calcul_PEC(msgbin)
    return spi.writebytes([bin2int(msgbin),bin2int(PECbin)])

def readconfig():
    msgbin = CMDbyte("RDCFG")
    PECbin = calcul_PEC(msgbin)
    spi.writebytes([bin2int(msgbin),bin2int(PECbin)])
    noread=True
    readed=[]
    while noread:
        read=spi.readbytes(1)
        readed.append(read)
        for x in read:
            if x!=255:
                noread=False
                read.append(spi.readbytes(7))
                break
    return readed




if __name__ == "__main__":
    

    # We only have SPI bus 0 available to us on the Pi
    bus = 0

    #Device is the chip select pin. Set to 0 or 1, depending on the connections
    device = 0

    # Enable SPI
    spi = spidev.SpiDev()

    # Open a connection to a specific bus and device (chip select pin)
    spi.open(bus, device)

    # Set SPI speed and mode
    spi.max_speed_hz = int(1/(1*1e-6))
    spi.mode = 3
    
    while True:
        print("stcomm",send_only("STCOMM"))
        print(spi.readbytes(20))
        # print(spi.readbytes(80))
        time.sleep(0.1)
