from machine import I2C, Pin
import time

# Dirección de los registros I2C del VEML6070
_VEML6070_ADDR_CMD = 0x39  # Dirección de escritura (comando)
_VEML6070_ADDR_LOW = 0x38  # Dirección de lectura (byte bajo)
_VEML6070_ADDR_HIGH = 0x39  # Dirección de lectura (byte alto)

# Tiempo de integración y su respectiva división para calibrar
_VEML6070_INTEGRATION_TIME = {
    "VEML6070_HALF_T": [0x00, 0],  # 0.5 T
    "VEML6070_1_T": [0x01, 1],  # 1 T
    "VEML6070_2_T": [0x02, 2],  # 2 T
    "VEML6070_4_T": [0x03, 4],  # 4 T
}

# Niveles de riesgo UV
_VEML6070_RISK_LEVEL = {
    "LOW": [0, 560],
    "MODERATE": [561, 1120],
    "HIGH": [1121, 1494],
    "VERY HIGH": [1495, 2054],
    "EXTREME": [2055, 9999],
}


class VEML6070:
    """
    Driver para el sensor UV VEML6070.
    """

    def __init__ (self, i2c: I2C, _veml6070_it: str = "VEML6070_1_T",
                  ack: bool = False) -> None:
        # Validación del tiempo de integración
        if _veml6070_it not in _VEML6070_INTEGRATION_TIME:
            raise ValueError(
                f"Tiempo de integración inválido. Valores válidos: {_VEML6070_INTEGRATION_TIME.keys()}")

        # Configuración inicial
        self.i2c = i2c
        self._it = _veml6070_it
        self._ack = ack
        self._ack_thd = 0x00

        # Configuración del sensor
        self.buf = bytearray(1)
        self.buf[0] = (self._ack << 5) | (
                    _VEML6070_INTEGRATION_TIME[self._it][0] << 2) | 0x02

        # Inicialización del sensor
        self._initialize_sensor()

    def _initialize_sensor (self) -> None:
        """
        Inicializa el sensor escribiendo en el registro de comandos.
        """
        self.i2c.writeto(_VEML6070_ADDR_CMD, self.buf)

        # Esperamos a que el sensor esté listo
        time.sleep(0.1)

    @property
    def uv_raw (self) -> int:
        """
        Obtiene el valor de la intensidad UV bruta del sensor.
        Lee dos registros consecutivos para obtener el valor crudo UV.
        """
        # Leer el byte más significativo (MSB) desde la dirección 0x39
        msb = self.i2c.readfrom(_VEML6070_ADDR_HIGH, 1)

        # Leer el byte menos significativo (LSB) desde la dirección 0x38
        lsb = self.i2c.readfrom(_VEML6070_ADDR_LOW, 1)

        # Convertir los dos bytes en un valor de 16 bits
        uv_value = (msb[0] << 8) | lsb[0]

        return uv_value

    def calibrate (self) -> None:
        """
        Realiza 10 lecturas del sensor y obtiene un valor base promedio.
        """
        readings = [self.uv_raw for _ in range(10)]
        calibration_value = sum(readings) // len(readings)
        print(f"Calibración completada. Valor base: {calibration_value}")

    def get_index (self, raw_value: int) -> str:
        """
        Calcula el nivel de riesgo UV basado en la lectura del sensor.
        """
        # Obtener el divisor del tiempo de integración
        div = _VEML6070_INTEGRATION_TIME[self._it][1]

        if div == 0:
            raise ValueError(
                "El índice UV solo está disponible para tiempos de integración 1, 2 y 4.")

        # Aseguramos que raw_value y div sean enteros
        adjusted_value = int(raw_value) // int(
            div)  # Dividir correctamente los enteros

        # Ajuste del valor crudo y determinar el nivel de riesgo
        for level, (lower, upper) in _VEML6070_RISK_LEVEL.items():
            if lower <= adjusted_value < upper:
                return level
        return "Desconocido"
