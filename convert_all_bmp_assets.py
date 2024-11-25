import os
from PIL import Image


def bmp_to_rgb565 (bmp_file, output_file):
    """Convierte un archivo BMP a RGB565 y lo guarda en output_file."""
    # Abre la imagen BMP
    img = Image.open(bmp_file)

    # Convierte la imagen a RGB
    img = img.convert("RGB")

    # Obtiene los píxeles de la imagen
    pixels = img.load()

    # Abre el archivo de salida
    with open(output_file, 'wb') as f:
        for y in range(img.height):
            for x in range(img.width):
                r, g, b = pixels[x, y]
                # Convierte el color RGB a RGB565
                rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                # Escribe los bytes en el archivo
                f.write(bytes([rgb565 >> 8, rgb565 & 0xFF]))

    print(f"Imagen convertida: {bmp_file} -> {output_file}")


def convert_all_bmps_in_directory (source_dir, output_dir):
    """Convierte todos los archivos BMP en el directorio source_dir a formato RGB565 y los guarda en output_dir."""

    # Asegúrate de que el directorio de salida exista
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Recorre todos los archivos en el directorio source_dir
    for filename in os.listdir(source_dir):
        if filename.endswith(".bmp"):
            # Ruta completa al archivo BMP
            bmp_file = os.path.join(source_dir, filename)

            # El nombre de salida tendrá la misma base pero con extensión .rgb565
            output_filename = os.path.splitext(filename)[0] + ".rgb565"
            output_file = os.path.join(output_dir, output_filename)

            # Convierte el BMP a RGB565 y guarda en la ruta de salida
            bmp_to_rgb565(bmp_file, output_file)


# Directorios de entrada y salida
source_directory = "assets"  # Directorio donde están los archivos .bmp
output_directory = "src/images"  # Directorio donde se guardarán los archivos .rgb565

# Convierte todos los BMP del directorio "assets" y guárdalos en "src/images"
convert_all_bmps_in_directory(source_directory, output_directory)
