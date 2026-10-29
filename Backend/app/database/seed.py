from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database.connection import engine, SessionLocal, Base
from app.models.entities import (
    Permiso,
    Rol,
    RolPermiso,
    Area,
    Usuario,
    Trabajador,
    ContactoEmergencia,
    Bitacora,
)
from app.core.security import get_password_hash


def init_db():
    print("Creando tablas en PostgreSQL...")
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas exitosamente.")

    db: Session = SessionLocal()
    try:
        # 1. Sembrar Permisos
        permisos_iniciales = [
            "GESTION_USUARIOS",
            "CREAR_USUARIO",
            "EDITAR_USUARIO",
            "ESTADO_USUARIO",
            "GESTION_ROLES",
            "GESTION_TRABAJADORES",
            "REGISTRAR_TRABAJADOR",
            "EDITAR_TRABAJADOR",
            "INACTIVAR_TRABAJADOR",
            "GESTION_AREAS",
            "VER_BITACORA",
            "PAGOS_ANTICIPOS_VER",
            "REGISTRAR_ANTICIPO",
            "REGISTRAR_LIQUIDACION",
            "REGISTRAR_PAGO_PARCIAL",
            "ANULAR_PAGO",
            "INVENTARIO_VER",
            "INVENTARIO_CREAR_PRODUCTO",
            "INVENTARIO_REGISTRAR_COMPRA",
            "INVENTARIO_REGISTRAR_SALIDA",
            "INVENTARIO_AJUSTE",
            "INVENTARIO_ANULAR",
            "INVENTARIO_GASTOS_REGISTRAR",
            "INVENTARIO_GASTOS_ANULAR",
            "INVENTARIO_REPORTES",
        ]

        permisos_db = {}
        for p_nombre in permisos_iniciales:
            p_obj = db.execute(select(Permiso).where(Permiso.permisos == p_nombre)).scalars().first()
            if not p_obj:
                p_obj = Permiso(permisos=p_nombre)
                db.add(p_obj)
                db.commit()
                db.refresh(p_obj)
            permisos_db[p_nombre] = p_obj

        # 2. Sembrar Roles
        roles_iniciales = [
            {
                "rol": "Super Administrador",
                "niveljerarquico": 1,
                "descripcion": "Acceso absoluto y control total de todo el sistema",
                "permisos": list(permisos_db.keys()),
            },
            {
                "rol": "Administrador",
                "niveljerarquico": 2,
                "descripcion": "Administración de usuarios, trabajadores, áreas y pagos",
                "permisos": [
                    "GESTION_USUARIOS",
                    "CREAR_USUARIO",
                    "EDITAR_USUARIO",
                    "GESTION_TRABAJADORES",
                    "REGISTRAR_TRABAJADOR",
                    "EDITAR_TRABAJADOR",
                    "INACTIVAR_TRABAJADOR",
                    "GESTION_AREAS",
                    "VER_BITACORA",
                    "PAGOS_ANTICIPOS_VER",
                    "REGISTRAR_ANTICIPO",
                    "REGISTRAR_LIQUIDACION",
                    "REGISTRAR_PAGO_PARCIAL",
                    "INVENTARIO_VER",
                    "INVENTARIO_CREAR_PRODUCTO",
                    "INVENTARIO_REGISTRAR_COMPRA",
                    "INVENTARIO_REGISTRAR_SALIDA",
                    "INVENTARIO_AJUSTE",
                    "INVENTARIO_ANULAR",
                    "INVENTARIO_GASTOS_REGISTRAR",
                    "INVENTARIO_GASTOS_ANULAR",
                    "INVENTARIO_REPORTES",
                ],
            },
            {
                "rol": "Operador",
                "niveljerarquico": 3,
                "descripcion": "Visualización y gestión operativa de trabajadores",
                "permisos": [
                    "GESTION_TRABAJADORES",
                    "REGISTRAR_TRABAJADOR",
                    "EDITAR_TRABAJADOR",
                    "PAGOS_ANTICIPOS_VER",
                    "INVENTARIO_VER",
                    "INVENTARIO_REGISTRAR_SALIDA",
                    "INVENTARIO_GASTOS_REGISTRAR",
                ],
            },
        ]

        roles_db = {}
        for r_info in roles_iniciales:
            r_obj = db.execute(select(Rol).where(Rol.rol == r_info["rol"])).scalars().first()
            if not r_obj:
                r_obj = Rol(
                    rol=r_info["rol"],
                    niveljerarquico=r_info["niveljerarquico"],
                    descripcion=r_info["descripcion"],
                )
                db.add(r_obj)
                db.commit()
                db.refresh(r_obj)

            # Sincronizar permisos del rol
            existentes_p_ids = {
                rp.permiso_id
                for rp in db.execute(
                    select(RolPermiso).where(RolPermiso.rol_id == r_obj.id)
                ).scalars().all()
            }
            for p_name in r_info["permisos"]:
                if p_name in permisos_db and permisos_db[p_name].id not in existentes_p_ids:
                    db.add(RolPermiso(rol_id=r_obj.id, permiso_id=permisos_db[p_name].id))
            db.commit()
            db.refresh(r_obj)
            roles_db[r_info["rol"]] = r_obj

        # 3. Sembrar Áreas de la Empresa
        areas_iniciales = [
            {"nombre": "Administración", "descripcion": "Área de gestión administrativa, contable y gerencial"},
            {"nombre": "Agricultura", "descripcion": "Área de producción agrícola, siembra y cosechas"},
            {"nombre": "Ganadería", "descripcion": "Área de producción ganadera, crianza y manejo bovino"},
            {"nombre": "Avicultura", "descripcion": "Área de producción avícola, granjas y derivados"},
            {"nombre": "Dirección General", "descripcion": "Alta dirección y presidencia"},
            {"nombre": "Sistemas e Informática", "descripcion": "Tecnología, desarrollo y soporte"},
            {"nombre": "Recursos Humanos", "descripcion": "Gestión de personal y talento"},
            {"nombre": "Finanzas y Contabilidad", "descripcion": "Administración financiera"},
            {"nombre": "Operaciones", "descripcion": "Producción y logística"},
        ]

        areas_db = {}
        for a_info in areas_iniciales:
            a_obj = db.execute(select(Area).where(Area.nombre == a_info["nombre"])).scalars().first()
            if not a_obj:
                a_obj = Area(
                    nombre=a_info["nombre"],
                    descripcion=a_info["descripcion"],
                    estado=True,
                )
                db.add(a_obj)
                db.commit()
                db.refresh(a_obj)
            areas_db[a_info["nombre"]] = a_obj

        # 4. Sembrar Períodos Salariales
        from app.models.entities import PeriodoSalarial
        periodos_iniciales = [
            {
                "mes": 9,
                "anio": 2026,
                "fecha_inicio": date(2026, 9, 1),
                "fecha_fin": date(2026, 9, 30),
                "fecha_pago_estimada": date(2026, 10, 5),
                "estado": "ABIERTO",
                "descripcion": "Septiembre 2026"
            },
            {
                "mes": 10,
                "anio": 2026,
                "fecha_inicio": date(2026, 10, 1),
                "fecha_fin": date(2026, 10, 31),
                "fecha_pago_estimada": date(2026, 11, 5),
                "estado": "ABIERTO",
                "descripcion": "Octubre 2026"
            },
            {
                "mes": 11,
                "anio": 2026,
                "fecha_inicio": date(2026, 11, 1),
                "fecha_fin": date(2026, 11, 30),
                "fecha_pago_estimada": date(2026, 12, 5),
                "estado": "ABIERTO",
                "descripcion": "Noviembre 2026"
            }
        ]
        for p_info in periodos_iniciales:
            p_existente = db.execute(
                select(PeriodoSalarial).where(
                    PeriodoSalarial.mes == p_info["mes"],
                    PeriodoSalarial.anio == p_info["anio"]
                )
            ).scalars().first()
            if not p_existente:
                p_obj = PeriodoSalarial(**p_info)
                db.add(p_obj)
                db.commit()

        # 4. Sembrar Super Administrador
        super_email = "juanpablovacacarvalho@gmail.com"
        super_admin = db.execute(select(Usuario).where(Usuario.email == super_email)).scalars().first()

        super_ci = "10000001"
        super_rol_id = roles_db["Super Administrador"].id

        if not super_admin:
            print(f"Creando Super Administrador: {super_email}...")
            super_admin = Usuario(
                ci=super_ci,
                nombre="Juan Pablo",
                apellido="Vaca Carvalho",
                email=super_email,
                contraseña=get_password_hash("123456"),
                genero="Masculino",
                fechanacimiento=date(1998, 5, 20),
                telefono="70000000",
                direccion="Santa Cruz, Bolivia",
                estado=True,
                rol_id=super_rol_id,
            )
            db.add(super_admin)
            db.commit()
            db.refresh(super_admin)

            # Crear trabajador asociado al Super Admin
            trabajador_admin = db.execute(select(Trabajador).where(Trabajador.ci == super_ci)).scalars().first()
            if not trabajador_admin:
                area_sistemas = areas_db.get("Sistemas e Informática") or list(areas_db.values())[0]
                trabajador_admin = Trabajador(
                    ci=super_ci,
                    nombres="Juan Pablo",
                    apellidos="Vaca Carvalho",
                    celular="70000000",
                    fecha_ingreso=date.today(),
                    cargo="Super Administrador de Sistemas",
                    sueldoBase=15000.00,
                    estado=True,
                    area_id=area_sistemas.id,
                )
                db.add(trabajador_admin)
                db.commit()
                db.refresh(trabajador_admin)

                # Contacto de emergencia de ejemplo
                contacto = ContactoEmergencia(
                    nombrecompleto="Contacto Familiar",
                    parentesco="Familiar",
                    celular="71111111",
                    trabajador_id=trabajador_admin.id,
                )
                db.add(contacto)
                db.commit()

            print("Super Administrador creado exitosamente con credenciales:")
            print(f"Email: {super_email} | Password: 123456")
        else:
            print("El Super Administrador ya se encuentra registrado.")

    except Exception as e:
        db.rollback()
        print(f"Error al inicializar la base de datos: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
