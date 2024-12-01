from Models.BH1750 import BH1750
from Models.BME680 import BME680_I2C, BME680  # Import BME680 for air_quality reading
from Models.CJMCU811 import CCS811
from Models.Sonometer import Sonometer
from Models.VEML6070 import VEML6070

from time import sleep_ms
import time


class WeatherStation:
    data_ranges = {
        "temperature": {
            "low": [0, 21],
            "medium": [21, 25],
            "high": [25, 1000],
        },
        "humidity": {
            "low": [0, 40],
            "medium": [40, 65],
            "high": [65, 100],
        },
        "pressure": {
            "low": [0, 1008],
            "medium": [1008, 1018],
            "high": [1018, 10000],
        },
        "air_quality": {
            "low": [0, 50],
            "medium": [50, 70],
            "high": [70, 100],
        },
        "co2": {
            "low": [0, 500],
            "medium": [500, 700],
            "high": [700, 10000],
        },
        "tvoc": {
            "low": [0, 65],
            "medium": [65, 220],
            "high": [220, 3000],
        },
        "light": {
            "low": [0, 100],
            "medium": [100, 2000],
            "high": [2000, 100000],
        },
        "uv": {
            "low": [0, 2],
            "medium": [2, 5],
            "high": [5, 11],
        },
        "sound": {
            "low": [-200, 40],
            "medium": [40, 60],
            "high": [60, 10000],
        },
    }
    data_images = {
        "temperature": {
            "low": "/images/temperature_low.rgb565",
            "medium": "/images/temperature_medium.rgb565",
            "high": "/images/temperature_high.rgb565",
        },
        "humidity": {
            "low": "/images/humidity_low.rgb565",
            "medium": "/images/humidity_medium.rgb565",
            "high": "/images/humidity_high.rgb565",
        },
        "pressure": {
            "low": "/images/pressure_low.rgb565",
            "medium": "/images/pressure_medium.rgb565",
            "high": "/images/pressure_high.rgb565",
        },
        "air_quality": {
            "low": "/images/air_quality_low.rgb565",
            "medium": "/images/air_quality_medium.rgb565",
            "high": "/images/air_quality_high.rgb565",
        },
        "co2": {
            "low": "/images/co2_low.rgb565",
            "medium": "/images/co2_medium.rgb565",
            "high": "/images/co2_high.rgb565",
        },
        "tvoc": {
            "low": "/images/tvoc_low.rgb565",
            "medium": "/images/tvoc_medium.rgb565",
            "high": "/images/tvoc_high.rgb565",
        },
        "light": {
            "low": "/images/light_low.rgb565",
            "medium": "/images/light_medium.rgb565",
            "high": "/images/light_high.rgb565",
        },
        "uv": {
            "low": "/images/uv_low.rgb565",
            "medium": "/images/uv_medium.rgb565",
            "high": "/images/uv_high.rgb565",
        },
        "sound": {
            "low": "/images/sound_low.rgb565",
            "medium": "/images/sound_medium.rgb565",
            "high": "/images/sound_high.rgb565",
        },
    }
    data = {
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
        "air_quality": {
            "max": None,
            "min": None,
            "avg": None,
            "current": None,
            "reads": None,
            "unit": "%",
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
        "light": {
            "max": None,
            "min": None,
            "avg": None,
            "current": None,
            "reads": None,
            "unit": "lum"
        },
        "uv": {
            "max": None,
            "min": None,
            "avg": None,
            "current": None,
            "risk_level": None,
            "reads": None,
            "unit": "uv"
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
        self.bme680 = BME680_I2C(i2c=rpi.i2c1, address=0x77, debug=False,
                                 temperature_offset=-1, refresh_rate=10)

        # Sensor CO2 y TVOC
        self.c = CCS811(i2c=rpi.i2c0, addr=0x5A, debug=debug)
        self.c_last_calibrate = time.time()

        # Sensor UV
        self.uv = VEML6070(rpi.i2c1)

        # Sensor de luz
        self.light = BH1750(0x23, rpi.i2c1, debug=debug)

        # Sonómetro
        self.sound = Sonometer(rpi, 26, debug=debug, voltage_range=2,
                               sensitivity_db=-42, voltage_offset=1.25)

    @staticmethod
    def get_range (sensor_type: str, value: float) -> str:
        """
        This method calculates and returns a string representation of a range based
        on the input value and sensor type. The logic of determining the range is
        implemented within the method. The returned string provides information
        regarding the range that the value falls into.

        :param sensor_type: The type of sensor for which the range has to be determined.
        :type sensor_type: str
        :param value: The input value for which the range has to be determined.
        :type value: float
        :return: A string representation of the range.
        :rtype: str
        """
        if sensor_type not in WeatherStation.data_ranges:
            raise ValueError(f"Unknown sensor type: {sensor_type}")

        ranges = WeatherStation.data_ranges[sensor_type]

        if ranges["low"][0] <= value <= ranges["low"][1]:
            return "low"
        elif ranges["medium"][0] <= value <= ranges["medium"][1]:
            return "medium"
        elif ranges["high"][0] <= value <= ranges["high"][1]:
            return "high"
        else:
            raise ValueError(
                f"Value {value} is out of range for sensor type {sensor_type}")

    def read_all(self):
        self.read_bme680()
        self.read_uv()
        self.read_light()
        self.read_c()
        self.read_sound()

    def read_sound(self):
        if self.sound:
            #self.data["sound"]["current"] = self.sound.get_db()
            self.data["sound"]["current"] = self.sound.get_db_spl(samples=100,
                                                                  interval=0.05)
            self.data["sound"]["reads"] = self.data["sound"]["reads"] + 1 if self.data["sound"]["reads"] else 1
            self.data["sound"]["max"] = max(self.data["sound"]["max"], self.data["sound"]["current"]) if self.data["sound"]["max"] is not None else self.data["sound"]["current"]
            self.data["sound"]["min"] = min(self.data["sound"]["min"], self.data["sound"]["current"]) if self.data["sound"]["min"] is not None else self.data["sound"]["current"]
            self.data["sound"]["avg"] = ((self.data["sound"]["avg"] or 0) * (self.data["sound"]["reads"] - 1) + self.data["sound"]["current"]) / self.data["sound"]["reads"]

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

            if self.bme680.is_gas_ready() and (self.bme680.gas is not None):
                self.data["gas"]["current"] = self.bme680.gas
                self.data["gas"]["reads"] = self.data["gas"]["reads"] + 1 if self.data["gas"]["reads"] else 1
                self.data["gas"]["max"] = max(self.data["gas"]["max"], self.bme680.gas) if self.data["gas"]["max"] is not None else self.bme680.gas
                self.data["gas"]["min"] = min(self.data["gas"]["min"], self.bme680.gas) if self.data["gas"]["min"] is not None else self.bme680.gas
                self.data["gas"]["avg"] = ((self.data["gas"]["avg"] or 0) * (self.data["gas"]["reads"] - 1) + self.bme680.gas) / self.data["gas"]["reads"]

            if self.bme680.is_gas_ready() and (self.bme680.air_quality() is not None):
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
            lux = self.light.measurement
            lumens = self.light.get_lumens(lux)

            self.data["light"]["current"] = lumens
            self.data["light"]["reads"] = self.data["light"]["reads"] + 1 if self.data["light"]["reads"] else 1
            self.data["light"]["max"] = max(self.data["light"]["max"], lumens) if self.data["light"]["max"] is not None else lumens
            self.data["light"]["min"] = min(self.data["light"]["min"], lumens) if self.data["light"]["min"] is not None else lumens
            self.data["light"]["avg"] = ((self.data["light"]["avg"] or 0) * (self.data["light"]["reads"] - 1) + lumens) / self.data["light"]["reads"]


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
        print('Lumens', self.data.get('light').get('current'))
        print('Lux:', self.light.measurement)
        print('UV:', self.data.get('uv').get('current'))
        print('Risk Level:', self.data.get('uv').get('risk_level'))
        print('')
        print('Sound dbl:', self.data.get('sound').get('current'))
        print('-------')