"""
logger.py
=========
Módulo de Logging Centralizado - Sistema Software FJ
Autor: Sarith Mulford
Fecha: 2026-05-13
Python: 3.12

Provee:
  - Configuración de un logger estándar de Python que escribe en 'software_fj.log'.
  - Un decorador @log_operacion para registrar automáticamente cada llamada
    a funciones críticas (entrada, salida y cualquier excepción).
  - Garantía de que la aplicación NUNCA se detiene ante un error de logging.

Estrategia de rotación:
  Usa RotatingFileHandler (máx. 5 MB por archivo, 3 archivos de respaldo)
  para que el log no crezca indefinidamente.
"""

import logging                          # Módulo estándar de Python para logs
import functools                        # Para preservar metadatos del decorador
import traceback                        # Para capturar el stack completo en errores

from logging.handlers import RotatingFileHandler  # Rotación automática del .log
from pathlib import Path                # Manejo multiplataforma de rutas

# ---------------------------------------------------------------------------
# Configuración global del logger
# ---------------------------------------------------------------------------

# Nombre único del logger para todo el sistema Software FJ
LOGGER_NAME = "SoftwareFJ"

# Ruta del archivo .log en el mismo directorio que este módulo
LOG_FILE = Path(__file__).parent / "software_fj.log"

# Formato estándar de cada línea del log:
# [2026-05-13 10:00:00,000] [INFO] [NombreLogger] mensaje
LOG_FORMAT = "[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _construir_logger() -> logging.Logger:
    """
    Construye y configura el logger global del sistema.

    Returns:
        logging.Logger: Instancia configurada y lista para usar.

    Nota: Esta función se llama UNA sola vez al importar el módulo.
    Si el logger ya existe (por reimportación) devuelve el existente
    sin agregar handlers duplicados.
    """
    # Obtiene (o crea) el logger con el nombre del sistema
    logger = logging.getLogger(LOGGER_NAME)

    # Si ya tiene handlers configurados, no agrega más (evita duplicados)
    if logger.handlers:
        return logger

    # Nivel mínimo: captura desde DEBUG en adelante
    logger.setLevel(logging.DEBUG)

    # ------------------------------------------------------------------
    # Handler 1: Archivo rotatorio (persiste entre sesiones)
    # ------------------------------------------------------------------
    try:
        archivo_handler = RotatingFileHandler(
            filename=str(LOG_FILE),    # Ruta del .log
            maxBytes=5 * 1024 * 1024,  # Rota al superar 5 MB
            backupCount=3,             # Mantiene hasta 3 archivos de respaldo
            encoding="utf-8",          # Soporta caracteres especiales (español)
            delay=False,               # Crea el archivo inmediatamente
        )
        archivo_handler.setLevel(logging.DEBUG)  # Registra todo en el archivo
        archivo_handler.setFormatter(
            logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)
        )
        logger.addHandler(archivo_handler)
    except (OSError, PermissionError) as exc:
        # Si no se puede escribir en disco, solo imprime la advertencia
        # y continúa con el handler de consola.
        print(f"[ADVERTENCIA] No se pudo crear el handler de archivo: {exc}")

    # ------------------------------------------------------------------
    # Handler 2: Consola (útil durante el desarrollo)
    # ------------------------------------------------------------------
    consola_handler = logging.StreamHandler()
    consola_handler.setLevel(logging.INFO)  # Solo INFO+ en consola (menos ruido)
    consola_handler.setFormatter(
        logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)
    )
    logger.addHandler(consola_handler)

    return logger


# Logger singleton: importable directamente desde otros módulos
logger = _construir_logger()


# ---------------------------------------------------------------------------
# Decorador @log_operacion
# ---------------------------------------------------------------------------

def log_operacion(nombre_operacion: str = ""):
    """
    Decorador de fábrica que envuelve una función con logging automático.

    Registra:
        - INFO al inicio de la operación (con argumentos).
        - INFO al finalizar exitosamente (con valor de retorno resumido).
        - ERROR si la función lanza una excepción (con traceback completo).

    El decorador NUNCA suprime excepciones: las vuelve a lanzar después
    de registrarlas, para que el llamador pueda manejarlas.

    Args:
        nombre_operacion (str): Etiqueta descriptiva de la operación.
                                Si está vacía, se usa el nombre de la función.

    Uso:
        @log_operacion("Registrar cliente")
        def registrar_cliente(self, cliente): ...

        @log_operacion()
        def calcular_costo(self): ...
    """

    def decorador(func):
        # functools.wraps preserva __name__, __doc__, etc. de la función original
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Determina la etiqueta de la operación
            etiqueta = nombre_operacion or func.__qualname__

            # Prepara una representación corta de los argumentos (máx. 120 chars)
            args_repr = ", ".join(repr(a) for a in args[1:])  # omite 'self'
            kwargs_repr = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
            todos_args = ", ".join(filter(None, [args_repr, kwargs_repr]))
            if len(todos_args) > 120:
                todos_args = todos_args[:117] + "..."

            # Registro de inicio
            logger.info("▶ INICIO '%s'(%s)", etiqueta, todos_args)

            try:
                # Ejecuta la función original
                resultado = func(*args, **kwargs)

                # Registro de finalización exitosa
                resultado_repr = repr(resultado)
                if len(resultado_repr) > 80:
                    resultado_repr = resultado_repr[:77] + "..."
                logger.info("✔ FIN '%s' → %s", etiqueta, resultado_repr)

                return resultado

            except Exception as exc:
                # Captura el traceback completo para el log
                tb_str = traceback.format_exc()

                # Registra el error con nivel ERROR
                logger.error(
                    "✘ ERROR en '%s': %s(%s)\n%s",
                    etiqueta,
                    type(exc).__name__,
                    exc,
                    tb_str,
                )

                # Re-lanza la excepción para que el llamador la maneje
                raise

        return wrapper

    return decorador


# ---------------------------------------------------------------------------
# Función auxiliar: registrar evento de negocio sin decorador
# ---------------------------------------------------------------------------

def log_evento(nivel: str, mensaje: str, *args, exc_info: bool = False) -> None:
    """
    Registra un evento de negocio en el logger global de forma segura.

    Esta función NUNCA lanza excepciones: si el logging falla, imprime
    en consola y continúa.

    Args:
        nivel   (str): Nivel del log ('debug', 'info', 'warning', 'error', 'critical').
        mensaje (str): Mensaje a registrar. Puede incluir %s, %d, etc.
        *args        : Argumentos para el formateo del mensaje.
        exc_info (bool): Si True, adjunta el traceback actual al mensaje.
    """
    try:
        # Mapeo de string a método del logger
        metodo = getattr(logger, nivel.lower(), logger.info)
        metodo(mensaje, *args, exc_info=exc_info)
    except Exception as log_exc:  # noqa: BLE001
        # Falló el logging mismo; última línea de defensa: imprimir en consola
        print(f"[LOG FALLIDO] {nivel.upper()} | {mensaje} | Error interno: {log_exc}")
