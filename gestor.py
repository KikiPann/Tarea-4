"""
gestor.py
=========
Módulo Gestor del Sistema - Software FJ
Autor: Sarith Mulford
Fecha: 2026-05-13
Python: 3.12

Gestiona las listas internas de Clientes, Servicios y Reservas.
Actúa como repositorio en memoria (sin base de datos).
Provee operaciones CRUD completas con manejo de excepciones.
"""

from datetime import datetime              # Para búsquedas y reportes por fecha
from entidades import Cliente              # Clase Cliente
from servicios import Servicio             # Clase base Servicio
from reserva import Reserva                # Clase Reserva

from excepciones import (
    InvalidDataError,              # Datos duplicados o inválidos
    ServiceUnavailableError,       # Servicio no encontrado o no disponible
    InvalidReservationStateError,  # Estado inválido de reserva
)
from logger import logger, log_operacion  # Logger centralizado


# ===========================================================================
# Clase GestorSistema
# ===========================================================================

class GestorSistema:
    """
    Gestor central del sistema Software FJ.

    Mantiene tres listas internas:
        _clientes  (list[Cliente]):  Clientes registrados.
        _servicios (list[Servicio]): Servicios disponibles.
        _reservas  (list[Reserva]):  Reservas realizadas.

    Garantiza:
        - No duplicar clientes por número de identificación.
        - No registrar servicios con IDs duplicados.
        - No confirmar reservas sobre servicios no disponibles.
        - Todas las operaciones están logueadas.

    Uso:
        gestor = GestorSistema()
        gestor.registrar_cliente(cliente)
        gestor.agregar_servicio(servicio)
        reserva = gestor.crear_reserva(cliente, servicio, fecha_inicio)
        gestor.confirmar_reserva(reserva.id_reserva)
    """

    def __init__(self) -> None:
        """Inicializa el gestor con listas vacías."""
        # Listas internas (sin base de datos)
        self._clientes: list[Cliente] = []
        self._servicios: list[Servicio] = []
        self._reservas: list[Reserva] = []

        logger.info("GestorSistema inicializado. Listas en memoria creadas.")

    # ==================================================================
    # Operaciones sobre Clientes
    # ==================================================================

    @log_operacion("Registrar cliente")
    def registrar_cliente(self, cliente: Cliente) -> None:
        """
        Registra un nuevo cliente en el sistema.

        Args:
            cliente (Cliente): Instancia de Cliente a registrar.

        Raises:
            InvalidDataError: Si el parámetro no es Cliente o la
                              identificación ya está registrada.
        """
        # Valida el tipo del parámetro
        if not isinstance(cliente, Cliente):
            raise InvalidDataError(
                campo="cliente",
                valor=type(cliente).__name__,
                mensaje="Solo se pueden registrar instancias de Cliente.",
            )

        # Verifica que no exista ya un cliente con la misma identificación
        for c_existente in self._clientes:
            if c_existente.identificacion == cliente.identificacion:
                raise InvalidDataError(
                    campo="identificacion",
                    valor=cliente.identificacion,
                    mensaje=(
                        f"Ya existe un cliente con identificación "
                        f"{cliente.identificacion} ('{c_existente.nombre}')."
                    ),
                )

        # Agrega el cliente a la lista interna
        self._clientes.append(cliente)
        logger.info(
            "✔ Cliente registrado: '%s' | ID: %d | Sistema: #%d",
            cliente.nombre,
            cliente.identificacion,
            cliente.id_entidad,
        )

    @log_operacion("Buscar cliente por identificación")
    def buscar_cliente(self, identificacion: int) -> Cliente | None:
        """
        Busca un cliente por su número de identificación.

        Args:
            identificacion (int): Número de identificación del cliente.

        Returns:
            Cliente | None: El cliente encontrado, o None si no existe.
        """
        for cliente in self._clientes:
            if cliente.identificacion == identificacion:
                return cliente
        logger.warning(
            "Cliente con identificación %d no encontrado.", identificacion
        )
        return None

    def listar_clientes(self) -> list[Cliente]:
        """
        Retorna una copia de la lista de clientes registrados.

        Returns:
            list[Cliente]: Lista de todos los clientes.
        """
        logger.debug("Listando %d cliente(s).", len(self._clientes))
        return list(self._clientes)  # Copia para proteger la lista interna

    # ==================================================================
    # Operaciones sobre Servicios
    # ==================================================================

    @log_operacion("Agregar servicio")
    def agregar_servicio(self, servicio: Servicio) -> None:
        """
        Agrega un nuevo servicio al catálogo del sistema.

        Args:
            servicio (Servicio): Instancia de Servicio a agregar.

        Raises:
            InvalidDataError: Si el parámetro no es Servicio o ya existe
                              un servicio con el mismo ID de entidad.
        """
        if not isinstance(servicio, Servicio):
            raise InvalidDataError(
                campo="servicio",
                valor=type(servicio).__name__,
                mensaje="Solo se pueden registrar instancias de Servicio.",
            )

        # Verifica duplicados por ID de entidad
        for s_existente in self._servicios:
            if s_existente.id_entidad == servicio.id_entidad:
                raise InvalidDataError(
                    campo="id_entidad",
                    valor=servicio.id_entidad,
                    mensaje=f"Ya existe un servicio con ID {servicio.id_entidad}.",
                )

        self._servicios.append(servicio)
        logger.info(
            "✔ Servicio agregado: '%s' [%s] | Precio base: $%.2f COP",
            servicio.nombre,
            servicio.__class__.__name__,
            servicio.precio_base,
        )

    @log_operacion("Buscar servicio por nombre")
    def buscar_servicio(self, nombre: str) -> Servicio | None:
        """
        Busca un servicio por nombre (búsqueda parcial, sin distinción de mayúsculas).

        Args:
            nombre (str): Nombre o parte del nombre del servicio.

        Returns:
            Servicio | None: El primer servicio encontrado, o None.
        """
        nombre_lower = nombre.lower().strip()
        for servicio in self._servicios:
            if nombre_lower in servicio.nombre.lower():
                return servicio
        logger.warning("Servicio con nombre '%s' no encontrado.", nombre)
        return None

    def listar_servicios(self, solo_disponibles: bool = False) -> list[Servicio]:
        """
        Retorna la lista de servicios, opcionalmente filtrada por disponibilidad.

        Args:
            solo_disponibles (bool): Si True, solo retorna servicios disponibles.

        Returns:
            list[Servicio]: Lista de servicios según el filtro.
        """
        if solo_disponibles:
            resultado = [s for s in self._servicios if s.disponible]
        else:
            resultado = list(self._servicios)
        logger.debug(
            "Listando %d servicio(s) (solo_disponibles=%s).",
            len(resultado),
            solo_disponibles,
        )
        return resultado

    # ==================================================================
    # Operaciones sobre Reservas
    # ==================================================================

    @log_operacion("Crear reserva")
    def crear_reserva(
        self,
        cliente: Cliente,
        servicio: Servicio,
        fecha_inicio: datetime,
        notas: str = "",
        **kwargs_costo,
    ) -> Reserva:
        """
        Crea una nueva reserva y la registra en el sistema.

        Args:
            cliente      (Cliente):   Cliente que solicita la reserva.
            servicio     (Servicio):  Servicio a reservar.
            fecha_inicio (datetime):  Fecha y hora programada.
            notas        (str):       Observaciones opcionales.
            **kwargs_costo:           Parámetros para calcular_costo()
                                      (ej. impuesto=0.19, descuento=0.10).

        Returns:
            Reserva: La reserva creada en estado 'pendiente'.

        Raises:
            InvalidDataError:        Si los datos de la reserva son inválidos.
            ServiceUnavailableError: Si el servicio no está disponible.
        """
        # Verifica que el cliente esté registrado en el sistema
        cliente_registrado = self.buscar_cliente(cliente.identificacion)
        if cliente_registrado is None:
            raise InvalidDataError(
                campo="cliente",
                valor=cliente.nombre,
                mensaje=(
                    f"El cliente '{cliente.nombre}' (ID: {cliente.identificacion}) "
                    "no está registrado en el sistema."
                ),
            )

        # Verifica que el servicio esté en el catálogo
        servicio_registrado = next(
            (s for s in self._servicios if s.id_entidad == servicio.id_entidad),
            None,
        )
        if servicio_registrado is None:
            raise InvalidDataError(
                campo="servicio",
                valor=servicio.nombre,
                mensaje=f"El servicio '{servicio.nombre}' no está registrado en el sistema.",
            )

        # Crea la reserva (la clase Reserva valida disponibilidad internamente)
        nueva_reserva = Reserva(
            cliente=cliente,
            servicio=servicio,
            fecha_inicio=fecha_inicio,
            notas=notas,
            **kwargs_costo,
        )

        # Agrega a la lista interna
        self._reservas.append(nueva_reserva)
        logger.info(
            "✔ Reserva #%d creada: Cliente='%s' | Servicio='%s'",
            nueva_reserva.id_reserva,
            cliente.nombre,
            servicio.nombre,
        )
        return nueva_reserva

    @log_operacion("Confirmar reserva por ID")
    def confirmar_reserva(self, id_reserva: int) -> float:
        """
        Busca y confirma una reserva por su ID.

        Args:
            id_reserva (int): ID de la reserva a confirmar.

        Returns:
            float: Costo total de la reserva confirmada.

        Raises:
            ServiceUnavailableError:      Si la reserva no se encuentra.
            InvalidReservationStateError: Si la reserva no puede confirmarse.
        """
        reserva = self._buscar_reserva_por_id(id_reserva)
        if reserva is None:
            raise ServiceUnavailableError(
                servicio=f"Reserva#{id_reserva}",
                motivo=f"No se encontró ninguna reserva con ID {id_reserva}.",
            )
        return reserva.confirmar()

    @log_operacion("Cancelar reserva por ID")
    def cancelar_reserva(self, id_reserva: int, motivo: str = "") -> None:
        """
        Busca y cancela una reserva por su ID.

        Args:
            id_reserva (int): ID de la reserva a cancelar.
            motivo     (str): Razón de la cancelación.

        Raises:
            ServiceUnavailableError:      Si la reserva no se encuentra.
            InvalidReservationStateError: Si la reserva no puede cancelarse.
        """
        reserva = self._buscar_reserva_por_id(id_reserva)
        if reserva is None:
            raise ServiceUnavailableError(
                servicio=f"Reserva#{id_reserva}",
                motivo=f"No se encontró ninguna reserva con ID {id_reserva}.",
            )
        reserva.cancelar(motivo or "Cancelada desde el gestor del sistema")

    @log_operacion("Completar reserva por ID")
    def completar_reserva(self, id_reserva: int) -> None:
        """
        Busca y completa una reserva por su ID.

        Args:
            id_reserva (int): ID de la reserva a completar.

        Raises:
            ServiceUnavailableError:      Si la reserva no se encuentra.
            InvalidReservationStateError: Si la reserva no puede completarse.
        """
        reserva = self._buscar_reserva_por_id(id_reserva)
        if reserva is None:
            raise ServiceUnavailableError(
                servicio=f"Reserva#{id_reserva}",
                motivo=f"No se encontró ninguna reserva con ID {id_reserva}.",
            )
        reserva.completar()

    def _buscar_reserva_por_id(self, id_reserva: int) -> Reserva | None:
        """
        Busca una reserva por su ID en la lista interna.

        Args:
            id_reserva (int): ID de la reserva a buscar.

        Returns:
            Reserva | None: La reserva encontrada, o None.
        """
        for reserva in self._reservas:
            if reserva.id_reserva == id_reserva:
                return reserva
        return None

    def listar_reservas(self, estado: str | None = None) -> list[Reserva]:
        """
        Lista todas las reservas, opcionalmente filtradas por estado.

        Args:
            estado (str | None): Estado a filtrar ('pendiente', 'confirmada', etc.).
                                 Si es None, retorna todas.

        Returns:
            list[Reserva]: Lista de reservas según el filtro.
        """
        if estado:
            resultado = [r for r in self._reservas if r.estado == estado]
        else:
            resultado = list(self._reservas)
        logger.debug(
            "Listando %d reserva(s) (estado=%s).", len(resultado), estado or "todas"
        )
        return resultado

    # ==================================================================
    # Reporte del sistema
    # ==================================================================

    def generar_reporte(self) -> str:
        """
        Genera un reporte completo del estado actual del sistema.

        Returns:
            str: Reporte formateado con totales y estadísticas.
        """
        # Calcula estadísticas de reservas
        total_reservas = len(self._reservas)
        confirmadas = sum(1 for r in self._reservas if r.estado == "confirmada")
        canceladas = sum(1 for r in self._reservas if r.estado == "cancelada")
        completadas = sum(1 for r in self._reservas if r.estado == "completada")
        pendientes = sum(1 for r in self._reservas if r.estado == "pendiente")

        # Calcula ingresos por reservas confirmadas y completadas
        ingresos = sum(
            r.costo_total
            for r in self._reservas
            if r.estado in ("confirmada", "completada")
        )

        # Calcula servicios disponibles
        disponibles = sum(1 for s in self._servicios if s.disponible)

        reporte = (
            f"\n{'█' * 60}\n"
            f"  📊 REPORTE DEL SISTEMA - Software FJ\n"
            f"  Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"{'█' * 60}\n"
            f"\n  📋 CLIENTES\n"
            f"  {'─' * 30}\n"
            f"  Total registrados    : {len(self._clientes)}\n"
            f"\n  🛎 SERVICIOS\n"
            f"  {'─' * 30}\n"
            f"  Total en catálogo    : {len(self._servicios)}\n"
            f"  Disponibles          : {disponibles}\n"
            f"  Ocupados/Suspendidos : {len(self._servicios) - disponibles}\n"
            f"\n  📅 RESERVAS\n"
            f"  {'─' * 30}\n"
            f"  Total creadas        : {total_reservas}\n"
            f"  Pendientes           : {pendientes}\n"
            f"  Confirmadas          : {confirmadas}\n"
            f"  Completadas          : {completadas}\n"
            f"  Canceladas           : {canceladas}\n"
            f"\n  💰 FINANCIERO\n"
            f"  {'─' * 30}\n"
            f"  Ingresos (conf+comp) : ${ingresos:,.2f} COP\n"
            f"{'█' * 60}\n"
        )

        logger.info("Reporte generado. Ingresos: $%.2f COP", ingresos)
        return reporte
