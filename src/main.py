import gc
import time
from time import sleep_ms
from Models.Api import Api
from Models.BME680 import *
from Models.RpiPico import RpiPico

# Importo variables de entorno
import env

# Habilito recolector de basura
gc.enable()

DEBUG = env.DEBUG

# Rpi Pico Model Instance
#rpi = RpiPico(ssid=env.AP_NAME, password=env.AP_PASS, debug=DEBUG, alternatives_ap=env.ALTERNATIVES_AP, hostname=env.HOSTNAME)
rpi = RpiPico(debug=DEBUG)

sleep_ms(100)


# Ejemplo instanciando I2C en bus 0.
i2c0 = rpi.set_i2c(4, 5, 0, 400000)

print(i2c0)

# Ejemplo escaneando todos los dispositivos encontrados por I2C.
print('Dispositivos encontrados por I2C:', i2c0.scan())

sleep_ms(200)

# Preparo la instancia para la comunicación con la API
#api = Api(controller=rpi, url=env.API_URL, path=env.API_PATH, token=env.API_TOKEN, device_id=env.DEVICE_ID, debug=env.DEBUG)


# Sincronizando reloj RTC
"""
sleep_ms(1000)

while not rpi.sync_rtc_time():

    if env.DEBUG:
        print('Intentando Obtener hora RTC de la API')

    sleep_ms(30000)
"""


print('break 1')
bme680 = BME680_I2C(i2c=i2c0, address=0x77, debug=False)

print('break 2')

while True:
  try:
    temp = str(round(bme680.temperature, 2)) + ' C'
    #temp = (bme.temperature) * (9/5) + 32
    #temp = str(round(temp, 2)) + 'F'
    
    hum = str(round(bme680.humidity, 2)) + ' %'
    
    pres = str(round(bme680.pressure, 2)) + ' hPa'
    
    gas = str(round(bme680.gas/1000, 2)) + ' KOhms'

    print('Temperature:', temp)
    print('Humidity:', hum)
    print('Pressure:', pres)
    print('Gas:', gas)
    print('-------')
  except OSError as e:
    print('Failed to read sensor.')
 
  sleep_ms(5000)


"""


# change this to match the location's pressure (hPa) at sea level
bme680.sea_level_pressure = 1013.25

# You will usually have to add an offset to account for the temperature of
# the sensor. This is usually around 5 degrees but varies by use. Use a
# separate temperature sensor to calibrate this one.
temperature_offset = -5

while True:
    print("\nTemperature: %0.1f C" % (bme680.temperature + temperature_offset))
    print("Gas: %d ohm" % bme680.gas)
    print("Humidity: %0.1f %%" % bme680.relative_humidity)
    print("Pressure: %0.3f hPa" % bme680.pressure)
    print("Altitude = %0.2f meters" % bme680.altitude)

    time.sleep(1)
"""





# Pausa preventiva al desarrollar (ajustar, pero si usas dos hilos puede ahorrar tiempo por bloqueos de hardware ante errores)
sleep_ms(3000)


def thread1 ():
    """
    Segundo hilo.

    En este hilo colocamos otras operaciones con cuidado frente a la
    concurrencia.

    Recomiendo utilizar sistemas de bloqueo y pruebas independientes con las
    funcionalidades que vayas a usar en paralelo. Se puede romper la ejecución.
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

    sleep_ms(10000)


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
