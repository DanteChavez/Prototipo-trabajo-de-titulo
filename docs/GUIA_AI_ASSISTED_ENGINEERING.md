# Guía práctica: AI-Assisted Engineering para este proyecto

## Idea central
La IA escribe; tú dueño de las decisiones y de la verificación. Tu trabajo pasa de "escribir código"
a: especificar bien, acotar, revisar y probar. Lo que no puedes verificar, no lo aceptes.

## El ciclo (repítelo por cada hito)
1. **Especificar** (`/spec`): la IA redacta la spec desde el PDF y tú la corriges. Es el paso más importante:
   una spec ambigua produce código ambiguo.
2. **Planificar**: antes de tocar archivos, la IA propone un plan. Lo lees y lo apruebas o corriges.
3. **Pruebas primero**: los criterios de aceptación se vuelven pruebas automáticas.
4. **Implementar** (`/implementar`): la IA codifica el cambio mínimo.
5. **Verificar**: se ejecutan pruebas y linter. Tú también ejecutas y pruebas a mano el flujo.
6. **Revisar** (`/revisar`): idealmente en una sesión/agente nueva, sin el contexto del autor.
7. **Commit** pequeño y descriptivo. Un requisito por commit.

## Cómo revisar código que no escribiste
- Empieza por la spec y las pruebas, luego el código: ¿las pruebas realmente comprueban el criterio?
- Pregunta a la IA "explícame este diff como si fuera mi examen". Si no lo entiendes, no lo aceptes.
- Desconfía de: pruebas que siempre pasan, código que no se ejecutó, dependencias nuevas, cambios fuera de la spec,
  manejo de errores que "traga" excepciones, secretos en el código.
- Ejecuta tú mismo el flujo del demo después de cada hito.

## Reglas de oro
- Cambios pequeños y frecuentes (git desde el día 1; commit antes de cada tarea grande).
- La IA no inventa comandos ni APIs: si dudas, pide que cite la documentación o que lo pruebe.
- Contexto corto y bueno: `AGENTS.md` breve, specs claras. No pegues el PDF completo en cada tarea.
- Los errores de la IA se corrigen mejorando `AGENTS.md` o la spec, no solo repitiendo el prompt.
- Una tarea por sesión; si la conversación se alarga y se confunde, abre una nueva con la spec.
- Registra en `docs/adr/` las decisiones y en tu informe cómo usaste la IA (te sirve para la defensa).

## Orden sugerido de trabajo
1. `git init`, primer commit con esta estructura.
2. Pedir `/spec` del hito H0 y revisarla.
3. `/implementar` H0 → `/revisar` → commit. Repetir con H1...H6.
4. Al final: ensayo del demo y prueba de carga ligera.

## Pasar de Antigravity a Claude Code
No hay que reescribir nada: ejecuta `scripts/setup-links.sh` y abre la carpeta con `claude`.
`CLAUDE.md` importa `AGENTS.md`; skills y workflows se reutilizan por enlaces simbólicos.
En Windows, los enlaces pueden requerir modo desarrollador o WSL; alternativa: copiar las carpetas.
