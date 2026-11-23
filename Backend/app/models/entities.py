import calendar
from datetime import date, time, datetime, timezone, timedelta
from typing import Optional, List
from decimal import Decimal

# Zona horaria oficial de Bolivia: UTC-4 (America/La_Paz)
TZ_BOLIVIA = timezone(timedelta(hours=-4))

def get_bolivia_now() -> datetime:
    return datetime.now(TZ_BOLIVIA)

def get_bolivia_date() -> date:
    return datetime.now(TZ_BOLIVIA).date()

def get_bolivia_time() -> time:
    return datetime.now(TZ_BOLIVIA).time().replace(microsecond=0)
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Date,
    Time,
    DateTime,
    Numeric,
    Text,
    ForeignKey,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column, foreign
from app.database.connection import Base


# Tabla intermedia ROLPERMISOS
class RolPermiso(Base):
    __tablename__ = "rolpermisos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rol_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("rol.id", ondelete="CASCADE"), nullable=False
    )
    permiso_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("permisos.id", ondelete="CASCADE"), nullable=False
    )


class Permiso(Base):
    __tablename__ = "permisos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    permisos: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Relación con roles
    roles = relationship("Rol", secondary="rolpermisos", back_populates="permisos")


class Rol(Base):
    __tablename__ = "rol"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rol: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    niveljerarquico: Mapped[int] = mapped_column(Integer, nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relaciones
    permisos = relationship(
        "Permiso", secondary="rolpermisos", back_populates="roles", lazy="joined"
    )
    usuarios = relationship("Usuario", back_populates="rol")


class Area(Base):
    __tablename__ = "area"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    estado: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relaciones
    trabajadores = relationship("Trabajador", back_populates="area")


class Usuario(Base):
    __tablename__ = "usuario"

    ci: Mapped[str] = mapped_column(String(30), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    genero: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    contraseña: Mapped[str] = mapped_column(String(255), nullable=False)
    fechanacimiento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(25), nullable=True)
    direccion: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    foto: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estado: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rol_id: Mapped[int] = mapped_column(Integer, ForeignKey("rol.id"), nullable=False)

    # Relaciones
    rol = relationship("Rol", back_populates="usuarios", lazy="joined")
    trabajador = relationship(
        "Trabajador",
        primaryjoin="Usuario.ci == foreign(Trabajador.ci)",
        back_populates="usuario",
        uselist=False,
    )
    bitacoras = relationship("Bitacora", back_populates="usuario", cascade="all, delete-orphan")


class Trabajador(Base):
    __tablename__ = "trabajador"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ci: Mapped[Optional[str]] = mapped_column(String(30), unique=True, nullable=True)
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    fotografia: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    celular: Mapped[Optional[str]] = mapped_column(String(25), nullable=True)
    fecha_ingreso: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    cargo: Mapped[str] = mapped_column(String(100), nullable=False)
    sueldoBase: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    estado: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # True: Activo, False: Inactivo
    fecha_inactividad: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    area_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("area.id", ondelete="SET NULL"), nullable=True
    )

    # Relaciones
    usuario = relationship(
        "Usuario",
        primaryjoin="Usuario.ci == foreign(Trabajador.ci)",
        back_populates="trabajador",
        uselist=False,
    )
    area = relationship("Area", back_populates="trabajadores", lazy="joined")
    contactos_emergencia = relationship(
        "ContactoEmergencia",
        back_populates="trabajador",
        cascade="all, delete-orphan",
        lazy="joined",
    )
    anticipos = relationship(
        "Anticipo",
        back_populates="trabajador",
        cascade="all, delete-orphan",
    )
    anticipos_rider = relationship(
        "AnticipoRider",
        back_populates="trabajador",
        cascade="all, delete-orphan",
    )
    liquidaciones = relationship(
        "Liquidacion",
        back_populates="trabajador",
        cascade="all, delete-orphan",
    )
    descuentos = relationship(
        "Descuento",
        back_populates="trabajador",
        cascade="all, delete-orphan",
    )


class ContactoEmergencia(Base):
    __tablename__ = "contactoemergencia"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombrecompleto: Mapped[str] = mapped_column(String(150), nullable=False)
    parentesco: Mapped[str] = mapped_column(String(50), nullable=False)
    celular: Mapped[str] = mapped_column(String(25), nullable=False)
    trabajador_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trabajador.id", ondelete="CASCADE"), nullable=False
    )

    # Relación
    trabajador = relationship("Trabajador", back_populates="contactos_emergencia")


class Bitacora(Base):
    __tablename__ = "bitacora"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fecha: Mapped[date] = mapped_column(Date, default=get_bolivia_date, nullable=False, index=True)
    hora: Mapped[time] = mapped_column(
        Time, default=get_bolivia_time, nullable=False
    )
    modulo: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    accion: Mapped[str] = mapped_column(String(50), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    usuario_ci: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("usuario.ci", ondelete="SET NULL"), nullable=True, index=True
    )

    # Relación
    usuario = relationship("Usuario", back_populates="bitacoras")


# =========================================================================
# MÓDULO DE PAGOS Y ANTICIPOS
# =========================================================================

class PeriodoSalarial(Base):
    __tablename__ = "periodo_salarial"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..12
    anio: Mapped[int] = mapped_column(Integer, nullable=False)  # e.g. 2026
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_pago_estimada: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="ABIERTO", nullable=False)  # ABIERTO, CERRADO
    descripcion: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "Septiembre 2026"

    # Relaciones
    anticipos = relationship("Anticipo", back_populates="periodo")
    anticipos_rider = relationship("AnticipoRider", back_populates="periodo")
    liquidaciones = relationship("Liquidacion", back_populates="periodo")
    descuentos = relationship("Descuento", back_populates="periodo")
    detalles_planilla = relationship("PlanillaDetalle", back_populates="periodo", cascade="all, delete-orphan")
    cierre = relationship("PlanillaCierre", back_populates="periodo", uselist=False, cascade="all, delete-orphan")

    @property
    def fecha_limite_pago(self) -> date:
        """Fin del mes siguiente al período para permitir ventana de tolerancia en liquidación de sueldos."""
        mes_sig = 1 if self.mes == 12 else self.mes + 1
        anio_sig = self.anio + 1 if self.mes == 12 else self.anio
        ultimo_dia = calendar.monthrange(anio_sig, mes_sig)[1]
        return date(anio_sig, mes_sig, ultimo_dia)


class PlanillaCierre(Base):
    __tablename__ = "planilla_cierre"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    periodo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("periodo_salarial.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    entregado_quincena: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    solicitud_quincena: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    diferencia_quincena: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)

    entregado_sueldo: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    solicitud_sueldo: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    diferencia_sueldo: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)

    otros_gastos: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    otros_gastos_detalle: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    total_diferencia: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    usuario_ci: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    usuario_nombre: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    fecha_cierre: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    periodo = relationship("PeriodoSalarial", back_populates="cierre")


class Anticipo(Base):
    __tablename__ = "anticipo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero_comprobante: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    trabajador_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trabajador.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    periodo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("periodo_salarial.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    fecha_solicitud: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    fecha_entrega: Mapped[date] = mapped_column(Date, default=date.today, nullable=False, index=True)
    importe: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    metodo_pago: Mapped[str] = mapped_column(String(50), default="EFECTIVO", nullable=False)
    es_periodo_siguiente: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    estado: Mapped[str] = mapped_column(
        String(30), default="PAGADO", nullable=False, index=True
    )  # SOLICITADO, AUTORIZADO, PAGADO, RECHAZADO, ANULADO
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    motivo_anulacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    usuario_id: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("usuario.ci", ondelete="SET NULL"), nullable=True, index=True
    )

    # Relaciones
    trabajador = relationship("Trabajador", back_populates="anticipos", lazy="joined")
    periodo = relationship("PeriodoSalarial", back_populates="anticipos", lazy="joined")
    usuario = relationship("Usuario", lazy="joined")

    @property
    def usuario_nombre(self) -> Optional[str]:
        if self.usuario:
            return f"{self.usuario.nombre} {self.usuario.apellido}".strip()
        return None


class AnticipoRider(Base):
    __tablename__ = "anticipo_rider"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero_comprobante: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    trabajador_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trabajador.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    periodo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("periodo_salarial.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    fecha_solicitud: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    fecha_entrega: Mapped[date] = mapped_column(Date, default=date.today, nullable=False, index=True)
    importe: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    metodo_pago: Mapped[str] = mapped_column(String(50), default="EFECTIVO", nullable=False)
    es_periodo_siguiente: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    estado: Mapped[str] = mapped_column(
        String(30), default="PAGADO", nullable=False, index=True
    )  # PAGADO, ANULADO
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    motivo_anulacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    usuario_id: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("usuario.ci", ondelete="SET NULL"), nullable=True, index=True
    )

    # Relaciones
    trabajador = relationship("Trabajador", back_populates="anticipos_rider", lazy="joined")
    periodo = relationship("PeriodoSalarial", back_populates="anticipos_rider", lazy="joined")
    usuario = relationship("Usuario", lazy="joined")

    @property
    def usuario_nombre(self) -> Optional[str]:
        if self.usuario:
            return f"{self.usuario.nombre} {self.usuario.apellido}".strip()
        return None


class Descuento(Base):
    __tablename__ = "descuento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero_comprobante: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    trabajador_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trabajador.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    periodo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("periodo_salarial.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    fecha: Mapped[date] = mapped_column(Date, default=date.today, nullable=False, index=True)
    importe: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    concepto: Mapped[str] = mapped_column(String(150), nullable=False)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(
        String(30), default="CONFIRMADO", nullable=False, index=True
    )  # CONFIRMADO, ANULADO
    motivo_anulacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    usuario_id: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("usuario.ci", ondelete="SET NULL"), nullable=True, index=True
    )
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    trabajador = relationship("Trabajador", back_populates="descuentos", lazy="joined")
    periodo = relationship("PeriodoSalarial", back_populates="descuentos", lazy="joined")
    usuario = relationship("Usuario", lazy="joined")

    @property
    def usuario_nombre(self) -> Optional[str]:
        if self.usuario:
            return f"{self.usuario.nombre} {self.usuario.apellido}".strip()
        return None


class PlanillaDetalle(Base):
    __tablename__ = "planilla_detalle"
    __table_args__ = (
        UniqueConstraint("periodo_id", "trabajador_id", name="uq_planilla_periodo_trabajador"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    periodo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("periodo_salarial.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trabajador_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trabajador.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    haber_basico: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    dias_trabajados: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    dias_manual: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    total_ganado: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relaciones
    periodo = relationship("PeriodoSalarial", back_populates="detalles_planilla")
    trabajador = relationship("Trabajador", lazy="joined")
class Liquidacion(Base):
    __tablename__ = "liquidacion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero_comprobante: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    trabajador_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trabajador.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    periodo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("periodo_salarial.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    fecha_liquidacion: Mapped[date] = mapped_column(Date, default=date.today, nullable=False, index=True)
    sueldo_base: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    ajustes: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    total_anticipos: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=0.00, nullable=False
    )  # Anticipos descontables aplicados
    monto_neto: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )  # sueldo_base + ajustes - total_anticipos
    monto_pagado: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=0.00, nullable=False
    )  # Suma de pagos realizados
    saldo_pendiente: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )  # monto_neto - monto_pagado
    estado: Mapped[str] = mapped_column(
        String(30), default="PENDIENTE", nullable=False, index=True
    )  # PENDIENTE, PARCIAL, LIQUIDADO, ANULADO
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    motivo_anulacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    usuario_id: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("usuario.ci", ondelete="SET NULL"), nullable=True, index=True
    )

    # Relaciones
    trabajador = relationship("Trabajador", back_populates="liquidaciones", lazy="joined")
    periodo = relationship("PeriodoSalarial", back_populates="liquidaciones", lazy="joined")
    pagos = relationship(
        "PagoLiquidacion",
        back_populates="liquidacion",
        cascade="all, delete-orphan",
        lazy="joined",
    )
    usuario = relationship("Usuario", lazy="joined")

    @property
    def usuario_nombre(self) -> Optional[str]:
        if self.usuario:
            return f"{self.usuario.nombre} {self.usuario.apellido}".strip()
        return None
class PagoLiquidacion(Base):
    __tablename__ = "pago_liquidacion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero_comprobante: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    liquidacion_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("liquidacion.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fecha_pago: Mapped[date] = mapped_column(Date, default=date.today, nullable=False, index=True)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tipo_pago: Mapped[str] = mapped_column(String(50), default="PAGO_PARCIAL", nullable=False, index=True)  # PAGO_QUINCENA, PAGO_PARCIAL, LIQUIDACION_FINAL, REVISION_QUINCENA
    metodo_pago: Mapped[str] = mapped_column(String(50), default="EFECTIVO", nullable=False)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(
        String(30), default="CONFIRMADO", nullable=False, index=True
    )  # CONFIRMADO, ANULADO
    motivo_anulacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    usuario_id: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("usuario.ci", ondelete="SET NULL"), nullable=True
    )

    # Relaciones
    liquidacion = relationship("Liquidacion", back_populates="pagos")
    usuario = relationship("Usuario", lazy="joined")

    @property
    def usuario_nombre(self) -> Optional[str]:
        if self.usuario:
            return f"{self.usuario.nombre} {self.usuario.apellido}".strip()
        return None


# =========================================================================
# MÓDULO DE INVENTARIO: ALMACÉN Y GASTOS MENORES
# =========================================================================

class Almacen(Base):
    __tablename__ = "almacen"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    foto: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    unidad_control: Mapped[str] = mapped_column(String(50), nullable=False)  # Litros, Kilogramos, Gramos, Unidades, Metros, etc.
    stock_actual: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    stock_minimo: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    precio_ultima_compra: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    precio_anterior_compra: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), default=None, nullable=True)
    fecha_ultima_compra: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    usuario_registro_ci: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("usuario.ci", ondelete="SET NULL"), nullable=True
    )
    estado: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relaciones
    usuario_registro = relationship("Usuario", lazy="joined")
    compras = relationship("CompraAlmacen", back_populates="producto", cascade="all, delete-orphan", order_by="desc(CompraAlmacen.id)")
    movimientos = relationship("MovimientoAlmacen", back_populates="producto", cascade="all, delete-orphan", order_by="desc(MovimientoAlmacen.id)")

    @property
    def usuario_registro_nombre(self) -> Optional[str]:
        if self.usuario_registro:
            return f"{self.usuario_registro.nombre} {self.usuario_registro.apellido}".strip()
        return None

    @property
    def estado_stock(self) -> str:
        if self.stock_actual <= 0:
            return "Agotado"
        if self.stock_actual <= self.stock_minimo:
            return "Stock bajo"
        return "Normal"

    @property
    def precio_anterior(self) -> Optional[Decimal]:
        return self.precio_anterior_compra

    @property
    def variacion_porcentual(self) -> Optional[Decimal]:
        if self.precio_anterior_compra and self.precio_anterior_compra > 0:
            var = ((self.precio_ultima_compra - self.precio_anterior_compra) / self.precio_anterior_compra) * Decimal("100.00")
            return round(var, 2)
        return None


class CompraAlmacen(Base):
    __tablename__ = "compra_almacen"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero_comprobante: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    almacen_id: Mapped[int] = mapped_column(Integer, ForeignKey("almacen.id", ondelete="RESTRICT"), nullable=False, index=True)
    cantidad_comprada: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    unidad_compra: Mapped[str] = mapped_column(String(50), nullable=False)  # Saco, Caja, Litro, etc.
    equivalencia_unidad: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("1.00"), nullable=False)
    cantidad_en_unidad_control: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    precio_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    precio_unitario_anterior: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    variacion_porcentual: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    fecha_compra: Mapped[date] = mapped_column(Date, default=date.today, nullable=False, index=True)
    proveedor: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    numero_factura: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    usuario_registro_ci: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("usuario.ci", ondelete="SET NULL"), nullable=True, index=True
    )
    estado: Mapped[str] = mapped_column(String(30), default="COMPLETADO", nullable=False, index=True)  # COMPLETADO, ANULADO
    motivo_anulacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    producto = relationship("Almacen", back_populates="compras")
    usuario_registro = relationship("Usuario", lazy="joined")
    movimientos = relationship("MovimientoAlmacen", back_populates="compra")

    @property
    def usuario_registro_nombre(self) -> Optional[str]:
        if self.usuario_registro:
            return f"{self.usuario_registro.nombre} {self.usuario_registro.apellido}".strip()
        return None


class MovimientoAlmacen(Base):
    __tablename__ = "movimiento_almacen"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero_comprobante: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    almacen_id: Mapped[int] = mapped_column(Integer, ForeignKey("almacen.id", ondelete="RESTRICT"), nullable=False, index=True)
    compra_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("compra_almacen.id", ondelete="SET NULL"), nullable=True, index=True
    )
    movimiento_original_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("movimiento_almacen.id", ondelete="SET NULL"), nullable=True
    )
    trabajador_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("trabajador.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    area_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("area.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    vehiculo_maquinaria: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    usuario_registro_ci: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("usuario.ci", ondelete="SET NULL"), nullable=True, index=True
    )
    tipo_movimiento: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True
    )  # ENTRADA_COMPRA, SALIDA_ENTREGA, DEVOLUCION, AJUSTE_POSITIVO, AJUSTE_NEGATIVO, REVERSION_ANULACION
    cantidad: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    cantidad_entrada: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    cantidad_salida: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    stock_anterior: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    stock_resultante: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fecha_movimiento: Mapped[date] = mapped_column(Date, default=get_bolivia_date, nullable=False, index=True)
    hora_movimiento: Mapped[time] = mapped_column(Time, default=get_bolivia_time, nullable=False)
    estado: Mapped[str] = mapped_column(String(30), default="CONFIRMADO", nullable=False, index=True)  # CONFIRMADO, ANULADO, REVERTIDO
    motivo_anulacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    producto = relationship("Almacen", back_populates="movimientos")
    compra = relationship("CompraAlmacen", back_populates="movimientos")
    trabajador = relationship("Trabajador", lazy="joined")
    area = relationship("Area", lazy="joined")
    usuario_registro = relationship("Usuario", lazy="joined")
    movimiento_original = relationship("MovimientoAlmacen", remote_side=[id])

    @property
    def usuario_registro_nombre(self) -> Optional[str]:
        if self.usuario_registro:
            return f"{self.usuario_registro.nombre} {self.usuario_registro.apellido}".strip()
        return None

    @property
    def trabajador_nombre(self) -> Optional[str]:
        if self.trabajador:
            return f"{self.trabajador.nombres} {self.trabajador.apellidos}".strip()
        return None

    @property
    def area_nombre(self) -> Optional[str]:
        if self.area:
            return self.area.nombre
        return None


class GastoMenor(Base):
    __tablename__ = "gasto_menor"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero_comprobante: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    foto_comprobante: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    importe_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    fecha_gasto: Mapped[date] = mapped_column(Date, default=date.today, nullable=False, index=True)
    area_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("area.id", ondelete="SET NULL"), nullable=True, index=True
    )
    trabajador_responsable_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("trabajador.id", ondelete="SET NULL"), nullable=True, index=True
    )
    metodo_pago: Mapped[str] = mapped_column(String(50), default="EFECTIVO", nullable=False)  # EFECTIVO, TRANSFERENCIA, CHEQUE, OTRO
    proveedor: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    numero_comprobante_fiscal: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    usuario_registro_ci: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("usuario.ci", ondelete="SET NULL"), nullable=True, index=True
    )
    estado: Mapped[str] = mapped_column(String(30), default="REGISTRADO", nullable=False, index=True)  # REGISTRADO, ANULADO, CORREGIDO
    motivo_anulacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relaciones
    area = relationship("Area", lazy="joined")
    trabajador_responsable = relationship("Trabajador", lazy="joined")
    usuario_registro = relationship("Usuario", lazy="joined")

    @property
    def usuario_registro_nombre(self) -> Optional[str]:
        if self.usuario_registro:
            return f"{self.usuario_registro.nombre} {self.usuario_registro.apellido}".strip()
        return None

    @property
    def trabajador_nombre(self) -> Optional[str]:
        if self.trabajador_responsable:
            return f"{self.trabajador_responsable.nombres} {self.trabajador_responsable.apellidos}".strip()
        return None

    @property
    def area_nombre(self) -> Optional[str]:
        if self.area:
            return self.area.nombre
        return None


# =========================================================================
# MÓDULO DE GANADERÍA (SPEC-001 — REGISTRO E IDENTIFICACIÓN DEL GANADO)
# =========================================================================

class Animal(Base):
    __tablename__ = "animal"
    __table_args__ = (
        UniqueConstraint("numero_arete", name="uq_animal_numero_arete"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_interno: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    numero_arete: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    nombre: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tipo: Mapped[str] = mapped_column(String(50), default="Bovino", nullable=False, index=True)
    raza: Mapped[str] = mapped_column(String(100), default="Nelore", nullable=False, index=True)
    sexo: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # MACHO, HEMBRA
    fecha_nacimiento: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    peso_inicial: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    peso_actual: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    fecha_ultimo_pesaje: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    estado: Mapped[str] = mapped_column(String(30), default="ACTIVO", nullable=False, index=True)  # ACTIVO, VENDIDO, FALLECIDO, ROBADO, PERDIDO, SACRIFICADO, DESCARTADO, BAJA
    procedencia: Mapped[str] = mapped_column(String(40), default="REGISTRO_MANUAL", nullable=False, index=True)  # REGISTRO_MANUAL, NACIMIENTO, COMPRA
    madre_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("animal.id", ondelete="SET NULL"), nullable=True, index=True
    )
    padre_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("animal.id", ondelete="SET NULL"), nullable=True, index=True
    )
    potrero_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("potrero.id", ondelete="SET NULL"), nullable=True, index=True
    )
    ubicacion: Mapped[str] = mapped_column(String(100), default="Potrero 1", nullable=False, index=True)
    propietario: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    usuario_registro_ci: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("usuario.ci", ondelete="SET NULL"), nullable=True, index=True
    )
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=get_bolivia_now, nullable=False)
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime, default=get_bolivia_now, onupdate=get_bolivia_now, nullable=False
    )

    # Relaciones
    madre = relationship("Animal", foreign_keys=[madre_id], remote_side=[id], lazy="selectin")
    padre = relationship("Animal", foreign_keys=[padre_id], remote_side=[id], lazy="selectin")
    potrero = relationship("Potrero", foreign_keys=[potrero_id], back_populates="animales", lazy="selectin")
    usuario_registro = relationship("Usuario", foreign_keys=[usuario_registro_ci], lazy="selectin")
    pesajes = relationship("PesajeGanado", back_populates="animal", cascade="all, delete-orphan", order_by="desc(PesajeGanado.fecha_pesaje)")
    historial_aretes = relationship("HistorialArete", back_populates="animal", cascade="all, delete-orphan", order_by="desc(HistorialArete.fecha_cambio)")


class PesajeGanado(Base):
    __tablename__ = "pesaje_ganado"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    animal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("animal.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fecha_pesaje: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    peso: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    variacion_anterior: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    responsable: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    usuario_ci: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("usuario.ci", ondelete="SET NULL"), nullable=True, index=True
    )
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=get_bolivia_now, nullable=False)

    # Relaciones
    animal = relationship("Animal", back_populates="pesajes")
    usuario = relationship("Usuario", lazy="joined")


class HistorialArete(Base):
    __tablename__ = "historial_arete"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    animal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("animal.id", ondelete="CASCADE"), nullable=False, index=True
    )
    arete_anterior: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    arete_nuevo: Mapped[str] = mapped_column(String(50), nullable=False)
    fecha_cambio: Mapped[date] = mapped_column(Date, default=get_bolivia_date, nullable=False, index=True)
    motivo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    usuario_ci: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("usuario.ci", ondelete="SET NULL"), nullable=True, index=True
    )
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=get_bolivia_now, nullable=False)

    # Relaciones
    animal = relationship("Animal", back_populates="historial_aretes")
    usuario = relationship("Usuario", lazy="joined")


class NacimientoGanado(Base):
    __tablename__ = "nacimiento_ganado"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero_comprobante: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    madre_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("animal.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    padre_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("animal.id", ondelete="SET NULL"), nullable=True, index=True
    )
    cria_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("animal.id", ondelete="SET NULL"), nullable=True, index=True
    )
    fecha_nacimiento: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    sexo_cria: Mapped[str] = mapped_column(String(20), nullable=False)
    peso_nacimiento: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    tipo_parto: Mapped[str] = mapped_column(String(40), default="UNICO", nullable=False)  # UNICO, GEMELAR, DISTOCICO
    estado_nacimiento: Mapped[str] = mapped_column(String(30), default="VIVO", nullable=False)  # VIVO, MUERTO_AL_NACER
    numero_arete_cria: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tipo_animal: Mapped[str] = mapped_column(String(50), default="Bovino", nullable=False)
    raza_cria: Mapped[str] = mapped_column(String(100), default="Nelore", nullable=False)
    ubicacion: Mapped[str] = mapped_column(String(100), nullable=False)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    usuario_ci: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("usuario.ci", ondelete="SET NULL"), nullable=True, index=True
    )
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=get_bolivia_now, nullable=False)

    # Relaciones
    madre = relationship("Animal", foreign_keys=[madre_id], lazy="selectin")
    padre = relationship("Animal", foreign_keys=[padre_id], lazy="selectin")
    cria = relationship("Animal", foreign_keys=[cria_id], lazy="selectin")
    usuario = relationship("Usuario", lazy="selectin")


class CompraGanado(Base):
    __tablename__ = "compra_ganado"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero_comprobante: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    proveedor: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    fecha_compra: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    documento_referencia: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    costos_adicionales: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    transporte: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    monto_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(30), default="CONFIRMADO", nullable=False, index=True)  # CONFIRMADO, ANULADO
    motivo_anulacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    usuario_ci: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("usuario.ci", ondelete="SET NULL"), nullable=True, index=True
    )
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=get_bolivia_now, nullable=False)

    # Relaciones
    detalles = relationship("CompraGanadoDetalle", back_populates="compra", cascade="all, delete-orphan", lazy="joined")
    usuario = relationship("Usuario", lazy="joined")


class CompraGanadoDetalle(Base):
    __tablename__ = "compra_ganado_detalle"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    compra_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("compra_ganado.id", ondelete="CASCADE"), nullable=False, index=True
    )
    animal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("animal.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    modalidad_precio: Mapped[str] = mapped_column(String(30), default="POR_ANIMAL", nullable=False)  # POR_ANIMAL, POR_KG
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    peso_compra: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    costo_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    # Relaciones
    compra = relationship("CompraGanado", back_populates="detalles")
    animal = relationship("Animal", lazy="selectin")


class VentaGanado(Base):
    __tablename__ = "venta_ganado"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero_comprobante: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    cliente: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    fecha_venta: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    modalidad_venta: Mapped[str] = mapped_column(String(30), default="POR_ANIMAL", nullable=False)  # POR_ANIMAL, POR_KG
    metodo_pago: Mapped[str] = mapped_column(String(50), default="EFECTIVO", nullable=False)
    transporte: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    descuentos: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    monto_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    documento_referencia: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(30), default="CONFIRMADO", nullable=False, index=True)  # CONFIRMADO, ANULADO
    motivo_anulacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    usuario_ci: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("usuario.ci", ondelete="SET NULL"), nullable=True, index=True
    )
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=get_bolivia_now, nullable=False)

    # Relaciones
    detalles = relationship("VentaGanadoDetalle", back_populates="venta", cascade="all, delete-orphan", lazy="joined")
    usuario = relationship("Usuario", lazy="joined")


class VentaGanadoDetalle(Base):
    __tablename__ = "venta_ganado_detalle"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    venta_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("venta_ganado.id", ondelete="CASCADE"), nullable=False, index=True
    )
    animal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("animal.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    numero_arete: Mapped[str] = mapped_column(String(50), nullable=False)  # Arete capturado al vender
    modalidad_precio: Mapped[str] = mapped_column(String(30), default="POR_ANIMAL", nullable=False)
    peso_venta: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    # Relaciones
    venta = relationship("VentaGanado", back_populates="detalles")
    animal = relationship("Animal", lazy="selectin")


class BajaGanado(Base):
    __tablename__ = "baja_ganado"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero_comprobante: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    animal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("animal.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    numero_arete: Mapped[str] = mapped_column(String(50), nullable=False)  # Arete capturado al dar de baja
    fecha_baja: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    motivo: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # FALLECIMIENTO, ROBO, PERDIDA, SACRIFICIO, DESCARTE, OTRO
    estado_animal_resultante: Mapped[str] = mapped_column(String(30), nullable=False)
    responsable: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    documento_adjunto: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(30), default="CONFIRMADO", nullable=False, index=True)  # CONFIRMADO, ANULADO
    motivo_anulacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    usuario_ci: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("usuario.ci", ondelete="SET NULL"), nullable=True, index=True
    )
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=get_bolivia_now, nullable=False)

    # Relaciones
    animal = relationship("Animal", lazy="selectin")
    usuario = relationship("Usuario", lazy="selectin")


class Potrero(Base):
    __tablename__ = "potrero"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    tipo_area: Mapped[str] = mapped_column(String(40), default="POTRERO", nullable=False, index=True)  # POTRERO, CORRAL, CUARENTENA, MATERNIDAD, OTRO
    superficie_ha: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    capacidad_cabezas: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    color_hex: Mapped[str] = mapped_column(String(20), default="#10b981", nullable=False)
    poligono_geojson: Mapped[str] = mapped_column(Text, nullable=False)
    centroide_lat: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6), nullable=True)
    centroide_lng: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), default="ACTIVO", nullable=False, index=True)  # ACTIVO, INACTIVO
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    usuario_registro_ci: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("usuario.ci", ondelete="SET NULL"), nullable=True, index=True
    )
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=get_bolivia_now, nullable=False)
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime, default=get_bolivia_now, onupdate=get_bolivia_now, nullable=False
    )

    # Relaciones
    usuario_registro = relationship("Usuario", lazy="selectin")
    animales = relationship("Animal", back_populates="potrero", foreign_keys="Animal.potrero_id")


class MovimientoGanado(Base):
    __tablename__ = "movimiento_ganado"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero_comprobante: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    fecha_movimiento: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    potrero_origen_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("potrero.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    potrero_destino_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("potrero.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    tipo_operacion: Mapped[str] = mapped_column(String(30), default="MANUAL", nullable=False)  # ARRASTRE_MAPA, MANUAL_INDIVIDUAL, MANUAL_GRUPAL
    cantidad_animales: Mapped[int] = mapped_column(Integer, nullable=False)
    motivo: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    responsable: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), default="CONFIRMADO", nullable=False, index=True)  # CONFIRMADO, ANULADO
    motivo_anulacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    usuario_ci: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("usuario.ci", ondelete="SET NULL"), nullable=True, index=True
    )
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=get_bolivia_now, nullable=False)

    # Relaciones
    potrero_origen = relationship("Potrero", foreign_keys=[potrero_origen_id], lazy="selectin")
    potrero_destino = relationship("Potrero", foreign_keys=[potrero_destino_id], lazy="selectin")
    usuario = relationship("Usuario", lazy="selectin")
    detalles = relationship("MovimientoGanadoDetalle", back_populates="movimiento", cascade="all, delete-orphan", lazy="selectin")


class MovimientoGanadoDetalle(Base):
    __tablename__ = "movimiento_ganado_detalle"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    movimiento_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("movimiento_ganado.id", ondelete="CASCADE"), nullable=False, index=True
    )
    animal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("animal.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    numero_arete: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    codigo_interno: Mapped[str] = mapped_column(String(50), nullable=False)
    potrero_origen_id: Mapped[int] = mapped_column(Integer, nullable=False)
    potrero_destino_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relaciones
    movimiento = relationship("MovimientoGanado", back_populates="detalles")
    animal = relationship("Animal", lazy="selectin")


# =========================================================================
# MÓDULO DE GANADERÍA (SPEC-003 — SANIDAD, TRATAMIENTOS Y VACUNACIÓN)
# =========================================================================

class SanidadVacuna(Base):
    __tablename__ = "sanidad_vacuna"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    nombre_comercial: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    enfermedad_objetivo: Mapped[str] = mapped_column(String(150), nullable=False)
    especie: Mapped[str] = mapped_column(String(50), default="BOVINO", nullable=False)
    dosis_defecto_ml: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    via_administracion: Mapped[str] = mapped_column(String(50), default="SUBCUTANEA", nullable=False)
    dias_retiro_carne: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dias_retiro_leche: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requiere_refuerzo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dias_refuerzo: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), default="ACTIVO", nullable=False, index=True)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=get_bolivia_now, nullable=False)


class SanidadMedicamento(Base):
    __tablename__ = "sanidad_medicamento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    nombre_comercial: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tipo_farmaco: Mapped[str] = mapped_column(String(50), default="ANTIBIOTICO", nullable=False, index=True)
    principio_activo: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    concentracion: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    unidad_medida: Mapped[str] = mapped_column(String(20), default="ML", nullable=False)
    via_administracion: Mapped[str] = mapped_column(String(50), default="INTRAMUSCULAR", nullable=False)
    dias_retiro_carne: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dias_retiro_leche: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    almacen_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("almacen.id", ondelete="SET NULL"), nullable=True, index=True
    )
    estado: Mapped[str] = mapped_column(String(20), default="ACTIVO", nullable=False, index=True)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=get_bolivia_now, nullable=False)

    # Relación
    almacen = relationship("Almacen", lazy="selectin")


class SanidadOperacion(Base):
    __tablename__ = "sanidad_operacion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero_comprobante: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    tipo_operacion: Mapped[str] = mapped_column(String(40), nullable=False, index=True)  # VACUNACION_INDIVIDUAL, VACUNACION_GRUPAL, TRATAMIENTO_INDIVIDUAL, TRATAMIENTO_GRUPAL, PREVENTIVO
    fecha_aplicacion: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    fecha_programada: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    potrero_origen_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("potrero.id", ondelete="SET NULL"), nullable=True, index=True
    )
    vacuna_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sanidad_vacuna.id", ondelete="SET NULL"), nullable=True, index=True
    )
    medicamento_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sanidad_medicamento.id", ondelete="SET NULL"), nullable=True, index=True
    )
    lote_producto: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    fecha_vencimiento_producto: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    diagnostico: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    sintomas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cantidad_animales: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    trabajador_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("trabajador.id", ondelete="SET NULL"), nullable=True, index=True
    )
    veterinario_nombre: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    costo_total_estimado: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    descontar_inventario: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    movimiento_almacen_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("movimiento_almacen.id", ondelete="SET NULL"), nullable=True
    )
    traslado_cuarentena_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("movimiento_ganado.id", ondelete="SET NULL"), nullable=True
    )
    estado: Mapped[str] = mapped_column(String(20), default="EJECUTADO", nullable=False, index=True)  # EJECUTADO, PROGRAMADO, ANULADO
    motivo_anulacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    usuario_ci: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("usuario.ci", ondelete="SET NULL"), nullable=True, index=True
    )
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=get_bolivia_now, nullable=False)

    # Relaciones
    detalles = relationship("SanidadOperacionDetalle", back_populates="operacion", cascade="all, delete-orphan", lazy="selectin")
    vacuna = relationship("SanidadVacuna", lazy="selectin")
    medicamento = relationship("SanidadMedicamento", lazy="selectin")
    potrero_origen = relationship("Potrero", foreign_keys=[potrero_origen_id], lazy="selectin")
    trabajador = relationship("Trabajador", foreign_keys=[trabajador_id], lazy="selectin")
    usuario = relationship("Usuario", foreign_keys=[usuario_ci], lazy="selectin")


class SanidadOperacionDetalle(Base):
    __tablename__ = "sanidad_operacion_detalle"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    operacion_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sanidad_operacion.id", ondelete="CASCADE"), nullable=False, index=True
    )
    animal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("animal.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    numero_arete: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    codigo_interno: Mapped[str] = mapped_column(String(50), nullable=False)
    dosis_aplicada: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    unidad_medida: Mapped[str] = mapped_column(String(20), default="ML", nullable=False)
    fecha_fin_retiro_carne: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    fecha_fin_retiro_leche: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    estado_aplicacion: Mapped[str] = mapped_column(String(20), default="APLICADO", nullable=False, index=True)  # APLICADO, PENDIENTE, RECHAZADO
    reaccion_adversa: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relaciones
    operacion = relationship("SanidadOperacion", back_populates="detalles")
    animal = relationship("Animal", lazy="selectin")
    seguimientos = relationship(
        "SanidadSeguimiento",
        back_populates="detalle",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(SanidadSeguimiento.fecha_seguimiento)"
    )


class SanidadSeguimiento(Base):
    __tablename__ = "sanidad_seguimiento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    detalle_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sanidad_operacion_detalle.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fecha_seguimiento: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    estado_salud: Mapped[str] = mapped_column(String(30), default="FAVORABLE", nullable=False)  # FAVORABLE, ESTABLE, DESFAVORABLE, RECUPERADO
    temperatura_c: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1), nullable=True)
    peso_actual_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    usuario_ci: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("usuario.ci", ondelete="SET NULL"), nullable=True, index=True
    )
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=get_bolivia_now, nullable=False)

    # Relaciones
    detalle = relationship("SanidadOperacionDetalle", back_populates="seguimientos")
    usuario = relationship("Usuario", foreign_keys=[usuario_ci], lazy="selectin")


# =========================================================================
# MÓDULO DE GESTIÓN AGRÍCOLA (SPEC-004)
# =========================================================================

class AreaAgricola(Base):
    __tablename__ = "area_agricola"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)  # AGR-0001
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # Ej: Parcela Norte 1
    superficie_ha: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    poligono_geojson: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # GeoJSON string [[lat, lng], ...]
    centroide_lat: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6), nullable=True)
    centroide_lng: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6), nullable=True)
    color_hex: Mapped[str] = mapped_column(String(20), default="#10B981", nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="ACTIVO", nullable=False, index=True)  # ACTIVO, INACTIVO
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=get_bolivia_now, nullable=False)
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime, default=get_bolivia_now, onupdate=get_bolivia_now, nullable=False
    )

    # Relaciones
    ciclos = relationship(
        "CicloAgricola",
        back_populates="area",
        cascade="all, delete-orphan",
        order_by="desc(CicloAgricola.fecha_inicio)",
        lazy="selectin"
    )

    @property
    def ciclo_activo(self):
        for c in self.ciclos:
            if c.estado == "ACTIVO":
                return c
        return None


class CicloAgricola(Base):
    __tablename__ = "ciclo_agricola"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    area_agricola_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("area_agricola.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cultivo: Mapped[str] = mapped_column(String(80), nullable=False, index=True)  # Soya, Maíz, Sorgo, Trigo, etc.
    variedad_hibrido: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Ej: Don Mario 68I68
    campana: Mapped[str] = mapped_column(String(80), nullable=False, index=True)  # Ej: Verano 2025/2026, Invierno 2026
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    superficie_utilizada_ha: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    fase_actual: Mapped[str] = mapped_column(
        String(30), default="PREPARACION", nullable=False, index=True
    )  # PREPARACION, SIEMBRA, MANEJO, COSECHA, FINALIZADO
    estado: Mapped[str] = mapped_column(
        String(20), default="ACTIVO", nullable=False, index=True
    )  # ACTIVO, FINALIZADO, CANCELADO
    fecha_cierre: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    total_cosechado: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    unidad_cosecha: Mapped[str] = mapped_column(String(20), default="TN", nullable=False)  # TN, KG, QQ
    rendimiento_promedio_ha: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)  # Ej: 3.45 TN/ha
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    usuario_ci: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("usuario.ci", ondelete="SET NULL"), nullable=True, index=True
    )
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=get_bolivia_now, nullable=False)
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime, default=get_bolivia_now, onupdate=get_bolivia_now, nullable=False
    )

    # Relaciones
    area = relationship("AreaAgricola", back_populates="ciclos")
    usuario = relationship("Usuario", foreign_keys=[usuario_ci], lazy="selectin")
    actividades_preparacion = relationship(
        "ActividadPreparacion",
        back_populates="ciclo",
        cascade="all, delete-orphan",
        order_by="ActividadPreparacion.fecha",
        lazy="selectin"
    )
    actividades_manejo = relationship(
        "ActividadManejo",
        back_populates="ciclo",
        cascade="all, delete-orphan",
        order_by="desc(ActividadManejo.fecha)",
        lazy="selectin"
    )
    cosechas = relationship(
        "CosechaRegistro",
        back_populates="ciclo",
        cascade="all, delete-orphan",
        order_by="desc(CosechaRegistro.fecha_cosecha)",
        lazy="selectin"
    )


class ActividadPreparacion(Base):
    __tablename__ = "actividad_preparacion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ciclo_agricola_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ciclo_agricola.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo_actividad: Mapped[str] = mapped_column(String(50), nullable=False)  # ARADO, RASTRA, ROLO, SUBSOLADO, OTRO
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    completada: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=get_bolivia_now, nullable=False)

    ciclo = relationship("CicloAgricola", back_populates="actividades_preparacion")


class ActividadManejo(Base):
    __tablename__ = "actividad_manejo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ciclo_agricola_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ciclo_agricola.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    tipo_actividad: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # FUMIGACION, HERBICIDA, INSECTICIDA, FUNGICIDA, FERTILIZACION, APLICACION_FOLIAR, OTRO
    producto_utilizado: Mapped[str] = mapped_column(String(120), nullable=False)
    cantidad_aplicada: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unidad_medida: Mapped[str] = mapped_column(String(20), default="LT", nullable=False)  # LT, KG, DOSIS
    dosis_por_ha: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    superficie_aplicada_ha: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=get_bolivia_now, nullable=False)

    ciclo = relationship("CicloAgricola", back_populates="actividades_manejo")


class CosechaRegistro(Base):
    __tablename__ = "cosecha_registro"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ciclo_agricola_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ciclo_agricola.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fecha_cosecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    fecha_fin_cosecha: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    cultivo_cosechado: Mapped[str] = mapped_column(String(80), nullable=False)
    superficie_cosechada_ha: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    cantidad_producida: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unidad_medida: Mapped[str] = mapped_column(String(20), default="TN", nullable=False)  # TN, KG, QQ
    rendimiento_calculado_ha: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=get_bolivia_now, nullable=False)

    ciclo = relationship("CicloAgricola", back_populates="cosechas")




