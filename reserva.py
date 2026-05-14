"""
reserva.py
==========
Modulo de Reservas - Sistema Software FJ
Autor: Sarith Mulford
Fecha: 2026-05-13
Python: 3.12

La clase Reserva integra un Cliente y un Servicio.
Gestiona el ciclo de vida completo de una reserva:
    PENDIENTE -> CONFIRMADA -> COMPLETADA
    PENDIENTE -> CANCELADA
    CONFIRMADA -> CANCELADA

Maneja estados y procesos con logica de excepciones completa:
    try / except / else / finally
    raise ... from ... (encadenamiento de excepciones)
"""

from datetime import datetime              # Registro de timestamps
from entidades import Cliente              # Clase Cliente
from servicios import Servicio             # Clase abstracta Servicio

from excepciones import (
    ServiceUnavailableError,        # Servicio no disponible para reservar
    InvalidReservationStateError,   # Operacion invalida segun el estado actual
    InvalidDataError,               # Datos invalidos en la construccion
    InconsistentCalculationError,   # Error en calculo de costo final
)
from logger import logger, log_operacion  # Logger y decorador


# ===========================================================================
# Clase Reserva
# ===========================================================================

class Reserva:
    """
    Integra un Cliente y un Servicio en una reserva formal del sistema.

    Ciclo de vida (estados):
        'pendiente'  -> Estado inicial tras crear la reserva.
        'confirmada' -> La reserva ha sido aceptada y el servicio esta ocupado.
        'cancelada'  -> La reserva fue cancelada (por cliente o sistema).
        'completada' -> El servicio se presto satisfactoriamente.

    Transiciones permitidas:
        pendiente  -> confirmada  (mediante confirmar())
        pendiente  -> cancelada   (mediante cancelar())
        confirmada -> cancelada   (mediante cancelar())
        confirmada -> completada  (mediante completar())

    Atributos:
        id_reserva      (int):       ID unico autoincremental.
        cliente         (Cliente):   Cliente que realiza la reserva.
        servicio        (Servicio):  Servicio que se reserva.
        fecha_solicitud (datetime):  Momento de creacion de la reserva.
        fecha_inicio    (datetime):  Inicio programado del servicio.
        estado          (str):       Estado actual de la reserva.
        costo_total     (float):     Costo calculado al confirmar.
        notas           (str):       Observaciones opcionales.
    """

    # Contador de clase para IDs unicos
    _contador_reservas: int = 0

    # Transiciones de estado permitidas (grafo de estados)
    _TRANSICIONES: dict[str, list[str]] = {
        "pendiente":  ["confirmada", "cancelada"],
        "confirmada": ["cancelada", "completada"],
        "cancelada":  [],    # Estado terminal
        "completada": [],    # Estado terminal
    }

    def __init__(
        self,
        cliente: Cliente,
        servicio: Servicio,
        fecha_inicio: datetime,
        notas: str = "",
        **kwargs_costo,
    ) -> None:
        """
        Crea una nueva reserva en estado 'pendiente'.

        Args:
            cliente        (Cliente):  Cliente que hace la reserva.
            servicio       (Servicio): Servicio a reservar.
            fecha_inicio   (datetime): Fecha y hora de inicio del servicio.
            notas          (str):      Observaciones opcionales.
            **kwargs_costo:            Parametros extra para calcular_costo()
                                       (ej. impuesto=0.19, descuento=0.10).

        Raises:
            InvalidDataError:        Si cliente/servicio/fecha no son validos.
            ServiceUnavailableError: Si el servicio no esta disponible.
        """
        # ---------------------------------------------------------------
        # Bloque try/except/else/finally completo
        # ---------------------------------------------------------------
        try:
            # --- Valida que cliente sea una instancia valida de Cliente ---
            if not isinstance(cliente, Cliente):
                raise InvalidDataError(
                    campo="cliente",
                    valor=type(cliente).__name__,
                    mensaje="El parametro 'cliente' debe ser una instancia de Cliente.",
                )

            # --- Valida que servicio sea una instancia valida de Servicio ---
            if not isinstance(servicio, Servicio):
                raise InvalidDataError(
                    campo="servicio",
                    valor=type(servicio).__name__,
                    mensaje="El parametro 'servicio' debe ser una instancia de Servicio.",
                )

            # --- Valida que fecha_inicio sea datetime ---
            if not isinstance(fecha_inicio, datetime):
                raise InvalidDataError(
                    campo="fecha_inicio",
                    valor=type(fecha_inicio).__name__,
                    mensaje="La fecha de inicio debe ser un objeto datetime.",
                )

            # --- Verifica que la fecha de inicio sea futura ---
            if fecha_inicio <= datetime.now():
                raise InvalidDataError(
                    campo="fecha_inicio",
                    valor=str(fecha_inicio),
                    mensaje="La fecha de inicio debe ser futura (posterior a ahora).",
                )

            # --- Verifica disponibilidad del servicio ---
            if not servicio.disponible:
                # Usa encadenamiento de excepciones (raise ... from ...)
                motivo = (
                    f"El servicio '{servicio.nombre}' "
                    f"esta en estado '{servicio.estado}'."
                )
                raise ServiceUnavailableError(
                    servicio=servicio.nombre,
                    motivo=motivo,
                )

        except (InvalidDataError, ServiceUnavailableError):
            # Re-lanza las excepciones de dominio sin modificarlas
            raise

        except Exception as exc_inesperada:
            # Para errores inesperados, encadena con un error descriptivo
            raise InvalidDataError(
                campo="reserva",
                valor="construccion",
                mensaje=f"Error inesperado al crear la reserva: {exc_inesperada}",
            ) from exc_inesperada

        else:
            # El bloque 'else' se ejecuta solo si NO hubo excepciones.
            # Aqui es seguro asignar todos los atributos.
            Reserva._contador_reservas += 1
            self.__id_reserva: int = Reserva._contador_reservas
            self.__cliente: Cliente = cliente
            self.__servicio: Servicio = servicio
            self.__fecha_solicitud: datetime = datetime.now()
            self.__fecha_inicio: datetime = fecha_inicio
            self.__estado: str = "pendiente"
            self.__costo_total: float = 0.0   # Se calcula al confirmar
            self.__notas: str = notas.strip() if notas else ""
            self.__kwargs_costo: dict = kwargs_costo  # Para usar al confirmar
            self.__historial: list[dict] = []   # Historial de cambios de estado

            logger.info(
                "Reserva #%d creada | Cliente: '%s' | Servicio: '%s' | Inicio: %s",
                self.__id_reserva,
                self.__cliente.nombre,
                self.__servicio.nombre,
                self.__fecha_inicio.strftime("%Y-%m-%d %H:%M"),
            )

        finally:
            # El bloque 'finally' SIEMPRE se ejecuta (incluso si hubo error).
            # Lo usamos para registrar el intento de creacion en el log.
            logger.debug(
                "Intento de creacion de reserva finalizado para cliente '%s'.",
                getattr(cliente, "nombre", "DESCONOCIDO"),
            )

    # ------------------------------------------------------------------
    # Propiedades de solo lectura
    # ------------------------------------------------------------------

    @property
    def id_reserva(self) -> int:
        """ID unico de la reserva."""
        return self.__id_reserva

    @property
    def cliente(self) -> Cliente:
        """Cliente asociado a la reserva."""
        return self.__cliente

    @property
    def servicio(self) -> Servicio:
        """Servicio asociado a la reserva."""
        return self.__servicio

    @property
    def fecha_solicitud(self) -> datetime:
        """Momento en que se creo la reserva."""
        return self.__fecha_solicitud

    @property
    def fecha_inicio(self) -> datetime:
        """Fecha y hora programada para el inicio del servicio."""
        return self.__fecha_inicio

    @property
    def estado(self) -> str:
        """Estado actual de la reserva."""
        return self.__estado

    @property
    def costo_total(self) -> float:
        """Costo total calculado de la reserva (0.0 si aun no confirmada)."""
        return self.__costo_total

    @property
    def notas(self) -> str:
        """Observaciones adicionales de la reserva."""
        return self.__notas

    # ------------------------------------------------------------------
    # Metodo privado: cambiar estado con validacion de transicion
    # ------------------------------------------------------------------

    def __cambiar_estado(self, nuevo_estado: str, razon: str = "") -> None:
        """
        Cambia el estado de la reserva si la transicion es valida.

        Args:
            nuevo_estado (str): Nuevo estado a asignar.
            razon        (str): Razon del cambio (para el historial).

        Raises:
            InvalidReservationStateError: Si la transicion no esta permitida.
        """
        # Verifica si la transicion esta permitida
        transiciones_validas = self._TRANSICIONES.get(self.__estado, [])
        if nuevo_estado not in transiciones_validas:
            raise InvalidReservationStateError(
                estado_actual=self.__estado,
                operacion=f"cambiar a '{nuevo_estado}'",
            )

        # Registra el cambio en el historial interno
        self.__historial.append({
            "desde": self.__estado,
            "hacia": nuevo_estado,
            "momento": datetime.now().isoformat(),
            "razon": razon or "Sin especificar",
        })

        # Realiza el cambio de estado
        estado_anterior = self.__estado
        self.__estado = nuevo_estado

        logger.info(
            "Reserva #%d: estado '%s' -> '%s' | Razon: %s",
            self.__id_reserva,
            estado_anterior,
            nuevo_estado,
            razon or "Sin especificar",
        )

    # ------------------------------------------------------------------
    # Metodo publico: confirmar()
    # ------------------------------------------------------------------

    @log_operacion("Confirmar reserva")
    def confirmar(self) -> float:
        """
        Confirma la reserva: calcula el costo, ocupa el servicio y
        cambia el estado a 'confirmada'.

        Returns:
            float: Costo total de la reserva confirmada.

        Raises:
            InvalidReservationStateError: Si la reserva no esta en estado 'pendiente'.
            InconsistentCalculationError: Si el calculo de costo falla.
            ServiceUnavailableError:      Si el servicio ya no esta disponible.
        """
        try:
            # Verifica el estado antes de proceder
            if self.__estado != "pendiente":
                raise InvalidReservationStateError(
                    estado_actual=self.__estado,
                    operacion="confirmar",
                )

            # Verifica nuevamente la disponibilidad del servicio
            # (puede haber cambiado desde que se creo la reserva)
            if not self.__servicio.disponible:
                raise ServiceUnavailableError(
                    servicio=self.__servicio.nombre,
                    motivo=(
                        f"El servicio '{self.__servicio.nombre}' "
                        f"ya no esta disponible (estado: '{self.__servicio.estado}')."
                    ),
                )

            # Calcula el costo usando los kwargs guardados (impuesto, descuento, etc.)
            try:
                self.__costo_total = self.__servicio.calcular_costo(**self.__kwargs_costo)
            except InconsistentCalculationError as calc_err:
                # Encadenamiento de excepcion: agrega contexto de la reserva
                raise InconsistentCalculationError(
                    operacion="confirmar_reserva",
                    detalle=(
                        f"Error al calcular el costo de la reserva #{self.__id_reserva}: "
                        f"{calc_err}"
                    ),
                ) from calc_err

            # Marca el servicio como ocupado (encapsulacion de estado)
            self.__servicio.estado = "ocupado"

            # Cambia el estado de la reserva
            self.__cambiar_estado("confirmada", "Confirmacion exitosa")

        except (
            InvalidReservationStateError,
            ServiceUnavailableError,
            InconsistentCalculationError,
        ):
            # Re-lanza las excepciones de dominio conocidas sin modificar
            raise

        except Exception as exc_inesperada:
            # Encadena errores inesperados con contexto adicional
            raise InconsistentCalculationError(
                operacion="confirmar_reserva",
                detalle=(
                    f"Error inesperado al confirmar la reserva "
                    f"#{self.__id_reserva}: {exc_inesperada}"
                ),
            ) from exc_inesperada

        else:
            # Bloque else: solo se ejecuta si NO hubo excepcion.
            # Pre-formateamos el costo: %,.2f no es soportado por logging.
            costo_fmt = f"${self.__costo_total:,.2f}"
            logger.info(
                "[OK] Reserva #%d CONFIRMADA | Costo total: %s COP",
                self.__id_reserva,
                costo_fmt,
            )
            return self.__costo_total

        finally:
            # Siempre se registra el intento de confirmacion
            logger.debug(
                "Proceso de confirmacion finalizado para Reserva #%d.",
                self.__id_reserva,
            )

    # ------------------------------------------------------------------
    # Metodo publico: cancelar()
    # ------------------------------------------------------------------

    @log_operacion("Cancelar reserva")
    def cancelar(self, motivo: str = "Cancelacion solicitada por el cliente") -> None:
        """
        Cancela la reserva y libera el servicio si estaba ocupado.

        Args:
            motivo (str): Razon de la cancelacion.

        Raises:
            InvalidReservationStateError: Si la reserva ya esta en estado terminal
                                          (cancelada o completada).
        """
        try:
            # Intenta cambiar el estado (validara la transicion internamente)
            self.__cambiar_estado("cancelada", motivo)

            # Si el servicio estaba ocupado, lo libera
            if self.__servicio.estado == "ocupado":
                self.__servicio.estado = "disponible"
                logger.info(
                    "Servicio '%s' liberado tras cancelacion de Reserva #%d.",
                    self.__servicio.nombre,
                    self.__id_reserva,
                )

        except InvalidReservationStateError:
            # Re-lanza para que el llamador maneje la excepcion
            raise

        except Exception as exc:
            # Encadena cualquier otro error inesperado
            raise InvalidReservationStateError(
                estado_actual=self.__estado,
                operacion="cancelar",
            ) from exc

        finally:
            # Registro del intento de cancelacion (siempre)
            logger.debug(
                "Proceso de cancelacion finalizado para Reserva #%d.",
                self.__id_reserva,
            )

    # ------------------------------------------------------------------
    # Metodo publico: completar()
    # ------------------------------------------------------------------

    @log_operacion("Completar reserva")
    def completar(self) -> None:
        """
        Marca la reserva como completada y libera el servicio.

        Raises:
            InvalidReservationStateError: Si la reserva no esta en estado 'confirmada'.
        """
        try:
            self.__cambiar_estado("completada", "Servicio prestado exitosamente")

            # Libera el servicio para futuras reservas
            self.__servicio.estado = "disponible"
            logger.info(
                "[OK] Reserva #%d COMPLETADA | Servicio '%s' disponible nuevamente.",
                self.__id_reserva,
                self.__servicio.nombre,
            )

        except InvalidReservationStateError:
            raise

        finally:
            logger.debug(
                "Proceso de completar finalizado para Reserva #%d.",
                self.__id_reserva,
            )

    # ------------------------------------------------------------------
    # Historial de cambios
    # ------------------------------------------------------------------

    def obtener_historial(self) -> list[dict]:
        """
        Retorna una copia del historial de cambios de estado.

        Returns:
            list[dict]: Lista de registros con 'desde', 'hacia', 'momento' y 'razon'.
        """
        return list(self.__historial)  # Retorna copia para proteger el original

    # ------------------------------------------------------------------
    # Representaciones estandar
    # ------------------------------------------------------------------

    def describir(self) -> str:
        """Descripcion completa de la reserva."""
        return (
            f"{'=' * 55}\n"
            f"  RESERVA #{self.__id_reserva:04d}\n"
            f"{'=' * 55}\n"
            f"  Estado          : {self.__estado.upper()}\n"
            f"  Cliente         : {self.__cliente.nombre} (ID: {self.__cliente.identificacion})\n"
            f"  Servicio        : {self.__servicio.nombre}\n"
            f"  Tipo servicio   : {self.__servicio.__class__.__name__}\n"
            f"  Fecha solicitud : {self.__fecha_solicitud.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"  Fecha inicio    : {self.__fecha_inicio.strftime('%Y-%m-%d %H:%M')}\n"
            f"  Costo total     : ${self.__costo_total:,.2f} COP\n"
            f"  Notas           : {self.__notas or 'Sin notas'}\n"
            f"{'=' * 55}"
        )

    def __str__(self) -> str:
        """Representacion amigable de la reserva."""
        return (
            f"[Reserva#{self.__id_reserva:04d}] "
            f"Cliente='{self.__cliente.nombre}' | "
            f"Servicio='{self.__servicio.nombre}' | "
            f"Estado='{self.__estado}' | "
            f"Costo=${self.__costo_total:,.2f}"
        )

    def __repr__(self) -> str:
        """Representacion tecnica para debugging."""
        return (
            f"Reserva("
            f"id={self.__id_reserva}, "
            f"cliente='{self.__cliente.nombre}', "
            f"servicio='{self.__servicio.nombre}', "
            f"estado='{self.__estado}')"
        )
