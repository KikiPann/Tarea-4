"""
servicios.py
============
Módulo de Servicios - Sistema Software FJ
Autor: Sarith Mulford
Fecha: 2026-05-13
Python: 3.12

Jerarquía de clases:
    EntidadBase (abstracta)
        └── Servicio (abstracta)
                ├── ReservaSala
                ├── AlquilerEquipo
                └── AsesoriaEspecializada

Polimorfismo:
    Cada subclase sobreescribe `calcular_costo()` y `describir()`.

Sobrecarga simulada:
    calcular_costo(*args, **kwargs) acepta parámetros opcionales para
    aplicar impuestos o descuentos sin cambiar la firma base.
"""

from abc import abstractmethod            # Métodos abstractos
from datetime import datetime             # Fechas y horas
from entidades import EntidadBase         # Clase abstracta raíz

from excepciones import (
    InvalidDataError,              # Datos inválidos en construcción
    ServiceUnavailableError,       # Servicio no disponible
    InconsistentCalculationError,  # Cálculo de costo inconsistente
)
from logger import logger, log_operacion  # Logger y decorador


# ===========================================================================
# Clase Abstracta: Servicio
# ===========================================================================

class Servicio(EntidadBase):
    """
    Clase abstracta base para todos los servicios ofrecidos por Software FJ.

    Define el contrato mínimo:
      - Todo servicio tiene: nombre, descripción, precio_base y estado.
      - Implementa calcular_costo() de forma abstracta (cada hijo difiere).
      - Implementa describir() de forma abstracta.
      - Provee disponible (bool): indica si el servicio puede reservarse.

    Sobrecarga de calcular_costo():
        Acepta argumentos opcionales *args/**kwargs para extensión sin
        modificar la firma de las subclases ni romper el contrato abstracto.

    Estados posibles del servicio:
        "disponible"  → puede reservarse
        "ocupado"     → ya tiene una reserva activa
        "suspendido"  → fuera de operación temporal (mantenimiento, etc.)
    """

    # Conjunto de estados permitidos (evita typos en tiempo de ejecución)
    ESTADOS_VALIDOS: frozenset[str] = frozenset(
        {"disponible", "ocupado", "suspendido"}
    )

    def __init__(
        self,
        nombre: str,
        descripcion: str,
        precio_base: float,
        estado: str = "disponible",
    ) -> None:
        """
        Inicializa el servicio con validación de todos los atributos base.

        Args:
            nombre       (str):   Nombre del servicio.
            descripcion  (str):   Descripción breve del servicio.
            precio_base  (float): Precio base en pesos colombianos (> 0).
            estado       (str):   Estado inicial ('disponible' por defecto).

        Raises:
            InvalidDataError: Si precio_base ≤ 0 o el estado no es válido.
        """
        # Llama al constructor de EntidadBase (valida nombre y asigna ID)
        super().__init__(nombre)

        # Valida la descripción del servicio
        if not isinstance(descripcion, str) or not descripcion.strip():
            raise InvalidDataError(
                campo="descripcion",
                valor=descripcion,
                mensaje="La descripción del servicio no puede estar vacía.",
            )
        self.__descripcion: str = descripcion.strip()

        # Valida el precio base: debe ser numérico y positivo
        if not isinstance(precio_base, (int, float)) or isinstance(precio_base, bool):
            raise InvalidDataError(
                campo="precio_base",
                valor=precio_base,
                mensaje="El precio base debe ser un número.",
            )
        if precio_base <= 0:
            raise InvalidDataError(
                campo="precio_base",
                valor=precio_base,
                mensaje="El precio base debe ser mayor que cero.",
            )
        self.__precio_base: float = float(precio_base)

        # Valida y asigna el estado
        self.estado = estado  # Usa el setter que valida

        logger.debug(
            "Servicio creado: ID=%d | Nombre='%s' | Precio base=%.2f | Estado='%s'",
            self.id_entidad,
            self.nombre,
            self.__precio_base,
            self.__estado,
        )

    # ------------------------------------------------------------------
    # Propiedades
    # ------------------------------------------------------------------

    @property
    def descripcion(self) -> str:
        """Descripción del servicio."""
        return self.__descripcion

    @property
    def precio_base(self) -> float:
        """Precio base del servicio en pesos colombianos."""
        return self.__precio_base

    @property
    def estado(self) -> str:
        """Estado actual del servicio."""
        return self.__estado

    @estado.setter
    def estado(self, nuevo_estado: str) -> None:
        """
        Actualiza el estado del servicio con validación.

        Args:
            nuevo_estado (str): Nuevo estado a asignar.

        Raises:
            InvalidDataError: Si el estado no está en ESTADOS_VALIDOS.
        """
        if nuevo_estado not in self.ESTADOS_VALIDOS:
            raise InvalidDataError(
                campo="estado",
                valor=nuevo_estado,
                mensaje=(
                    f"Estado '{nuevo_estado}' no válido. "
                    f"Use: {sorted(self.ESTADOS_VALIDOS)}"
                ),
            )
        self.__estado: str = nuevo_estado

    @property
    def disponible(self) -> bool:
        """True si el servicio puede reservarse (estado == 'disponible')."""
        return self.__estado == "disponible"

    # ------------------------------------------------------------------
    # Métodos abstractos: DEBEN implementarse en cada subclase
    # ------------------------------------------------------------------

    @abstractmethod
    def calcular_costo(self, *args, **kwargs) -> float:
        """
        Calcula el costo total del servicio.

        Sobrecarga simulada mediante *args/**kwargs:
            - Sin argumentos: retorna precio_base.
            - Con 'impuesto' (float 0.0-1.0): aplica impuesto al costo.
            - Con 'descuento' (float 0.0-1.0): aplica descuento al costo.
            - Con 'duracion_horas' (float): multiplica por horas usadas.

        Returns:
            float: Costo total calculado.

        Raises:
            InconsistentCalculationError: Si los parámetros generan un costo inválido.
        """
        ...

    @abstractmethod
    def describir(self) -> str:
        """Descripción completa del servicio para mostrar al usuario."""
        ...

    # ------------------------------------------------------------------
    # Método auxiliar de "sobrecarga": aplica modificadores al costo
    # ------------------------------------------------------------------

    def _aplicar_modificadores(
        self,
        costo_base: float,
        *args,
        impuesto: float = 0.0,
        descuento: float = 0.0,
        **kwargs,
    ) -> float:
        """
        Aplica impuesto y/o descuento a un costo base.

        Simula sobrecarga de métodos: si se llama calcular_costo() sin
        argumentos, devuelve el precio base. Con argumentos, modifica el total.

        Args:
            costo_base (float):   Costo antes de modificadores.
            impuesto   (float):   Porcentaje de impuesto (0.0 = 0%, 0.19 = 19%).
            descuento  (float):   Porcentaje de descuento (0.0 = 0%, 0.10 = 10%).
            *args, **kwargs:      Ignorados (extensibilidad futura).

        Returns:
            float: Costo modificado redondeado a 2 decimales.

        Raises:
            InconsistentCalculationError: Si impuesto o descuento están fuera de [0, 1].
        """
        # Valida rango del impuesto
        if not (0.0 <= impuesto <= 1.0):
            raise InconsistentCalculationError(
                operacion="aplicar_impuesto",
                detalle=(
                    f"La tasa de impuesto {impuesto} está fuera del rango válido [0.0, 1.0]."
                ),
            )
        # Valida rango del descuento
        if not (0.0 <= descuento <= 1.0):
            raise InconsistentCalculationError(
                operacion="aplicar_descuento",
                detalle=(
                    f"El porcentaje de descuento {descuento} está fuera del rango [0.0, 1.0]."
                ),
            )
        # Calcula: (costo_base * (1 + impuesto)) * (1 - descuento)
        costo_con_impuesto = costo_base * (1.0 + impuesto)
        costo_final = costo_con_impuesto * (1.0 - descuento)

        # Verifica que el resultado sea positivo (sanity check)
        if costo_final < 0:
            raise InconsistentCalculationError(
                operacion="calcular_costo_final",
                detalle=(
                    f"El costo final resultó negativo ({costo_final:.2f}). "
                    "Verifique los parámetros de impuesto y descuento."
                ),
            )

        return round(costo_final, 2)

    def __str__(self) -> str:
        """Representación amigable del servicio."""
        return (
            f"[{self.__class__.__name__}#{self.id_entidad}] "
            f"{self.nombre} | Estado: {self.__estado} | "
            f"Precio base: ${self.__precio_base:,.2f}"
        )


# ===========================================================================
# Subclase 1: ReservaSala
# ===========================================================================

class ReservaSala(Servicio):
    """
    Servicio de reserva de sala de reuniones o trabajo.

    Atributos adicionales:
        capacidad      (int):   Máximo de personas permitidas.
        duracion_horas (float): Duración de la reserva en horas.
        numero_sala    (str):   Identificador físico de la sala (ej. 'A-201').

    Costo:
        precio_base × duracion_horas [+ impuesto] [- descuento]
    """

    def __init__(
        self,
        nombre: str,
        descripcion: str,
        precio_hora: float,
        duracion_horas: float,
        capacidad: int,
        numero_sala: str,
        estado: str = "disponible",
    ) -> None:
        """
        Constructor de ReservaSala.

        Args:
            nombre         (str):   Nombre del servicio de sala.
            descripcion    (str):   Descripción breve.
            precio_hora    (float): Precio por hora (en COP).
            duracion_horas (float): Duración de la reserva en horas (> 0).
            capacidad      (int):   Capacidad máxima de personas (> 0).
            numero_sala    (str):   Código de la sala (no vacío).
            estado         (str):   Estado inicial.

        Raises:
            InvalidDataError: Si duracion_horas ≤ 0, capacidad ≤ 0 o numero_sala vacía.
        """
        # Llama al constructor de Servicio con precio_hora como precio_base
        super().__init__(nombre, descripcion, precio_hora, estado)

        # Valida la duración de la reserva
        if not isinstance(duracion_horas, (int, float)) or duracion_horas <= 0:
            raise InvalidDataError(
                campo="duracion_horas",
                valor=duracion_horas,
                mensaje="La duración en horas debe ser un número positivo mayor que cero.",
            )
        self.__duracion_horas: float = float(duracion_horas)

        # Valida la capacidad de la sala
        if not isinstance(capacidad, int) or isinstance(capacidad, bool) or capacidad <= 0:
            raise InvalidDataError(
                campo="capacidad",
                valor=capacidad,
                mensaje="La capacidad de la sala debe ser un entero positivo.",
            )
        self.__capacidad: int = capacidad

        # Valida el número/código de sala
        if not isinstance(numero_sala, str) or not numero_sala.strip():
            raise InvalidDataError(
                campo="numero_sala",
                valor=numero_sala,
                mensaje="El número de sala no puede estar vacío.",
            )
        self.__numero_sala: str = numero_sala.strip()

        logger.info(
            "ReservaSala creada: Sala='%s' | Capacidad=%d | Duración=%.1fh | Precio/h=$%.2f",
            self.__numero_sala,
            self.__capacidad,
            self.__duracion_horas,
            self.precio_base,
        )

    # ------------------------------------------------------------------
    # Propiedades específicas de ReservaSala
    # ------------------------------------------------------------------

    @property
    def duracion_horas(self) -> float:
        """Duración de la reserva en horas."""
        return self.__duracion_horas

    @property
    def capacidad(self) -> int:
        """Capacidad máxima de personas en la sala."""
        return self.__capacidad

    @property
    def numero_sala(self) -> str:
        """Código identificador de la sala."""
        return self.__numero_sala

    # ------------------------------------------------------------------
    # Implementación del método abstracto: calcular_costo (POLIMORFISMO)
    # ------------------------------------------------------------------

    @log_operacion("Calcular costo ReservaSala")
    def calcular_costo(self, *args, **kwargs) -> float:
        """
        Calcula el costo de la reserva de sala.

        Sobrecarga simulada mediante kwargs:
            - Sin kwargs: precio_hora × duracion_horas
            - impuesto=0.19: agrega IVA del 19%
            - descuento=0.10: aplica 10% de descuento
            - duracion_horas=X: sobreescribe la duración original

        Args:
            *args: Ignorados.
            **kwargs:
                impuesto      (float): Tasa de impuesto [0.0, 1.0].
                descuento     (float): Tasa de descuento [0.0, 1.0].
                duracion_horas (float): Duración alternativa en horas.

        Returns:
            float: Costo total redondeado a 2 decimales.

        Raises:
            InconsistentCalculationError: Si los parámetros son inválidos.
        """
        # Permite sobreescribir la duración desde kwargs (sobrecarga)
        duracion = kwargs.pop("duracion_horas", self.__duracion_horas)

        # Valida la duración (puede venir de kwargs)
        if not isinstance(duracion, (int, float)) or duracion <= 0:
            raise InconsistentCalculationError(
                operacion="calcular_costo_sala",
                detalle=f"Duración inválida: {duracion}. Debe ser un número positivo.",
            )

        # Costo base: precio por hora × número de horas
        costo_base = self.precio_base * float(duracion)

        # Aplica modificadores (impuesto/descuento) si se proporcionaron
        return self._aplicar_modificadores(costo_base, *args, **kwargs)

    # ------------------------------------------------------------------
    # Implementación del método abstracto: describir (POLIMORFISMO)
    # ------------------------------------------------------------------

    def describir(self) -> str:
        """Descripción completa de la reserva de sala."""
        return (
            f"{'─' * 50}\n"
            f"  SERVICIO: Reserva de Sala\n"
            f"{'─' * 50}\n"
            f"  Sala            : {self.__numero_sala}\n"
            f"  Nombre          : {self.nombre}\n"
            f"  Descripción     : {self.descripcion}\n"
            f"  Capacidad       : {self.__capacidad} personas\n"
            f"  Duración        : {self.__duracion_horas:.1f} horas\n"
            f"  Precio por hora : ${self.precio_base:,.2f} COP\n"
            f"  Costo estimado  : ${self.calcular_costo():,.2f} COP\n"
            f"  Estado          : {self.estado}\n"
            f"{'─' * 50}"
        )


# ===========================================================================
# Subclase 2: AlquilerEquipo
# ===========================================================================

class AlquilerEquipo(Servicio):
    """
    Servicio de alquiler de equipos tecnológicos o físicos.

    Atributos adicionales:
        tipo_equipo    (str):   Categoría del equipo (ej. 'Portátil', 'Proyector').
        numero_serie   (str):   Número de serie único del equipo.
        dias_alquiler  (int):   Número de días de alquiler (>= 1).

    Costo:
        precio_dia × dias_alquiler [+ impuesto] [- descuento]
    """

    def __init__(
        self,
        nombre: str,
        descripcion: str,
        precio_dia: float,
        tipo_equipo: str,
        numero_serie: str,
        dias_alquiler: int,
        estado: str = "disponible",
    ) -> None:
        """
        Constructor de AlquilerEquipo.

        Args:
            nombre        (str):   Nombre descriptivo del equipo.
            descripcion   (str):   Descripción breve.
            precio_dia    (float): Precio de alquiler por día (COP).
            tipo_equipo   (str):   Categoría del equipo.
            numero_serie  (str):   Número de serie único.
            dias_alquiler (int):   Número de días de alquiler (>= 1).
            estado        (str):   Estado inicial del servicio.

        Raises:
            InvalidDataError: Si dias_alquiler < 1 o tipo_equipo/numero_serie vacíos.
        """
        super().__init__(nombre, descripcion, precio_dia, estado)

        # Valida tipo de equipo
        if not isinstance(tipo_equipo, str) or not tipo_equipo.strip():
            raise InvalidDataError(
                campo="tipo_equipo",
                valor=tipo_equipo,
                mensaje="El tipo de equipo no puede estar vacío.",
            )
        self.__tipo_equipo: str = tipo_equipo.strip()

        # Valida número de serie
        if not isinstance(numero_serie, str) or not numero_serie.strip():
            raise InvalidDataError(
                campo="numero_serie",
                valor=numero_serie,
                mensaje="El número de serie del equipo no puede estar vacío.",
            )
        self.__numero_serie: str = numero_serie.strip()

        # Valida días de alquiler
        if not isinstance(dias_alquiler, int) or isinstance(dias_alquiler, bool) or dias_alquiler < 1:
            raise InvalidDataError(
                campo="dias_alquiler",
                valor=dias_alquiler,
                mensaje="Los días de alquiler deben ser un entero mayor o igual a 1.",
            )
        self.__dias_alquiler: int = dias_alquiler

        logger.info(
            "AlquilerEquipo creado: '%s' | Serie='%s' | Días=%d | Precio/día=$%.2f",
            self.__tipo_equipo,
            self.__numero_serie,
            self.__dias_alquiler,
            self.precio_base,
        )

    # ------------------------------------------------------------------
    # Propiedades
    # ------------------------------------------------------------------

    @property
    def tipo_equipo(self) -> str:
        """Tipo/categoría del equipo."""
        return self.__tipo_equipo

    @property
    def numero_serie(self) -> str:
        """Número de serie único del equipo."""
        return self.__numero_serie

    @property
    def dias_alquiler(self) -> int:
        """Número de días de alquiler."""
        return self.__dias_alquiler

    # ------------------------------------------------------------------
    # Implementación: calcular_costo (POLIMORFISMO)
    # ------------------------------------------------------------------

    @log_operacion("Calcular costo AlquilerEquipo")
    def calcular_costo(self, *args, **kwargs) -> float:
        """
        Calcula el costo del alquiler del equipo.

        Sobrecarga simulada:
            - Sin kwargs: precio_dia × dias_alquiler
            - dias_alquiler=X: sobreescribe los días de alquiler
            - impuesto=0.19: agrega IVA del 19%
            - descuento=0.05: aplica 5% de descuento

        Returns:
            float: Costo total del alquiler.

        Raises:
            InconsistentCalculationError: Si los parámetros resultan inválidos.
        """
        # Permite sobreescribir días desde kwargs (sobrecarga simulada)
        dias = kwargs.pop("dias_alquiler", self.__dias_alquiler)

        if not isinstance(dias, int) or dias < 1:
            raise InconsistentCalculationError(
                operacion="calcular_costo_equipo",
                detalle=f"Días de alquiler inválidos: {dias}. Debe ser un entero >= 1.",
            )

        # Costo base: precio por día × número de días
        costo_base = self.precio_base * dias

        return self._aplicar_modificadores(costo_base, *args, **kwargs)

    # ------------------------------------------------------------------
    # Implementación: describir (POLIMORFISMO)
    # ------------------------------------------------------------------

    def describir(self) -> str:
        """Descripción completa del alquiler de equipo."""
        return (
            f"{'─' * 50}\n"
            f"  SERVICIO: Alquiler de Equipo\n"
            f"{'─' * 50}\n"
            f"  Tipo de equipo  : {self.__tipo_equipo}\n"
            f"  Nombre          : {self.nombre}\n"
            f"  Descripción     : {self.descripcion}\n"
            f"  Número de serie : {self.__numero_serie}\n"
            f"  Días de alquiler: {self.__dias_alquiler} días\n"
            f"  Precio por día  : ${self.precio_base:,.2f} COP\n"
            f"  Costo estimado  : ${self.calcular_costo():,.2f} COP\n"
            f"  Estado          : {self.estado}\n"
            f"{'─' * 50}"
        )


# ===========================================================================
# Subclase 3: AsesoriaEspecializada
# ===========================================================================

class AsesoriaEspecializada(Servicio):
    """
    Servicio de asesoría técnica o profesional especializada.

    Atributos adicionales:
        especialidad   (str):   Área de especialización (ej. 'Redes', 'Seguridad').
        nombre_asesor  (str):   Nombre del asesor asignado.
        sesiones       (int):   Número de sesiones contratadas (>= 1).
        precio_sesion  (float): Precio por sesión (mismo que precio_base).

    Costo:
        precio_sesion × sesiones [+ impuesto] [- descuento]

    Nota: Los asesores senior tienen un recargo automático del 20%
          si se pasa el kwarg asesor_senior=True.
    """

    def __init__(
        self,
        nombre: str,
        descripcion: str,
        precio_sesion: float,
        especialidad: str,
        nombre_asesor: str,
        sesiones: int,
        estado: str = "disponible",
    ) -> None:
        """
        Constructor de AsesoriaEspecializada.

        Args:
            nombre         (str):   Nombre del servicio de asesoría.
            descripcion    (str):   Descripción del alcance.
            precio_sesion  (float): Precio por sesión de asesoría (COP).
            especialidad   (str):   Área o especialidad de la asesoría.
            nombre_asesor  (str):   Nombre del profesional a cargo.
            sesiones       (int):   Número de sesiones contratadas (>= 1).
            estado         (str):   Estado inicial del servicio.

        Raises:
            InvalidDataError: Si sesiones < 1 o especialidad/nombre_asesor vacíos.
        """
        super().__init__(nombre, descripcion, precio_sesion, estado)

        # Valida especialidad
        if not isinstance(especialidad, str) or not especialidad.strip():
            raise InvalidDataError(
                campo="especialidad",
                valor=especialidad,
                mensaje="La especialidad de la asesoría no puede estar vacía.",
            )
        self.__especialidad: str = especialidad.strip()

        # Valida nombre del asesor
        if not isinstance(nombre_asesor, str) or not nombre_asesor.strip():
            raise InvalidDataError(
                campo="nombre_asesor",
                valor=nombre_asesor,
                mensaje="El nombre del asesor no puede estar vacío.",
            )
        self.__nombre_asesor: str = nombre_asesor.strip()

        # Valida número de sesiones
        if not isinstance(sesiones, int) or isinstance(sesiones, bool) or sesiones < 1:
            raise InvalidDataError(
                campo="sesiones",
                valor=sesiones,
                mensaje="El número de sesiones debe ser un entero mayor o igual a 1.",
            )
        self.__sesiones: int = sesiones

        logger.info(
            "AsesoriaEspecializada creada: '%s' | Asesor='%s' | Sesiones=%d | Precio=$%.2f",
            self.__especialidad,
            self.__nombre_asesor,
            self.__sesiones,
            self.precio_base,
        )

    # ------------------------------------------------------------------
    # Propiedades
    # ------------------------------------------------------------------

    @property
    def especialidad(self) -> str:
        """Área de especialización."""
        return self.__especialidad

    @property
    def nombre_asesor(self) -> str:
        """Nombre del asesor profesional."""
        return self.__nombre_asesor

    @property
    def sesiones(self) -> int:
        """Número de sesiones contratadas."""
        return self.__sesiones

    # ------------------------------------------------------------------
    # Implementación: calcular_costo (POLIMORFISMO)
    # ------------------------------------------------------------------

    @log_operacion("Calcular costo AsesoriaEspecializada")
    def calcular_costo(self, *args, **kwargs) -> float:
        """
        Calcula el costo total de la asesoría.

        Sobrecarga simulada:
            - Sin kwargs: precio_sesion × sesiones
            - sesiones=X: sobreescribe el número de sesiones
            - impuesto=0.19: agrega IVA del 19%
            - descuento=0.15: aplica 15% de descuento
            - asesor_senior=True: aplica recargo del 20% por seniority

        Returns:
            float: Costo total de la asesoría.

        Raises:
            InconsistentCalculationError: Si los parámetros resultan inválidos.
        """
        # Permite sobreescribir sesiones desde kwargs (sobrecarga simulada)
        sesiones = kwargs.pop("sesiones", self.__sesiones)

        if not isinstance(sesiones, int) or sesiones < 1:
            raise InconsistentCalculationError(
                operacion="calcular_costo_asesoria",
                detalle=f"Número de sesiones inválido: {sesiones}. Debe ser un entero >= 1.",
            )

        # Extrae el flag de asesor senior (sobrecarga adicional)
        asesor_senior = kwargs.pop("asesor_senior", False)

        # Costo base: precio × sesiones
        costo_base = self.precio_base * sesiones

        # Recargo del 20% si el asesor es senior
        if asesor_senior:
            costo_base *= 1.20
            logger.debug(
                "Recargo senior (20%%) aplicado. Costo base ajustado: $%.2f",
                costo_base,
            )

        return self._aplicar_modificadores(costo_base, *args, **kwargs)

    # ------------------------------------------------------------------
    # Implementación: describir (POLIMORFISMO)
    # ------------------------------------------------------------------

    def describir(self) -> str:
        """Descripción completa del servicio de asesoría."""
        return (
            f"{'─' * 50}\n"
            f"  SERVICIO: Asesoría Especializada\n"
            f"{'─' * 50}\n"
            f"  Especialidad    : {self.__especialidad}\n"
            f"  Nombre servicio : {self.nombre}\n"
            f"  Descripción     : {self.descripcion}\n"
            f"  Asesor asignado : {self.__nombre_asesor}\n"
            f"  Sesiones        : {self.__sesiones}\n"
            f"  Precio/sesión   : ${self.precio_base:,.2f} COP\n"
            f"  Costo estimado  : ${self.calcular_costo():,.2f} COP\n"
            f"  Estado          : {self.estado}\n"
            f"{'─' * 50}"
        )
