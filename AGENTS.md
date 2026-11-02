# Prototipo: Software de apoyo a la práctica de programación en laboratorios docentes

Este archivo es la FUENTE ÚNICA de instrucciones para cualquier agente de IA
(Antigravity, Claude Code u otro). `CLAUDE.md` solo lo importa. No dupliques contenido.

## Contexto
Prototipo de un trabajo de título (Ingeniería Civil Informática, Universidad de Valparaíso).
El documento de análisis completo está en `docs/Trabajo_Titulo.pdf` (RF-01..RF-13, RNF-01..RNF-08, CU-01..CU-07).
Idioma del proyecto: español (documentación, commits y comentarios); identificadores de código en inglés.

## Qué es y qué NO es (alcance del prototipo)
Es una demostración funcional mínima de la idea central: estudiantes programan en JupyterHub
con contenedores efímeros, el profesor ve su código casi en tiempo real y existe un portafolio
de entregas con plazo límite. El detalle está en `docs/PROTOTYPE_SCOPE.md`.
NO implementar nada fuera de ese alcance aunque el PDF lo describa. Si algo parece faltar, pregunta.

## Stack (decisiones vigentes, ver docs/adr/)
- Kubernetes de un solo nodo con k3d (desarrollo) e instalación de JupyterHub con Helm (Zero to JupyterHub).
- Volúmenes persistentes (PVC) por estudiante: `personal/` y `shipping/`.
- Servicio académico pequeño (Python + FastAPI + SQLite) para secciones, ejercicios y entregas.
- Autenticación del prototipo: autenticador simple. Microsoft SSO queda como trabajo futuro (RF-01 parcial).
- Versiones fijadas en ADR 0003, no cambiar sin confirmar

## Comandos
Se completan a medida que existan. Si un comando no está aquí, no lo inventes: búscalo o pregunta.
- Instalar dependencias: (pendiente)
- Ejecutar pruebas: (pendiente)
- Levantar entorno local: (pendiente)

## Forma de trabajo (obligatoria)
1. Spec primero: toda funcionalidad parte de un archivo en `docs/specs/` (usa `_template.md`).
   Sin spec aprobada por el humano, no se escribe código.
2. Cambios pequeños: un requisito (RF) por rama/commit. Máximo ~300 líneas por cambio.
3. Pruebas junto con el código: cada criterio de aceptación de la spec debe tener una prueba.
4. Antes de dar algo por terminado: ejecutar pruebas y linter y reportar el resultado real.
   Nunca afirmes que algo funciona si no lo ejecutaste.
5. Terminar cada tarea con un resumen: qué cambió, qué probaste, qué dudas quedan.
6. Decisiones de arquitectura nuevas se registran como ADR en `docs/adr/`.

## Reglas de código
- Python 3.12, tipado con type hints, formateo con ruff.
- Funciones cortas, sin dependencias nuevas sin justificarlas en la spec o ADR.
- Seguridad (RNF-08): contenedores sin root, `allowPrivilegeEscalation: false`; nunca ejecutar código
  de estudiantes fuera de un contenedor aislado.
- Nunca subir secretos, credenciales ni datos reales de estudiantes. Usar datos ficticios.

## Límites: pedir confirmación humana antes de
- Borrar archivos o carpetas, reescribir historia de git, o cambiar `docs/` de análisis.
- Instalar software a nivel de sistema o modificar la configuración del clúster.
- Agregar una dependencia o cambiar el stack.

## Estructura
- `docs/` documentación, specs y ADR · `src/` código · `scripts/` utilidades
- `.agents/` skills y workflows compartidos (Antigravity). `.claude/` son enlaces simbólicos hacia ahí.
