# Beacon Software
# Made in collaboration with Mr. Douglas Chin

from time import sleep
import servercom
from beacon_client import BeaconClient

with open('cert.pem', 'r') as fp:
    server_cert=fp.read()

servercom.CUBESERVER_DEFAULT_CONFIG.API_HOST = '192.168.252.1'
servercom.CUBESERVER_DEFAULT_CONFIG.API_PORT = 8889

frequency = 32768

highPower = digitalio.DigitalInOut(board.D10)
highPower.direction = digitalio.Direction.OUTPUT
highPower.value = True

# Init PulseIO:
pulse_ir = pulseio.PulseOut(board.D5, frequency=frequency, duty_cycle=2 ** 15)
pulse_red = pulseio.PulseOut(board.D6, frequency=frequency, duty_cycle=2 ** 15)
encoder = adafruit_irremote.GenericTransmit(header=[3000, 3800], one=[550, 550], zero=[550, 1700], trail=3800)

# Init I2C:
i2c = board.I2C()

#set the potentiometer to volitile and simple log attenuation
i2c.try_lock()
i2c.writeto(0x28, bytes([0x84, 0x30]))
i2c.unlock()



def tx_packet(packet: bytes, output=pulse_ir):
    if len(packet) < 1:
        return
    print(packet)
    time.sleep(0.15)
    encoder.transmit(output, [byte for byte in packet])
    time.sleep(0.15)

def tx_chunk(message: bytes, output=pulse_ir):
    i = 0
    chunk_size = 6
    while i <= len(message):
        chunk = message[i : ((i + chunk_size) if len(message) - i > chunk_size else len(message))]
        if len(chunk) == 0:
            break
        print(chunk)
        time.sleep(0.15)
        encoder.transmit(output, chunk)
        time.sleep(0.15)
        i += chunk_size

def set_intensity(intensity: int):
    i2c.try_lock()
    i2c.writeto(0x28, chr(intensity).encode())
    i2c.unlock()

def tx_message(dest: int, intensity: int, message: bytes):
    set_intensity(intensity)
    if dest == 1:
        output = pulse_red
    else:
        output = pulse_ir
    while message[0] == b'\x07':
        tx_packet(b'\x07', output=output)
        message = message[1:]
    tx_packet(len(message).to_bytes(2, 'big'), output=output)
    for line in message.split(b'\r\n'):
        tx_chunk(line + b'\r\n', output=output)


# Actually connect to the server:
c = servercom.Connection(server_cert=server_cert, _force=True, verbose=True)
bc = None
while bc is None:
    try:
        bc = BeaconClient(c)
    except:
        sleep(1)
        continue

print("Connected!")

@bc.commandhook
def tx_message(dest, intensity, message) -> int:
    print("Dest:", dest)
    print("Intensity:", intensity)
    print("Message:", message)
    return len(message)

bc.run_client_listener()
