---
description: Revisión crítica del último cambio contra su spec y las reglas del proyecto
---

Actúa como revisor independiente, no como autor. Sin modificar archivos:

1. Compara el cambio (git diff) con su spec: ¿cada criterio de aceptación está cubierto por una prueba real?
2. Busca: código fuera de alcance, secretos, dependencias nuevas sin justificar, violaciones de RNF-08 (root, privilegios, red).
3. Ejecuta las pruebas y reporta el resultado real.
4. Entrega una lista priorizada de hallazgos (crítico / importante / menor) con archivo y línea.
