# Consigna: raíces enteras de un polinomio mónico (RE, Turing-aceptable, acepta exactamente las entradas que tienen al menos una raíz entera
# puede no terminar en el caso contrario).
# Versión CONCURRENTE en Python (misma lógica, búsqueda de ±n; posible no-terminación)

from threading import Thread, Event, Lock
import time  

def termino_independiente(polinomio):
    return polinomio[-1]

# El coeficiente mayor del polinomio determina esta cantidad
def obtener_cantidad_maxima_raices(polinomio):
    grado = len(polinomio) - 1
    return grado

def reemplazar_x(polinomio, entero):
    grado = len(polinomio) - 1
    resultado = 0
    for i, coeficiente in enumerate(polinomio):
        exponente = grado - i
        resultado += coeficiente * (entero ** exponente)
    return resultado

def obtener_raices_enteras_concurrente(polinomio, cantidad_raices, workers=4):
    """
    Misma idea que la versión secuencial:
    - Se prueban ±n para n=1,2,3,... hasta reunir 'cantidad_raices'.
    - Concurrencia: 'workers' hilos se reparten los n en saltos (stride) = workers.
      Ej.: con 3 hilos -> hilo0: n=1,4,7,... ; hilo1: n=2,5,8,... ; hilo2: n=3,6,9,...
    - Turing-aceptable: puede no terminar si no hay suficientes raíces enteras.
    """
    raices_enteras = []
    done = Event()
    lock = Lock()

    def worker(idx):
        # idx: 0..workers-1 -> n inicial = idx+1
        n = idx + 1
        while not done.is_set():
            # Chequear +n
            if reemplazar_x(polinomio, n) == 0:
                with lock:
                    if len(raices_enteras) < cantidad_raices:
                        raices_enteras.append(n)
                        if len(raices_enteras) >= cantidad_raices:
                            done.set()
                            break
            # Chequear -n
            if reemplazar_x(polinomio, -n) == 0:
                with lock:
                    if len(raices_enteras) < cantidad_raices:
                        raices_enteras.append(-n)
                        if len(raices_enteras) >= cantidad_raices:
                            done.set()
                            break
            n += workers  # avanzar por stride

    hilos = [Thread(target=worker, args=(i,), daemon=True) for i in range(workers)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()  # si no se encuentran suficientes raíces, esto puede no terminar (RE)

    return raices_enteras


# ------------------------------
# Bench de tiempo preciso (perf_counter)

polinomio = [1, -6000, 11_000_000, -6_000_000_000_000_000_000]
raices_max = obtener_cantidad_maxima_raices(polinomio)

for workers in [1]:
    t0 = time.perf_counter()
    raices = obtener_raices_enteras_concurrente(polinomio, raices_max, workers=workers)
    t1 = time.perf_counter()
    print(f"Hilos: {workers} -> Raíces: {raices} | Tiempo: {t1 - t0:.6f} s")
