package main

import (
	"context"
	"flag"
	"fmt"
	"math/big"
	"strconv"
	"strings"
	"sync"
	"time"
)

// ===================== Utilidades de polinomio =====================

func obtenerCantidadMaximaRaices(polinomio []*big.Int) int {
	return len(polinomio) - 1 // grado
}

// evalúa P(x) == 0 ?
func evalEsCero(coeffs []*big.Int, x int64) bool {
	deg := len(coeffs) - 1
	sum := big.NewInt(0)
	xbig := big.NewInt(x)

	for i, c := range coeffs {
		exp := deg - i
		if exp == 0 {
			sum.Add(sum, c)
		} else {
			pow := new(big.Int).Exp(xbig, big.NewInt(int64(exp)), nil) // x^exp
			term := new(big.Int).Mul(c, pow)                           // c * x^exp
			sum.Add(sum, term)
		}
	}
	return sum.Cmp(big.NewInt(0)) == 0
}

func toBigSlice(ints []int64) []*big.Int {
	out := make([]*big.Int, len(ints))
	for i, v := range ints {
		out[i] = big.NewInt(v)
	}
	return out
}

func parseCoeffs(csv string) ([]*big.Int, error) {
	fields := strings.Split(csv, ",")
	ints := make([]int64, 0, len(fields))
	for _, f := range fields {
		f = strings.TrimSpace(f)
		if f == "" {
			continue
		}
		v, err := strconv.ParseInt(f, 10, 64)
		if err != nil {
			return nil, fmt.Errorf("coeficiente inválido %q: %w", f, err)
		}
		ints = append(ints, v)
	}
	if len(ints) < 2 {
		return nil, fmt.Errorf("se requieren al menos 2 coeficientes")
	}
	return toBigSlice(ints), nil
}

// ===================== Búsqueda RE concurrente (±n con stride) =====================

func obtenerRaicesEnterasConcurrente(
	ctx context.Context,
	polinomio []*big.Int,
	cantidadRaices int,
	workers int,
	trace bool,
) []int64 {

	raices := make([]int64, 0, cantidadRaices)
	var mu sync.Mutex

	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	var wg sync.WaitGroup
	wg.Add(workers)

	for idx := 0; idx < workers; idx++ {
		go func(id int) {
			defer wg.Done()
			n := int64(id + 1) // arranque: 1..workers

			if trace {
				fmt.Printf("[W%d] inicio → n=%d, %d, %d, ... (stride=%d)\n",
					id, n, n+int64(workers), n+2*int64(workers), workers)
			}

			for {
				select {
				case <-ctx.Done():
					return
				default:
					// +n
					if evalEsCero(polinomio, n) {
						mu.Lock()
						if len(raices) < cantidadRaices {
							raices = append(raices, n)
							if trace {
								fmt.Printf("[W%d] raíz +%d\n", id, n)
							}
							if len(raices) >= cantidadRaices {
								cancel()
								mu.Unlock()
								return
							}
						}
						mu.Unlock()
					}
					// -n
					if evalEsCero(polinomio, -n) {
						mu.Lock()
						if len(raices) < cantidadRaices {
							raices = append(raices, -n)
							if trace {
								fmt.Printf("[W%d] raíz -%d\n", id, n)
							}
							if len(raices) >= cantidadRaices {
								cancel()
								mu.Unlock()
								return
							}
						}
						mu.Unlock()
					}
					n += int64(workers) // siguiente del stride
				}
			}
		}(idx)
	}

	wg.Wait() // si no hay suficientes raíces enteras, NO termina (RE)
	return raices
}

// ===================== Main =====================

func main() {
	// Flags
	polyName := flag.String("poly", "p1", "Polinomio predefinido: p1|p2|p3|p4")
	coeffsCSV := flag.String("coeffs", "", "Coeficientes custom CSV (grado decreciente), p.ej: 1,-6,11,-6")
	workers := flag.Int("workers", 4, "Cantidad de workers concurrentes")
	trace := flag.Bool("trace", false, "Mostrar traza mínima por worker")
	flag.Parse()

	// Polinomios monicos predefinidos (coeficientes en grado decreciente).
	// NO se definen a partir de raíces, están dados DIRECTAMENTE por coeficientes:
	// p1: x^3 - 6000x^2 + 11_000_000x - 6_000_000_000  (grado 3)
	p1 := toBigSlice([]int64{1, -6000, 11_000_000, -6_000_000_000})

	// p2: x^4 - 5x^3 + 7x^2 - 3x - 6  (grado 4)  // puede tener <4 raíces enteras → RE no termina
	p2 := toBigSlice([]int64{1, -5, 7, -3, -6})

	// p3: x^2 + 1  (grado 2)  // 0 raíces enteras → RE no termina
	p3 := toBigSlice([]int64{1, 0, 1})

	// p4: x^2 - 15_000_000 x + 50_000_000_000_000  (grado 2)  // raíces enteras grandes → tarda más
	p4 := toBigSlice([]int64{1, -15_000_000, 50_000_000_000_000})

	// Elegir polinomio
	var poly []*big.Int
	if *coeffsCSV != "" {
		var err error
		poly, err = parseCoeffs(*coeffsCSV)
		if err != nil {
			fmt.Println("Error al parsear -coeffs:", err)
			return
		}
	} else {
		switch *polyName {
		case "p1":
			poly = p1
		case "p2":
			poly = p2
		case "p3":
			poly = p3
		case "p4":
			poly = p4
		default:
			fmt.Println("Polinomio no reconocido. Usa -poly=p1|p2|p3|p4 o bien -coeffs=...")
			return
		}
	}

	maxRaices := obtenerCantidadMaximaRaices(poly)
	fmt.Printf("Polinomio=%s | grado=%d (máx raíces a buscar) | workers=%d\n", *polyName, maxRaices, *workers)

	t0 := time.Now()
	raices := obtenerRaicesEnterasConcurrente(context.Background(), poly, maxRaices, *workers, *trace)
	elap := time.Since(t0)

	fmt.Printf("Raíces encontradas: %v | Tiempo: %s\n", raices, elap)
	// Nota: si el polinomio tiene < grado raíces enteras, este programa NO termina (RE).
}
