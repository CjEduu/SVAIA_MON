# SVAIA_MON
Proyecto para Ingeniería del Software Seguro 



# Para comenzar
Clona el repositorio
```
  git clone https://github.com/CjEduu/SVAIA_MON.git
```


# Dependencias
En el caso de uso de consumidor, la mayoría las maneja uv, excepto mariadb114.

Si estamos utilizando nix/nixos será suficiente con:
```
  nix develop && uv sync
```

En caso contrario, primero debemos instalar mariadb114, hacer un sync y luego añadir mariadb:
```
  Tras instalar mariadb114:
  uv sync && uv add mariadb
```
Probablemente tambien haga falta
```
  uv pip install -e .
```

# Ejecutar
Tras ello podremos entrar al entorno virtual sin problemas y ejecutar todo con:
```
  source ./venv/bin/activate
  chmod +x deploy.sh && ./deploy.sh start
```

Para parar la ejecución de los procesos:
```
  ./deploy.sh stop
```


Siento mucho que no haya conseguido una forma más ergonómica, al haber partes en flask y FastAPI no lo he conseguido.

# Agente
En la carpeta svaia/agents se encuentra el código fuente del agente básico que introduciríamos en nuestros pcs a
monitorizar.
Para simplificar la cosa, he incluido un binario que debería funcionar en máquinas x64_86 y evitar la compilación.
Si aun así quisieramos compilar el agente, simplemente en la carpeta agents/

```
  cargo build --release 
```
