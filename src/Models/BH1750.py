import math
from micropython import const
from utime import sleep_ms
from machine import I2C


class BH1750:
    """Clase para el sensor de luz ambiente digital BH1750

    El datasheet se puede encontrar en https://components101.com/sites/default/files/component_datasheet/BH1750.pdf
    """

    # Modos de medición
    MEASUREMENT_MODE_CONTINUOUSLY = const(1)
    MEASUREMENT_MODE_ONE_TIME = const(2)

    # Resoluciones de medición
    RESOLUTION_HIGH = const(0)
    RESOLUTION_HIGH_2 = const(1)
    RESOLUTION_LOW = const(2)

    # Tiempos de medición
    MEASUREMENT_TIME_DEFAULT = const(69)
    MEASUREMENT_TIME_MIN = const(31)
    MEASUREMENT_TIME_MAX = const(254)

    def __init__ (self, addr: int, i2c: I2C, debug: bool = False):
        """Inicializa el sensor BH1750.

        :param addr: Dirección I2C del sensor.
        :param i2c: Instancia del bus I2C.
        :param debug: Modo de depuración.
        """
        self._address = addr
        self._i2c = i2c
        self._measurement_mode = BH1750.MEASUREMENT_MODE_ONE_TIME
        self._resolution = BH1750.RESOLUTION_HIGH
        self._measurement_time = BH1750.MEASUREMENT_TIME_DEFAULT

        self._write_measurement_time()
        self._write_measurement_mode()

    def configure (self, measurement_mode: int, resolution: int,
                   measurement_time: int):
        """Configura el sensor BH1750.

        :param measurement_mode: Medición continua o única.
        :param resolution: Resolución de las mediciones (alta, alta2 o baja).
        :param measurement_time: Duración de una sola medición.
        """
        if measurement_time not in range(BH1750.MEASUREMENT_TIME_MIN,
                                         BH1750.MEASUREMENT_TIME_MAX + 1):
            raise ValueError(
                "El tiempo de medición debe estar entre {0} y {1}".format(
                    BH1750.MEASUREMENT_TIME_MIN, BH1750.MEASUREMENT_TIME_MAX))

        self._measurement_mode = measurement_mode
        self._resolution = resolution
        self._measurement_time = measurement_time

        self._write_measurement_time()
        self._write_measurement_mode()

    def _write_measurement_time (self):
        """Escribe el tiempo de medición en el sensor."""
        buffer = bytearray(1)

        high_bit = 1 << 6 | self._measurement_time >> 5
        low_bit = 3 << 5 | (self._measurement_time << 3) >> 3

        buffer[0] = high_bit
        self._i2c.writeto(self._address, buffer)

        buffer[0] = low_bit
        self._i2c.writeto(self._address, buffer)

    def _write_measurement_mode (self):
        """Escribe el modo y resolución de medición en el sensor."""
        buffer = bytearray(1)

        buffer[0] = self._measurement_mode << 4 | self._resolution
        self._i2c.writeto(self._address, buffer)
        sleep_ms(24 if self._measurement_time == BH1750.RESOLUTION_LOW else 180)

    def reset (self):
        """Limpia el registro de datos de iluminancia."""
        self._i2c.writeto(self._address, bytearray(b'\x07'))

    def power_on (self):
        """Enciende el sensor BH1750."""
        self._i2c.writeto(self._address, bytearray(b'\x01'))

    def power_off (self):
        """Apaga el sensor BH1750."""
        self._i2c.writeto(self._address, bytearray(b'\x00'))

    def get_lumens (self, luxRead: float = None) -> float:
        """
        Obtiene la cantidad de lúmenes.

        :param luxRead: Lectura de lux opcional.
        :return: Lumens o None.
        """
        lux = luxRead if luxRead else self.measurement
        area = 0.25 * 0.3  # Área en mm (0.25mm x 0.3mm)
        lumens = lux * area

        return lumens if lumens >= 0.0 else None

    @property
    def measurement (self) -> float:
        """Devuelve la última medición de iluminancia en lux."""
        if self._measurement_mode == BH1750.MEASUREMENT_MODE_ONE_TIME:
            self._write_measurement_mode()

        buffer = bytearray(2)
        self._i2c.readfrom_into(self._address, buffer)
        lux = (buffer[0] << 8 | buffer[1]) / (1.2 * (
                BH1750.MEASUREMENT_TIME_DEFAULT / self._measurement_time))

        if self._resolution == BH1750.RESOLUTION_HIGH_2:
            return lux / 2
        else:
            return lux

    def measurements (self):
        """Función generadora que continúa proporcionando las últimas mediciones.
        Debido a que el tiempo de medición está muy afectado por la resolución y el
        tiempo de medición configurado, esta función intenta calcular el tiempo de
        espera apropiado entre las mediciones.

        Ejemplo de uso:

        for measurement in bh1750.measurements():  # bh1750 es una instancia de esta clase
            print(measurement)
        """
        while True:
            yield self.measurement

            if self._measurement_mode == BH1750.MEASUREMENT_MODE_CONTINUOUSLY:
                base_measurement_time = 16 if self._measurement_time == BH1750.RESOLUTION_LOW else 120
                sleep_ms(math.ceil(
                    base_measurement_time * self._measurement_time / BH1750.MEASUREMENT_TIME_DEFAULT))
