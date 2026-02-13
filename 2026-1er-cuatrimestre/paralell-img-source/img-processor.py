#!/usr/bin/env python3
import time
import threading
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
from concurrent.futures import ThreadPoolExecutor

NUM_IMAGES = 10000
NUM_WORKERS = 8

class ImageProcessor:
    SIZES = {
        'thumbnail': (150, 150),
        'medium': (500, 500),
        'large': (1200, 1200)
    }
    
    def __init__(self, watermark_text="© Mi Tienda 2026"):
        self.watermark_text = watermark_text
        self.stats = {
            'processed': 0,
            'errors': 0,
            'total_time': 0
        }
        self.lock = threading.Lock()
    
    def process_single_image(self, image_data, image_id):
        """
        Procesa una imagen individual:
        1. Resize a múltiples tamaños
        2. Aplica marca de agua
        3. Optimiza compresión
        """
        try:
            start_time = time.time()
            original = Image.open(io.BytesIO(image_data))
            if original.mode != 'RGB':
                original = original.convert('RGB')
            
            results = {}
            
            for size_name, dimensions in self.SIZES.items():
                img = original.copy()
                img.thumbnail(dimensions, Image.Resampling.LANCZOS)
                img = img.filter(ImageFilter.SHARPEN)
                img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150))
                img = self._add_watermark(img, size_name)
                
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85, optimize=True)
                results[size_name] = buffer.getvalue()
            
            
            processing_time = time.time() - start_time
        
            with self.lock:
                self.stats['processed'] += 1
                self.stats['total_time'] += processing_time
            
            return {
                'id': image_id,
                'images': results,
                'processing_time': processing_time,
                'success': True
            }
            
        except Exception as e:
            with self.lock:
                self.stats['errors'] += 1
            
            return {
                'id': image_id,
                'error': str(e),
                'success': False
            }
    
    def _add_watermark(self, img, size_name):
        draw = ImageDraw.Draw(img)
        
        width, height = img.size
        font_size = max(12, min(width, height) // 20)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        text = f"{self.watermark_text} [{size_name}]"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = width - text_width - 10
        y = height - text_height - 10
        
        padding = 5
        draw.rectangle(
            [x - padding, y - padding, x + text_width + padding, y + text_height + padding],
            fill=(0, 0, 0, 128)
        )
        
        draw.text((x, y), text, fill=(255, 255, 255, 200), font=font)
        
        return img
    
    def reset_stats(self):
        with self.lock:
            self.stats = {
                'processed': 0,
                'errors': 0,
                'total_time': 0
            }

def generate_sample_images(count):
    print(f"Generando {count} imágenes de muestra...")
    images = []
    
    for i in range(count):
        img = Image.new('RGB', (800, 600))
        draw = ImageDraw.Draw(img)
        
        r = (i * 37) % 256
        g = (i * 73) % 256
        b = (i * 109) % 256
        draw.rectangle([0, 0, 800, 600], fill=(r, g, b))
        
        for j in range(50):
            x1 = (i * j * 17) % 700
            y1 = (i * j * 23) % 500
            x2 = x1 + 100
            y2 = y1 + 100
            color = ((r + j * 25) % 256, (g + j * 35) % 256, (b + j * 45) % 256)
            draw.ellipse([x1, y1, x2, y2], fill=color)
        
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=90)
        image_data = buffer.getvalue()
        
        images.append((image_data, f"product_{i:03d}"))
    
    print(f"{count} imágenes generadas ({sum(len(img[0]) for img in images) / 1024 / 1024:.2f} MB)\n")
    return images

def process_sequential(images, processor):
    print("Procesando imágenes secuencialmente")
    print("=" * 60)
    
    processor.reset_stats()
    start_time = time.time()
    
    results = []
    for image_data, image_id in images:
        result = processor.process_single_image(image_data, image_id)
        results.append(result)
        
        if len(results) % 20 == 0:
            print(f"  Procesadas: {len(results)}/{len(images)}")
    
    total_time = time.time() - start_time
    
    print(f"\nResultados Secuenciales:")
    print(f"  Tiempo total: {total_time:.2f}s")
    print(f"  Procesadas: {processor.stats['processed']}")
    print(f"  Errores: {processor.stats['errors']}")
    print(f"  Promedio por imagen: {total_time / len(images):.3f}s")
    print()
    
    return results, total_time

def process_parallel(images, processor, num_workers=8):
    print(f"Procesando imágenes en paralelo ({num_workers} threads)")
    print("=" * 60)
    
    processor.reset_stats()
    start_time = time.time()
    results = []
    completed = 0
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [
            executor.submit(processor.process_single_image, image_data, image_id)
            for image_data, image_id in images
        ]
        
        for future in futures:
            result = future.result()
            results.append(result)
            completed += 1
            
            if completed % 20 == 0:
                print(f"  Procesadas: {completed}/{len(images)}")
    
    total_time = time.time() - start_time
    
    print(f"\nResultados Paralelos:")
    print(f"  Tiempo total: {total_time:.2f}s")
    print(f"  Procesadas: {processor.stats['processed']}")
    print(f"  Errores: {processor.stats['errors']}")
    print(f"  Promedio por imagen: {total_time / len(images):.3f}s")
    print()
    
    return results, total_time

def save_sample_results(results, output_dir="output_samples"):  
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print(f"Guardando muestras en {output_dir}/")
    
    saved = 0
    for result in results:
        if result['success'] and saved < 3:
            image_id = result['id']
            for size_name, image_data in result['images'].items():
                filename = output_path / f"{image_id}_{size_name}.jpg"
                with open(filename, 'wb') as f:
                    f.write(image_data)
            saved += 1
    
    print(f"Guardadas {saved} imágenes de muestra (3 tamaños cada una)\n")

def main():
    print("\n" + "=" * 60)
    print("  Procesamiento de imágenes: Secuencial vs Paralelo")
    print("=" * 60 + "\n")
    
    images = generate_sample_images(NUM_IMAGES)
    processor = ImageProcessor()
    seq_results, seq_time = process_sequential(images, processor)
    par_results, par_time = process_parallel(images, processor, NUM_WORKERS)
    
    print("=" * 60)
    print("Comparación Final")
    print("=" * 60)
    print(f"Secuencial:  {seq_time:.2f}s")
    print(f"Paralelo:    {par_time:.2f}s ({NUM_WORKERS} threads)")
    print(f"Speedup:     {seq_time / par_time:.2f}x")
    print(f"Eficiencia:  {(seq_time / par_time) / NUM_WORKERS * 100:.1f}%")
    print("=" * 60 + "\n")
    save_sample_results(par_results)
    print("¡Procesamiento completado!\n")

if __name__ == "__main__":
    main()