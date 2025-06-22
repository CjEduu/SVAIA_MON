<<<<<<< HEAD
import os
import unittest

from secure_log_manager.src.SecureLogManager import (
    SecureLogManager,
    monitor_funciones,
)


class TestSecureLogManager(unittest.TestCase):
    def setUp(self):
        # Presuponemos que se ejecuta desde el root del proyecto
        self.log_file = "./svaia/secure_log_manager/test/logs/log_test_secure_manager.log"
        if not os.path.exists(self.log_file):
             open(self.log_file,'w').close()
        self.secure_logger = SecureLogManager(debug_mode=0)
        self.secure_logger.configure_logging(log_file=self.log_file)
        monitor = monitor_funciones(self.secure_logger)

        class MockGestor:
            @monitor(log_level="error")
            def __init__(self, clave_maestra: str):
                """Inicializa el gestor con una clave maestra."""
                self.clave_maestra = clave_maestra

            @monitor(log_level="info")
            def anadir_credencial(self, clave_maestra: str, servicio: str, usuario: str, password: str) -> None:
                print("INTO AÑADIR CREDENCIAL")

            @monitor(log_level="critical")
            def obtener_password(self, clave_maestra: str, servicio: str, usuario: str) -> str:
                print("INTO OBTENER")
                return "TEST"

        self.gestor_mock = MockGestor("123")

    def test_verificar_cadena_real(self):
        self.secure_logger.inicializar_log()
        self.gestor_mock.anadir_credencial("CLAVE MAESTRA","SERVICIO","USER","PASSWORDSECRETA")
        self.gestor_mock.obtener_password("CLAVE MAESTRA","SERVICIO","USER")
        self.assertTrue(self.secure_logger.verificar_cadena_hashes(self.log_file))

    def test_log_tampering_detection(self):
        self.secure_logger.inicializar_log()
        self.gestor_mock.anadir_credencial("CLAVE MAESTRA","SERVICIO","USER","PASSWORDSECRETA")
        # Tamper with log
        with open(self.log_file, "a") as f:
            f.write("TAMPERED LINE\n")
        self.assertFalse(self.secure_logger.verificar_cadena_hashes(self.log_file))

    def test_invalid_log_level(self):
        # Should raise an exception or handle gracefully if log level is invalid
        with self.assertRaises(Exception):
            @monitor_funciones(self.secure_logger)
            def dummy_func():
                pass
            dummy_func(log_level="notalevel")


=======
import os
import unittest

from secure_log_manager.src.SecureLogManager import (
    SecureLogManager,
    monitor_funciones,
)


class TestSecureLogManager(unittest.TestCase):
    def setUp(self):
        # Presuponemos que se ejecuta desde el root del proyecto
        self.log_file = "./svaia/secure_log_manager/test/logs/log_test_secure_manager.log"
        if not os.path.exists(self.log_file):
             open(self.log_file,'w').close()
        self.secure_logger = SecureLogManager(debug_mode=0)
        self.secure_logger.configure_logging(log_file=self.log_file)
        monitor = monitor_funciones(self.secure_logger)

        class MockGestor:
            @monitor(log_level="error")
            def __init__(self, clave_maestra: str):
                """Inicializa el gestor con una clave maestra."""
                self.clave_maestra = clave_maestra

            @monitor(log_level="info")
            def anadir_credencial(self, clave_maestra: str, servicio: str, usuario: str, password: str) -> None:
                print("INTO AÑADIR CREDENCIAL")

            @monitor(log_level="critical")
            def obtener_password(self, clave_maestra: str, servicio: str, usuario: str) -> str:
                print("INTO OBTENER")
                return "TEST"

        self.gestor_mock = MockGestor("123")

    def test_verificar_cadena_real(self):
        self.secure_logger.inicializar_log()
        self.gestor_mock.anadir_credencial("CLAVE MAESTRA","SERVICIO","USER","PASSWORDSECRETA")
        self.gestor_mock.obtener_password("CLAVE MAESTRA","SERVICIO","USER")
        self.assertTrue(self.secure_logger.verificar_cadena_hashes(self.log_file))

>>>>>>> ddb9f5b88c0198c24a781439214a720dd9b7b5c2
