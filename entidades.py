"""
entidades.py
============
Módulo de Entidades Base - Sistema Software FJ
Autor: Sarith Mulford
Fecha: 2026-05-13
Python: 3.12

Contiene:
  - EntidadBase: Clase abstracta raíz del sistema.
  - Cliente: Implementación con encapsulación estricta y validaciones robustas.

Principios aplicados:
  - Abstracción: EntidadBase define la interfaz común.
  - Encapsulación: Cliente usa propiedades (@property) con setters validados.
  - Polimorfismo: __str__ y __repr__ sobreescritos en cada clase.
"""

import re                           # Expresiones regulares para validar email
from abc import ABC, abstractmethod  # Soporte para clases abstractas
from datetime import date            # Manejo de fechas de nacimiento

from excepciones import InvalidDataError   # Excepción personalizada de datos
from logger import logger, log_operacion   # Logger centralizado y decorador


# ===========================================================================
# Clase Abstracta Base: EntidadBase
# ===========================================================================

class EntidadBase(ABC):
    """
    Clase abstracta raíz de todas las entidades del sistema Software FJ.

    Define el contrato mínimo que TODA entidad debe cumplir:
      - Tener un identificador único (id_entidad).
      - Implementar el método abstracto `describir()`.
      - Proveer representaciones textuales estándar (__str__ y __repr__).

    Herencia directa:
        Cliente → EntidadBase
        Servicio → EntidadBase  (ver servicios.py)

    Nota: No puede instanciarse directamente por ser abstracta.
    """

    # Contador de clase para generar IDs únicos y autoincremental
    _contador_global: int = 0

    def __init__(self, nombre: str) -> None:
        """
        Inicializa la entidad asignando un ID único autoincremental.

        Args:
            nombre (str): Nombre descriptivo de la entidad.

        Raises:
            InvalidDataError: Si el nombre es vacío o no es cadena de texto.
        """
        # Validación del nombre: debe ser string no vacío
        if not isinstance(nombre, str) or not nombre.strip():
            raise InvalidDataError(
                campo="nombre",
                valor=nombre,
                mensaje="El nombre de la entidad no puede estar vacío.",
            )

        # Incrementa el contador global y asigna el ID a esta instancia
        EntidadBase._contador_global += 1
        self.__id_entidad: int = EntidadBase._contador_global

        # Almacena el nombre limpio (sin espacios extra)
        self.__nombre: str = nombre.strip()

        # Registra la creación en el log
        logger.debug("Entidad creada: ID=%d, Nombre='%s'", self.__id_entidad, self.__nombre)

    # ------------------------------------------------------------------
    # Propiedades de solo lectura (no modificables desde fuera)
    # ------------------------------------------------------------------

    @property
    def id_entidad(self) -> int:
        """ID único autoincremental de la entidad (solo lectura)."""
        return self.__id_entidad

    @property
    def nombre(self) -> str:
        """Nombre de la entidad."""
        return self.__nombre

    @nombre.setter
    def nombre(self, nuevo_nombre: str) -> None:
        """
        Permite actualizar el nombre con validación.

        Args:
            nuevo_nombre (str): Nuevo nombre a asignar.

        Raises:
            InvalidDataError: Si el valor no es válido.
        """
        # Reutiliza la misma validación que en __init__
        if not isinstance(nuevo_nombre, str) or not nuevo_nombre.strip():
            raise InvalidDataError(
                campo="nombre",
                valor=nuevo_nombre,
                mensaje="El nombre no puede ser vacío o nulo.",
            )
        self.__nombre = nuevo_nombre.strip()

    # ------------------------------------------------------------------
    # Método abstracto: todas las subclases DEBEN implementarlo
    # ------------------------------------------------------------------

    @abstractmethod
    def describir(self) -> str:
        """
        Retorna una descripción textual completa de la entidad.

        Returns:
            str: Descripción legible para mostrar al usuario.
        """
        ...  # Las subclases proveen la implementación

    # ------------------------------------------------------------------
    # Representaciones estándar de Python
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        """Representación amigable para el usuario final."""
        return f"[{self.__class__.__name__}#{self.__id_entidad}] {self.__nombre}"

    def __repr__(self) -> str:
        """Representación técnica útil para debugging."""
        return (
            f"{self.__class__.__name__}("
            f"id={self.__id_entidad!r}, "
            f"nombre={self.__nombre!r})"
        )


# ===========================================================================
# Clase Cliente (hereda de EntidadBase)
# ===========================================================================

class Cliente(EntidadBase):
    """
    Representa a un cliente registrado en el sistema Software FJ.

    Aplica encapsulación ESTRICTA:
      - Todos los atributos son privados (prefijo doble __).
      - Solo accesibles/modificables a través de propiedades con validaciones.

    Valida:
      - Nombre: solo letras, espacios y acentos (mínimo 2 palabras).
      - Email: formato RFC 5322 simplificado.
      - Identificación: entero positivo.
      - Teléfono: dígitos, +, () y espacios, mínimo 7 dígitos.
      - Fecha de nacimiento: objeto date, mayor de 18 años.

    Ejemplo de uso:
        cliente = Cliente(
            nombre="Juan Pérez",
            email="juan@example.com",
            identificacion=12345678,
            telefono="+57 300 123 4567",
            fecha_nacimiento=date(1990, 6, 15),
        )
    """

    # Expresión regular para validar emails (simplificada pero robusta)
    _REGEX_EMAIL = re.compile(
        r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    )

    # Expresión regular para validar nombres (letras, espacios y acentos)
    _REGEX_NOMBRE = re.compile(
        r"^[a-zA-ZáéíóúÁÉÍÓÚüÜñÑ]+([\s\-][a-zA-ZáéíóúÁÉÍÓÚüÜñÑ]+)+$"
    )

    # Expresión regular para validar teléfonos
    _REGEX_TELEFONO = re.compile(r"^[\d\s\+\(\)\-]{7,20}$")

    def __init__(
        self,
        nombre: str,
        email: str,
        identificacion: int,
        telefono: str,
        fecha_nacimiento: date,
    ) -> None:
        """
        Constructor del Cliente con validación completa de todos los campos.

        Args:
            nombre           (str):  Nombre completo (mínimo 2 palabras).
            email            (str):  Dirección de correo electrónico válida.
            identificacion   (int):  Número de identificación positivo único.
            telefono         (str):  Número de teléfono con formato flexible.
            fecha_nacimiento (date): Fecha de nacimiento (mayor de 18 años).

        Raises:
            InvalidDataError: Si cualquier campo no supera la validación.
        """
        # Primero valida el nombre antes de llamar al padre
        # (el padre también valida, pero esta validación es más estricta)
        self._validar_nombre_completo(nombre)

        # Llama al constructor de EntidadBase (asigna ID y nombre base)
        super().__init__(nombre)

        # Asigna cada campo usando los setters (que incluyen validación)
        # El orden importa: primero se asignan los que no dependen de otros
        self.email = email                      # Usa el setter validado
        self.identificacion = identificacion    # Usa el setter validado
        self.telefono = telefono                # Usa el setter validado
        self.fecha_nacimiento = fecha_nacimiento  # Usa el setter validado

        # Registra la creación exitosa del cliente en el log
        logger.info(
            "Cliente registrado → ID=%d | Nombre='%s' | Email='%s'",
            self.id_entidad,
            self.nombre,
            self.__email,  # acceso directo al atributo privado dentro de la clase
        )

    # ------------------------------------------------------------------
    # Propiedad: email
    # ------------------------------------------------------------------

    @property
    def email(self) -> str:
        """Dirección de correo electrónico del cliente."""
        return self.__email

    @email.setter
    def email(self, valor: str) -> None:
        """
        Valida y asigna el email del cliente.

        Args:
            valor (str): Nuevo email a validar.

        Raises:
            InvalidDataError: Si el email no tiene formato válido.
        """
        # Verifica que sea un string
        if not isinstance(valor, str):
            raise InvalidDataError(
                campo="email",
                valor=valor,
                mensaje="El email debe ser una cadena de texto.",
            )
        # Limpia espacios y convierte a minúsculas
        valor_limpio = valor.strip().lower()

        # Verifica el formato con la expresión regular
        if not self._REGEX_EMAIL.match(valor_limpio):
            raise InvalidDataError(
                campo="email",
                valor=valor,
                mensaje=f"El email '{valor}' no tiene un formato válido.",
            )
        # Asigna al atributo privado
        self.__email: str = valor_limpio

    # ------------------------------------------------------------------
    # Propiedad: identificacion
    # ------------------------------------------------------------------

    @property
    def identificacion(self) -> int:
        """Número de identificación único del cliente."""
        return self.__identificacion

    @identificacion.setter
    def identificacion(self, valor: int) -> None:
        """
        Valida y asigna la identificación del cliente.

        Args:
            valor (int): Número de identificación positivo.

        Raises:
            InvalidDataError: Si el valor no es un entero positivo.
        """
        # Verifica que sea entero (int, no bool)
        if not isinstance(valor, int) or isinstance(valor, bool):
            raise InvalidDataError(
                campo="identificacion",
                valor=valor,
                mensaje="La identificación debe ser un número entero.",
            )
        # Verifica que sea positivo
        if valor <= 0:
            raise InvalidDataError(
                campo="identificacion",
                valor=valor,
                mensaje="La identificación debe ser un número positivo.",
            )
        self.__identificacion: int = valor

    # ------------------------------------------------------------------
    # Propiedad: telefono
    # ------------------------------------------------------------------

    @property
    def telefono(self) -> str:
        """Número de teléfono del cliente."""
        return self.__telefono

    @telefono.setter
    def telefono(self, valor: str) -> None:
        """
        Valida y asigna el teléfono del cliente.

        Args:
            valor (str): Número de teléfono con formato flexible.

        Raises:
            InvalidDataError: Si el formato no es válido.
        """
        if not isinstance(valor, str):
            raise InvalidDataError(
                campo="telefono",
                valor=valor,
                mensaje="El teléfono debe ser una cadena de texto.",
            )
        valor_limpio = valor.strip()
        if not self._REGEX_TELEFONO.match(valor_limpio):
            raise InvalidDataError(
                campo="telefono",
                valor=valor,
                mensaje=f"El teléfono '{valor}' no tiene un formato válido.",
            )
        self.__telefono: str = valor_limpio

    # ------------------------------------------------------------------
    # Propiedad: fecha_nacimiento
    # ------------------------------------------------------------------

    @property
    def fecha_nacimiento(self) -> date:
        """Fecha de nacimiento del cliente."""
        return self.__fecha_nacimiento

    @fecha_nacimiento.setter
    def fecha_nacimiento(self, valor: date) -> None:
        """
        Valida y asigna la fecha de nacimiento del cliente.

        Args:
            valor (date): Fecha de nacimiento. El cliente debe ser mayor de 18 años.

        Raises:
            InvalidDataError: Si el valor no es un objeto date o el cliente es menor.
        """
        # Verifica que sea un objeto date (pero no datetime, para ser estrictos)
        if not isinstance(valor, date):
            raise InvalidDataError(
                campo="fecha_nacimiento",
                valor=valor,
                mensaje="La fecha de nacimiento debe ser un objeto datetime.date.",
            )
        # Calcula la edad aproximada
        hoy = date.today()
        edad = (
            hoy.year - valor.year
            - ((hoy.month, hoy.day) < (valor.month, valor.day))
        )
        if edad < 18:
            raise InvalidDataError(
                campo="fecha_nacimiento",
                valor=str(valor),
                mensaje=f"El cliente debe ser mayor de 18 años. Edad calculada: {edad}.",
            )
        self.__fecha_nacimiento: date = valor

    # ------------------------------------------------------------------
    # Métodos de instancia
    # ------------------------------------------------------------------

    @staticmethod
    def _validar_nombre_completo(nombre: str) -> None:
        """
        Valida que el nombre tenga al menos 2 palabras y solo letras/acentos.

        Args:
            nombre (str): Nombre a validar.

        Raises:
            InvalidDataError: Si el nombre no cumple con las reglas.
        """
        if not isinstance(nombre, str) or not nombre.strip():
            raise InvalidDataError(
                campo="nombre",
                valor=nombre,
                mensaje="El nombre no puede estar vacío.",
            )
        # Verifica formato con regex
        if not Cliente._REGEX_NOMBRE.match(nombre.strip()):
            raise InvalidDataError(
                campo="nombre",
                valor=nombre,
                mensaje=(
                    "El nombre debe contener al menos 2 palabras "
                    "y solo letras (sin números ni símbolos)."
                ),
            )

    @log_operacion("Obtener ficha de cliente")
    def describir(self) -> str:
        """
        Retorna una ficha completa del cliente.

        Returns:
            str: Información formateada del cliente.
        """
        # Oculta parte del email por privacidad en la descripción pública
        partes_email = self.__email.split("@")
        email_ofuscado = partes_email[0][:3] + "***@" + partes_email[1]

        return (
            f"{'=' * 50}\n"
            f"  FICHA DE CLIENTE\n"
            f"{'=' * 50}\n"
            f"  ID Sistema    : {self.id_entidad}\n"
            f"  Nombre        : {self.nombre}\n"
            f"  Identificación: {self.__identificacion}\n"
            f"  Email         : {email_ofuscado}\n"
            f"  Teléfono      : {self.__telefono}\n"
            f"  Nacimiento    : {self.__fecha_nacimiento.strftime('%d/%m/%Y')}\n"
            f"{'=' * 50}"
        )

    def __eq__(self, other: object) -> bool:
        """Dos clientes son iguales si tienen la misma identificación."""
        if not isinstance(other, Cliente):
            return NotImplemented
        return self.__identificacion == other.__identificacion  # type: ignore[attr-defined]

    def __hash__(self) -> int:
        """Hash basado en la identificación para uso en sets y diccionarios."""
        return hash(self.__identificacion)
