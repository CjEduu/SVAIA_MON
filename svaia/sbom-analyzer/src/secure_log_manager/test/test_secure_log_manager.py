import unittest

from secure_log_manager.SecureLogManager import (
    SecureLogManager,
    monitor_funciones,
)


class TestSecureLogManager(unittest.TestCase):
    def setUp(self):
        self.log_file = "./logs/log_test_secure_manager.log"
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