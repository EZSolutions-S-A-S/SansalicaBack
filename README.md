<div align="center">

# 🏠 Sansalica Backend

**El motor de datos detrás del catálogo inmobiliario de Sansalica**

<p>
  <img src="https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django 6.0" />
  <img src="https://img.shields.io/badge/DRF-Django%20REST%20Framework-A30000?style=for-the-badge&logo=django&logoColor=white" alt="Django REST Framework" />
  <img src="https://img.shields.io/badge/Storage-Cloudflare%20R2-F38020?style=for-the-badge&logo=cloudflare&logoColor=white" alt="Cloudflare R2" />
</p>

<p>
  <img src="https://img.shields.io/badge/status-en%20diseño-yellow?style=flat-square" alt="Status: en diseño" />
  <img src="https://img.shields.io/badge/python-3.13-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.13" />
  <img src="https://img.shields.io/badge/license-privado-lightgrey?style=flat-square" alt="Licencia privada" />
</p>

</div>

<br>

API construida en **Django + Django REST Framework** para administrar y servir el catálogo de propiedades de Sansalica: control total sobre el modelo de datos, imágenes en almacenamiento propio y un contrato estable para cualquier cliente que lo consuma.

<br>

## 🧱 El modelo: `Inmueble`

<table>
<tr><th>Campo</th><th>Tipo</th><th>Detalle</th></tr>
<tr><td><code>title</code></td><td>texto corto</td><td>título del anuncio</td></tr>
<tr><td><code>operation_type</code></td><td>selección única</td><td><code>Venta</code> · <code>Alquiler</code></td></tr>
<tr><td><code>property_type</code></td><td>selección única</td><td><code>Casa</code> · <code>Apartamento</code> · <code>Local Comercial</code> · <code>Terreno</code></td></tr>
<tr><td><code>price</code></td><td>número</td><td></td></tr>
<tr><td><code>square_meters</code></td><td>número</td><td></td></tr>
<tr><td><code>floor</code></td><td>número</td><td>opcional</td></tr>
<tr><td><code>bedrooms</code></td><td>número</td><td>opcional</td></tr>
<tr><td><code>bathrooms</code></td><td>número</td><td>opcional</td></tr>
<tr><td><code>parking_spots</code></td><td>número</td><td>opcional</td></tr>
<tr><td><code>features</code></td><td>lista de texto</td><td></td></tr>
<tr><td><code>amenities</code></td><td>lista de texto</td><td></td></tr>
<tr><td><code>location</code></td><td>texto corto</td><td></td></tr>
<tr><td><code>description</code></td><td>texto largo</td><td></td></tr>
<tr><td><code>photos</code></td><td>adjuntos</td><td>múltiples imágenes JPG/PNG</td></tr>
<tr><td><code>status</code></td><td>selección única</td><td><code>Disponible</code> · <code>Reservado</code> · <code>Vendido</code></td></tr>
<tr><td><code>featured</code></td><td>booleano</td><td></td></tr>
</table>

<br>

## 🎯 Decisiones de diseño

<table>
<tr><th>Área</th><th>Decisión</th><th>Motivo</th></tr>
<tr>
  <td><strong>Naming de la API</strong></td>
  <td>Campos en inglés, estilo <code>snake_case</code></td>
  <td>Contrato de datos estable y consistente</td>
</tr>
<tr>
  <td><strong>Imágenes</strong></td>
  <td>Cloudflare R2 (S3-compatible) vía <code>django-storages</code> + <code>boto3</code></td>
  <td>Sin costo de egress — clave para un catálogo de fotos con tráfico público</td>
</tr>
<tr>
  <td><strong>Lectura</strong><br><code>GET /inmuebles</code></td>
  <td>API Key vía header <code>Authorization: Api-Key &lt;token&gt;</code></td>
  <td>Acceso simple y controlado para clientes de solo lectura</td>
</tr>
<tr>
  <td><strong>Escritura</strong><br>crear / editar / borrar</td>
  <td>Solo vía Django Admin, con login de staff</td>
  <td>Solo la inmobiliaria administra el catálogo, sin exponer endpoints de escritura</td>
</tr>
<tr>
  <td><strong>Alcance funcional</strong></td>
  <td>CRUD + filtros (<code>operation_type</code>, <code>property_type</code>, rango de precio, <code>status</code>, <code>featured</code>) + búsqueda + paginación</td>
  <td>Evita sobrecargar a los clientes con catálogos grandes</td>
</tr>
</table>

<br>

## 🗺️ Roadmap

- [ ] App `inmuebles` con el modelo `Inmueble`
- [ ] Serializers DRF
- [ ] Autenticación por API Key (lectura) + Django Admin (escritura)
- [ ] Filtros, búsqueda y paginación en el ViewSet
- [ ] Integración de imágenes con Cloudflare R2
- [ ] Panel de administración para gestión del catálogo

<br>

## 📦 Estado actual

> Este repositorio contiene por ahora solo el scaffold inicial de Django (`django-admin startproject`). La implementación del modelo, serializers, autenticación, filtros y storage está en la fase de diseño, documentada arriba para guiar el desarrollo.
