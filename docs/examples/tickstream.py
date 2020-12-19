from lemon_markets.data.streams import TickStream
from time import sleep


def cb(*args):  # sample callback function. accepts however many arguments
    print(args)  # and prints them as a tuple


if __name__ == '__main__':  # <-- this is a so called 'mainguard'. it is necessary if you use TickStream or QuoteStream on Windows
    ts = TickStream(cb)  # initialising tickstream object
    ts.subscribe('US88160R1014')  # subscribing to tick data from tesla
    sleep(30)  # keeping the script alive for 30 seconds
