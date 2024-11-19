from machine import I2C
import time


# Dirección por defecto del sensor (dirección I2C)
CCS811_ADDR = const(0x5A)
CCS811_ADDR1 = const(0x5B)

# Comandos del CCS811
CCS811_STATUS = const(0x00)
CCS811_MEAS_MODE = const(0x01)
CCS811_ALG_RESULT_DATA = const(0x02)
CCS811_RAW_DATA = const(0x03)
CCS811_ENV_DATA = const(0x05)
CCS811_NTC = const(0x06)
CCS811_THRESHOLDS = const(0x10)
CCS811_BASELINE = const(0x11)
CCS811_HW_ID = const(0x20)
CCS811_HW_VERSION = const(0x21)
CCS811_FW_BOOT_VERSION = const(0x23)
CCS811_FW_APP_VERSION = const(0x24)
CCS811_ERROR_ID = const(0xE0)
CCS811_APP_START = const(0xF4)
CCS811_SW_RESET = const(0xFF)


class CCS811:
    """ 
    Controlador del sensor CCS811 para medir la concentración de CO2 y compuestos orgánicos volátiles (TVOC).
    """

    def __init__(self, i2c: I2C, addr: int = CCS811_ADDR, debug=False) -> None:
        """
        Inicializa el sensor CCS811.

        :param i2c: Instancia del bus I2C para la comunicación.
        :param addr: Dirección I2C del sensor. Por defecto es 0x5A.
        """
        self.i2c = i2c
        self.addr = addr
        self.tVOC: int = 0
        self.CO2: int = 420
        self.start_time: float = time.time()  # Guardamos el tiempo de inicio para comprobar el timeout de 20 minutos
        self.DEBUG = debug

        # Comprobamos que el sensor esté disponible en el bus I2C
        devices = i2c.scan()
        if self.addr not in devices:
            raise ValueError('Sensor CCS811 no encontrado. Verifique el cableado y conecte nWake a tierra.')
        
        self.setup()

    def print_error(self) -> None:
        """ Muestra el mensaje de error correspondiente según el código de error del sensor. """
        error = self.i2c.readfrom_mem(self.addr, CCS811_ERROR_ID, 1)
        message = 'Error: '

        if (error[0] >> 5) & 1:
            message += 'HeaterSupply '
        elif (error[0] >> 4) & 1:
            message += 'HeaterFault '
        elif (error[0] >> 3) & 1:
            message += 'MaxResistance '
        elif (error[0] >> 2) & 1:
            message += 'MeasModeInvalid '
        elif (error[0] >> 1) & 1:
            message += 'ReadRegInvalid '
        elif (error[0] >> 0) & 1:
            message += 'MsgInvalid '

        print(message)

    def configure_ccs811(self) -> None:
        """ Configura el sensor CCS811, comprobando el ID de hardware y validando la aplicación del firmware. """
        hardware_id = self.i2c.readfrom_mem(self.addr, CCS811_HW_ID, 1)

        if hardware_id[0] != 0x81:
            raise ValueError('ID de hardware incorrecto. Verifique la conexión y asegúrese de que nWake esté a tierra.')

        if self.check_for_error():
            self.print_error()
            raise ValueError('Error al arrancar el sensor.')

        if not self.app_valid():
            raise ValueError('Aplicación del sensor no válida.')

        # Iniciamos la aplicación del CCS811
        self.i2c.writeto(self.addr, bytearray([0xF4]))

        if self.check_for_error():
            self.print_error()
            raise ValueError('Error al iniciar la aplicación.')

        # Configuramos el modo de funcionamiento del sensor (modo de medida)
        self.set_drive_mode(1)

        if self.check_for_error():
            self.print_error()
            raise ValueError('Error al configurar el modo de funcionamiento.')

    def setup(self) -> None:
        """ Configuración inicial del sensor y lectura del valor de baseline. """
        print('Iniciando lectura del CCS811...')
        self.configure_ccs811()
        result = self.get_base_line()

        print(f'Baseline para este sensor: {result}')

    def get_base_line(self) -> int:
        """ Lee el valor del baseline del sensor. """
        b = self.i2c.readfrom_mem(self.addr, CCS811_BASELINE, 2)
        baselineMSB = b[0]
        baselineLSB = b[1]
        baseline = (baselineMSB << 8) | baselineLSB
        return baseline

    def check_for_error(self) -> bool:
        """ Verifica si hay errores en el sensor. """
        value = self.i2c.readfrom_mem(self.addr, CCS811_STATUS, 1)
        return (value[0] >> 0) & 1

    def app_valid(self) -> bool:
        """ Verifica si la aplicación del sensor es válida. """
        value = self.i2c.readfrom_mem(self.addr, CCS811_STATUS, 1)
        return (value[0] >> 4) & 1

    def set_drive_mode(self, mode: int) -> None:
        """ Establece el modo de funcionamiento del sensor. """
        if mode > 4:
            mode = 4
        self.i2c.writeto_mem(self.addr, CCS811_MEAS_MODE, bytearray([0b00011000]))
        time.sleep(2)

    def data_available(self) -> bool:
        """ Comprueba si los datos están disponibles para leer. """
        value = self.i2c.readfrom_mem(self.addr, CCS811_STATUS, 1)
        return (value[0] >> 3) & 0x01

    def read_sensor_data(self) -> None:
        """ Lee los datos del sensor (CO2 y TVOC). """
        if self.data_available():
            register = self.i2c.readfrom_mem(self.addr, CCS811_ALG_RESULT_DATA, 4)
            co2HB = register[0]
            co2LB = register[1]
            tVOCHB = register[2]
            tVOCLB = register[3]
            self.CO2 = ((co2HB << 8) | co2LB)
            self.tVOC = ((tVOCHB << 8) | tVOCLB)

    def readeCO2(self) -> int:
        """ Lee el valor de CO2 en partes por millón (ppm). """
        self.read_sensor_data()
        return self.CO2

    def readtVOC(self) -> int:
        """ Lee el valor de TVOC en partes por billón (ppb). """
        self.read_sensor_data()
        return self.tVOC

    def reset(self) -> None:
        """ Realiza un reset por software del sensor. """
        seq = bytearray([0x11, 0xE5, 0x72, 0x8A])
        self.i2c.writeto_mem(self.addr, CCS811_SW_RESET, seq)

    def put_envdata(self, humidity: float, temp: float) -> None:
        """
        Establece los datos ambientales (humedad y temperatura) para mejorar las mediciones de CO2 y TVOC.
        
        :param humidity: Humedad relativa en porcentaje.
        :param temp: Temperatura en grados Celsius.
        """
        envregister = bytearray([0x00, 0x00, 0x00, 0x00])
        envregister[0] = int(humidity) << 1
        t = int(temp // 1)
        tf = temp % 1
        t_H = (t + 25) << 9
        t_L = int(tf * 512)
        t_comb = t_H | t_L
        envregister[2] = t_comb >> 8
        envregister[3] = t_comb & 0xFF
        self.i2c.writeto_mem(self.addr, CCS811_ENV_DATA, envregister)

    def is_ready(self) -> bool:
        """
        Verifica si el sensor tiene datos válidos y si han pasado más de 20 minutos desde su inicialización.

        :return: `True` si los datos están listos y han pasado más de 20 minutos, `False` en caso contrario.
        """
        elapsed_time = time.time() - self.start_time

        return self.data_available() and elapsed_time > 1200  # 20 minutos = 1200
