import io
import mimetypes
import os

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

# Se registra explícito en vez de confiar en que la versión de Python del
# servidor ya reconozca '.webp' por su cuenta — sin esto, R2/S3 podría servir
# el archivo con un Content-Type genérico que rompe que el navegador lo
# muestre como imagen en vez de descargarlo.
mimetypes.add_type('image/webp', '.webp')

WEBP_QUALITY = 82


def compress_image(image_file) -> ContentFile:
    """Recomprime una imagen subida a WebP, manteniendo sus dimensiones.

    No cambia ancho/alto — solo reduce el peso del archivo (WebP comprime
    mejor que JPEG/PNG a calidad visual equivalente). De paso aplica la
    rotación EXIF antes de descartar los metadatos (algunas fotos de celular
    solo guardan un flag de rotación en vez de rotar los píxeles reales; sin
    esto, la foto podría quedar de lado una vez convertida).
    """
    image = Image.open(image_file)
    image = ImageOps.exif_transpose(image)

    if image.mode not in ('RGB', 'RGBA'):
        image = image.convert('RGBA' if 'transparency' in image.info else 'RGB')

    buffer = io.BytesIO()
    image.save(buffer, format='WEBP', quality=WEBP_QUALITY)
    buffer.seek(0)

    base_name = os.path.splitext(getattr(image_file, 'name', 'photo'))[0]
    return ContentFile(buffer.read(), name=f'{base_name}.webp')
