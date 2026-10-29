from datetime import date, time, datetime
from typing import Optional, List
from decimal import Decimal
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
    liquidaciones = relationship(
        "Liquidacion",
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
    fecha: Mapped[date] = mapped_column(Date, default=date.today, nullable=False, index=True)
    hora: Mapped[time] = mapped_column(
        Time, default=lambda: datetime.now().time(), nullable=False
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
    liquidaciones = relationship("Liquidacion", back_populates="periodo")


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
    fecha_movimiento: Mapped[date] = mapped_column(Date, default=date.today, nullable=False, index=True)
    hora_movimiento: Mapped[time] = mapped_column(Time, default=lambda: datetime.now().time(), nullable=False)
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

