# Alcance del prototipo

Objetivo: demostrar de extremo a extremo los dos problemas del trabajo
(1. ver el código del estudiante en sala, 2. registrar la práctica por sesión) con el mínimo de piezas.

## Incluido (en este orden de implementación)
| Hito | Requisitos | Qué se demuestra |
|---|---|---|
| H0 | RF-06, RNF-01, RNF-05 | JupyterHub + KubeSpawner en k3s/kind de un nodo: login → pod efímero → destrucción por inactividad. |
| H1 | RF-07, RNF-02 | Volumen persistente por estudiante con `personal/` y `shipping/`; los archivos sobreviven al pod. |
| H2 | RF-05, RF-10 (versión mínima) | Secciones, profesores y estudiantes cargados desde un CSV/seed (sin pantallas CRUD completas). |
| H3 | RF-12, RF-08 | El profesor publica un ejercicio con plazo; el estudiante lo ve y lo copia a `personal/`. |
| H4 | RF-09, RNF-03 | Entrega a `shipping/` con validación de plazo; tras el cierre queda solo lectura. |
| H5 | RF-11, RNF-07 | El profesor lee en solo lectura el `personal/` de un estudiante de su sección (autoguardado ≤ 60 s). |
| H6 | RF-13 | Vista del profesor con matriz de entregas y apertura de una copia ejecutable de prueba. |

## Simplificado a propósito
- RF-01/RF-02: autenticador simple con 3 roles de prueba. Microsoft SSO = trabajo futuro.
- RF-03/RF-04: carga por seed/CSV, sin interfaz CRUD.
- RNF-04: prueba de carga ligera (script con N pods), no 40–80 estudiantes reales.
- Interfaz: la mínima necesaria (puede ser una extensión/servicio simple de JupyterHub o páginas básicas).

## Fuera del alcance
Escalamiento real a varios nodos, alta disponibilidad, notificaciones, estadísticas avanzadas,
evaluación automática, edición colaborativa en vivo.

## Criterio de "prototipo listo"
Un demo de ~10 minutos donde: un estudiante entra, programa, entrega; el profesor ve el código
en vivo, publica un ejercicio con plazo y revisa el portafolio; y se muestra que un pod se destruye
sin perder archivos.
