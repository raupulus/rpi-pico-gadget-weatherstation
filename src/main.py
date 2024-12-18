import gc
import time
from time import sleep_ms
from Models.Api import Api
from Models.RpiPico import RpiPico
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
    sleep_ms(1000)

    # Intenta obtener timestamp para poner en hora el RTC
    rpi.sync_rtc_time()

    # Preparo la instancia para la comunicación con la API
    api = Api(controller=rpi, url=env.API_URL, path=env.API_PATH, token=env.API_TOKEN, device_id=env.DEVICE_ID, debug=env.DEBUG)
else:
    rpi = RpiPico(debug=DEBUG)

sleep_ms(100)

# Led 1 Encendido
led1 = Pin(20, Pin.OUT)
led1.on()

# Led 2 Indica ciclo de trabajo
led2 = Pin(21, Pin.OUT)

# Led 3 Indica subida a la API
led3 = Pin(22, Pin.OUT)

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

# Pantalla principal 128x160px
spi1 = SPI(1, baudrate=8000000, polarity=0, phase=0,
           firstbit=SPI.MSB, sck=Pin(10), mosi=Pin(11), miso=None)

display = DisplayST7735_128x160(spi1, rst=9, ce=13, dc=12, btn_display_on=2,
                                pin_backlight=3,
                                orientation=env.DISPLAY_ORIENTATION, debug=env.DEBUG, timeout=env.DISPLAY_TIMEOUT)
display.displayHeadInfo(wifi_status=rpi.wifi_status())
display.displayFooterInfo()
sleep_ms(display.DELAY)
display.grid_create()

# Sonómetro Test
"""
from Models.Sonometer import Sonometer
sound = Sonometer(rpi, 26, debug=True)
while True:
    rms = sound.calc_rms(100)
    db = sound.get_db()
    db_spl = sound.get_db_spl()
    print('RMS: ', rms)
    print('DB: ', db)
    print('DB SPL: ', db_spl)
    print('')
    sleep_ms(50)
"""

# Pausa preventiva al desarrollar (ajustar, pero si usas dos hilos puede ahorrar tiempo por bloqueos de hardware ante errores)
sleep_ms(3000)

# Almacena el último minuto para solo actualizar hora en el footer cuando cambia
last_minute = 0

def thread0 ():
    """
    Primer hilo, flujo principal de la aplicación.
    En este hilo colocamos toda la lógica principal de funcionamiento.
    """
    global last_minute

    if env.DEBUG:
        print('')
        print('Inicia hilo principal (thread0)')

    led2.on()

    # Se leen todos los sensores
    ws.read_all()

    # Compruebo si se enciende o apaga la pantalla
    display.loop()

    if DEBUG:
        ws.debug()

    localtime = rpi.get_rtc_local_time()
    minute = localtime[4]
    localtime_str = rpi.get_rtc_local_time_string_spanish()

    if localtime_str and minute != last_minute:
        last_minute = minute
        display.displayFooterInfo(center=localtime_str)

    display.grid_update()

    # Si la subida a la api está habilitada en las variables de entorno
    if API_UPLOAD:
        current_time = time.time()

        # Comprueba para subir solo una vez cada minuto
        if current_time - api.last_upload_time >= 60:
            led3.on()

            if not rpi.is_rtc_set:
                rpi.sync_rtc_time()

            if DEBUG:
                print('Subiendo datos a la API')

            api.upload_weather_data(ws.data)
            api.last_upload_time = current_time

            if DEBUG:
                print('Reiniciando estadísticas para nueva fase de trabajo')

            # Reinicia las estadísticas tras la subida
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
        sleep_ms(1000)
