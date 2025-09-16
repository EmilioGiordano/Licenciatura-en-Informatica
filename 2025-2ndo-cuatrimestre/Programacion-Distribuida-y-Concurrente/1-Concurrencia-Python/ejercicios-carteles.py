import threading
import time

# Tiempo de inicio del programa
start_time = time.time()

def mostrar_cartel(color, tiempo):
    while True:
        time.sleep(tiempo)
        elapsed_time = time.time() - start_time
        print(f"{color} {int(elapsed_time):02d}")

def main():
    # Crear y ejecutar los hilos concurrentes
    hilo_rojo = threading.Thread(target=mostrar_cartel, args=("ROJO", 3))
    hilo_azul = threading.Thread(target=mostrar_cartel, args=("AZUL", 5))
    
    # Configurar los hilos como daemon para que terminen cuando el programa principal termine
    hilo_rojo.daemon = True
    hilo_azul.daemon = True
    
    print("Iniciando programa...")
    print("Tiempos de despliegue:")
    
    # Iniciar los hilos
    hilo_rojo.start()
    hilo_azul.start()
    
    try:
        # Mantener el programa principal ejecutándose
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nPrograma terminado")

if __name__ == "__main__":
    main()