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
        Calcula el valor RMS (Root Mean Square) de la señal de entrada.
        :param samples: Número de muestras a promediar para obtener el RMS.
        :return: El valor RMS de la señal.
        """
        sum_squares = 0
        for _ in range(samples):
            voltage = self.rpi.read_analog_input(self.pin) - self.offset_voltage
            sum_squares += voltage ** 2  # Sumo los cuadrados de los voltajes
            time.sleep(0.01)  # Pausa pequeña entre lecturas

        rms = math.sqrt(sum_squares / samples)  # Calcula el RMS

        return rms

    def get_db (self, rms_value=None):
        """
        Convierte un valor RMS a decibelios (dB).
        :return: El valor en decibelios.
        """

        if rms_value is None:
            rms_value = self.calc_rms()

        # Convierto RMS a dB con respecto a un valor de referencia (self.voltage_range)
        # Si el valor RMS es 0, evito la división por cero y retorno un mínimo.
        if rms_value == 0:
            return -100  # Un valor arbitrario muy bajo para no tener log(0)

        # Calculo los dB con referencia al rango de voltage que detecta el mic.
        return 20 * math.log10(rms_value / self.voltage_range)

    def get_db_spl (self):
        """
        Convierte el voltaje RMS de la señal a dB SPL (Sound pressure level).
        :param sensitivity_db: La sensibilidad del micrófono en dB a max voltage.
        :return: El nivel de presión sonora en dB SPL.
        """
        rms_voltage = self.calc_rms()

        sensitive_db = abs(self.sensitivity_db)

        # Cálculo de dB SPL
        return (20 * math.log10(rms_voltage / self.voltage_range) + sensitive_db)

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
