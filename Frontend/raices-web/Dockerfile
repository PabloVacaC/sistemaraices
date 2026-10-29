# --- Etapa 1: Compilación de Angular ---
FROM node:22-alpine AS build

WORKDIR /app

# Copiar archivos de dependencias
COPY package.json package-lock.json ./
RUN npm ci

# Copiar el código fuente y compilar para producción
COPY . .
RUN npm run build -- --configuration=production

# --- Etapa 2: Servidor Web Nginx Ligero ---
FROM nginx:alpine

# Copiar configuración personalizada de Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar los archivos compilados de Angular desde la Etapa 1
COPY --from=build /app/dist/raices-web/browser /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

