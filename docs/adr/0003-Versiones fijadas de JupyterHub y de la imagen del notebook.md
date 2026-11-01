# ADR 0002: k3d como clúster Kubernetes de desarrollo

Estado: aceptada

# Contexto

El prototipo requiere un clúster Kubernetes de un solo nodo donde correr JupyterHub con KubeSpawner (RNF-05), y que a la vez se pueda ejecutar en dos equipos con Windows 10: el de desarrollo (32 GB de RAM) y el de la demostración (16 GB). El proyecto se ejecuta dentro de WSL2 con Docker Engine (sin Docker Desktop) para reducir el consumo de memoria y tener el mismo entorno en ambos equipos

# Opciones consideradas
Opción	Ventajas	Desventajas
k3d (k3s dentro de Docker)	Liviano, crear y borrar el clúster toma segundos, usa k3s (el mismo que se usaría en un servidor real), permite agregar nodos con un comando	Menos conocido que kind
kind	Muy usado y bien documentado	Algo más pesado, sin ventajas decisivas para este caso
Kubernetes de Docker Desktop	Se activa con una casilla	Difícil de reiniciar y de simular varios nodos, depende de Docker Desktop
minikube	Buena documentación	Más pesado, sin ventaja para este caso

# Decisión

Se usa k3d para el desarrollo y la demostración. JupyterHub se instala con Helm mediante el chart oficial Zero to JupyterHub. Todo se ejecuta dentro de WSL2 con Docker Engine.