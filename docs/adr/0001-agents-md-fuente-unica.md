# ADR 0001: AGENTS.md como fuente única de instrucciones para agentes

Estado: aceptada

## Contexto
Se usará Antigravity ahora y Claude Code después. Cada herramienta tiene su archivo y carpetas propias.

## Decisión
- `AGENTS.md` contiene todas las instrucciones; `CLAUDE.md` solo lo importa con `@AGENTS.md`.
- Skills y workflows viven en `.agents/`; `.claude/skills` y `.claude/commands` son enlaces simbólicos (`scripts/setup-links.sh`).
- Specs y ADR en `docs/` son neutrales respecto a la herramienta.

## Consecuencias
Migrar a Claude Code no requiere reescribir nada. Mantener `AGENTS.md` bajo 12.000 caracteres
(límite de Antigravity por archivo de reglas).
