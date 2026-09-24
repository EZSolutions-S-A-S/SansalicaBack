import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from PIL import Image

from inmuebles.infrastructure.image_processing import compress_image


def _uploaded_image(name='foto.png', size=(800, 600), color='red', fmt='PNG'):
    buffer = io.BytesIO()
    Image.new('RGB', size, color=color).save(buffer, format=fmt)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=f'image/{fmt.lower()}')


class CompressImageTests(SimpleTestCase):
    def test_output_is_webp(self):
        result = compress_image(_uploaded_image())
        self.assertTrue(result.name.endswith('.webp'))
        image = Image.open(result)
        self.assertEqual(image.format, 'WEBP')

    def test_dimensions_are_preserved(self):
        result = compress_image(_uploaded_image(size=(800, 600)))
        image = Image.open(result)
        self.assertEqual(image.size, (800, 600))

    def test_output_is_smaller_than_uncompressed_input(self):
        original = _uploaded_image(size=(1200, 900), fmt='BMP', name='foto.bmp')
        original_size = original.size
        result = compress_image(original)
        self.assertLess(len(result.read()), original_size)

    def test_reencoded_file_is_a_valid_readable_image(self):
        result = compress_image(_uploaded_image())
        image = Image.open(result)
        image.load()  # fuerza la decodificación completa, no solo el header

    def test_rotated_exif_orientation_is_applied_before_compressing(self):
        buffer = io.BytesIO()
        image = Image.new('RGB', (800, 600), color='blue')
        exif = image.getexif()
        exif[0x0112] = 6  # orientación "rotar 90° a la derecha"
        image.save(buffer, format='JPEG', exif=exif)
        uploaded = SimpleUploadedFile('foto.jpg', buffer.getvalue(), content_type='image/jpeg')

        result = compress_image(uploaded)
        rotated = Image.open(result)
        # Tras aplicar la orientación EXIF (rotar 90°), ancho y alto se intercambian.
        self.assertEqual(rotated.size, (600, 800))
