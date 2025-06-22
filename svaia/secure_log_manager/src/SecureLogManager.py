<<<<<<< HEAD
import inspect
import logging
from functools import wraps
from getpass import getuser
from hashlib import sha256
from os import PathLike
from typing import Optional

from .log_util import (
    archivo_vacio,
    existe_archivo,
    get_tiempo_legible,
    read_last_line,
)


class ErrorReadingLog(Exception):
    pass

class ErrorInvalidLogLevel(Exception):
    pass

class SecureLogManager:
    """
    Clase que maneja el registro seguro de logs con funcionalidades de hash para verificar la integridad.

    Attributes:
        debug_mode (int): Modo de depuración para el nivel de logging
        log_file: Archivo donde se guardarán los logs
        logger: Objeto logger de la biblioteca logging
        handler: Manejador de archivos para el logger
        formatter: Formateador para los mensajes de log
    """

    def __init__(self,debug_mode:int):
        """
        Inicializa el gestor de logs seguros.

        Args:
            debug_mode (int): Modo de depuración para establecer el nivel de logging
        """
        self.debug_mode = debug_mode
        self.log_file = None
        self.logger = None
        self.handler = None
        self.formatter = None

    def inicializar_log(self):

        """
        Inicializa el archivo de log. Si el archivo no existe, lo crea.
        Si existe y no está vacío, lo limpia.

        Raises:
            Exception: Si no se ha proporcionado un archivo de log
        """
        if not self.log_file:
            print("Please provide a log file")
            raise Exception("Please provide a log file")

        if not existe_archivo(self.log_file):
            print("\n",archivo_vacio(self.log_file))
            open(self.log_file, "w").close()

        if not archivo_vacio(self.log_file):
            open(self.log_file, "w").close()

        # Start the log with the initialization message
        current_time = get_tiempo_legible()
        log_msg = f"Inicialización del log en el tiempo {current_time}"
        self.anadir_al_log(logging.INFO,log_msg)

    def configure_logging(self,log_file:PathLike|str):
        """
        Configura el sistema de logging.

        Args:
            log_file (PathLike|str): Ruta al archivo donde se guardarán
        
        """
        #Get logger
        self.log_file = log_file
        self.logger = logging.getLogger("secure_log_manager")
        self.logger.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)

        #Set up a handler to log to log_file
        self.handler = logging.FileHandler(log_file,encoding="utf-8")
        self.handler.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)

        #Setup a format
        self.formatter = logging.Formatter("%(asctime)s %(levelname)s |%(message)s|","%Y-%m-%d %H:%M:%S")

        #Assemble!
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)

    @staticmethod
    def hash_msg(msg:str)->str:
        """
            Necesario para abstraer el proceso de hash, por si queremos cambiar funciones, y también facilitar la comprobación
        """
        hashed = sha256(msg.encode()).hexdigest()
        return hashed

    def anadir_al_log(self,nivel_log:int,log_string:str):
        """
        Añade una entrada al log con un hash calculado basado en el mensaje anterior.

        Args:
            nivel_log (int): Nivel de logging (DEBUG=10, INFO=20, WARNING=30, ERROR=40, CRITICAL=50)
            log_string (str): Mensaje que se quiere registrar en el log

        Note:
            El hash se calcula concatenando el hash del mensaje anterior con el nuevo mensaje.
            Si es el primer mensaje, se usa una cadena vacía como hash anterior.
        """
        
        if not self.logger:
            print("Please configure logger before proceeding.")
            return

        if nivel_log not in (0,10,20,30,40,50):
            print("Please set a valid nivel log.")
            return

        last_hash = self.leer_ultimo_hash(self.log_file)
        if last_hash is None:
            last_hash = ""

        # The string to hash is hash [last_hash + new log_string]
        to_hash = last_hash + log_string
        new_hash = self.hash_msg(to_hash)

        log_string = "'" + new_hash + "'" +  ": "  + log_string
        self.logger.log(nivel_log,log_string)

    @staticmethod
    def leer_ultimo_hash(log_file: PathLike | str) -> Optional[str]:
        """
            Lee la última línea del archivo de log y extrae el dato después de la fecha y el tipo de log.

            Parámetros:
                log_file (str): Ruta del archivo de log.

            Retorna:
                str: El dato extraído (hash) , o None si el archivo no existe o está vacío.
        """

        if not existe_archivo(log_file) or archivo_vacio(log_file):
            return None

        last_line = read_last_line(log_file)

        #   We can do it with regex
        #   result = re.findall("'(\w+)':",last_line)
        #   Better with indices imo, it allows different hash sizes and it should not be problematic

        slash_idx = last_line.find('|')
        if slash_idx == -1:
            raise ErrorReadingLog

        end_idx = last_line.find(':',slash_idx)
        if end_idx == -1:
            raise ErrorReadingLog

        return last_line[slash_idx+2:end_idx-1]

    @staticmethod
    def verificar_cadena_hashes(log_file: PathLike | str) -> bool:
        """
        Verifica que la cadena de hashes en el archivo de log sea correcta.

        Parámetros:
            log_file (str): Ruta del archivo de log.

        Retorna:
            bool: True si la cadena de hashes es correcta, False si hay algún error.
        """
        if not existe_archivo(log_file):
            print("Input a valid log_file")
            return False

        #Lets get the whole log
        lines:list[str] =  list()
        with open(log_file,"r",encoding="utf-8") as f:
            lines.extend(f.readlines())


        last_hash = ""
        for line in lines:
            # Find the start/end of the hash in the string
            first_slash_idx = line.find('|')
            hash_end_idx = line.find(':',first_slash_idx)

            # The logstring is everything after the ': ' and before the last '|'
            log_string = line[hash_end_idx+2:-2]

            # Hash it
            to_hash = last_hash + log_string

            # Retrieve the correct hash of the msg and also calculate it
            correct_hash = line[first_slash_idx+2:hash_end_idx-1]
            curr_hash = SecureLogManager.hash_msg(to_hash)

            # Et voilá
            print("\nLOGSTRING:",log_string)
            print("\nCORRECT:",correct_hash,"\nCALCULATED:",curr_hash)
            if correct_hash != curr_hash:
                return False

            last_hash = correct_hash
            
        return True

def monitor_funciones(log_manager:SecureLogManager):
    """
        Devuelve un wrapper con parametros dado un LogManager.
    """
    def decorador_con_parametros(log_level:str, sensitive_args_names: Optional[set[str]] = None):
        """
        Decorador que registra la ejecución de funciones con diferentes niveles de log y manejo de argumentos sensibles.
    
        Args:
            log_level (str): Nivel de log a utilizar ("debug", "info", "warning", "error", "critical")
            sensitive_args_names (Optional[set[str]]): Conjunto de nombres de argumentos considerados sensibles
                que serán enmascarados en el log. Por defecto incluye "password", "credential", "api_key",
                "clave" y "clave_maestra"
    
        Raises:
            ErrorInvalidLogLevel: Si el nivel de log especificado no es válido
    
        Returns:
            function: Decorador configurado con el nivel de log y argumentos sensibles especificados
        """
        logger = log_manager
        if sensitive_args_names is None:
            sensitive_args_names = {"password", "credential", "api_key", "clave", "clave_maestra"}
        match log_level:
            case "debug":
                log_level_int = logging.DEBUG
            case "info":
                log_level_int = logging.INFO
            case "warning":
                log_level_int = logging.WARNING
            case "error":
                log_level_int = logging.ERROR
            case "critical":
                log_level_int = logging.CRITICAL
            case _:
                raise ErrorInvalidLogLevel
        def decorador(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Inspect function signature to check parameters
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                safe_args = dict()
                for param_name, arg_value in bound_args.arguments.items():
                    if param_name.lower() in sensitive_args_names:
                        safe_args[param_name] = '****'
                    elif param_name == 'self':
                        continue
                    else:
                        safe_args[param_name] = arg_value


                # Check current user
                curr_user = getuser()

                log_msg = f"{curr_user} | Calling function '{func.__name__}'. Args: {safe_args}"
                # Execute function
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    log_msg += f"Function '{func.__name__}' failed with error: {e}"
                    logger.anadir_al_log(logging.ERROR,log_msg)
                    raise

                log_msg += f" -> Resultado: {result}"
                logger.anadir_al_log(log_level_int,log_msg)
                return result
            return wrapper
        return decorador

    return decorador_con_parametros


=======
import inspect
import logging
from functools import wraps
from getpass import getuser
from hashlib import sha256
from os import PathLike
from typing import Optional

from .log_util import (
    archivo_vacio,
    existe_archivo,
    get_tiempo_legible,
    read_last_line,
)


class ErrorReadingLog(Exception):
    pass

class ErrorInvalidLogLevel(Exception):
    pass

class SecureLogManager:
    """
    Clase que maneja el registro seguro de logs con funcionalidades de hash para verificar la integridad.

    Attributes:
        debug_mode (int): Modo de depuración para el nivel de logging
        log_file: Archivo donde se guardarán los logs
        logger: Objeto logger de la biblioteca logging
        handler: Manejador de archivos para el logger
        formatter: Formateador para los mensajes de log
    """

    def __init__(self,debug_mode:int):
        """
        Inicializa el gestor de logs seguros.

        Args:
            debug_mode (int): Modo de depuración para establecer el nivel de logging
        """
        self.debug_mode = debug_mode
        self.log_file = None
        self.logger = None
        self.handler = None
        self.formatter = None

    def inicializar_log(self):

        """
        Inicializa el archivo de log. Si el archivo no existe, lo crea.
        Si existe y no está vacío, lo limpia.

        Raises:
            Exception: Si no se ha proporcionado un archivo de log
        """
        if not self.log_file:
            print("Please provide a log file")
            raise Exception("Please provide a log file")

        if not existe_archivo(self.log_file):
            print("\n",archivo_vacio(self.log_file))
            open(self.log_file, "w").close()

        if not archivo_vacio(self.log_file):
            open(self.log_file, "w").close()

        # Start the log with the initialization message
        current_time = get_tiempo_legible()
        log_msg = f"Inicialización del log en el tiempo {current_time}"
        self.anadir_al_log(logging.INFO,log_msg)

    def configure_logging(self,log_file:PathLike|str):
        """
        Configura el sistema de logging.

        Args:
            log_file (PathLike|str): Ruta al archivo donde se guardarán
        
        """
        #Get logger
        self.log_file = log_file
        self.logger = logging.getLogger("secure_log_manager")
        self.logger.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)

        #Set up a handler to log to log_file
        self.handler = logging.FileHandler(log_file,encoding="utf-8")
        self.handler.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)

        #Setup a format
        self.formatter = logging.Formatter("%(asctime)s %(levelname)s |%(message)s|","%Y-%m-%d %H:%M:%S")

        #Assemble!
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)

    @staticmethod
    def hash_msg(msg:str)->str:
        """
            Necesario para abstraer el proceso de hash, por si queremos cambiar funciones, y también facilitar la comprobación
        """
        hashed = sha256(msg.encode()).hexdigest()
        return hashed

    def anadir_al_log(self,nivel_log:int,log_string:str):
        """
        Añade una entrada al log con un hash calculado basado en el mensaje anterior.

        Args:
            nivel_log (int): Nivel de logging (DEBUG=10, INFO=20, WARNING=30, ERROR=40, CRITICAL=50)
            log_string (str): Mensaje que se quiere registrar en el log

        Note:
            El hash se calcula concatenando el hash del mensaje anterior con el nuevo mensaje.
            Si es el primer mensaje, se usa una cadena vacía como hash anterior.
        """
        
        if not self.logger:
            print("Please configure logger before proceeding.")
            return

        if nivel_log not in (0,10,20,30,40,50):
            print("Please set a valid nivel log.")
            return

        last_hash = self.leer_ultimo_hash(self.log_file)
        if last_hash is None:
            last_hash = ""

        # The string to hash is hash [last_hash + new log_string]
        to_hash = last_hash + log_string
        new_hash = self.hash_msg(to_hash)

        log_string = "'" + new_hash + "'" +  ": "  + log_string
        self.logger.log(nivel_log,log_string)

    @staticmethod
    def leer_ultimo_hash(log_file: PathLike | str) -> Optional[str]:
        """
            Lee la última línea del archivo de log y extrae el dato después de la fecha y el tipo de log.

            Parámetros:
                log_file (str): Ruta del archivo de log.

            Retorna:
                str: El dato extraído (hash) , o None si el archivo no existe o está vacío.
        """

        if not existe_archivo(log_file) or archivo_vacio(log_file):
            return None

        last_line = read_last_line(log_file)

        #   We can do it with regex
        #   result = re.findall("'(\w+)':",last_line)
        #   Better with indices imo, it allows different hash sizes and it should not be problematic

        slash_idx = last_line.find('|')
        if slash_idx == -1:
            raise ErrorReadingLog

        end_idx = last_line.find(':',slash_idx)
        if end_idx == -1:
            raise ErrorReadingLog

        return last_line[slash_idx+2:end_idx-1]

    @staticmethod
    def verificar_cadena_hashes(log_file: PathLike | str) -> bool:
        """
        Verifica que la cadena de hashes en el archivo de log sea correcta.

        Parámetros:
            log_file (str): Ruta del archivo de log.

        Retorna:
            bool: True si la cadena de hashes es correcta, False si hay algún error.
        """
        if not existe_archivo(log_file):
            print("Input a valid log_file")
            return False

        #Lets get the whole log
        lines:list[str] =  list()
        with open(log_file,"r",encoding="utf-8") as f:
            lines.extend(f.readlines())


        last_hash = ""
        for line in lines:
            # Find the start/end of the hash in the string
            first_slash_idx = line.find('|')
            hash_end_idx = line.find(':',first_slash_idx)

            # The logstring is everything after the ': ' and before the last '|'
            log_string = line[hash_end_idx+2:-2]

            # Hash it
            to_hash = last_hash + log_string

            # Retrieve the correct hash of the msg and also calculate it
            correct_hash = line[first_slash_idx+2:hash_end_idx-1]
            curr_hash = SecureLogManager.hash_msg(to_hash)

            # Et voilá
            print("\nLOGSTRING:",log_string)
            print("\nCORRECT:",correct_hash,"\nCALCULATED:",curr_hash)
            if correct_hash != curr_hash:
                return False

            last_hash = correct_hash
            
        return True

def monitor_funciones(log_manager:SecureLogManager):
    """
        Devuelve un wrapper con parametros dado un LogManager.
    """
    def decorador_con_parametros(log_level:str, sensitive_args_names: Optional[set[str]] = None):
        """
        Decorador que registra la ejecución de funciones con diferentes niveles de log y manejo de argumentos sensibles.
    
        Args:
            log_level (str): Nivel de log a utilizar ("debug", "info", "warning", "error", "critical")
            sensitive_args_names (Optional[set[str]]): Conjunto de nombres de argumentos considerados sensibles
                que serán enmascarados en el log. Por defecto incluye "password", "credential", "api_key",
                "clave" y "clave_maestra"
    
        Raises:
            ErrorInvalidLogLevel: Si el nivel de log especificado no es válido
    
        Returns:
            function: Decorador configurado con el nivel de log y argumentos sensibles especificados
        """
        logger = log_manager
        if sensitive_args_names is None:
            sensitive_args_names = {"password", "credential", "api_key", "clave", "clave_maestra"}
        match log_level:
            case "debug":
                log_level_int = logging.DEBUG
            case "info":
                log_level_int = logging.INFO
            case "warning":
                log_level_int = logging.WARNING
            case "error":
                log_level_int = logging.ERROR
            case "critical":
                log_level_int = logging.CRITICAL
            case _:
                raise ErrorInvalidLogLevel
        def decorador(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Inspect function signature to check parameters
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                safe_args = dict()
                for param_name, arg_value in bound_args.arguments.items():
                    if param_name.lower() in sensitive_args_names:
                        safe_args[param_name] = '****'
                    elif param_name == 'self':
                        continue
                    else:
                        safe_args[param_name] = arg_value


                # Check current user
                curr_user = getuser()

                log_msg = f"{curr_user} | Calling function '{func.__name__}'. Args: {safe_args}"
                # Execute function
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    log_msg += f"Function '{func.__name__}' failed with error: {e}"
                    logger.anadir_al_log(logging.ERROR,log_msg)
                    raise

                log_msg += f" -> Resultado: {result}"
                logger.anadir_al_log(log_level_int,log_msg)
                return result
            return wrapper
        return decorador

    return decorador_con_parametros


>>>>>>> ddb9f5b88c0198c24a781439214a720dd9b7b5c2
