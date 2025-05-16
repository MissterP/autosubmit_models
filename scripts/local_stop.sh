#!/bin/bash
# Script para detener el entorno de desarrollo local

# Cargar variables de entorno
if [ -f .env ]; then
    source .env
else
    echo "Error: archivo .env no encontrado"
    exit 1
fi

# Detener el contenedor de TimescaleDB
echo "Deteniendo TimescaleDB..."
cd docker
docker compose -f compose.local.yaml down
cd ..

# Limpiar recursos de Docker (imágenes, volúmenes y builds)
echo "Limpiando recursos de Docker..."

# Preguntar al usuario si desea realizar una limpieza completa
read -p "¿Deseas eliminar todos los volúmenes no utilizados? (s/N): " clean_volumes
read -p "¿Deseas eliminar todas las imágenes no utilizadas? (s/N): " clean_images
read -p "¿Deseas eliminar todos los builds de Docker? (s/N): " clean_builds

# Ejecutar limpieza según las respuestas del usuario
if [[ "$clean_volumes" =~ ^[Ss]$ ]]; then
    echo "Eliminando volúmenes no utilizados..."
    docker volume prune -f
fi

if [[ "$clean_images" =~ ^[Ss]$ ]]; then
    echo "Eliminando imágenes no utilizadas..."
    docker image prune -a -f
fi

if [[ "$clean_builds" =~ ^[Ss]$ ]]; then
    echo "Eliminando builds de Docker..."
    docker builder prune -a -f
fi

echo "Entorno de desarrollo local detenido y limpieza completada"