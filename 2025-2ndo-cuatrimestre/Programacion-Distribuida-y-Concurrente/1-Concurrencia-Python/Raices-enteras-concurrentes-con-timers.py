# Teoría de la computación – Actividad Práctica
# Consigna: raíces enteras de un polinomio mónico (RE, Turing-aceptable)
# Versión CONCURRENTE en Python (misma lógica, búsqueda de ±n; posible no-terminación)

from threading import Thread, Event, Lock
import time  # opcional si querés medir

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

def obtener_raices_enteras_concurrente(
    polinomio,
    cantidad_raices,
    workers=4,
    mostrar_traza=True
):
    """
    Misma idea que la versión secuencial:
    - Se prueban ±n para n=1,2,3,... hasta reunir 'cantidad_raices'.
    - Concurrencia: 'workers' hilos se reparten los n en saltos (stride) = workers.
    - Turing-aceptable: puede no terminar si no hay suficientes raíces enteras.
    - Traza mínima (si mostrar_traza=True):
        * Cada hilo muestra sus primeros 3 n que probará (para visualizar el stride).
        * Muestra cuando encuentra una raíz (+n o -n).
        * Al completar la cantidad de raíces, anuncia detención.
    """
    raices_enteras = []
    done = Event()
    lock = Lock()

    def worker(idx):
        n = idx + 1
        # Mostrar una sola vez el "patrón" de este hilo (primeros 3 n)
        if mostrar_traza:
            primeros = [n + k*workers for k in range(3)]
            print(f"[Hilo {idx}] inicio concurrente → probará n={primeros[0]}, {primeros[1]}, {primeros[2]}, ...")

        while not done.is_set():
            # Chequear +n
            if reemplazar_x(polinomio, n) == 0:
                with lock:
                    if len(raices_enteras) < cantidad_raices:
                        raices_enteras.append(n)
                        if mostrar_traza:
                            print(f"[Hilo {idx}] raíz encontrada en +{n}")
                        if len(raices_enteras) >= cantidad_raices:
                            done.set()
                            if mostrar_traza:
                                print(f"[Hilo {idx}] meta alcanzada, deteniendo hilos…")
                            break
            # Chequear -n
            if reemplazar_x(polinomio, -n) == 0:
                with lock:
                    if len(raices_enteras) < cantidad_raices:
                        raices_enteras.append(-n)
                        if mostrar_traza:
                            print(f"[Hilo {idx}] raíz encontrada en -{n}")
                        if len(raices_enteras) >= cantidad_raices:
                            done.set()
                            if mostrar_traza:
                                print(f"[Hilo {idx}] meta alcanzada, deteniendo hilos…")
                            break
            n += workers  # avanzar por stride

    hilos = [Thread(target=worker, args=(i,), daemon=True) for i in range(workers)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()  # si no se encuentran suficientes raíces, esto puede no terminar (RE)

    return raices_enteras


# ------------------------------
# Ejemplo de uso sencillo
if __name__ == "__main__":
    # Polinomio con raíces 1000, 2000, 3000 (rápido)
    polinomio = [1, -6000, 11_000_000, -6_000_000_000_000_000_000_000_000]
    raices_max = obtener_cantidad_maxima_raices(polinomio)

    # Probá con diferentes cantidades de hilos:
    for w in [1, 2, 4]:
        print(f"\n=== Ejecutando con {w} hilos (concurrente) ===")
        t0 = time.perf_counter()
        raices = obtener_raices_enteras_concurrente(polinomio, raices_max, workers=w, mostrar_traza=True)
        t1 = time.perf_counter()
        print(f"[Resultado] Hilos={w} → Raíces: {raices} | Tiempo={t1 - t0:.6f}s")
