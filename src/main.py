import gc
import time
from time import sleep_ms
from Models.Api import Api
from Models.BME680 import BME680_I2C
from Models.CJMCU811 import CCS811
from Models.RpiPico import RpiPico
from Models.VEML6070 import VEML6070
from Models.DisplayST7735_128x160 import DisplayST7735_128x160
from machine import Pin, SPI

# Importo variables de entorno
import env
from Models.WeatherStation import WeatherStation
from env import API_UPLOAD

# Habilito recolector de basura
gc.enable()

DEBUG = env.DEBUG
API_UPLOAD = API_UPLOAD

# Rpi Pico Model Instance
if API_UPLOAD:
    rpi = RpiPico(ssid=env.AP_NAME, password=env.AP_PASS, debug=DEBUG, alternatives_ap=env.ALTERNATIVES_AP, hostname=env.HOSTNAME)

    # Sincronizando reloj RTC
    """
    sleep_ms(1000)

    while not rpi.sync_rtc_time():

        if env.DEBUG:
            print('Intentando Obtener hora RTC de la API')

        sleep_ms(30000)
    """

    # Preparo la instancia para la comunicación con la API
    api = Api(controller=rpi, url=env.API_URL, path=env.API_PATH, token=env.API_TOKEN, device_id=env.DEVICE_ID, debug=env.DEBUG)
else:
    rpi = RpiPico(debug=DEBUG)

rpi.led_on()

sleep_ms(100)

# Led 1 Encendido
led1 = Pin(28, Pin.OUT)
#led1.on()

# Led 2 Indica ciclo de trabajo
led2 = Pin(27, Pin.OUT)

# Led 3 Indica subida a la API
led3 = Pin(26, Pin.OUT)

sleep_ms(100)

# Ejemplo instanciando I2C en bus 0.
i2c0 = rpi.set_i2c(4, 5, 0, 100000)
i2c1 = rpi.set_i2c(14, 15, 1, 400000)


if DEBUG:
    print(i2c0)
    print(i2c1)

    # Ejemplo escaneando todos los dispositivos encontrados por I2C.
    print('Dispositivos encontrados por I2C0:', i2c0.scan())
    print('Dispositivos encontrados por I2C1:', i2c1.scan())

sleep_ms(100)


ws = WeatherStation(debug=DEBUG, rpi=rpi)

sleep_ms(100)

# Realizo 10 lecturas de calibración
for i in range(10):
    ws.read_all()
    sleep_ms(1000)

ws.reset_stats()

while True:
    ws.read_all()
    ws.debug()
    sleep_ms(5000)

# Pantalla principal 128x160px
cs = Pin(13, Pin.OUT)
reset = Pin(9, Pin.OUT)

spi1 = SPI(1, baudrate=8000000, polarity=0, phase=0,
           firstbit=SPI.MSB, sck=Pin(10), mosi=Pin(11), miso=None)

display = DisplayST7735_128x160(spi1, rst=9, ce=13, dc=12, btn_display_on=8, orientation=env.DISPLAY_ORIENTATION, debug=env.DEBUG, timeout=env.DISPLAY_TIMEOUT)
display.displayFooterInfo()
sleep_ms(display.DELAY)
display.tableCreate(0, demo=True)

# Pausa preventiva al desarrollar (ajustar, pero si usas dos hilos puede ahorrar tiempo por bloqueos de hardware ante errores)
sleep_ms(3000)

def thread1 ():
    """
    Segundo hilo.
    """

    if env.DEBUG:
        print('')
        print('Inicia hilo principal (thread1)')


def thread0 ():
    """
    Primer hilo, flujo principal de la aplicación.
    En este hilo colocamos toda la lógica principal de funcionamiento.
    """

    if env.DEBUG:
        print('')
        print('Inicia hilo principal (thread0)')

    led2.on()

    # Se leen todos los sensores
    ws.read_all()

    if DEBUG:
        ws.debug()

    if API_UPLOAD:
        led3.on()
        api.upload_weather_data(ws.data)
        ws.reset_stats()
        led3.off()

    led2.off()


while True:
    try:
        thread0()
    except Exception as e:
        if env.DEBUG:
            print('Error: ', e)

        if env.DEBUG:
            print('Memoria antes de liberar: ', gc.mem_free())

        gc.collect()

        if env.DEBUG:
            print("Memoria después de liberar:", gc.mem_free())
    finally:
        sleep_ms(10000)
