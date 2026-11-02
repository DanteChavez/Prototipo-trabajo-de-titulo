# ADR 0003: Versiones fijadas de JupyterHub y de la imagen del notebook

Estado: aceptada

# Contexto

El prototipo se ejecuta en dos equipos (desarrollo y demostración) y debe comportarse igual en ambos. Usar versiones sin fijar (“la última”) podría producir diferencias entre equipos o entre fechas. Además, el PC de demostración tiene 16 GB de RAM, por lo que se busca una imagen simple y límites de memoria por pod acotados.

# Decisión
Componente	Valor
Chart de Helm	Zero to JupyterHub (jupyterhub/jupyterhub), versión 4.4.4 (JupyterHub 5.5.4)
Repositorio del chart	https://hub.jupyter.org/helm-chart/
Imagen del notebook (prototipo)	quay.io/jupyter/base-notebook:2024-08-26
Clúster	k3d, versión de k3s: v1.35.5-k3s1 (ver kubectl get nodes)

Fecha de la decisión: 2026-11-01.

Reglas:

* El chart se instala siempre con --version 4.4.4.
* La imagen se referencia por un tag concreto, nunca por latest.
* Cambiar cualquiera de estas versiones requiere actualizar este ADR y confirmación humana.

# Motivos

* Chart 4.4.4: es la versión estable más reciente al momento de la decisión (sin sufijos de prueba). Fijarla garantiza el mismo despliegue en ambos equipos.
* base-notebook: es la imagen más simple, con descarga y arranque más rápidos y menos disco. El prototipo solo necesita demostrar el ciclo de vida del pod y la edición de código, no librerías científicas. El consumo de RAM depende de los límites por pod y de lo que el estudiante ejecute, no del tamaño de la imagen.

# Alternativas consideradas
scipy-notebook: trae librerías científicas que el prototipo no necesita y ocupa varios GB de disco.
minimal-notebook: agrega git y herramientas de terminal; es una opción si luego se requieren.
Imagen propia (base-notebook + matplotlib): prevista para la versión real, ya que los estudiantes usarían como máximo matplotlib. Requiere cargarla al clúster con k3d image import o publicarla en un registro.
# Consecuencias
* Despliegues reproducibles entre el PC de desarrollo y el de demostración.
* Las actualizaciones de versión son decisiones explícitas y registradas.
* Pendiente: verificar compatibilidad del chart con la versión de Kubernetes del clúster (helm show chart jupyterhub/jupyterhub --version 4.4.4 | grep -i kubeVersion) y completar 2024-08-26 y v1.35.5-k3s1.