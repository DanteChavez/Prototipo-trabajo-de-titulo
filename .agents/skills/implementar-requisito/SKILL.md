---
name: implementar-requisito
description: Usar cuando se pida implementar un requisito (RF/RNF) o un hito del prototipo a partir de una spec aprobada en docs/specs/. Guía el ciclo plan, pruebas, código, verificación.
---

# Implementar un requisito a partir de una spec

1. Lee `AGENTS.md`, `docs/PROTOTYPE_SCOPE.md` y la spec indicada. Si no hay spec aprobada, detente y propón crearla.
2. Escribe un plan corto (archivos a tocar, orden, riesgos) y espera la aprobación del humano.
3. Escribe primero las pruebas de los criterios de aceptación y confirma que fallan.
4. Implementa el cambio mínimo que las hace pasar. No agregues funciones fuera de la spec.
5. Ejecuta pruebas y linter. Reporta la salida real, no una suposición.
6. Actualiza la spec (estado y checklist) y la sección "Comandos" de `AGENTS.md` si aparecieron comandos nuevos.
7. Entrega un resumen: qué cambió, cómo se probó, qué queda dudoso y qué debe revisar el humano con más atención.
