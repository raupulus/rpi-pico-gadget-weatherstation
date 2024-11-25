from Models.BME680 import BME680_I2C, BME680  # Import BME680 for air_quality reading
from Models.CJMCU811 import CCS811
from Models.VEML6070 import VEML6070

from time import sleep_ms
import time


class WeatherStation:
    data = {
        "air_quality": {
            "max": None,
            "min": None,
            "avg": None,
            "current": None,
            "reads": None,
            "unit": "%"
        },
        "temperature": {
            "max": None,
            "min": None,
            "avg": None,
            "current": None,
            "reads": None,
            "unit": "C"
        },
        "humidity": {
            "max": None,
            "min": None,
            "avg": None,
            "current": None,
            "reads": None,
            "unit": "%"
        },
        "pressure": {
            "max": None,
            "min": None,
            "avg": None,
            "current": None,
            "reads": None,
            "unit": "mbar"
        },
        "gas": {
            "max": None,
            "min": None,
            "avg": None,
            "current": None,
            "reads": None,
            "unit": "ohms"
        },
        "co2": {
            "max": None,
            "min": None,
            "avg": None,
            "current": None,
            "reads": None,
            "unit": "ppm"
        },
        "tvoc": {
            "max": None,
            "min": None,
            "avg": None,
            "current": None,
            "reads": None,
            "unit": "ppb"
        },
        "uv": {
            "max": None,
            "min": None,
            "avg": None,
            "current": None,
            "risk_level": None,
            "reads": None,
            "unit": "index"
        },
        "light": {
            "max": None,
            "min": None,
            "avg": None,
            "current": None,
            "reads": None,
            "unit": "lux"
        },
        "sound": {
            "max": None,
            "min": None,
            "avg": None,
            "current": None,
            "reads": None,
            "unit": "dB"
        }
    }

    def __init__ (self, rpi, debug=False):
        self.DEBUG = debug
        self.rpi = rpi

        # Sensor Bosh BME680
        self.bme680 = BME680_I2C(i2c=rpi.i2c0, address=0x77, debug=False, temperature_offset=-1)

        # Sensor CO2 y TVOC
        self.c = CCS811(i2c=rpi.i2c0, addr=0x5A, debug=debug)
        self.c_last_calibrate = time.time()

        # Sensor UV
        self.uv = VEML6070(rpi.i2c1)

        # Sensor de luz
        self.light = None

    def read_all(self):
        self.read_bme680()
        self.read_uv()
        self.read_light()
        self.read_c()

    def read_bme680(self):
        if self.bme680:
            if self.bme680.temperature is not None:
                self.data["temperature"]["current"] = self.bme680.temperature
                self.data["temperature"]["reads"] = self.data["temperature"]["reads"] + 1 if self.data["temperature"]["reads"] else 1
                self.data["temperature"]["max"] = max(self.data["temperature"]["max"], self.bme680.temperature) if self.data["temperature"]["max"] is not None else self.bme680.temperature
                self.data["temperature"]["min"] = min(self.data["temperature"]["min"], self.bme680.temperature) if self.data["temperature"]["min"] is not None else self.bme680.temperature
                self.data["temperature"]["avg"] = ((self.data["temperature"]["avg"] or 0) * (self.data["temperature"]["reads"] - 1) + self.bme680.temperature) / self.data["temperature"]["reads"]

            if self.bme680.pressure is not None:
                self.data["pressure"]["current"] = self.bme680.pressure
                self.data["pressure"]["reads"] = self.data["pressure"]["reads"] + 1 if self.data["pressure"]["reads"] else 1
                self.data["pressure"]["max"] = max(self.data["pressure"]["max"], self.bme680.pressure) if self.data["pressure"]["max"] is not None else self.bme680.pressure
                self.data["pressure"]["min"] = min(self.data["pressure"]["min"], self.bme680.pressure) if self.data["pressure"]["min"] is not None else self.bme680.pressure
                self.data["pressure"]["avg"] = ((self.data["pressure"]["avg"] or 0) * (self.data["pressure"]["reads"] - 1) + self.bme680.pressure) / self.data["pressure"]["reads"]

            if self.bme680.humidity is not None:
                self.data["humidity"]["current"] = self.bme680.humidity
                self.data["humidity"]["reads"] = self.data["humidity"]["reads"] + 1 if self.data["humidity"]["reads"] else 1
                self.data["humidity"]["max"] = max(self.data["humidity"]["max"], self.bme680.humidity) if self.data["humidity"]["max"] is not None else self.bme680.humidity
                self.data["humidity"]["min"] = min(self.data["humidity"]["min"], self.bme680.humidity) if self.data["humidity"]["min"] is not None else self.bme680.humidity
                self.data["humidity"]["avg"] = ((self.data["humidity"]["avg"] or 0) * (self.data["humidity"]["reads"] - 1) + self.bme680.humidity) / self.data["humidity"]["reads"]

            if self.bme680.is_gas_ready() and self.bme680.gas is not None:
                self.data["gas"]["current"] = self.bme680.gas
                self.data["gas"]["reads"] = self.data["gas"]["reads"] + 1 if self.data["gas"]["reads"] else 1
                self.data["gas"]["max"] = max(self.data["gas"]["max"], self.bme680.gas) if self.data["gas"]["max"] is not None else self.bme680.gas
                self.data["gas"]["min"] = min(self.data["gas"]["min"], self.bme680.gas) if self.data["gas"]["min"] is not None else self.bme680.gas
                self.data["gas"]["avg"] = ((self.data["gas"]["avg"] or 0) * (self.data["gas"]["reads"] - 1) + self.bme680.gas) / self.data["gas"]["reads"]

            if self.bme680.is_gas_ready() and self.bme680.air_quality() is not None:
                self.data["air_quality"]["current"] = self.bme680.air_quality()
                self.data["air_quality"]["reads"] = self.data["air_quality"]["reads"] + 1 if self.data["air_quality"]["reads"] else 1
                self.data["air_quality"]["max"] = max(self.data["air_quality"]["max"], self.bme680.air_quality()) if self.data["air_quality"]["max"] is not None else self.bme680.air_quality()
                self.data["air_quality"]["min"] = min(self.data["air_quality"]["min"], self.bme680.air_quality()) if self.data["air_quality"]["min"] is not None else self.bme680.air_quality()
                self.data["air_quality"]["avg"] = ((self.data["air_quality"]["avg"] or 0) * (self.data["air_quality"]["reads"] - 1) + self.bme680.air_quality()) / self.data["air_quality"]["reads"]

    def read_c(self):

        if self.c:
            temperature = self.data["temperature"]["current"]
            humidity = self.data["humidity"]["current"]

            if self.c.is_ready():
                current_time = time.time()
                if temperature and humidity and ( current_time - self.c_last_calibrate) >= 300:
                    self.c.put_envdata(humidity=humidity, temp=temperature)
                    self.c_last_calibrate = current_time

                    sleep_ms(100)

                self.c.read_sensor_data()
                sleep_ms(50)

                co2 = self.c.CO2
                tVOC = self.c.tVOC

                self.data["co2"]["current"] = co2
                self.data["tvoc"]["current"] = tVOC
                self.data["co2"]["reads"] = self.data["co2"]["reads"] + 1 if self.data["co2"]["reads"] else 1
                self.data["tvoc"]["reads"] = self.data["tvoc"]["reads"] + 1 if self.data["tvoc"]["reads"] else 1
                self.data["co2"]["max"] = max(self.data["co2"]["max"], co2) if self.data["co2"]["max"] is not None else co2
                self.data["co2"]["min"] = min(self.data["co2"]["min"], co2) if self.data["co2"]["min"] is not None else co2
                self.data["co2"]["avg"] = ((self.data["co2"]["avg"] or 0) * (self.data["co2"]["reads"] - 1) + co2) / self.data["co2"]["reads"]
                self.data["tvoc"]["max"] = max(self.data["tvoc"]["max"], tVOC) if self.data["tvoc"]["max"] is not None else tVOC
                self.data["tvoc"]["min"] = min(self.data["tvoc"]["min"], tVOC) if self.data["tvoc"]["min"] is not None else tVOC
                self.data["tvoc"]["avg"] = ((self.data["tvoc"]["avg"] or 0) * (self.data["tvoc"]["reads"] - 1) + tVOC) / self.data["tvoc"]["reads"]

    def read_uv(self):
        if self.uv:
            if self.uv.uv_raw is not None:
                self.data["uv"]["current"] = self.uv.uv_raw
                self.data["uv"]["risk_level"] = self.uv.get_index(self.data["uv"]["current"])
                self.data["uv"]["reads"] = self.data["uv"]["reads"] + 1 if self.data["uv"]["reads"] else 1
                self.data["uv"]["max"] = max(self.data["uv"]["max"], self.uv.uv_raw) if self.data["uv"]["max"] is not None else self.uv.uv_raw
                self.data["uv"]["min"] = min(self.data["uv"]["min"], self.uv.uv_raw) if self.data["uv"]["min"] is not None else self.uv.uv_raw
                self.data["uv"]["avg"] = ((self.data["uv"]["avg"] or 0) * (self.data["uv"]["reads"] - 1) + self.uv.uv_raw) / self.data["uv"]["reads"]

    def read_light(self):
        if self.light:
            pass


    def reset_stats(self):
        for key in self.data:
            for subkey in self.data[key]:
                if subkey is not 'unit':
                    self.data[key][subkey] = None

    def debug(self):
        print('Temperature:', self.data.get('temperature').get('current'))
        print('Humidity:', self.data.get('humidity').get('current'))
        print('Pressure:', self.data.get('pressure').get('current'))
        print('Gas ready:', self.bme680.is_gas_ready())
        print('Gas:', self.data.get('gas').get('current'))
        print('Air Quality:', self.data.get('air_quality').get('current'))
        print('')
        print('CO2/tVOC Ready:', self.c.is_ready())
        print('CO2 level:', self.data.get('co2').get('current'))
        print('tVOC level:', self.data.get('tvoc').get('current'))
        print('')
        print('UV:', self.data.get('uv').get('current'))
        print('Risk Level:', self.data.get('uv').get('risk_level'))
        print('-------')