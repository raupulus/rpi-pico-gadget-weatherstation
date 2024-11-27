import time
import math
from collections import deque


class Sonometer:
    def __init__ (self, pin=26, debug=False):
        """
        Inicializa el sonómetro.
        :param pin: El pin ADC al que está conectado el micrófono (por defecto 26).
        :param debug: Si es True, imprime información de depuración.
        """
        self.pin = pin  # El pin analógico donde se conecta el micrófono
        self.debug = debug

        # Cola para almacenar las últimas 30 lecturas (mantiene solo las últimas 30)
        self.reads = deque(maxlen=30)

    def calc_rms (self, samples=100):
        """
        Calcula el valor RMS (Root Mean Square) de la señal de entrada.
        :param samples: Número de muestras a promediar para obtener el RMS.
        :return: El valor RMS de la señal.
        """
        sum_squares = 0
        for _ in range(samples):
            voltage = self.read_analog_input(
                self.pin)  # Lee el voltaje del pin usando read_analog_input
            sum_squares += voltage ** 2  # Suma los cuadrados de los voltajes
            time.sleep(0.01)  # Pausa pequeña entre lecturas

        rms = math.sqrt(sum_squares / samples)  # Calcula el RMS
        if self.debug:
            print(f"Valor RMS: {rms:.5f}V")
        return rms

    def get_db (self, rms_value):
        """
        Convierte un valor RMS a decibelios (dB).
        :param rms_value: El valor RMS que se va a convertir a dB.
        :return: El valor en decibelios.
        """
        # Convertimos RMS a dB con respecto a un valor de referencia (1V)
        # Si el valor RMS es 0, evitamos la división por cero y retornamos un valor mínimo.
        if rms_value == 0:
            return -100  # Un valor arbitrario muy bajo para no tener log(0)
        dB = 20 * math.log10(
            rms_value / 1)  # Calculamos los dB con referencia de 1V
        if self.debug:
            print(f"Valor en dB: {dB:.2f} dB")
        return dB

    def loop_read (self):
        """
        Lee constantemente el valor RMS y lo almacena en la lista `reads`.
        Este método se puede llamar desde otro hilo para ejecutar en segundo plano.
        """
        while True:
            rms_value = self.calc_rms(100)  # Obtiene el valor RMS
            self.reads.append(
                rms_value)  # Almacena el RMS en la cola (de tamaño 30)
            if self.debug:
                print(f"Lectura RMS añadida: {rms_value:.5f}V")
            time.sleep(
                0.5)  # Lee cada medio segundo (ajustable según necesidades)

    def get_db_loop (self):
        """
        Obtiene los valores de dB a partir de las 30 últimas lecturas almacenadas en `reads`.
        :return: Lista de los últimos 30 valores en dB.
        """
        db_values = [self.get_db(rms) for rms in self.reads]
        if self.debug:
            print(f"Últimos valores en dB: {db_values}")
        return db_values

    def read_analog_input (self, pin):
        """
        Función para leer el valor analógico de un pin.
        Aquí debes implementar la forma en que se lee el pin, ya que parece ser específica de tu plataforma.
        :param pin: El pin ADC que se va a leer.
        :return: El valor del voltaje en el pin.
        """
        # Implementación de lectura de voltaje (esto debe ser sustituido por tu código de lectura específico).
        # Aquí simplemente llamamos a la función rpi.read_analog_input(pin) que mencionaste en tu mensaje.

        voltage = rpi.read_analog_input(
            pin)  # Obtiene el voltaje directamente de tu función personalizada
        return voltage
