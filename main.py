"""
main.py
=======
Punto de Entrada Principal - Sistema Software FJ
Autor: Sarith Mulford
Fecha: 2026-05-13
Python: 3.12

Este módulo es el punto de entrada del sistema.
Ejecuta la simulación automática de 10 operaciones y genera el log.

Estructura del proyecto:
    excepciones.py  → Excepciones personalizadas (InvalidDataError, etc.)
    logger.py       → Sistema de logging centralizado con decorador
    entidades.py    → Clase abstracta EntidadBase + Clase Cliente
    servicios.py    → Jerarquía: Servicio → ReservaSala/AlquilerEquipo/Asesoria
    reserva.py      → Clase Reserva con ciclo de vida y manejo de excepciones
    gestor.py       → GestorSistema: repositorio en memoria + operaciones CRUD
    simulacion.py   → 10 operaciones automáticas de demostración
    main.py         → Este archivo: punto de entrada

Ejecución:
    python -X utf8 main.py   (Windows: activa modo UTF-8, PEP 540)

Salida:
    - Resultados en consola
    - software_fj.log con todos los eventos y errores registrados
"""

import sys                            # Para verificar versión de Python
import io                             # Para reconfigurar stdout con UTF-8
from logger import logger, log_evento  # Logger centralizado
from simulacion import ejecutar_simulacion  # Función de simulación

# ---------------------------------------------------------------------------
# Fuerza la salida estándar a UTF-8 en Windows (evita UnicodeEncodeError)
# ---------------------------------------------------------------------------
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding='utf-8',
        errors='replace',  # Reemplaza chars no codificables en lugar de fallar
    )


def verificar_version_python() -> None:
    """
    Verifica que la versión de Python sea 3.12 o superior.

    Raises:
        SystemExit: Si la versión de Python es anterior a 3.12.
    """
    version = sys.version_info
    if version < (3, 12):
        print(
            f"❌ Error: Se requiere Python 3.12 o superior.\n"
            f"   Versión actual: {version.major}.{version.minor}.{version.micro}\n"
            f"   Por favor, actualice su instalación de Python."
        )
        sys.exit(1)


def main() -> None:
    """
    Función principal del sistema Software FJ.

    Flujo de ejecución:
        1. Verifica la versión de Python.
        2. Registra el inicio del sistema en el log.
        3. Ejecuta la simulación de 10 operaciones.
        4. Captura cualquier error crítico no manejado y lo registra.
        5. Registra el cierre del sistema en el log.
    """
    # ------------------------------------------------------------------
    # Paso 1: Verifica versión de Python (PEP 3.12+)
    # ------------------------------------------------------------------
    verificar_version_python()

    # ------------------------------------------------------------------
    # Paso 2: Registra el inicio del sistema
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  [*] SISTEMA DE GESTION SOFTWARE FJ")
    print("  (c) 2026 Software FJ - UNAD Programacion Orientada a Objetos")
    print("=" * 60)
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Modulos cargados: excepciones, logger, entidades,")
    print(f"                    servicios, reserva, gestor, simulacion")
    print("=" * 60)

    log_evento("info", "Sistema Software FJ iniciado. Python %s", sys.version.split()[0])

    # ------------------------------------------------------------------
    # Paso 3: Ejecuta la simulación completa
    # ------------------------------------------------------------------
    try:
        ejecutar_simulacion()

    except KeyboardInterrupt:
        # El usuario presiono Ctrl+C para interrumpir la ejecucion
        print("\n\n[!] Simulacion interrumpida por el usuario (Ctrl+C).")
        log_evento("warning", "Simulacion interrumpida por el usuario (KeyboardInterrupt).")

    except Exception as exc_critica:
        # Error critico no esperado: se registra pero el programa no se cuelga
        print(f"\n[X] Error critico inesperado: {type(exc_critica).__name__}: {exc_critica}")
        log_evento(
            "critical",
            "Error critico no manejado: %s: %s",
            type(exc_critica).__name__,
            exc_critica,
            exc_info=True,
        )

    finally:
        # ------------------------------------------------------------------
        # Paso 4: Cierra el sistema de forma limpia (siempre se ejecuta)
        # ------------------------------------------------------------------
        log_evento("info", "Sistema Software FJ cerrado correctamente.")
        print("\n  [LOG] Revisa 'software_fj.log' para el historial completo.")
        print("  Hasta pronto.\n")


# ===========================================================================
# Punto de entrada estándar de Python
# ===========================================================================
if __name__ == "__main__":
    # Solo ejecuta main() cuando el script se corre directamente,
    # no cuando se importa como módulo en otro archivo.
    main()
