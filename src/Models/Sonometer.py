import time
import math


class Sonometer:
    def __init__ (self, rpi, pin=26, debug=False, voltage_range=2.0,
                  sensitivity_db=-42, voltage_offset=1.25):
        """
        Initialize a microphone sensor class.

        This class is used to interface with a microphone sensor module connected to
        a Raspberry Pi. It reads the analog input from the microphone and provides
        functionalities to process the audio signals.

        :param rpi: The Raspberry Pi object facilitating the GPIO operations
        :param pin: El pin ADC al que está conectado el micrófono (por defecto 26).
        :param debug: Si es True, imprime información de depuración.
        :param voltage_range: Max voltage for microphone input. Default is 1.0
        :param sensitivity_db: The sensitivity of the microphone in decibels. Default is -42

        :type pin: int
        :type debug: bool
        :type voltage_range: float
        :type sensitivity_db: float
        """
        self.pin = pin  # El pin analógico donde se conecta el micrófono
        self.debug = debug
        self.rpi = rpi
        self.voltage_range = voltage_range
        self.sensitivity_db = sensitivity_db
        self.offset_voltage = voltage_offset

        # Cola para almacenar las últimas 30 lecturas (mantiene solo las últimas 30)
        self.reads = []

    def calc_rms (self, samples=100):
        """
        Calcula el valor RMS de la señal de entrada.
        :param samples: Número de muestras a promediar para obtener el RMS.
        :return: El valor RMS de la señal.
        """
        sum_squares = 0
        for _ in range(samples):
            voltage = self.rpi.read_analog_input(self.pin) - self.offset_voltage
            sum_squares += voltage ** 2
            time.sleep(0.01)  # Pausa pequeña entre lecturas

        rms = math.sqrt(sum_squares / samples)

        print("voltage: ", self.rpi.read_analog_input(self.pin))

        return rms

    def get_db(self, rms_value=None):
        """
        Convierte un valor RMS a decibelios (dB).
        :param rms_value: Si no se proporciona, se calcula el RMS internamente.
        :return: El valor en decibelios.
        """
        if rms_value is None:
            rms_value = self.calc_rms()

        # Evita log(0) en el cálculo
        if rms_value == 0:
            return -100  # Valor arbitrario bajo para representar la ausencia de señal

        # Convertir el valor RMS a decibelios
        db_value = 20 * math.log10(rms_value / self.voltage_range)
        return db_value

    def get_db_spl (self, samples=1024, interval=1.0):
        """
        Convierte el promedio de 1024 voltajes leídos a un nivel de presión sonora (dB SPL) usando una escala lineal.
        El rango de voltajes va de 1.25V (0 dB SPL) a 3.33V (100 dB SPL).
        :param samples: Número de muestras a tomar (por defecto 1024).
        :param interval: Intervalo en segundos entre las muestras (por defecto 1 segundo).
        :return: El nivel de presión sonora en dB SPL basado en el promedio de las muestras.
        """
        max_voltage = 1.25
        #total_voltage = 0.0

        # Tomar las muestras
        start_time = time.time()  # Marca el tiempo de inicio
        for _ in range(samples):
            voltage = self.rpi.read_analog_input(self.pin)

            if voltage > max_voltage:
                max_voltage = voltage

            #total_voltage += voltage
            time.sleep(interval / samples)  # Intervalo entre las muestras, 1 segundo dividido por el número de muestras

        # Calcular el promedio de las muestras
        #avg_voltage = total_voltage / samples

        #print('AVG_Voltage:', avg_voltage)
        #print('max_voltage:', max_voltage)

        # Aseguramos que el voltaje esté dentro del rango esperado
        if max_voltage < 1.25:
            max_voltage = 1.25  # Limitar el valor mínimo a 1.25V
        elif max_voltage > 3.33:
            max_voltage = 3.33  # Limitar el valor máximo a 3.33V

        # Cálculo lineal entre mínimo (0 dB SPL) y máximo (100 dB SPL)
        db_spl = ((max_voltage - self.offset_voltage) / (
                    3.33 - self.offset_voltage)) * 100

        return db_spl

    def loop_read (self):
        """
        Lee constantemente el valor RMS y lo almacena en la lista `reads`.
        Este método se puede llamar desde otro hilo para ejecutar en segundo plano.
        """
        while True:
            rms_value = self.calc_rms(100)  # Obtiene el valor RMS
            self.reads.append(
                rms_value)  # Almacena el RMS en la cola

            # Si hay más de 30 lecturas elimino la más antigua
            if len(self.reads) > 30:
                self.reads.pop(0)

            # Intervalo entre lecturas
            time.sleep(0.5)

    def get_db_loop (self):
        """
        Obtiene los valores de dB a partir de las 30 últimas lecturas almacenadas en `reads`.
        :return: Lista de los últimos 30 valores en dB.
        """
        db_values = []

        if self.reads:
            avg_rms = sum(self.reads) / len(self.reads)
            avg_db = self.get_db(avg_rms)
            db_values.append(avg_db)

        return db_values
