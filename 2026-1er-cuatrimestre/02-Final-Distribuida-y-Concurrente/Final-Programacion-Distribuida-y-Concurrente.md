# Fundamentos de la programación paralela - Procesamiento de Imágenes
Docente: Augusto Villa Monte
Alumno: Emilio Giordano
Asignatura: Programación Distribuida y Concurrente
Fecha de entrega: 13/02/2025
## Introducción
En la **ejecución secuencial**, las instrucciones se procesan una tras otra en un único flujo de control. En la **ejecución paralela**, varias tareas se ejecutan simultáneamente en distintos núcleos de la CPU, reduciendo el tiempo total cuando el trabajo es divisible en unidades independientes.
En Python, el **GIL (Global Interpreter Lock)** históricamente limita el paralelismo real con hilos: solo un hilo puede ejecutar bytecode Python a la vez. Los threads ofrecen *concurrencia* (intercalado de tareas) pero no *paralelismo real* en tareas CPU-intensivas. **Python 3.14t (free-threading)** elimina esta restricción permitiendo paralelismo real con hilos.
## Tipos de Paralelismo
Durante la lectura y realización de pruebas de código sobre programación distribuida, concurrente y paralela, he identificado dos enfoques principales para aplicar procesamiento paralelo:
1. **Paralelismo de múltiples jobs independientes (N-jobs):** Ejecutar N tareas completas en paralelo, donde cada hilo procesa una tarea de inicio a fin. Ejemplos:
    - Procesar 100 imágenes donde cada hilo procesa una imagen completa
    - Un pipeline completo de un proceso, que puede incluir: descarga y lectura de un archivo CSV, filtrado e inserción de los datos del CSV a una Base de Datos.
2. **Paralelismo algorítmico (1-job):** Paralelizar un único algoritmo subdividiendo su trabajo interno. Ejemplo: Merge Sort recursivo donde cada hilo ordena una porción del array.

Este informe se enfoca en el **primer caso**.
## Caso de Estudio: Procesamiento Paralelo de Imágenes
### Descripción del Problema
Se requiere procesar 1000 imágenes de productos para una tienda online. Cada imagen debe redimensionarse a 3 tamaños (thumbnail 150×150, medium 500×500, large 1200×1200), aplicarse filtros de mejora (SHARPEN, UnsharpMask), añadir marca de agua y optimizarse para web (compresión JPEG). Para este caso experimental, también se generarán las imágenes.
**Características que favorecen el paralelismo:**
- **Tareas independientes:** Procesar la imagen A no afecta a la imagen B
- **CPU-intensivo:** Manipulación de píxeles requiere operaciones matemáticas intensivas
- **Sin estado compartido:** No hay datos compartidos entre tareas que requieran sincronización
### Implementación
**Código secuencial:**
```python
results = []
for image_data, image_id in images:
    result = processor.process_single_image(image_data, image_id)
    results.append(result)
```
Cada imagen espera a que termine la anterior.

**Código paralelo:**
```python
with ThreadPoolExecutor(max_workers=num_workers) as executor:
    futures = [
        executor.submit(processor.process_single_image, image_data, image_id)
        for image_data, image_id in images
    ]
    results = [f.result() for f in futures]
```
$n$ hilos procesan hasta $n$ imágenes simultáneamente.
### Operaciones CPU-Intensivas
Operaciones de Pillow encargadas del procesamiento:
```python
# Resize con algoritmo LANCZOS (procesamiento matemático intensivo)
img.thumbnail(dimensions, Image.Resampling.LANCZOS)

# Filtros que procesan cada píxel
img.filter(ImageFilter.SHARPEN)
img.filter(ImageFilter.UnsharpMask(radius=2, percent=150))

# Compresión JPEG optimizada
img.save(buffer, format='JPEG', quality=85, optimize=True)
```
Estas operaciones, internamente, están implementadas en C y liberan a Python del GIL durante su ejecución, permitiendo paralelismo real incluso en Python < 3.14. Estas operaciones provienen de la biblioteca Pillow importada al inicio del código: `from PIL import Image, ImageDraw, ImageFont, ImageFilter`
## Resultados Experimentales
### Configuración
- **Hardware:** CPU de 8 núcleos
- **Dataset:** 1000 imágenes de 800×600 píxeles
- **Python:** 3.12.6 & 3.14t
- **Workers:** 8 threads
### Resultados obtenidos
Se realizaron pruebas con 100, 1000 y 10000 imágenes, todas realizadas bajo las mismas condiciones. Para cada cantidad de imágenes, se ejecutó una vez con la versión `3.12.6`, y otra con la versión `3.14t` de Python.

| Versión | Imágenes | Secuencial | Paralelo | Speedup | Eficiencia |
| ------- | -------- | ---------- | -------- | ------- | ---------- |
| 3.12.6  | 100      | 4.38s      | 1.29s    | 3.39x   | 42.4%      |
| 3.14t   | 100      | 4.45s      | 0.81s    | 5.52x   | 69.0%      |
| 3.12.6  | 1000     | 42.77s     | 13.34s   | 3.21x   | 40.1%      |
| 3.14t   | 1000     | 45.77s     | 8.37s    | 5.47x   | 68.3%      |
| 3.12.6  | 10000    | 455.61s    | 195.40s  | 2.33x   | 29.1%      |
| 3.14t   | 10000    | 471.00s    | 76.27s   | 6.18x   | 77.2%      |
El paralelismo muestra mejoras consistentes en todos los casos, con speedups entre 3.4x y 6.2x dependiendo de la versión de Python.
Se destacan dos diferencias primordiales: Las ejecuciones secuenciales se realizaron en menor tiempo con la versión `3.12.6`, mientras que sucede lo contrario con las ejecuciones paralelas, con un amplio margen de mejora para la versión `free-threading` frente a la versión estándar de Python. 
A pesar de haber utilizado PIL, se obtienen mejores resultados al utilizar la versión `3.14t` al implementar paralelismo.
El tiempo de ejecución puede variar entre ejecutar el mismo programa con el mismo número de imágenes y la misma versión, pero es una diferencia insignificante y esperable.
**Observación 1: Free-threading mejora el speedup paralelo**
- Python 3.14t obtiene consistentemente mejor speedup (5.5-6.2x) que 3.12.6 (2.3-3.4x).
- A pesar de que Pillow libera el GIL en operaciones C, free-threading beneficia las operaciones Python (ImageDraw, gestión de memoria).
**Observación 2: Overhead de free-threading en ejecución secuencial** 
- Python 3.14t es ligeramente más lento en modo secuencial (~3% más lento).
- Este overhead es el precio de eliminar el GIL, pero se compensa con creces en paralelo.
**Observación 3: Escalabilidad con carga de trabajo** 
- Con 10000 imágenes, la eficiencia mejora (77.2%) comparado con 100 imágenes (69.0%).
- El overhead de creación de threads se amortiza mejor con mayor volumen de trabajo.
**Observación 4: Degradación en Python 3.12.6** 
- La eficiencia cae de 42.4% (100 imgs) a 29.1% (10000 imgs) con GIL activo 
- Indica contención del GIL que empeora con más threads activos simultáneamente
### Interpretación
La diferencia fundamental radica en cómo cada versión maneja la sincronización: 
- **Python 3.12.6:** Aunque Pillow libera el GIL para operaciones C, el overhead de adquisición/liberación constante del GIL limita el speedup.
- **Python 3.14t:** Sin GIL, todos los threads ejecutan verdaderamente en paralelo sin contención. 
El speedup de ~6x con 8 cores (75% de eficiencia) refleja que aproximadamente el 25% del tiempo de procesamiento involucra operaciones Python puras (gestión de objetos, estadísticas) que se benefician de free-threading.
## Análisis: ¿Por Qué Funciona Tan Bien?
Cada imagen es procesada sin comunicación con otras:
```python
# Thread 1: procesa imagen_001.jpg
# Thread 2: procesa imagen_002.jpg  } Sin compartir datos
# ...                               } Sin sincronización
# Thread 8: procesa imagen_008.jpg
# Thread 1: procesa imagen_009.jpg
# Thread 2: procesa imagen_010.jpg
# ...
# Thread 8: procesa imagen_016.jpg
```
Elimina race conditions y necesidad de locks (excepto para estadísticas compartidas).
Cada imagen requiere aproximadamente el mismo tiempo (~0.34s), evitando que algunos threads terminen mucho antes que otros.
Las operaciones de Pillow (filtros, resize, compresión) están implementadas en C y liberan el GIL durante su ejecución. Esto permite paralelismo real incluso sin free-threading. Un caso similar ocurre al ejecutar código Python con Numpy, el cual está implementado en C con paralelismo, permitiendo abstraerse estas cuestiones.
Los threads no necesitan sincronizar datos frecuentemente, solo al actualizar estadísticas:
```python
with self.lock:
    self.stats['processed'] += 1  # Única sincronización
```
## Limitaciones y Consideraciones
### Cuándo NO usar este enfoque:
- **Las tareas son muy rápidas (< 10ms):** El overhead de threading supera el beneficio
- **Hay pocas tareas (< número de cores):** No hay suficiente trabajo para todos los cores
- **Tareas interdependientes:** Requiere sincronización que reduce eficiencia
- **Recursos compartidos limitados:** Disco, red, base de datos pueden ser cuellos de botella ante un escenario donde los recursos sean muy limitados.
### Alternativas:
- `multiprocessing`: Para evitar completamente el GIL, pero con mayor overhead de IPC
- **Python 3.14t free-threading:** Para código Python puro CPU-intensivo
- **Procesamiento asíncrono:** Para tareas I/O-bound (descargas, APIs)
## Conclusión
La distribución paralela de trabajo mejora significativamente los tiempos de ejecución cuando el problema es divisible en tareas independientes. Sin embargo, el beneficio no siempre es lineal: en casos con tareas muy rápidas, pocas tareas, o alta interdependencia, el overhead puede reducir o incluso anular las ganancias.
Es importante distinguir que este informe se enfoca en **paralelismo de N-jobs independientes**, donde cada tarea es autónoma. En contraste, el **paralelismo algorítmico** (paralelizar un único algoritmo grande subdividiéndolo) enfrenta desafíos adicionales como la Ley de Amdahl, sincronización entre fragmentos, y balanceo de carga, lo que puede limitar significativamente el speedup alcanzable.
El paralelismo de N-jobs independientes es efectivo cuando:
1. Las tareas son **independientes** (sin estado compartido)
2. Son **CPU-intensivas** (justifican el overhead de threading)
3. Hay **suficiente trabajo** para todos los cores disponibles
El caso de procesamiento de imágenes demuestra que, bajo estas condiciones, el paralelismo reduce drásticamente los tiempos de ejecución.


## Referencias
**Código:**
- Código completo: `image_processor.py` — Procesamiento secuencial y paralelo con `ThreadPoolExecutor`

**Documentación Python:**
- Python Free-Threading: https://docs.python.org/3/howto/free-threading-python.html
- Global Interpreter Lock (GIL): https://docs.python.org/3/glossary.html#term-global-interpreter-lock
- PEP 703 – Making the GIL Optional: https://peps.python.org/pep-0703/
- Threading & Concurrent Futures: https://docs.python.org/3/library/concurrent.futures.html

**Bibliotecas:**
- Pillow PyPI: https://pypi.org/project/pillow/
- Pillow Documentation: https://pillow.readthedocs.io/en/stable/
- Pillow Release 9.3.0 (GIL improvements): https://pillow.readthedocs.io/en/stable/releasenotes/9.3.0.html
- Pillow Release 10.3.0: https://pillow.readthedocs.io/en/stable/releasenotes/10.3.0.html

**Conceptos teóricos:**
- Speedup: https://en.wikipedia.org/wiki/Speedup
- Efficiency: https://en.wikipedia.org/wiki/Parallel_efficiency
- Amdahl's Law: https://en.wikipedia.org/wiki/Amdahl%27s_law


