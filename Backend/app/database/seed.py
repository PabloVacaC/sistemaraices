from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select, text, func
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
    Potrero,
    Animal,
    SanidadVacuna,
    SanidadMedicamento,
    SanidadOperacion,
    SanidadOperacionDetalle,
    SanidadSeguimiento,
    AreaAgricola,
    CicloAgricola,
    ActividadPreparacion,
    ActividadManejo,
    CosechaRegistro,
)
import json
from decimal import Decimal
from app.core.security import get_password_hash


TRABAJADORES_EXCEL = [
    {"nombres": "EBERT", "apellidos": "ORETEA", "cargo": "ENCARGADO GENERAL", "area": "DON FELIPE", "fecha_ingreso": "2025-01-27", "sueldoBase": 7000.0, "estado": True},
    {"nombres": "CLEITON", "apellidos": "ASIAMA", "cargo": "ENCARGADO PLANTA Y CONFINAMIENTO", "area": "DON CESAR", "fecha_ingreso": "2023-07-07", "sueldoBase": 4000.0, "estado": True},
    {"nombres": "MARCOS", "apellidos": "PACHECO", "cargo": "OPERADOR", "area": "DON CESAR", "fecha_ingreso": "2026-03-07", "sueldoBase": 3700.0, "estado": True},
    {"nombres": "PEDRO", "apellidos": "ORTIZ", "cargo": "ENCARGADO VAQUEROS", "area": "DON FELIPE", "fecha_ingreso": "2025-01-10", "sueldoBase": 3700.0, "estado": True},
    {"nombres": "JUAN", "apellidos": "C. MOLINA", "cargo": "OPERADOR", "area": "DON FELIPE", "fecha_ingreso": "2026-07-07", "sueldoBase": 3700.0, "estado": True},
    {"nombres": "J,", "apellidos": "EDUARDO CAYUBA", "cargo": "CONFINAMIENTO", "area": "DON FELIPE", "fecha_ingreso": "2025-06-16", "sueldoBase": 3700.0, "estado": True},
    {"nombres": "MARTIN", "apellidos": "FARFAN", "cargo": "OPERADOR", "area": "DON FELIPE", "fecha_ingreso": "2026-01-04", "sueldoBase": 3700.0, "estado": True},
    {"nombres": "ROBER R.", "apellidos": "RIVERA VALDIVIA", "cargo": "Veterinario Jr Postura", "area": "AVICOLA DON CESAR", "fecha_ingreso": "2026-03-30", "sueldoBase": 3500.0, "estado": True},
    {"nombres": "RUBEN", "apellidos": "MELGAR", "cargo": "ENCARGADO DE MANTENIMIENTO", "area": "DON FELIPE", "fecha_ingreso": "2024-05-31", "sueldoBase": 3500.0, "estado": True},
    {"nombres": "YOCELIN", "apellidos": "GUERRA", "cargo": "Encargada Filtros y Planta de Alimento", "area": "PLANTA DE ALIMENTO", "fecha_ingreso": "2026-05-04", "sueldoBase": 3500.0, "estado": True},
    {"nombres": "ELENA", "apellidos": "DUTRA", "cargo": "COCINA", "area": "DON FELIPE", "fecha_ingreso": "2026-07-13", "sueldoBase": 3300.0, "estado": True},
    {"nombres": "EBERTO", "apellidos": "MASAI TAPIOSI", "cargo": "VAQUERO", "area": "DON FELIPE", "fecha_ingreso": "2026-09-19", "sueldoBase": 3300.0, "estado": True},
    {"nombres": "DAVID", "apellidos": "GUZMAN MEDINA", "cargo": "VAQUERO", "area": "DON CESAR", "fecha_ingreso": "2026-07-26", "sueldoBase": 3300.0, "estado": True},
    {"nombres": "FRANCISCO", "apellidos": "SOSA", "cargo": "AYUDANTE CONF.", "area": "DON FELIPE", "fecha_ingreso": "2026-07-29", "sueldoBase": 2900.0, "estado": True},
    {"nombres": "MARIA", "apellidos": "SHENEIDER", "cargo": "COCINA", "area": "DON CESAR", "fecha_ingreso": "2024-01-29", "sueldoBase": 3300.0, "estado": True},
    {"nombres": "TERESA", "apellidos": "BAILABA", "cargo": "ENCARGADA ALIMENTACIÓN", "area": "DON FELIPE", "fecha_ingreso": "2025-01-27", "sueldoBase": 3300.0, "estado": True},
    {"nombres": "CRISTOBAL", "apellidos": "CAYUBA", "cargo": "VAQUERO", "area": "DON FELIPE", "fecha_ingreso": "2025-09-02", "sueldoBase": 3300.0, "estado": True},
    {"nombres": "JORGE", "apellidos": "GARCIA", "cargo": "OPERADOR", "area": "DON FELIPE", "fecha_ingreso": "2026-06-10", "sueldoBase": 2900.0, "estado": False},
    {"nombres": "ALFREDO", "apellidos": "ARREDONDO VACA", "cargo": "VAQUERO", "area": "DON FELIPE", "fecha_ingreso": "2026-02-10", "sueldoBase": 3300.0, "estado": False},
    {"nombres": "JESUS", "apellidos": "JUSTINIANO", "cargo": "VAQUERO", "area": "DON FELIPE", "fecha_ingreso": "2026-10-16", "sueldoBase": 3700.0, "estado": True},
    {"nombres": "MARTIN", "apellidos": "URRURI", "cargo": "COCINA", "area": "DON FELIPE", "fecha_ingreso": "2026-07-21", "sueldoBase": 2900.0, "estado": True},
    {"nombres": "LEONCIO", "apellidos": "YOVIO", "cargo": "VAQUERO JR", "area": "DON FELIPE", "fecha_ingreso": "2026-02-09", "sueldoBase": 3300.0, "estado": True},
    {"nombres": "DIEGO", "apellidos": "CABRERA JUSTINIANO", "cargo": "AYUDANTE CONF. PLANTA Y JARDINERIA", "area": "PLANTA DE ALIMENTO", "fecha_ingreso": "2026-03-22", "sueldoBase": 3300.0, "estado": True},
    {"nombres": "FERNANDO", "apellidos": "TOMICHA", "cargo": "GALPONERO", "area": "AVICOLA DON CESAR", "fecha_ingreso": "2026-03-06", "sueldoBase": 3000.0, "estado": True},
    {"nombres": "JUANITO", "apellidos": "LIMON", "cargo": "AYUDANTE CONF. PLANTA Y JARDINERIA", "area": "PLANTA DE ALIMENTO", "fecha_ingreso": "2026-10-07", "sueldoBase": 2900.0, "estado": True},
    {"nombres": "BISMAR", "apellidos": "LIMPIAS", "cargo": "APOYO AGRICOLA E INVENTARIOS", "area": "DON FELIPE", "fecha_ingreso": "2026-05-15", "sueldoBase": 3300.0, "estado": True},
    {"nombres": "ISMAEL", "apellidos": "GALARZA", "cargo": "CLASIFICADRORA", "area": "AVICOLA DON CESAR", "fecha_ingreso": "2026-07-01", "sueldoBase": 2900.0, "estado": True},
    {"nombres": "YERIG", "apellidos": "MONTERO ROJA", "cargo": "GALPONERO", "area": "AVICOLA DON CESAR", "fecha_ingreso": "2026-06-30", "sueldoBase": 2900.0, "estado": True},
    {"nombres": "ALVERTO", "apellidos": "MONTERO ROJA", "cargo": "GALPONERO", "area": "AVICOLA DON CESAR", "fecha_ingreso": "2026-06-30", "sueldoBase": 2900.0, "estado": True},
    {"nombres": "ARNALDO", "apellidos": "MASAI", "cargo": "AYUDANTE CONF. PLANTA Y JARDINERIA", "area": "DON CESAR", "fecha_ingreso": "2026-10-09", "sueldoBase": 3300.0, "estado": False},
    {"nombres": "SERGIO", "apellidos": "ROCA S.", "cargo": "LIMPIA ALAMBRE", "area": "DON CESAR", "fecha_ingreso": "2026-08-11", "sueldoBase": 2900.0, "estado": True},
    {"nombres": "CARLOS H.", "apellidos": "VARGAS D.", "cargo": "APOYO CONFINAMIENTO", "area": "DON FELIPE", "fecha_ingreso": "2026-08-11", "sueldoBase": 2900.0, "estado": True},
    {"nombres": "JULIO", "apellidos": "CESAR CUIGAY", "cargo": "OPERADOR", "area": "DON FELIPE", "fecha_ingreso": "2026-10-07", "sueldoBase": 3500.0, "estado": False},
    {"nombres": "JULIO", "apellidos": "MENDOZA", "cargo": "OPERADOR", "area": "DON FELIPE", "fecha_ingreso": "2026-10-07", "sueldoBase": 2900.0, "estado": True},
    {"nombres": "MARCELO", "apellidos": "BORORA", "cargo": "OPERADOR", "area": "DON FELIPE", "fecha_ingreso": "2026-08-21", "sueldoBase": 2900.0, "estado": False},
    {"nombres": "JORGE", "apellidos": "SURUBI CASTRO", "cargo": "OPERADOR", "area": "DON FELIPE", "fecha_ingreso": "2026-10-21", "sueldoBase": 2900.0, "estado": True},
    {"nombres": "JOSE", "apellidos": "ALFREDO VILLA", "cargo": "OPERADOR", "area": "DON FELIPE", "fecha_ingreso": "2026-10-19", "sueldoBase": 2900.0, "estado": True},
    {"nombres": "ROXANA", "apellidos": "PEREZ GUERRA", "cargo": "OPERADOR", "area": "DON FELIPE", "fecha_ingreso": "2026-10-19", "sueldoBase": 2900.0, "estado": True},
    {"nombres": "IGNACIO", "apellidos": "YUBANORE", "cargo": "OPERADOR", "area": "DON FELIPE", "fecha_ingreso": "2026-10-20", "sueldoBase": 3000.0, "estado": True},
    {"nombres": "HENRY", "apellidos": "CUBA NAVA", "cargo": "OPERADOR", "area": "DON FELIPE", "fecha_ingreso": "2026-09-14", "sueldoBase": 3500.0, "estado": True},
    {"nombres": "FELIPE", "apellidos": "VACUARY", "cargo": "OPERADOR", "area": "DON FELIPE", "fecha_ingreso": "2026-10-01", "sueldoBase": 2900.0, "estado": False},
    {"nombres": "PEDRO", "apellidos": "SURUBI CASTRO", "cargo": "OPERADOR", "area": "DON FELIPE", "fecha_ingreso": "2026-10-19", "sueldoBase": 2900.0, "estado": True},
    {"nombres": "LEONARDO", "apellidos": "SOLETO GUTIERREZ", "cargo": "GALPONERO", "area": "AVICOLA DON CESAR", "fecha_ingreso": "2026-09-30", "sueldoBase": 2900.0, "estado": True},
]


def init_db():
    print("Creando tablas en PostgreSQL...")
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas exitosamente.")

    # Migraciones seguras no destructivas para columnas nuevas
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE trabajador ADD COLUMN IF NOT EXISTS fecha_inactividad DATE;"))
            conn.execute(text("ALTER TABLE anticipo ADD COLUMN IF NOT EXISTS es_periodo_siguiente BOOLEAN NOT NULL DEFAULT FALSE;"))
            conn.execute(text("ALTER TABLE animal ADD COLUMN IF NOT EXISTS potrero_id INT REFERENCES potrero(id) ON DELETE SET NULL;"))
            conn.execute(text("ALTER TABLE actividad_manejo ADD COLUMN IF NOT EXISTS dosis_por_ha NUMERIC(10, 2);"))
            conn.execute(text("ALTER TABLE actividad_manejo ADD COLUMN IF NOT EXISTS superficie_aplicada_ha NUMERIC(10, 2);"))
            
            # Sincronización automática de potrero_id para animales existentes (SPEC-002)
            conn.execute(text("""
                UPDATE animal a
                SET potrero_id = p.id, ubicacion = p.nombre
                FROM potrero p
                WHERE a.potrero_id IS NULL
                  AND p.estado = 'ACTIVO'
                  AND (
                      LOWER(TRIM(a.ubicacion)) = LOWER(TRIM(p.nombre))
                      OR LOWER(TRIM(a.ubicacion)) = LOWER(TRIM(p.codigo))
                  );
            """))
            conn.execute(text("""
                UPDATE animal
                SET potrero_id = (SELECT id FROM potrero WHERE estado = 'ACTIVO' ORDER BY id ASC LIMIT 1),
                    ubicacion = (SELECT nombre FROM potrero WHERE estado = 'ACTIVO' ORDER BY id ASC LIMIT 1)
                WHERE potrero_id IS NULL
                  AND (SELECT COUNT(*) FROM potrero WHERE estado = 'ACTIVO') > 0;
            """))
            conn.commit()
            print("Migraciones incrementales y sincronización de potreros aplicadas correctamente.")
        except Exception as ex:
            print(f"Nota de migración incremental: {ex}")

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
            "PLANILLA_VER",
            "PLANILLA_EDITAR",
            "PLANILLA_CERRAR",
            "DESCUENTOS_REGISTRAR",
            "DESCUENTOS_ANULAR",
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
            "GANADERIA_VER",
            "GANADERIA_CREAR",
            "GANADERIA_PESAJES",
            "GANADERIA_COMPRAS",
            "GANADERIA_VENTAS",
            "GANADERIA_BAJAS",
            "GANADERIA_EDITAR",
            "AGRICULTURA_VER",
            "AGRICULTURA_GESTIONAR",
            "APICULTURA_VER",
            "APICULTURA_GESTIONAR",
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
                    "PLANILLA_VER",
                    "PLANILLA_EDITAR",
                    "PLANILLA_CERRAR",
                    "DESCUENTOS_REGISTRAR",
                    "DESCUENTOS_ANULAR",
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
                    "GANADERIA_VER",
                    "GANADERIA_CREAR",
                    "GANADERIA_PESAJES",
                    "GANADERIA_COMPRAS",
                    "GANADERIA_VENTAS",
                    "GANADERIA_BAJAS",
                    "GANADERIA_EDITAR",
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
                    "PLANILLA_VER",
                    "PAGOS_ANTICIPOS_VER",
                    "INVENTARIO_VER",
                    "INVENTARIO_REGISTRAR_SALIDA",
                    "INVENTARIO_GASTOS_REGISTRAR",
                    "GANADERIA_VER",
                    "GANADERIA_PESAJES",
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
            {"nombre": "DON FELIPE", "descripcion": "Hacienda Don Felipe (Ganadería y Confinamiento)"},
            {"nombre": "DON CESAR", "descripcion": "Hacienda Don Cesar (Producción y Confinamiento)"},
            {"nombre": "AVICOLA DON CESAR", "descripcion": "Granjas Avícolas Don Cesar (Postura y Galpones)"},
            {"nombre": "PLANTA DE ALIMENTO", "descripcion": "Planta de Alimento Balanceado y Filtros"},
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

        from app.modules.pagos.service import asegurar_periodos_automaticos
        asegurar_periodos_automaticos(db)

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

            print("Super Administrador creado exitosamente con credenciales:")
            print(f"Email: {super_email} | Password: 123456")
        else:
            print("El Super Administrador ya se encuentra registrado.")

        # Asegurar trabajador asociado al Super Admin si no existe
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

            contacto = ContactoEmergencia(
                nombrecompleto="Contacto Familiar",
                parentesco="Familiar",
                celular="71111111",
                trabajador_id=trabajador_admin.id,
            )
            db.add(contacto)
            db.commit()

        # 5. Sembrar los 43 Trabajadores Oficiales del Excel (optimizado en 1 consulta)
        print("Sincronizando trabajadores del Excel oficial...")
        existentes_set = set(
            db.execute(select(Trabajador.nombres, Trabajador.apellidos)).all()
        )
        nuevos_trabs = []
        for w in TRABAJADORES_EXCEL:
            if (w["nombres"], w["apellidos"]) not in existentes_set:
                area_obj = areas_db.get(w["area"]) or areas_db.get("Operaciones") or list(areas_db.values())[0]
                t_nuevo = Trabajador(
                    nombres=w["nombres"],
                    apellidos=w["apellidos"],
                    cargo=w["cargo"],
                    area_id=area_obj.id,
                    fecha_ingreso=date.fromisoformat(w["fecha_ingreso"]),
                    sueldoBase=w["sueldoBase"],
                    estado=w["estado"],
                )
                db.add(t_nuevo)
                existentes_set.add((w["nombres"], w["apellidos"]))
        db.commit()
        print("Trabajadores del Excel oficial sincronizados con éxito.")

        # 6. Sembrar Potreros y Corrales iniciales y migrar animales existentes
        print("Verificando potreros y corrales iniciales...")
        total_potreros = db.scalar(select(func.count(Potrero.id))) or 0
        if total_potreros == 0:
            potreros_init = [
                Potrero(
                    codigo="POT-0001",
                    nombre="Potrero 1",
                    tipo_area="POTRERO",
                    superficie_ha=Decimal("45.50"),
                    capacidad_cabezas=80,
                    color_hex="#10b981",
                    poligono_geojson=json.dumps({
                        "type": "Polygon",
                        "coordinates": [[
                            [-62.251458, -17.919267],
                            [-62.246458, -17.919267],
                            [-62.246458, -17.923267],
                            [-62.251458, -17.923267],
                            [-62.251458, -17.919267]
                        ]]
                    }),
                    centroide_lat=Decimal("-17.921267"),
                    centroide_lng=Decimal("-62.248958"),
                    estado="ACTIVO",
                    observaciones="Potrero principal de pastoreo norte",
                ),
                Potrero(
                    codigo="POT-0002",
                    nombre="Potrero 2",
                    tipo_area="POTRERO",
                    superficie_ha=Decimal("50.00"),
                    capacidad_cabezas=90,
                    color_hex="#3b82f6",
                    poligono_geojson=json.dumps({
                        "type": "Polygon",
                        "coordinates": [[
                            [-62.246458, -17.919267],
                            [-62.241458, -17.919267],
                            [-62.241458, -17.923267],
                            [-62.246458, -17.923267],
                            [-62.246458, -17.919267]
                        ]]
                    }),
                    centroide_lat=Decimal("-17.921267"),
                    centroide_lng=Decimal("-62.243958"),
                    estado="ACTIVO",
                    observaciones="Potrero de rotación pasto Brachiaria",
                ),
                Potrero(
                    codigo="POT-0003",
                    nombre="Potrero Don Felipe",
                    tipo_area="POTRERO",
                    superficie_ha=Decimal("60.00"),
                    capacidad_cabezas=100,
                    color_hex="#8b5cf6",
                    poligono_geojson=json.dumps({
                        "type": "Polygon",
                        "coordinates": [[
                            [-62.251458, -17.923267],
                            [-62.241458, -17.923267],
                            [-62.241458, -17.928267],
                            [-62.251458, -17.928267],
                            [-62.251458, -17.923267]
                        ]]
                    }),
                    centroide_lat=Decimal("-17.925767"),
                    centroide_lng=Decimal("-62.246458"),
                    estado="ACTIVO",
                    observaciones="Área Don Felipe sur",
                ),
                Potrero(
                    codigo="COR-0001",
                    nombre="CORRAL DE MANEJO",
                    tipo_area="CORRAL",
                    superficie_ha=Decimal("1.50"),
                    capacidad_cabezas=40,
                    color_hex="#f59e0b",
                    poligono_geojson=json.dumps({
                        "type": "Polygon",
                        "coordinates": [[
                            [-62.246958, -17.922967],
                            [-62.245958, -17.922967],
                            [-62.245958, -17.923567],
                            [-62.246958, -17.923567],
                            [-62.246958, -17.922967]
                        ]]
                    }),
                    centroide_lat=Decimal("-17.923267"),
                    centroide_lng=Decimal("-62.246458"),
                    estado="ACTIVO",
                    observaciones="Corral central con manga y brete",
                ),
            ]
            for p in potreros_init:
                db.add(p)
            db.commit()
            print("Potreros y Corrales iniciales creados exitosamente.")

        # Sincronizar animales existentes que tengan potrero_id NULL
        potrero_1 = db.execute(select(Potrero).where(Potrero.nombre == "Potrero 1")).scalars().first()
        corral_m = db.execute(select(Potrero).where(Potrero.nombre == "CORRAL DE MANEJO")).scalars().first()

        if potrero_1 and corral_m:
            animales_sin_potrero = db.execute(select(Animal).where(Animal.potrero_id.is_(None))).scalars().all()
            for an in animales_sin_potrero:
                u = (an.ubicacion or "").upper()
                if "CORRAL" in u:
                    an.potrero_id = corral_m.id
                    an.ubicacion = "CORRAL DE MANEJO"
                else:
                    an.potrero_id = potrero_1.id
                    an.ubicacion = "Potrero 1"
            if animales_sin_potrero:
                db.commit()
                print(f"Se sincronizaron {len(animales_sin_potrero)} animales existentes con sus potreros.")

        # =========================================================================
        # SEED SANIDAD Y MEDICAMENTOS (SPEC-003)
        # =========================================================================
        vacunas_count = db.execute(select(func.count(SanidadVacuna.id))).scalar() or 0
        if vacunas_count == 0:
            vacunas_init = [
                SanidadVacuna(
                    codigo="VAC-001",
                    nombre="Fiebre Aftosa (Bivalente O/A)",
                    nombre_comercial="Aftosa Oficial Senasag",
                    enfermedad_objetivo="Fiebre Aftosa tipos O y A",
                    especie="BOVINO",
                    dosis_defecto_ml=Decimal("2.00"),
                    via_administracion="SUBCUTANEA",
                    dias_retiro_carne=21,
                    dias_retiro_leche=0,
                    requiere_refuerzo=True,
                    dias_refuerzo=180,
                    estado="ACTIVO",
                    observaciones="Campaña obligatoria oficial del Senasag Bolivia para erradicación de aftosa.",
                ),
                SanidadVacuna(
                    codigo="VAC-002",
                    nombre="Rabia Paresiante Bovina",
                    nombre_comercial="Rabisin / Cepa ERA Pasteur",
                    enfermedad_objetivo="Rabia Paresiante transmitida por murciélagos hematófagos",
                    especie="BOVINO",
                    dosis_defecto_ml=Decimal("2.00"),
                    via_administracion="SUBCUTANEA",
                    dias_retiro_carne=21,
                    dias_retiro_leche=0,
                    requiere_refuerzo=True,
                    dias_refuerzo=365,
                    estado="ACTIVO",
                    observaciones="Vacunación sistemática en áreas ganaderas tropicales y endémicas.",
                ),
                SanidadVacuna(
                    codigo="VAC-003",
                    nombre="Mancha / Gangrena / Enterotoxemia (Clostridial 8 vías)",
                    nombre_comercial="Covexin 8 / Clostrisan",
                    enfermedad_objetivo="Carbunclo Sintomático, Edema Maligno, Enterotoxemia",
                    especie="BOVINO",
                    dosis_defecto_ml=Decimal("5.00"),
                    via_administracion="SUBCUTANEA",
                    dias_retiro_carne=21,
                    dias_retiro_leche=0,
                    requiere_refuerzo=True,
                    dias_refuerzo=30,
                    estado="ACTIVO",
                    observaciones="Esencial en terneros y vaquillas a partir de los 3 meses de edad.",
                ),
                SanidadVacuna(
                    codigo="VAC-004",
                    nombre="Brucelosis Bovina Cepa RB51",
                    nombre_comercial="Brucelosis RB-51",
                    enfermedad_objetivo="Brucella abortus",
                    especie="BOVINO",
                    dosis_defecto_ml=Decimal("2.00"),
                    via_administracion="SUBCUTANEA",
                    dias_retiro_carne=21,
                    dias_retiro_leche=0,
                    requiere_refuerzo=False,
                    dias_refuerzo=None,
                    estado="ACTIVO",
                    observaciones="Dosis única para terneras hembras entre 3 y 8 meses. No revacunar machos.",
                ),
                SanidadVacuna(
                    codigo="VAC-005",
                    nombre="Complejo Reproductivo Bovino (IBR / DVB / Lepto)",
                    nombre_comercial="Cattle Master 4+L5",
                    enfermedad_objetivo="Rinotraqueítis Infecciosa Bovina, Diarrea Viral Bovina y Leptospirosis",
                    especie="BOVINO",
                    dosis_defecto_ml=Decimal("5.00"),
                    via_administracion="SUBCUTANEA",
                    dias_retiro_carne=21,
                    dias_retiro_leche=0,
                    requiere_refuerzo=True,
                    dias_refuerzo=30,
                    estado="ACTIVO",
                    observaciones="Prevención de mermas reproductivas, abortos y reabsorciones embrionarias.",
                ),
            ]
            for v in vacunas_init:
                db.add(v)
            db.commit()
            print(f"Catálogo de {len(vacunas_init)} vacunas precargadas exitosamente.")

        medicamentos_count = db.execute(select(func.count(SanidadMedicamento.id))).scalar() or 0
        if medicamentos_count == 0:
            medicamentos_init = [
                SanidadMedicamento(
                    codigo="MED-001",
                    nombre="Ivermectina 1% L.A.",
                    nombre_comercial="Ivomec / Bovimec 1%",
                    tipo_farmaco="ANTIPARASITARIO_INTERNO",
                    principio_activo="Ivermectina",
                    concentracion="10 mg/ml (1%)",
                    unidad_medida="ML",
                    via_administracion="SUBCUTANEA",
                    dias_retiro_carne=28,
                    dias_retiro_leche=28,
                    estado="ACTIVO",
                    observaciones="Control de nematodos gastrointestinales, parásitos pulmonares y garrapatas. Dosis: 1 ml cada 50 kg.",
                ),
                SanidadMedicamento(
                    codigo="MED-002",
                    nombre="Ivermectina 3.15% Larga Acción",
                    nombre_comercial="Master LP / Ivomec Gold",
                    tipo_farmaco="ANTIPARASITARIO_EXTERNO",
                    principio_activo="Ivermectina formulación de liberación lenta",
                    concentracion="31.5 mg/ml (3.15%)",
                    unidad_medida="ML",
                    via_administracion="SUBCUTANEA",
                    dias_retiro_carne=122,
                    dias_retiro_leche=122,
                    estado="ACTIVO",
                    observaciones="Alto poder residual para invernada. IMPORTANTE: Retiro prolongado de 122 días antes del faeneo.",
                ),
                SanidadMedicamento(
                    codigo="MED-003",
                    nombre="Oxitetraciclina L.A. 200",
                    nombre_comercial="Terramicina L.A. / Emicina Líquida",
                    tipo_farmaco="ANTIBIOTICO",
                    principio_activo="Oxitetraciclina base anhidra",
                    concentracion="200 mg/ml (20%)",
                    unidad_medida="ML",
                    via_administracion="INTRAMUSCULAR",
                    dias_retiro_carne=28,
                    dias_retiro_leche=7,
                    estado="ACTIVO",
                    observaciones="Tratamiento de neumonías, anaplasmosis, pietín y metritis. Dosis: 1 ml cada 10 kg en masa muscular profunda.",
                ),
                SanidadMedicamento(
                    codigo="MED-004",
                    nombre="Flunixin Meglumine 5%",
                    nombre_comercial="Banamine / Flunixin Inyectable",
                    tipo_farmaco="ANTIINFLAMATORIO",
                    principio_activo="Flunixin base meglumina",
                    concentracion="50 mg/ml (5%)",
                    unidad_medida="ML",
                    via_administracion="INTRAMUSCULAR",
                    dias_retiro_carne=4,
                    dias_retiro_leche=1,
                    estado="ACTIVO",
                    observaciones="Antiinflamatorio no esteroide con efecto analgésico y antipirético rápido. Dosis: 2.2 mg/kg.",
                ),
                SanidadMedicamento(
                    codigo="MED-005",
                    nombre="Complejo B + Hierro + Cacodilato",
                    nombre_comercial="Catosal B12 / Hematofos B12",
                    tipo_farmaco="VITAMINICO",
                    principio_activo="Vitamina B1, B2, B6, B12, Cacodilato de Sodio y Hierro",
                    concentracion="Multivitamínico hematopoyético",
                    unidad_medida="ML",
                    via_administracion="INTRAMUSCULAR",
                    dias_retiro_carne=0,
                    dias_retiro_leche=0,
                    estado="ACTIVO",
                    observaciones="Reconstituyente celular, estimulante del apetito y optimizador de ganancia de peso en engorde.",
                ),
                SanidadMedicamento(
                    codigo="MED-006",
                    nombre="Curabichera Líquido / Spray con Plata",
                    nombre_comercial="Larvispray / Curabichera Plata",
                    tipo_farmaco="DESINFECTANTE",
                    principio_activo="Cipermetrina + DDVP + Sulfadiazina de Plata",
                    concentracion="Aerosol / Pasta tópica",
                    unidad_medida="APLICACION",
                    via_administracion="TOPICA",
                    dias_retiro_carne=3,
                    dias_retiro_leche=0,
                    estado="ACTIVO",
                    observaciones="Tratamiento preventivo y curativo de miasis (bicheras) en descorne, castración, marcación y ombligo de recién nacidos.",
                ),
            ]
            for m in medicamentos_init:
                db.add(m)
            db.commit()
            print(f"Catálogo de {len(medicamentos_init)} medicamentos precargados exitosamente.")

        # 9. Sembrar Áreas y Ciclos Agrícolas Iniciales (SPEC-004)
        if db.query(func.count(AreaAgricola.id)).scalar() == 0:
            print("Sembrando parcelas agrícolas y ciclos de demostración...")
            
            # Polígono 1: Parcela Norte - Lote 1 (cerca de -17.920, -62.248)
            poly1 = [
                [-17.918500, -62.249500],
                [-17.918500, -62.242000],
                [-17.922000, -62.242000],
                [-17.922000, -62.249500],
            ]
            area1 = AreaAgricola(
                codigo="AGR-0001",
                nombre="Parcela Norte - Lote 1",
                superficie_ha=Decimal("120.50"),
                poligono_geojson=json.dumps(poly1),
                centroide_lat=Decimal("-17.920250"),
                centroide_lng=Decimal("-62.245750"),
                color_hex="#10B981",  # Verde esmeralda (Manejo/Fumigación activo)
                estado="ACTIVO",
                observaciones="Lote de alto rendimiento con suelo franco-arcilloso y curvas de nivel.",
            )
            db.add(area1)
            db.flush()

            # Ciclo 1 Activo: Soya Don Mario en Fase Manejo/Fumigación
            ciclo1 = CicloAgricola(
                area_agricola_id=area1.id,
                cultivo="Soya",
                variedad_hibrido="Don Mario 68I68",
                campana="Verano 2025/2026",
                fecha_inicio=date(2025, 11, 15),
                superficie_utilizada_ha=Decimal("120.50"),
                fase_actual="MANEJO",
                estado="ACTIVO",
                observaciones="Siembra directa con inoculación biológica de semilla.",
            )
            db.add(ciclo1)
            db.flush()

            # Actividades de preparación del Ciclo 1 (completadas)
            db.add(ActividadPreparacion(
                ciclo_agricola_id=ciclo1.id,
                tipo_actividad="ARADO",
                fecha=date(2025, 11, 5),
                completada=True,
                observaciones="Arado de cincel profundo."
            ))
            db.add(ActividadPreparacion(
                ciclo_agricola_id=ciclo1.id,
                tipo_actividad="RASTRA",
                fecha=date(2025, 11, 10),
                completada=True,
                observaciones="Rastreada niveladora doble acción."
            ))
            db.add(ActividadPreparacion(
                ciclo_agricola_id=ciclo1.id,
                tipo_actividad="ROLO",
                fecha=date(2025, 11, 12),
                completada=True,
                observaciones="Rolado para emparejar rastrojo."
            ))

            # Actividades de Manejo del Ciclo 1 (Fumigaciones realizadas)
            db.add(ActividadManejo(
                ciclo_agricola_id=ciclo1.id,
                fecha=date(2025, 12, 5),
                tipo_actividad="HERBICIDA",
                producto_utilizado="Glifosato 75.7% WG + 2,4-D",
                cantidad_aplicada=Decimal("240.00"),
                unidad_medida="LT",
                observaciones="Control post-emergente temprano de malezas de hoja ancha."
            ))
            db.add(ActividadManejo(
                ciclo_agricola_id=ciclo1.id,
                fecha=date(2026, 1, 10),
                tipo_actividad="FUNGICIDA",
                producto_utilizado="Priori Xtra (Azoxistrobina + Ciproconazol)",
                cantidad_aplicada=Decimal("40.00"),
                unidad_medida="LT",
                observaciones="Prevención de roya asiática y mancha ojo de rana."
            ))

            # Ciclo Histórico Finalizado en Parcela 1: Trigo Invierno 2025
            ciclo_hist = CicloAgricola(
                area_agricola_id=area1.id,
                cultivo="Trigo",
                variedad_hibrido="Motacú",
                campana="Invierno 2025",
                fecha_inicio=date(2025, 5, 20),
                fecha_cierre=date(2025, 9, 28),
                superficie_utilizada_ha=Decimal("120.00"),
                fase_actual="FINALIZADO",
                estado="FINALIZADO",
                total_cosechado=Decimal("325.20"),
                unidad_cosecha="TN",
                rendimiento_promedio_ha=Decimal("2.71"),
                observaciones="Campaña invernal con buena pluviometría y sanidad foliar.",
            )
            db.add(ciclo_hist)
            db.flush()

            db.add(CosechaRegistro(
                ciclo_agricola_id=ciclo_hist.id,
                fecha_cosecha=date(2025, 9, 28),
                cultivo_cosechado="Trigo",
                superficie_cosechada_ha=Decimal("120.00"),
                cantidad_producida=Decimal("325.20"),
                unidad_medida="TN",
                rendimiento_calculado_ha=Decimal("2.71"),
                observaciones="Cosecha mecanizada con humedad de grano al 13.5%."
            ))

            # Polígono 2: Parcela Sur - Lote 2 (cerca de -17.925, -62.245)
            poly2 = [
                [-17.923000, -62.249000],
                [-17.923000, -62.243000],
                [-17.927000, -62.243000],
                [-17.927000, -62.249000],
            ]
            area2 = AreaAgricola(
                codigo="AGR-0002",
                nombre="Parcela Sur - Lote 2",
                superficie_ha=Decimal("95.00"),
                poligono_geojson=json.dumps(poly2),
                centroide_lat=Decimal("-17.925000"),
                centroide_lng=Decimal("-62.246000"),
                color_hex="#F59E0B",  # Ámbar (Fase Preparación)
                estado="ACTIVO",
                observaciones="Lote en preparación para siembra de Maíz híbrido.",
            )
            db.add(area2)
            db.flush()

            ciclo2 = CicloAgricola(
                area_agricola_id=area2.id,
                cultivo="Maíz",
                variedad_hibrido="Dekalb DK-7910",
                campana="Verano 2025/2026",
                fecha_inicio=date(2026, 2, 1),
                superficie_utilizada_ha=Decimal("95.00"),
                fase_actual="PREPARACION",
                estado="ACTIVO",
                observaciones="Barbecho químico previo y descompactación.",
            )
            db.add(ciclo2)
            db.flush()

            db.add(ActividadPreparacion(
                ciclo_agricola_id=ciclo2.id,
                tipo_actividad="ARADO",
                fecha=date(2026, 2, 5),
                completada=True,
                observaciones="Roturación de suelo."
            ))
            db.add(ActividadPreparacion(
                ciclo_agricola_id=ciclo2.id,
                tipo_actividad="RASTRA",
                fecha=date(2026, 2, 12),
                completada=True,
                observaciones="Rastra pesada desterronadora."
            ))
            db.add(ActividadPreparacion(
                ciclo_agricola_id=ciclo2.id,
                tipo_actividad="ROLO",
                fecha=date(2026, 2, 18),
                completada=False,
                observaciones="Pendiente de pase de rolo previo a la sembradora neumática."
            ))

            db.commit()
            print("Parcelas agrícolas y ciclos de demostración creados exitosamente.")

    except Exception as e:
        db.rollback()
        print(f"Error al inicializar la base de datos: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
