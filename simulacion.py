"""
simulacion.py
=============
Modulo de Simulacion - Sistema Software FJ
Autor: Sarith Mulford
Fecha: 2026-05-13
Python: 3.12

Ejecuta 10 operaciones automaticas que demuestran TODAS las caracteristicas
del sistema:

  Op. 01 -> Registro de cliente VALIDO
  Op. 02 -> Registro de cliente INVALIDO (nombre sin apellido)
  Op. 03 -> Registro de cliente INVALIDO (email malformado)
  Op. 04 -> Registro de cliente INVALIDO (identificacion negativa)
  Op. 05 -> Creacion de servicio ReservaSala con parametros erroneos
  Op. 06 -> Creacion de servicios VALIDOS (Sala, Equipo, Asesoria)
  Op. 07 -> Reserva EXITOSA con confirmacion y calculo de costo
  Op. 08 -> Reserva FALLIDA (servicio ya ocupado)
  Op. 09 -> Cancelacion de una reserva existente
  Op. 10 -> Calculo de costo con sobrecarga (impuesto + descuento)

Principio clave: el sistema NUNCA se detiene ante un error.
Cada excepcion es capturada, logueada y la simulacion continua.
"""

import sys
import io

# Fuerza UTF-8 en consola Windows para evitar UnicodeEncodeError
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace"
    )

from datetime import date, datetime, timedelta   # Fechas para pruebas
from entidades import Cliente                    # Clase Cliente
from servicios import ReservaSala, AlquilerEquipo, AsesoriaEspecializada
from gestor import GestorSistema                 # Gestor central
from excepciones import (                        # Excepciones personalizadas
    InvalidDataError,
    ServiceUnavailableError,
    InconsistentCalculationError,
    InvalidReservationStateError,
)
from logger import logger, log_evento            # Logger centralizado


# ---------------------------------------------------------------------------
# Funcion auxiliar: imprime encabezado de operacion
# ---------------------------------------------------------------------------

def _encabezado(numero: int, titulo: str) -> None:
    """
    Imprime un encabezado formateado para cada operacion de la simulacion.

    Args:
        numero (int): Numero de la operacion (1-10).
        titulo (str): Descripcion breve de la operacion.
    """
    print(f"\n{'=' * 60}")
    print(f"  OPERACION {numero:02d}: {titulo}")
    print(f"{'=' * 60}")
    log_evento("info", "INICIO Operacion %02d: %s", numero, titulo)


def _resultado(exito: bool, mensaje: str) -> None:
    """
    Imprime el resultado de una operacion con indicador visual.

    Args:
        exito   (bool): True si la operacion fue exitosa.
        mensaje (str):  Descripcion del resultado.
    """
    # ASCII-safe: no usa emojis para evitar problemas de encoding en Windows
    icono = "[OK]" if exito else "[X]"
    print(f"  {icono} {mensaje}")
    nivel = "info" if exito else "warning"
    log_evento(nivel, "%s %s", "OK" if exito else "FALLO", mensaje)


# ---------------------------------------------------------------------------
# Funcion principal de simulacion
# ---------------------------------------------------------------------------

def ejecutar_simulacion() -> None:
    """
    Ejecuta las 10 operaciones automaticas de simulacion del sistema Software FJ.

    Demuestra:
        - Registros validos e invalidos de clientes.
        - Creacion de servicios con parametros erroneos y correctos.
        - Reservas exitosas y fallidas.
        - Confirmacion, cancelacion y ciclo de vida completo.
        - Sobrecarga de metodos con impuesto y descuento.
        - Captura de todas las excepciones con logging sin detener el sistema.
    """
    print("\n" + "=" * 60)
    print("   [>>] SIMULACION DEL SISTEMA SOFTWARE FJ")
    print("   Ejecutando 10 operaciones automaticas...")
    print("=" * 60)

    log_evento("info", "Inicio de simulacion del sistema Software FJ")

    # Instancia el gestor central (repositorio en memoria)
    gestor = GestorSistema()

    # Variables para reutilizar entre operaciones
    cliente_valido_1 = None      # Se asigna en Op. 01
    cliente_valido_2 = None      # Se asigna internamente en Op. 06
    sala_disponible = None       # Se asigna en Op. 06
    equipo_disponible = None     # Se asigna en Op. 06
    asesoria_disponible = None   # Se asigna en Op. 06
    reserva_1 = None             # Se asigna en Op. 07

    # ===================================================================
    # OPERACION 01: Registro de cliente VALIDO
    # ===================================================================
    _encabezado(1, "Registro de cliente VALIDO")
    try:
        cliente_valido_1 = Cliente(
            nombre="Maria Fernanda Gonzalez",
            email="maria.gonzalez@softwarefj.com",
            identificacion=10234567,
            telefono="+57 301 234 5678",
            fecha_nacimiento=date(1990, 3, 15),
        )
        gestor.registrar_cliente(cliente_valido_1)
        _resultado(True, f"Cliente registrado: {cliente_valido_1.nombre}")
        print(cliente_valido_1.describir())

    except InvalidDataError as e:
        _resultado(False, f"Error inesperado: {e}")

    # ===================================================================
    # OPERACION 02: Registro de cliente INVALIDO (nombre sin apellido)
    # ===================================================================
    _encabezado(2, "Registro de cliente INVALIDO -> nombre incompleto")
    try:
        cliente_invalido = Cliente(
            nombre="Carlos",                   # <- Solo 1 palabra: INVALIDO
            email="carlos@softwarefj.com",
            identificacion=20345678,
            telefono="300 987 6543",
            fecha_nacimiento=date(1985, 7, 22),
        )
        gestor.registrar_cliente(cliente_invalido)
        _resultado(True, "Cliente registrado (no deberia llegar aqui)")

    except InvalidDataError as e:
        # El sistema captura el error, lo loguea y CONTINUA
        _resultado(False, f"[Capturado correctamente] {e}")

    finally:
        # El bloque finally se ejecuta siempre, demostrando su uso
        print("  -> Operacion 02 finalizada (finally siempre se ejecuta)")

    # ===================================================================
    # OPERACION 03: Registro de cliente INVALIDO (email malformado)
    # ===================================================================
    _encabezado(3, "Registro de cliente INVALIDO -> email malformado")
    try:
        cliente_email_malo = Cliente(
            nombre="Luis Alberto Martinez",
            email="esto-no-es-un-email",       # <- Email sin @: INVALIDO
            identificacion=30456789,
            telefono="301 111 2222",
            fecha_nacimiento=date(1992, 11, 5),
        )
        gestor.registrar_cliente(cliente_email_malo)

    except InvalidDataError as e:
        _resultado(False, f"[Capturado correctamente] {e}")

    # ===================================================================
    # OPERACION 04: Registro de cliente INVALIDO (identificacion negativa)
    # ===================================================================
    _encabezado(4, "Registro de cliente INVALIDO -> identificacion negativa")
    try:
        cliente_id_malo = Cliente(
            nombre="Ana Maria Rodriguez",
            email="ana.rodriguez@softwarefj.com",
            identificacion=-9999,              # <- Negativo: INVALIDO
            telefono="+57 315 999 0000",
            fecha_nacimiento=date(1988, 4, 12),
        )
        gestor.registrar_cliente(cliente_id_malo)

    except InvalidDataError as e:
        _resultado(False, f"[Capturado correctamente] {e}")

    # ===================================================================
    # OPERACION 05: Creacion de servicio ReservaSala con parametros erroneos
    # ===================================================================
    _encabezado(5, "Creacion de ReservaSala con parametros ERRONEOS")

    # Caso A: precio negativo
    try:
        sala_mala_precio = ReservaSala(
            nombre="Sala Ejecutiva Premium",
            descripcion="Sala de reuniones de alta gama",
            precio_hora=-50_000.0,             # <- Precio negativo: INVALIDO
            duracion_horas=2.0,
            capacidad=10,
            numero_sala="A-101",
        )
    except InvalidDataError as e:
        _resultado(False, f"[A - precio negativo] {e}")

    # Caso B: duracion cero
    try:
        sala_mala_duracion = ReservaSala(
            nombre="Sala Coworking Norte",
            descripcion="Espacio de trabajo compartido",
            precio_hora=30_000.0,
            duracion_horas=0,                  # <- Duracion cero: INVALIDO
            capacidad=8,
            numero_sala="B-205",
        )
    except InvalidDataError as e:
        _resultado(False, f"[B - duracion cero] {e}")

    # Caso C: numero de sala vacio
    try:
        sala_mala_codigo = ReservaSala(
            nombre="Sala Innovacion",
            descripcion="Sala equipada con pizarron digital",
            precio_hora=45_000.0,
            duracion_horas=1.5,
            capacidad=6,
            numero_sala="",                    # <- Codigo vacio: INVALIDO
        )
    except InvalidDataError as e:
        _resultado(False, f"[C - numero de sala vacio] {e}")

    # ===================================================================
    # OPERACION 06: Creacion de servicios VALIDOS y segundo cliente
    # ===================================================================
    _encabezado(6, "Creacion de servicios VALIDOS y segundo cliente")
    try:
        # --- Registra un segundo cliente valido ---
        cliente_valido_2 = Cliente(
            nombre="Andres Felipe Ospina",
            email="andres.ospina@softwarefj.com",
            identificacion=40567890,
            telefono="+57 320 456 7890",
            fecha_nacimiento=date(1995, 8, 20),
        )
        gestor.registrar_cliente(cliente_valido_2)
        _resultado(True, f"Cliente 2 registrado: {cliente_valido_2.nombre}")

        # --- ReservaSala valida ---
        sala_disponible = ReservaSala(
            nombre="Sala Directivos A-301",
            descripcion="Sala de juntas con capacidad para directivos",
            precio_hora=80_000.0,
            duracion_horas=3.0,
            capacidad=12,
            numero_sala="A-301",
        )
        gestor.agregar_servicio(sala_disponible)
        _resultado(True, f"Sala creada: {sala_disponible.nombre}")
        print(sala_disponible.describir())

        # --- AlquilerEquipo valido ---
        equipo_disponible = AlquilerEquipo(
            nombre="Portatil HP EliteBook - Alquiler",
            descripcion="Portatil empresarial con software de diseno",
            precio_dia=35_000.0,
            tipo_equipo="Portatil",
            numero_serie="HP-EB-2024-007",
            dias_alquiler=5,
        )
        gestor.agregar_servicio(equipo_disponible)
        _resultado(True, f"Equipo creado: {equipo_disponible.nombre}")
        print(equipo_disponible.describir())

        # --- AsesoriaEspecializada valida ---
        asesoria_disponible = AsesoriaEspecializada(
            nombre="Asesoria en Ciberseguridad",
            descripcion="Consultoria en proteccion de datos y redes",
            precio_sesion=250_000.0,
            especialidad="Ciberseguridad",
            nombre_asesor="Ing. Roberto Vargas",
            sesiones=4,
        )
        gestor.agregar_servicio(asesoria_disponible)
        _resultado(True, f"Asesoria creada: {asesoria_disponible.nombre}")
        print(asesoria_disponible.describir())

    except (InvalidDataError, ServiceUnavailableError) as e:
        _resultado(False, f"Error inesperado en Op. 06: {e}")

    # ===================================================================
    # OPERACION 07: Reserva EXITOSA con confirmacion
    # ===================================================================
    _encabezado(7, "Reserva EXITOSA -> creacion + confirmacion")
    try:
        # La fecha de inicio debe ser futura
        fecha_inicio = datetime.now() + timedelta(days=2)

        # Crea la reserva con IVA del 19%
        reserva_1 = gestor.crear_reserva(
            cliente=cliente_valido_1,
            servicio=sala_disponible,
            fecha_inicio=fecha_inicio,
            notas="Reunion de directivos Q2 2026",
            impuesto=0.19,                     # <- Sobrecarga: aplica IVA 19%
        )
        _resultado(True, f"Reserva creada: {reserva_1}")

        # Confirma la reserva (calcula el costo con IVA)
        costo = gestor.confirmar_reserva(reserva_1.id_reserva)
        _resultado(
            True,
            f"Reserva #{reserva_1.id_reserva} CONFIRMADA -> Costo: ${costo:,.2f} COP"
        )
        print(reserva_1.describir())

    except (InvalidDataError, ServiceUnavailableError, InconsistentCalculationError) as e:
        _resultado(False, f"Error al crear/confirmar reserva: {e}")

    # ===================================================================
    # OPERACION 08: Reserva FALLIDA (servicio ya ocupado)
    # ===================================================================
    _encabezado(8, "Reserva FALLIDA -> servicio ya ocupado")
    try:
        fecha_inicio_2 = datetime.now() + timedelta(days=3)

        # Intenta reservar la MISMA sala que ya esta ocupada
        reserva_fallida = gestor.crear_reserva(
            cliente=cliente_valido_2,
            servicio=sala_disponible,          # <- Sala ocupada tras Op. 07
            fecha_inicio=fecha_inicio_2,
            notas="Intento de reserva sobre sala ocupada",
        )
        _resultado(True, "Reserva creada (no deberia llegar aqui)")

    except ServiceUnavailableError as e:
        # El sistema captura el error y CONTINUA sin detenerse
        _resultado(False, f"[Capturado correctamente] {e}")

    except InvalidDataError as e:
        _resultado(False, f"[Datos invalidos] {e}")

    # ===================================================================
    # OPERACION 09: Cancelacion de reserva existente
    # ===================================================================
    _encabezado(9, "Cancelacion de reserva existente")
    try:
        if reserva_1 is not None:
            gestor.cancelar_reserva(
                id_reserva=reserva_1.id_reserva,
                motivo="Cancelada por reorganizacion de agenda del cliente",
            )
            _resultado(
                True,
                f"Reserva #{reserva_1.id_reserva} cancelada. "
                f"Sala liberada: {sala_disponible.estado}"
            )

            # Intenta cancelar la MISMA reserva de nuevo (error esperado)
            print("\n  -> Intentando cancelar la misma reserva nuevamente...")
            gestor.cancelar_reserva(
                id_reserva=reserva_1.id_reserva,
                motivo="Segundo intento de cancelacion",
            )
            _resultado(True, "Segunda cancelacion (no deberia llegar aqui)")

        else:
            print("  [!] reserva_1 es None (Op. 07 fallo), saltando cancelacion.")

    except InvalidReservationStateError as e:
        # Error esperado: no se puede cancelar una reserva ya cancelada
        _resultado(False, f"[Capturado correctamente] {e}")

    # ===================================================================
    # OPERACION 10: Sobrecarga de calcular_costo con impuesto + descuento
    # ===================================================================
    _encabezado(10, "Sobrecarga de calcular_costo con impuesto + descuento")
    try:
        if equipo_disponible and asesoria_disponible:
            # --- Costo de equipo con IVA 19% y descuento 10% ---
            costo_equipo_base = equipo_disponible.calcular_costo()
            costo_equipo_iva = equipo_disponible.calcular_costo(impuesto=0.19)
            costo_equipo_desc = equipo_disponible.calcular_costo(descuento=0.10)
            costo_equipo_ambos = equipo_disponible.calcular_costo(
                impuesto=0.19,
                descuento=0.10,
            )
            print(f"\n  [EQUIPO] '{equipo_disponible.nombre}'")
            print(f"     Costo base              : ${costo_equipo_base:>12,.2f} COP")
            print(f"     Con IVA 19%             : ${costo_equipo_iva:>12,.2f} COP")
            print(f"     Con descuento 10%       : ${costo_equipo_desc:>12,.2f} COP")
            print(f"     Con IVA 19% + desc 10%  : ${costo_equipo_ambos:>12,.2f} COP")
            _resultado(True, "Sobrecarga de equipo calculada exitosamente")

            # --- Costo de asesoria senior con descuento ---
            costo_asesoria_junior = asesoria_disponible.calcular_costo()
            costo_asesoria_senior = asesoria_disponible.calcular_costo(
                asesor_senior=True,            # <- Recargo 20% por seniority
                impuesto=0.19,
                descuento=0.05,
            )
            print(f"\n  [ASESORIA] '{asesoria_disponible.nombre}'")
            print(f"     Costo asesor junior     : ${costo_asesoria_junior:>12,.2f} COP")
            print(f"     Costo asesor senior     : ${costo_asesoria_senior:>12,.2f} COP")
            print("     (senior = +20% base, +IVA 19%, -descuento 5%)")
            _resultado(True, "Sobrecarga de asesoria calculada exitosamente")

            # --- Prueba de error: impuesto fuera de rango ---
            print("\n  -> Probando impuesto invalido (2.5 en lugar de 0.25)...")
            try:
                costo_invalido = equipo_disponible.calcular_costo(impuesto=2.5)
            except InconsistentCalculationError as e:
                _resultado(False, f"[Capturado correctamente] {e}")

        else:
            print("  [!] Servicios no disponibles (Op. 06 fallo), saltando Op. 10.")

    except (InconsistentCalculationError, InvalidDataError) as e:
        _resultado(False, f"Error inesperado en sobrecarga: {e}")

    # ===================================================================
    # RESERVA BONUS: confirmada y completada para que el reporte muestre ingresos
    # La sala fue cancelada en Op.09 y quedo libre. Ahora hacemos una reserva
    # de equipo que se confirma y completa para mostrar ingresos reales.
    # ===================================================================
    if cliente_valido_2 and equipo_disponible and equipo_disponible.disponible:
        try:
            fecha_eq = datetime.now() + timedelta(days=5)
            reserva_2 = gestor.crear_reserva(
                cliente=cliente_valido_2,
                servicio=equipo_disponible,
                fecha_inicio=fecha_eq,
                notas="Alquiler de portatil para proyecto remoto",
                impuesto=0.19,
                descuento=0.05,
            )
            gestor.confirmar_reserva(reserva_2.id_reserva)
            gestor.completar_reserva(reserva_2.id_reserva)
            _resultado(True, f"Reserva bonus completada: {reserva_2}")
        except Exception as e:
            _resultado(False, f"Error en reserva bonus: {e}")

    # ===================================================================
    # REPORTE FINAL
    # ===================================================================
    print("\n" + "=" * 60)
    print("   [REPORTE] REPORTE FINAL DEL SISTEMA")
    print("=" * 60)
    print(gestor.generar_reporte())

    print("\n" + "=" * 60)
    print("   [OK] SIMULACION COMPLETADA - El sistema nunca se detuvo")
    print("   [LOG] Log guardado en: software_fj.log")
    print("=" * 60)

    log_evento("info", "Simulacion completada exitosamente. Todas las operaciones ejecutadas.")
