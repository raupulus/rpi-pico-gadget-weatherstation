#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from math import floor, ceil
from time import time, sleep_ms
from Lib.ST7735 import ST7735
from machine import Pin

from Models.WeatherStation import WeatherStation


class DisplayST7735_128x160():
    TIME_TO_OFF = 10  # Tiempo en minutos para apagar la pantalla
    DISPLAY_ORIENTATION = 3  # Orientación de la pantalla
    DEBUG = False

    DELAY = 0x80

    DISPLAY_WIDTH = 160
    DISPLAY_HEIGHT = 128

    locked = False

    # Colores por secciones (de más claro a más oscuro)
    COLORS = {
        'white': 0xFFFF,
        'black': 0x0000,

        # Rojos
        'red1': 0xF800,
        'red2': 0xD800,
        'red3': 0xB800,
        'red4': 0x9000,
        'red5': 0x7800,

        # Amarillos
        'yellow1': 0xFFE0,
        'yellow2': 0xEE20,
        'yellow3': 0xC618,
        'yellow4': 0x8400,
        'yellow5': 0x7C00,

        # Verdes
        'green1': 0x07E0,
        'green2': 0x06E0,
        'green3': 0x04E0,
        'green4': 0x02E0,
        'green5': 0x01E0,

        # Azules
        'blue1': 0x001F,
        'blue2': 0x003F,
        'blue3': 0x005F,
        'blue4': 0x007F,
        'blue5': 0x009F,

        # Rosas
        'pink1': 0xFC9F,
        'pink2': 0xF81F,
        'pink3': 0xD69A,
        'pink4': 0xBDF7,
        'pink5': 0xA953,

        # Grises
        'gray1': 0x7BEF,
        'gray2': 0x739C,
        'gray3': 0x6318,
        'gray4': 0x4A49,
        'gray5': 0x2104,

        'orange1': 0xFD60,
        'orange2': 0xFD20,
        'orange3': 0xFB80,
        'orange4': 0xFAE0,
        'orange5': 0xFA60
    }

    # TODO: Añadir más fuentes y controlar bloques para no solapar, hacer grid almacenado
    FONTS = {
        'normal': {
            'h': 7,  # Alto de la letra
            'w': 5,  # Ancho de la letra
            'font': 'font5x7.fnt',  # Fuente
            'line_height': 9,  # Alto de la línea
            'font_padding': 1  # Espacio entre carácteres, 1 por defecto
        },
    }

    def __init__(self, spi, rst=9, ce=13, dc=12, offset=0, c_mode='RGB', btn_display_on=None, orientation=3, timeout=10, debug=False, color=0, background=0x000, pin_backlight=None):
        self.display = ST7735(spi, rst, ce, dc, offset, c_mode, color=color, background=background)
        self.display.set_rotation(orientation)

        # Estado inicial de la pantalla
        self.reset()

        # Tiempo en el que se encendió la pantalla por primera vez
        self.display_on_at = time()
        self.display_on = True  # Indica si la pantalla está encendida o apagada
        self.DEBUG = debug

        self.DISPLAY_ORIENTATION = orientation
        self.TIME_TO_OFF = timeout

        if self.DISPLAY_ORIENTATION == 1:
            self.DISPLAY_WIDTH = 160
            self.DISPLAY_HEIGHT = 128
        elif self.DISPLAY_ORIENTATION == 2:
            self.DISPLAY_WIDTH = 128
            self.DISPLAY_HEIGHT = 160
        elif self.DISPLAY_ORIENTATION == 3:
            self.DISPLAY_WIDTH = 160
            self.DISPLAY_HEIGHT = 128
        elif self.DISPLAY_ORIENTATION == 4:
            self.DISPLAY_WIDTH = 128
            self.DISPLAY_HEIGHT = 160

        if btn_display_on is not None:
            self.btn_display_on = Pin(btn_display_on, Pin.IN, Pin.PULL_DOWN)
            self.btn_display_on.irq(trigger=Pin.IRQ_RISING, handler=self.callbackDisplayOn)

            sleep_ms(100)

        if pin_backlight is not None:
            self.pin_backlight = Pin(pin_backlight, Pin.OUT)
            self.pin_backlight.on()
            sleep_ms(100)

    def reset(self):
        """
        Prepara el estado inicial de la pantalla.
        """

        while self.locked:
            sleep_ms(10)

        self.locked = True

        self.display.reset()
        self.display.begin()
        self.display.set_rotation(self.DISPLAY_ORIENTATION)

        self.locked = False

        self.cleanDisplay()

    def cleanDisplay(self):

        while self.locked:
            sleep_ms(10)

        try:
            self.locked = True

            black = self.COLORS['black']
            self.display._bground = black
            self.display.set_rotation(self.DISPLAY_ORIENTATION)
            self.display.fill_screen(black)
            self.display.draw_block(0, 0, self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT, black)
        except Exception as e:
            if self.DEBUG:
                print('Error en cleanDisplay(): {}'.format(e))
        finally:
            self.locked = False

    def loop(self):
        """
        Mientras la pantalla esté encendida, comprobar si se apaga cada 10 segundos
        """

        diffSeconds = time() - self.display_on_at
        diffMinutes = diffSeconds / 60

        if diffMinutes > self.TIME_TO_OFF and self.display_on:
            self.display_on = False

            # Apaga el led para la pantalla
            if self.pin_backlight is not None:
                self.pin_backlight.off()

            #self.cleanDisplay()

        #elif not self.display_on:
        #    self.callbackDisplayOn()

    def callbackDisplayOn(self, pin=None):
        """
        Callback para encender la pantalla, se dispara al pulsar el botón de encendido
        """
        if self.btn_display_on.value() == 1:
            while self.locked:
                if self.DEBUG:
                    print('Esperando a que se desbloquee la pantalla en callbackDisplayOn()')

                sleep_ms(10)

            try:
                self.display_on = True

                # Enciende el led de la pantalla
                if self.pin_backlight is not None:
                    self.pin_backlight.on()

                #self.reset()
                self.display_on_at = time()

                #self.displayHeadInfo(wifi_status=False)
                #self.displayFooterInfo()
                #sleep_ms(self.DELAY)
                #self.grid_create()
            except Exception as e:
                if self.DEBUG:
                    print('Error al encender la pantalla: {}'.format(e))
            finally:
                self.locked = False

        else:
            # En caso de entrar con la pantalla encendida, la apago
            self.display_on = False

            if self.pin_backlight is not None:
                self.pin_backlight.off()

            #self.cleanDisplay()

        sleep_ms(50)


    def printChar(self, x, y, ch, color, bg_color):
        if not self.display_on:
            return

        while self.locked:
            if self.DEBUG:
                print('Esperando a que se desbloquee la pantalla en printChar()')

            sleep_ms(10)

        try:
            self.locked = True

            font = self.FONTS['normal']  ## Fuente
            font_height = font['h']  # Alto de la letra
            font_width = font['w']  # Ancho de la letra
            font_padding = font['font_padding']

            fp = (ord(ch)-0x20) * font_width
            f = open(font['font'], 'rb')
            f.seek(fp)
            b = f.read(font_width)
            char_buf = bytearray(b)
            char_buf.append(0)

            font_height_padding = font_height + font_padding
            font_width_padding = font_width + font_padding

            # Creo la imagen del carácter teniendo en cuenta padding
            char_image = bytearray()
            for bit in range(font_height_padding):
                for c in range(font_width_padding):
                    if ((char_buf[c] >> bit) & 1) > 0:
                        char_image.append(color >> font_height_padding)
                        char_image.append(color & 0xff)
                    else:
                        char_image.append(bg_color >> font_height_padding)
                        char_image.append(bg_color & 0xff)

            self.display.draw_bmp(x, y, font_width_padding, font_height_padding, char_image)
        except Exception as e:
            if self.DEBUG:
                print('Error en printChar(): {}'.format(e))
        finally:
            self.locked = False

    def printByPos(self, line, pos, content, length = None, color = 0xFFE0, background = 0x0000):
        """
        Imprime contenido en una posición determinada borrando previamente el contenido si recibe longitud

        line: integer, línea en eje vertical dónde se imprimirá el contenido
        pos: integer, posición en eje horizontal dónde se imprimirá el contenido
        content: string, contenido a dibujar
        length: integer, longitud del contenido a borrar (cantidad de carácteres). Esto es para no dejar residuos de contenido anterior
        """

        font = self.FONTS['normal']  ## Fuente
        font_width = font['w']  # Ancho de la letra

        # Espacio entre carácteres teniendo en cuenta el paddding
        font_total_width = font_width + (font['font_padding'] * 2)
        line_height = font['line_height']  # Altura dónde inicia cada línea

        # Cantidad máxima de carácteres en la línea
        max_line_chars = floor(self.DISPLAY_WIDTH / (font_width + font['font_padding']))

        content = str(content)

        if len(content) > max_line_chars:
            content = content[0:max_line_chars]

        pixels_x = pos * font_total_width # Posición en eje horizontal para iniciar a dibujar
        pixels_y = line * line_height # Posición en eje vertical para iniciar a dibujar

        # Si recibo la longitud, borro el contenido previo
        if length:
            clean_length_width = int(length) * font_total_width

            self.display.draw_block(pixels_x, pixels_y, clean_length_width, line_height, background)

        pixels_x_counter = pixels_x

        for ch in (content):
            self.printChar(pixels_x_counter, pixels_y + font['font_padding'], ch, color, background)
            pixels_x_counter += font_width + font['font_padding']


    def displayHeadInfo(self, wifi_status):
        """
        La primera fila de la pantalla será para mostrar información del estado en general. Esta información contempla:
        - Estado de la conexión wifi
        - Estado de la subida de datos a la API
        - ¿Título o logotipo?
        """

        while self.locked:
            if self.DEBUG:
                print('Esperando a que se desbloquee la pantalla en displayHeadInfo()')

            sleep_ms(10)

        font = self.FONTS['normal']  ## Fuente
        font_width = font['w']  # Ancho de la letra
        font_total_width = font_width + (font['font_padding'] * 2)

        # Cantidad máxima de carácteres en la línea
        max_line_chars = floor(self.DISPLAY_WIDTH / font_total_width)

        color = self.COLORS['yellow1']
        background = self.COLORS['red3']

        ## Dibujar fondo de una línea
        self.display.draw_block(0, 0, self.DISPLAY_WIDTH, font['line_height'], background)

        """
        NOMBRE
        """
        center_content = ' WEATHER STATION'

        self.printByPos(0, 0, center_content, len(center_content),
                        color, background)

        """
        INFORMACIÓN DEL WIFI
        """
        block_wireless_width = 7 # Ancho del bloque carácteres para la información del wifi

        # Posición del comienzo para el estado del wifi. Calculado desde la derecha de la pantalla
        pos_wireless_start = max_line_chars - block_wireless_width
        wifi_on = 'ON' if wifi_status >= 3 else 'OFF'
        content = ' W: ' + wifi_on # W: ON | W: OFF

        self.printByPos(0, pos_wireless_start, content, block_wireless_width, color, background)


    def displayFooterInfo(self, center = 'WEATHER STATION'):

        while self.locked:
            if self.DEBUG:
                print('Esperando a que se desbloquee la pantalla en displayFooterInfo()')

            sleep_ms(10)

        font = self.FONTS['normal']  ## Fuente
        font_width = font['w']  # Ancho de la letra
        font_total_width = font_width + font['font_padding']

        # Cantidad máxima de carácteres en la línea
        max_line_chars = floor(self.DISPLAY_WIDTH / font_total_width)

        """
        INFORMACIÓN EN EL CENTRO
        """
        start_x = floor((max_line_chars/2) - (len(center) / 2))

        line = floor((self.DISPLAY_HEIGHT / font['line_height']) - 1)

        color = self.COLORS['black']
        background = self.COLORS['white']

        try:
            # TODO: Extraer el "draw_block" a un método de esta clase
            self.locked = True
            self.display.draw_block(0, line * font['line_height'], self.DISPLAY_WIDTH, font['line_height'], background)

        except Exception as e:
            if self.DEBUG:
                print('Error al dibujar el bloque de información en el footer: ' + str(e))
        finally:
            self.locked = False

        self.printByPos(line, start_x, center, len(center), color, background)


    def load_bmp(self, path, x, y, width, height):
        def load_bmp (filename):
            with open(filename, 'rb') as f:
                return f.read()

        image = load_bmp(path)

        self.display.draw_bmp(x, y, width, height, image)

    def grid_create (self):
        """
        Crea el grid de 3x3 cuadrados dónde se colocarán los elementos.
        La cuadrícula se encuentra en el centro de la pantalla con un
        margen superior e inferior de 9px para respetar el encabezado y el
        footer.
        """
        cell_width = self.DISPLAY_WIDTH // 3
        cell_height = (
                                  self.DISPLAY_HEIGHT - 18) // 3  # 18px for header and footer
        bg_color = self.COLORS['black']

        data_images = WeatherStation.data_images

        # Iterate over 3 rows and 3 columns
        for row in range(3):

            if row == 0:
                columns = ['temperature', 'air_quality', 'light']
            elif row == 1:
                columns = ['humidity', 'co2', 'uv']
            elif row == 2:
                columns = ['pressure', 'tvoc', 'sound']
            else:
                continue

            for col in range(3):
                images = data_images.get(columns[col])
                image = images.get('medium')

                x = col * cell_width
                y = row * cell_height + 9  # Adding the 9px top margin

                self.display.draw_block(x, y, cell_width, cell_height, bg_color)

                img_width = 15
                img_height = 30
                img_y = y + (cell_height - img_height) // 2

                # Placeholder for the image
                #self.display.draw_block(x, img_y, img_width, img_height, self.COLORS['gray4'])

                self.load_bmp(image, x, img_y, img_width, img_height)

    def grid_update (self):
        """
        Actualiza los datos en el grid de 3x3 cuadrados en el centro de la pantalla.
        """
        data = WeatherStation.data

        if not data:
            return

        cell_width = self.DISPLAY_WIDTH // 3
        cell_height = (
                                  self.DISPLAY_HEIGHT - 18) // 3  # 18px for header and footer
        margin = 1
        img_width = 15
        img_height = 30  # Assumed height based on 'grid_create'

        font = self.FONTS['normal']
        text_color = self.COLORS['white']
        bg_color = self.COLORS['black']

        font_total_height = font['line_height']
        total_text_height = 2 * font_total_height  # Para dos líneas de texto

        data_ranges = WeatherStation.data_ranges
        data_images = WeatherStation.data_images

        # Iterar sobre 3 filas y 3 columnas
        for row in range(3):
            if row == 0:
                columns = ['temperature', 'air_quality', 'light']
            elif row == 1:
                columns = ['humidity', 'co2', 'uv']
            elif row == 2:
                columns = ['pressure', 'tvoc', 'sound']
            else:
                continue

            for col in range(3):
                stats = data.get(columns[col])
                value = stats.get('current')
                unit = stats.get('unit')

                ranges = data_ranges.get(columns[col])
                images = data_images.get(columns[col])

                sensor_range = 'medium'

                if isinstance(value, float):
                    sensor_range = WeatherStation.get_range(columns[col], value)

                    if value > 999.9:
                        value = int(value)
                    else:
                        value = round(value, 1)
                elif isinstance(value, int):
                    sensor_range = WeatherStation.get_range(columns[col], value)

                elif value is None:
                    value = '-'

                image = images.get(sensor_range)

                # Asegúrate de que 'value' sea una cadena
                if not isinstance(value, str):
                    value = str(value)

                # Asegúrate de que 'unit' sea una cadena
                if not isinstance(unit, str):
                    unit = str(unit)

                # Centramos las cadenas a 5 caracteres
                value = value.center(5)
                unit = unit.center(5)

                x = col * cell_width
                y = row * cell_height + 9  # Añadiendo margen superior de 9px

                # Ajuste para centrar texto verticalmente dentro de la celda
                text_y = y + (
                        cell_height - total_text_height) // 2  # Donde comienza el texto dentro de la celda

                text_x = x + img_width + margin  # Ajustar la posición x en base al ancho de la imagen y el margen de manera uniforme para todas las columnas

                text_pos_x = ceil(
                    text_x // (font['w'] + (font['font_padding'] * 2))) + margin

                # Replicar cálculo de posición de la imagen de grid_create
                img_y = y + (cell_height - img_height) // 2

                # Dibujar la nueva imagen en la misma posición
                self.load_bmp(image, x, img_y, img_width, img_height)

                # Ajustar posición vertical del texto usando text_y
                self.printByPos(
                    text_y // font['line_height'],
                    text_pos_x,
                    value,
                    None,
                    text_color,
                    bg_color
                )
                self.printByPos(
                    (text_y // font['line_height']) + 1,
                    text_pos_x,
                    unit,
                    None,
                    text_color,
                    bg_color
                )
