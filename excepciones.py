"""
excepciones.py
==============
Módulo de Excepciones Personalizadas - Sistema Software FJ
Autor: Sarith Mulford
Fecha: 2026-05-13
Python: 3.12

Define al menos 3 excepciones personalizadas que cubren los casos de error
más relevantes del dominio del negocio.  Todas heredan de Exception para
poder capturarse de forma granular sin suprimir otros errores inesperados.
"""


# ---------------------------------------------------------------------------
# Excepción 1: Datos inválidos suministrados por el usuario o el sistema
# ---------------------------------------------------------------------------
class InvalidDataError(Exception):
    """
    Se lanza cuando un dato requerido no cumple las reglas de validación.

    Ejemplos de uso:
        - Nombre de cliente vacío o con caracteres inválidos.
        - Correo electrónico sin formato válido.
        - Número de identificación negativo o nulo.
        - Fechas fuera de rango lógico.

    Atributos:
        campo   (str): Nombre del campo que falló la validación.
        valor   (any): Valor problemático que se intentó asignar.
        mensaje (str): Descripción amigable del problema.
    """

    def __init__(self, campo: str, valor, mensaje: str = ""):
        # Construye un mensaje detallado para facilitar el debugging
        self.campo = campo
        self.valor = valor
        self.mensaje = mensaje or f"El campo '{campo}' recibió un valor inválido: {valor!r}"
        # Llama al constructor padre con el mensaje completo
        super().__init__(self.mensaje)

    def __str__(self) -> str:
        """Representación legible de la excepción."""
        return f"[InvalidDataError] Campo='{self.campo}' | Valor={self.valor!r} | {self.mensaje}"


# ---------------------------------------------------------------------------
# Excepción 2: Servicio no disponible (capacidad, estado, horario, etc.)
# ---------------------------------------------------------------------------
class ServiceUnavailableError(Exception):
    """
    Se lanza cuando se intenta usar un servicio que no está disponible.

    Ejemplos de uso:
        - Sala ya reservada en el horario solicitado.
        - Equipo fuera de servicio o en mantenimiento.
        - Asesoría sin cupos disponibles.
        - Servicio cancelado o suspendido.

    Atributos:
        servicio (str): Nombre o identificador del servicio afectado.
        motivo   (str): Razón por la que el servicio no está disponible.
    """

    def __init__(self, servicio: str, motivo: str = ""):
        # Guarda el nombre del servicio para uso externo
        self.servicio = servicio
        self.motivo = motivo or f"El servicio '{servicio}' no está disponible en este momento."
        super().__init__(self.motivo)

    def __str__(self) -> str:
        """Representación legible de la excepción."""
        return f"[ServiceUnavailableError] Servicio='{self.servicio}' | Motivo: {self.motivo}"


# ---------------------------------------------------------------------------
# Excepción 3: Cálculo de costo inconsistente o matemáticamente inválido
# ---------------------------------------------------------------------------
class InconsistentCalculationError(Exception):
    """
    Se lanza cuando el motor de cálculo de costos detecta una inconsistencia.

    Ejemplos de uso:
        - Descuento mayor que el precio base (costo negativo).
        - Tasa de impuesto fuera del rango 0.0 – 1.0.
        - Duración cero o negativa en un servicio por horas.
        - División por cero en fórmulas de prorrateo.

    Atributos:
        operacion (str): Nombre de la operación de cálculo que falló.
        detalle   (str): Descripción técnica del problema.
    """

    def __init__(self, operacion: str, detalle: str = ""):
        self.operacion = operacion
        self.detalle = detalle or f"Error de cálculo en la operación '{operacion}'."
        super().__init__(self.detalle)

    def __str__(self) -> str:
        """Representación legible de la excepción."""
        return f"[InconsistentCalculationError] Operación='{self.operacion}' | {self.detalle}"


# ---------------------------------------------------------------------------
# Excepción 4 (bonus): Estado de reserva inválido para la operación pedida
# ---------------------------------------------------------------------------
class InvalidReservationStateError(Exception):
    """
    Se lanza cuando se intenta realizar una operación sobre una reserva cuyo
    estado actual no lo permite.

    Ejemplos de uso:
        - Confirmar una reserva ya cancelada.
        - Cancelar una reserva que nunca fue confirmada.
        - Completar una reserva que aún está pendiente de confirmación.

    Atributos:
        estado_actual  (str): Estado actual de la reserva.
        operacion      (str): Operación que se intentó ejecutar.
    """

    def __init__(self, estado_actual: str, operacion: str):
        self.estado_actual = estado_actual
        self.operacion = operacion
        mensaje = (
            f"No se puede ejecutar '{operacion}' "
            f"sobre una reserva en estado '{estado_actual}'."
        )
        super().__init__(mensaje)

    def __str__(self) -> str:
        """Representación legible de la excepción."""
        return (
            f"[InvalidReservationStateError] "
            f"Estado='{self.estado_actual}' | Operación='{self.operacion}'"
        )
