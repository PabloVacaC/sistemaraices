/**
 * Utilidad de compresión y optimización de imágenes en el cliente (Browser).
 * 
 * Reduce drásticamente el peso de fotografías capturadas con cámaras de smartphones
 * o archivos de alta resolución (de 3-10 MB a ~40-90 KB), evitando la saturación
 * de la red, memoria y base de datos.
 */

export interface ImageCompressionOptions {
  maxWidth?: number;
  maxHeight?: number;
  quality?: number; // 0.1 a 1.0
  mimeType?: 'image/webp' | 'image/jpeg';
}

const DEFAULT_OPTIONS: Required<ImageCompressionOptions> = {
  maxWidth: 1024,
  maxHeight: 1024,
  quality: 0.8,
  mimeType: 'image/webp',
};

export async function compressImageFile(
  file: File,
  options: ImageCompressionOptions = {}
): Promise<string> {
  const opts = { ...DEFAULT_OPTIONS, ...options };

  return new Promise((resolve, reject) => {
    // Si no es imagen, rechazar
    if (!file.type.startsWith('image/')) {
      return reject(new Error('El archivo no es una imagen válida.'));
    }

    const img = new Image();
    const objectUrl = URL.createObjectURL(file);

    img.onload = () => {
      URL.revokeObjectURL(objectUrl);

      let { width, height } = img;
      const { maxWidth, maxHeight, quality, mimeType } = opts;

      // Calcular nuevas dimensiones manteniendo la relación de aspecto
      if (width > maxWidth || height > maxHeight) {
        if (width / height > maxWidth / maxHeight) {
          height = Math.round((height * maxWidth) / width);
          width = maxWidth;
        } else {
          width = Math.round((width * maxHeight) / height);
          height = maxHeight;
        }
      }

      // Crear canvas y dibujar imagen escalada con filtro de alta calidad
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        return reject(new Error('No se pudo obtener el contexto 2D del canvas.'));
      }

      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(img, 0, 0, width, height);

      // Intentar exportar en WebP, con fallback automático a JPEG si el navegador no lo soporta
      let compressedDataUrl = canvas.toDataURL(mimeType, quality);
      if (!compressedDataUrl.startsWith(`data:${mimeType}`)) {
        compressedDataUrl = canvas.toDataURL('image/jpeg', quality);
      }

      const originalKB = (file.size / 1024).toFixed(1);
      const compressedKB = (compressedDataUrl.length * (3 / 4) / 1024).toFixed(1);
      console.info(
        `[Compresión de Imagen] Original: ${originalKB} KB -> Comprimido: ${compressedKB} KB (${width}x${height}px)`
      );

      resolve(compressedDataUrl);
    };

    img.onerror = (err) => {
      URL.revokeObjectURL(objectUrl);
      reject(err);
    };

    img.src = objectUrl;
  });
}

