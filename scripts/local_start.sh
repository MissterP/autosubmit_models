#!/bin/bash

if [ -f .env ]; then
    source .env
else
    echo "Error: .env file not found"
    exit 1
fi


if ! mount | grep -q "$ESARCHIVE_PATH"; then
    echo "Mounting remote filesystem at $ESARCHIVE_PATH"

    if [ ! -d "$ESARCHIVE_PATH" ]; then
        echo "Creating mount point at $ESARCHIVE_PATH"
        mkdir -p "$ESARCHIVE_PATH"
    fi

    if [ -z "$SSH_PASSWORD" ]; then

        sshfs ${SSH_USER}@${SSH_HOST}:${REMOTE_PATH} "$ESARCHIVE_PATH" -o ro
    else

        echo "$SSH_PASSWORD" | sshfs ${SSH_USER}@${SSH_HOST}:${REMOTE_PATH} "$ESARCHIVE_PATH" -o ro,password_stdin
    fi
    echo "Remote filesystem successfully mounted"
else
    echo "ESARCHIVE is already mounted at $ESARCHIVE_PATH"
fi


echo "Starting TimescaleDB in Docker..."
cd docker
docker compose -f compose.local.yaml up -d
cd ..


echo "Checking if TimescaleDB is running..."
for i in {1..60}; do
    if docker exec autosubmit_models_timescaledb pg_isready -U postgres -d metrics &>/dev/null; then
        echo "TimescaleDB is ready!"
        # Espera adicional para asegurar que TimescaleDB esté completamente inicializada
        echo "Waiting an additional 5 seconds for TimescaleDB to be fully operational..."
        sleep 5
        break
    fi
    echo "Waiting for TimescaleDB to be ready... ($i/60)"
    sleep 1
    if [ $i -eq 60 ]; then
        echo "TimescaleDB did not start within the expected time."
        exit 1
    fi
done

# Función para manejar la terminación limpia
cleanup() {
    echo "Stopping the application..."
    
    # Enviamos SIGTERM al proceso python para una terminación limpia
    if [ ! -z "$PID" ] && ps -p $PID > /dev/null; then
        echo "Sending SIGTERM to Python process (PID: $PID)"
        kill -TERM $PID
        
        # Esperamos hasta 15 segundos para que termine limpiamente
        for i in {1..15}; do
            if ! ps -p $PID > /dev/null; then
                echo "Application shut down successfully."
                break
            fi
            echo "Waiting for application to shut down... ($i/15)"
            sleep 1
        done
        
        # Si aún está en ejecución, lo forzamos a terminar
        if ps -p $PID > /dev/null; then
            echo "Application didn't shut down gracefully, forcing termination..."
            kill -9 $PID
        fi
    else
        echo "Python process is not running or already terminated"
    fi
    
    # Asegurarnos de detener también los contenedores Docker si es necesario
    echo "Stopping Docker containers..."
    cd docker && docker compose -f compose.local.yaml down
    cd ..

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
    
    echo "Cleanup completed."
    exit 0
}

# Configurar manejadores de señales
trap cleanup SIGINT SIGTERM

echo "Running the API locally..."
echo "The API will be available at http://${API_HOST}:${API_PORT}"

# Run the Python process in foreground so signals are properly propagated
exec python -m src.main &
PID=$!
echo "Started Python process with PID: $PID"

# Wait for the process to finish or for a signal to be received
wait $PID || true
echo "Python process has terminated with status $?"

# After the Python process terminates, call the cleanup function to ensure proper shutdown
cleanup