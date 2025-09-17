# Ejecución de raíces enteras (.exe)

Este proyecto permite encontrar las raíces enteras de diferentes polinomios usando un ejecutable (`raices-go.exe`).

---

## Cómo ejecutar

La forma general es:

```bash
.\raices-go.exe -poly=NOMBRE_POLINOMIO -workers=CANTIDAD
```
- poly → indica el polinomio a evaluar.
- workers → cantidad de workers concurrentes a usar.

### Polinomios

1. **P1**: Grado 3
   - Polinomio: $x^3 - 6000x^2 + 11,000,000x - 6,000,000,000$
   - Comando:  
     ```bash
     .\raices-go.exe -poly=p1 -workers=2
     ```

2. **P2**: Grado 4
   - Polinomio: $x^4 - 5x^3 + 7x^2 - 3x - 6$
   - Comando:  
     ```bash
     .\raices-go.exe -poly=p2 -workers=2
     ```

3. **P3**: Grado 2
   - Polinomio:  $x^2 + 1$

   - Comando:  
     ```bash
     .\raices-go.exe -poly=p3 -workers=2
     ```

4. **P4**: Grado 4
   - Polinomio: $x^2 - 15,000,000x + 50,000,000,000,000$
   - Comando:  
     ```bash
     .\raices-go.exe -poly=p4 -workers=2
     ```
