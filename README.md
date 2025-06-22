# SVAIA_MON
Proyecto para Ingeniería del Software Seguro 

# Para comenzar
Clona el repositorio
```
  git clone https://github.com/CjEduu/SVAIA_MON.git
```

# Dependencias
Para utilizar uv nativo:
```
  uv sync 
```

Con pip:
```
  uv pip install -r requirements.txt
```

Por último, para permitir la gestión correcta de los imports
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

Importante, si por error ejecutamos 2 veces seguidas "start", deberemos parar los procesos a mano, ya que el archivo con los PID se borra automáticamente,
para ello podemos usar 'killall flask/fastapi' o el método que consideremos más conveniente.

# Agente
En la carpeta svaia/agents se encuentra el código fuente del agente básico que introduciríamos en nuestros pcs a
monitorizar.
Para simplificar la cosa, he incluido un binario que debería funcionar en máquinas x86_64 y evitar la compilación.
Si aun así quisieramos compilar el agente, simplemente en la carpeta agents/

```
  cargo build --release 
```

Para ello necesitaremos, evidentemente, cargo. Además, es necesario cambiar los path a monitorizar en el archivo Settings.toml


# Test
Para ejecutar los test, desde la raíz del proyecto
```
pytest
  
```
