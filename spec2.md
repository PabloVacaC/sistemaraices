# SPEC-002 — Gestión de Potreros y Movimiento de Ganado

## 1. Contexto y objetivo

El submódulo **Gestión de Potreros y Movimiento de Ganado** forma parte integral del módulo principal **Ganadería** del ERP Sistemas Raíces. Su objetivo es proporcionar una herramienta cartográfica visual y administrativa basada en un **mapa satelital interactivo** para la delimitación geográfica de las áreas del predio (potreros de pastoreo, corrales de manejo, corrales de engorde, maternidades y zonas de cuarentena), y el control en tiempo real de la distribución y traslado de cabezas de ganado entre dichas áreas.

El sistema permite visualizar sobre imágenes satelitales de alta resolución los polígonos perimetrales de cada potrero y corral, distribuyendo representativamente los animales pertenecientes a cada área mediante puntos individuales interactivos. Los traslados de ganado pueden ejecutarse de dos maneras complementarias:
1. **Movimiento visual mediante arrastre (Drag & Drop)**: El operador arrastra individualmente el punto de un animal desde su área de origen hasta soltarlo dentro del polígono del potrero o corral de destino, activando una verificación de contención geográfica (*point-in-polygon*) y una ventana modal de confirmación administrativa.
2. **Movimiento manual (Individual o Grupal)**: El operador selecciona uno o múltiples animales mediante una lista con casillas de verificación (*checkboxes*) y selecciona el potrero de destino mediante formulario, permitiendo trasladar lotes enteros con fecha, motivo y responsable opcional.

Este submódulo opera de manera vinculada con el submódulo **Registro / Identificación del Ganado** (SPEC-001): no duplica registros biológicos de animales ni almacena catálogos paralelos. La ubicación actual del ganado se mantiene sincronizada bidireccionalmente: cada animal cuenta con una referencia relacional `potrero_id` (ForeignKey) y conserva su campo `ubicacion` (denominación textual) permanentemente actualizado, garantizando retrocompatibilidad con los 10 animales ya registrados en el establecimiento y con todos los reportes preexistentes.

El submódulo se ubica en el menú lateral de navegación **exactamente en medio de `Registro / Identificación del Ganado` y `Bitácora de Auditoría`**.

---

## 2. Usuarios y actores

### 2.1. Administrador / Propietario del Establecimiento
- Configura las coordenadas geográficas centrales del predio y el encuadre inicial del mapa satelital.
- Dibuja, ajusta vértices y edita los perímetros geográficos de los potreros y corrales.
- Registra la superficie en hectáreas y la capacidad estimada de carga animal de cada potrero.
- Supervisa los mapas de calor, ocupación de potreros y traslados ejecutados por el personal.
- Autoriza o ejecuta la anulación controlada de movimientos erróneos.

### 2.2. Encargado de Ganado / Mayordomo de Campo
- Consulta la distribución de cabezas de ganado por potrero desde computadoras de escritorio, tablets o teléfonos móviles.
- Registra rotaciones de pastoreo, cambios de corral, traslados a maternidad o cuarentena.
- Mueve animales arrastrándolos sobre el mapa o seleccionando lotes para movimiento masivo.
- Identifica animales específicos por su número de arete físico o código interno inmutable (GAN-XXXX).

### 2.3. Personal Autorizado de Registro y Pesaje
- Consulta el historial de movimientos de cualquier animal desde su Ficha Perfil 360°.
- Vincula movimientos con pesajes periódicos o tratamientos veterinarios.

---

## 3. Historias de usuario

- **HU-01 — Ubicación en el menú lateral:** Como usuario, quiero acceder al submódulo mediante un botón denominado `Gestión de Potreros y Movimientos` ubicado en el menú lateral exactamente entre `Registro / Identificación del Ganado` y `Bitácora de Auditoría`.
- **HU-02 — Mapa satelital interactivo:** Como usuario, quiero visualizar un mapa satelital nítido y de carga rápida del establecimiento (utilizando la capa global satelital de Esri World Imagery sin costos de API) para ubicar los potreros y corrales.
- **HU-03 — Vista panorámica inicial:** Como usuario, quiero que el mapa inicie encuadrado automáticamente en toda la extensión del predio, abarcando todos los potreros y corrales registrados.
- **HU-04 — Nomenclatura libre y flexible:** Como administrador, quiero nombrar libremente mis potreros y corrales (ej: *Potrero 1*, *Potrero 2*, *Potrero Don Felipe*, *Corral de Manejo*, *Potrero Don Cesar*) sin estar restringido a denominaciones fijas como A, B, C o D, para que los animales ya existentes calcen de inmediato sin reasignaciones forzadas.
- **HU-05 — Delimitación de potreros y corrales:** Como administrador, quiero dibujar polígonos sobre el mapa satelital definiendo los límites perimetrales de cada área, especificando si se trata de un `POTRERO`, `CORRAL`, `CUARENTENA`, `MATERNIDAD` u `OTRO`.
- **HU-06 — Edición de vértices y perímetros:** Como administrador, quiero mover, agregar o eliminar vértices de los polígonos directamente sobre el mapa para reflejar cambios en alambradas y divisiones de potreros.
- **HU-07 — Distribución visual automática de animales:** Como usuario, quiero que los animales asignados a un potrero aparezcan como puntos individuales distribuidos automáticamente dentro de su perímetro (enjambre/cuadrícula algorítmica representativa) sin necesidad de posicionarlos uno a uno a mano.
- **HU-08 — Zoom progresivo inteligente:** Como usuario, quiero que al alejar el mapa se visualice el nombre del potrero y su total de cabezas, y al acercar el mapa aparezcan nítidamente los puntos individuales de cada animal con su arete y código.
- **HU-09 — Ficha rápida al hacer clic en animal:** Como usuario, quiero hacer clic sobre el punto de un animal en el mapa para ver una tarjeta flotante con su arete, código interno, sexo, raza, peso actual y un botón para abrir su Perfil 360°.
- **HU-10 — Traslado individual por arrastre (Drag & Drop):** Como usuario, quiero hacer clic sobre un animal, arrastrar su punto sobre el mapa y soltarlo dentro de otro potrero o corral; el sistema debe detectar automáticamente el nuevo polígono y pedir confirmación antes de guardar el movimiento.
- **HU-11 — Traslado masivo / por lote:** Como usuario, quiero abrir el panel lateral de un potrero, marcar varios animales con casillas de verificación (o "Seleccionar Todos") y trasladarlos conjuntamente al potrero destino en una sola operación.
- **HU-12 — Metadatos opcionales de movimiento:** Como usuario, quiero poder registrar opcionalmente el motivo del traslado (rotación, engorde, destete, cuarentena, etc.), el trabajador responsable y observaciones.
- **HU-13 — Alerta de sobrecapacidad:** Como usuario, quiero que el sistema me advierta visualmente si el traslado hará que el potrero destino supere su capacidad estimada de cabezas, permitiéndome confirmar la operación si es deliberada.
- **HU-14 — Historial cronológico de movimientos:** Como usuario, quiero consultar el historial completo de movimientos del establecimiento (con código de comprobante, fecha, origen, destino, cantidad de animales y responsable) y auditar los traslados pasados de cada animal en su ficha histórica.
- **HU-15 — Anulación controlada de traslados:** Como administrador, quiero poder anular un movimiento reciente erróneo, devolviendo los animales a su potrero anterior de forma atómica y auditada en la Bitácora.
- **HU-16 — Animales vendidos o dados de baja:** Como usuario, quiero que cuando un animal pase a estado `VENDIDO`, `FALLECIDO`, `ROBADO` o `BAJA` en el submódulo de Identificación, desaparezca automáticamente del mapa y de los potreros activos, conservando su historial previo intacto.
- **HU-17 — Adaptabilidad móvil y táctil:** Como usuario en campo, quiero utilizar el mapa, consultar animales y mover lotes desde mi tablet o teléfono móvil con controles táctiles optimizados.

---

## 4. Requisitos funcionales (EARS)

### 4.1. Navegación y Ubicación en el Sistema
- **RF-01 (Ubicación en Sidebar):** EL SISTEMA deberá mostrar el enlace de acceso denominado **`Gestión de Potreros y Movimientos`** en el menú lateral, posicionado **inmediatamente debajo de `Registro / Identificación del Ganado` y justo antes de `Bitácora de Auditoría`**, con el icono cartográfico representativo.
- **RF-02 (Ruta Angular):** EL SISTEMA deberá registrar y resolver la ruta `/dashboard/potreros` asociada al componente visual `PotrerosComponent`.

### 4.2. Infraestructura Cartográfica y Mapa Satelital
- **RF-03 (Motor de Mapa):** EL SISTEMA deberá utilizar la biblioteca **Leaflet** con la capa de teselas satelitales **Esri World Imagery** (`https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}`), garantizando alta resolución satelital global, navegación fluida sin costos de suscripción ni dependencia de claves API de facturación externa.
- **RF-04 (Capa Híbrida de Referencia):** EL SISTEMA deberá superponer opcionalmente etiquetas de lugares y límites administrativos de Esri (`World_Boundaries_and_Places`) para facilitar la orientación geográfica.
- **RF-05 (Encuadre y Centrado Inicial):** CUANDO se cargue el submódulo, EL SISTEMA deberá calcular la envolvente geográfica (*Bounding Box / fitBounds*) de todos los potreros y corrales registrados y ajustar el mapa satelital para mostrar la totalidad del establecimiento en pantalla.
- **RF-06 (Ubicación Predeterminada):** SI no existen potreros delimitados, EL SISTEMA deberá centrar el mapa en las coordenadas configuradas del predio (por defecto: `-17.923267, -62.246458`, zoom 15).

### 4.3. Administración de Áreas (Potreros, Corrales e Instalaciones)
- **RF-07 (Nomenclatura Libre):** EL SISTEMA deberá permitir nombrar libremente cada área registrada (ej: `Potrero 1`, `Potrero 2`, `Potrero Don Cesar`, `Potrero Don Felipe`, `Corral de Manejo`, `Corral de Engorde`, `Zona Cuarentena`, `Maternidad`). No se impondrán nombres rígidos del tipo A, B, C o D.
- **RF-08 (Tipología de Área):** EL SISTEMA deberá clasificar cada área según su uso operativo mediante el campo `tipo_area`:
  - `POTRERO` (Pastoreo extensivo o rotacional).
  - `CORRAL` (Corral de manejo, brete, manga o engorde intensivo).
  - `CUARENTENA` (Aislamiento sanitario).
  - `MATERNIDAD` (Vacas paridas y crías lactantes).
  - `OTRO` (Instalación auxiliar o potrero de descanso).
- **RF-09 (Trazado y Delimitación Poligonal):** EL SISTEMA deberá proporcionar herramientas interactivas de dibujo sobre el mapa satelital para trazar el perímetro poligonal cerrado de cada potrero o corral, capturando sus vértices en formato GeoJSON (`coordinates: [[[lng, lat], ...]]`).
- **RF-010 (Edición de Vértices):** EL SISTEMA deberá permitir a usuarios autorizados activar el modo edición sobre cualquier potrero existente, permitiendo arrastrar vértices, insertar nuevos puntos intermedios, suprimir vértices y recalcular automáticamente el área y el centroide.
- **RF-011 (Cálculo de Superficie):** EL SISTEMA deberá calcular de forma geométrica y automática la superficie aproximada en hectáreas (ha) a partir del polígono trazado (usando fórmulas geodésicas esferoidales).
- **RF-012 (Capacidad de Carga Animal):** EL SISTEMA deberá registrar para cada potrero su capacidad estimada en cabezas de ganado.
- **RF-013 (Paleta de Colores Diferenciada):** EL SISTEMA deberá asignar o permitir seleccionar un color distintivo para cada potrero/corral, renderizando el polígono con un trazo sólido de borde (2px) y un relleno translúcido (opacidad 0.25 en reposo, 0.45 al pasar el cursor o seleccionar).
- **RF-014 (Desactivación Protegida):** CUANDO un usuario intente desactivar o eliminar un potrero que contenga animales activos, EL SISTEMA deberá bloquear la acción e indicar que primero deben trasladarse los animales presentes hacia otra ubicación.

### 4.4. Representación y Distribución Visual de Animales
- **RF-015 (Asignación Automática de Puntos):** EL SISTEMA deberá calcular algorítmicamente y en tiempo de ejecución las coordenadas visuales de cada animal perteneciente al potrero, distribuyéndolos de forma homogénea (*pseudo-random scatter* acotado o malla interna equidistante) estrictamente dentro del polígono del potrero.
- **RF-016 (Zoom Progresivo y Nivel de Detalle):**
  - **Zoom lejano (escala predio, zoom < 16):** El mapa mostrará los polígonos coloreados con una insignia flotante (*badge*) que indique el nombre del potrero y la cantidad de animales activos presentes (ej: `Potrero 1: 8 cabezas`).
  - **Zoom cercano (escala operativa, zoom >= 16):** El mapa renderizará los puntos individuales de cada animal con icono representativo según sexo (`🐂` Macho, `🐄` Hembra) y color según categoría o estado.
- **RF-017 (Tooltip y Tarjeta Rápida):** Al posar el cursor o hacer clic sobre un punto de animal, EL SISTEMA mostrará un cuadro emergente con:
  - Arete oficial (o "S/N").
  - Código interno (GAN-XXXX).
  - Nombre o alias (si existe).
  - Raza y Sexo.
  - Peso actual en kg.
  - Botón "Ver Perfil 360°" (que abre la ficha integral del animal).
  - Botón "Trasladar Animal".

### 4.5. Movimiento de Ganado por Arrastre (Drag & Drop)
- **RF-018 (Arrastre Individual):** EL SISTEMA deberá permitir hacer clic sostenido (o toque táctil prolongado) sobre el punto de un animal y arrastrarlo libremente a través del mapa satelital.
- **RF-019 (Detección Point-in-Polygon):** Al soltar el marcador del animal, EL SISTEMA deberá ejecutar un algoritmo geométrico de punto en polígono (Ray-Casting Algorithm) para identificar sobre qué potrero o corral cayó el cursor.
- **RF-020 (Validación de Mismo Origen):** SI el animal es soltado dentro del mismo potrero donde ya se encuentra, EL SISTEMA cancelará el traslado sin registrar movimiento redundante y devolverá el punto a su posición original.
- **RF-021 (Soltado Fuera de Todo Potrero):** SI el animal es soltado en un área que no pertenece a ningún polígono delimitado, EL SISTEMA mostrará una notificación de aviso ("Ubicación no válida: debe soltar el animal dentro de un potrero o corral registrado") y devolverá el punto a su origen.
- **RF-022 (Ventana Modal de Confirmación de Arrastre):** CUANDO el animal sea soltado dentro de un potrero destino válido diferente al origen, EL SISTEMA abrirá de inmediato una ventana modal de confirmación con:
  - Datos del animal (Código, Arete, Nombre, Raza).
  - Potrero de origen y Potrero de destino.
  - Fecha del movimiento (predeterminada en la fecha actual de Bolivia, editable).
  - Campo opcional: Motivo del traslado (selector desplegable con motivos estándar + "Otro").
  - Campo opcional: Responsable del traslado (texto o selector de trabajador).
  - Campo opcional: Observaciones.
  - Botones "Confirmar Traslado" y "Cancelar".
- **RF-023 (Cancelación de Arrastre):** SI el usuario presiona "Cancelar" o cierra el modal, el animal regresará a su posición original y no se modificará la base de datos.

### 4.6. Movimiento Manual (Individual y por Lotes)
- **RF-024 (Panel Lateral de Potrero):** Al seleccionar un potrero en el mapa satelital o en la lista, se desplegará un panel lateral derecho con las características del área y la tabla de todos los animales actualmente presentes.
- **RF-025 (Selección Múltiple):** La lista de animales del potrero dispondrá de casillas de verificación individuales y una casilla maestra "Seleccionar Todos", mostrando un contador en tiempo real de animales seleccionados.
- **RF-026 (Botón "Trasladar Lote"):** Al tener uno o más animales seleccionados, se habilitará el botón principal `Trasladar Seleccionados (N)`, abriendo el modal de movimiento por lote.
- **RF-027 (Formulario de Movimiento Masivo):** El modal permitirá elegir el potrero o corral de destino en una lista desplegable (excluyendo el actual), fecha de movimiento, motivo, responsable y notas.
- **RF-028 (Ejecución Atómica de Lotes):** Al confirmar, el backend procesará el traslado de todos los animales seleccionados en una única transacción atómica SQL: si un solo animal falla (por ejemplo, porque fue vendido concurrentemente), la operación completa se revierte (*rollback*).

### 4.7. Reglas de Negocio, Integridad y Estados
- **RF-029 (Sincronización Bidireccional con SPEC-001):**
  - Cada vez que un animal sea trasladado a un nuevo potrero, el backend actualizará atómicamente:
    `animal.potrero_id = nuevo_potrero.id`
    `animal.ubicacion = nuevo_potrero.nombre`
  - Toda consulta previa de `animal.ubicacion` (reportes, filtros de SPEC-001, exportaciones a Excel) continuará funcionando de forma idéntica y sin discrepancias.
- **RF-030 (Compatibilidad con Animales Existentes):** Los 10 animales que actualmente existen en la base de datos con `"Potrero 1"` y `"CORRAL DE MANEJO"` se asociarán automáticamente mediante migración de datos al registrarse los potreros con esos mismos nombres, sin requerir reingreso manual.
- **RF-031 (Exclusión de Animales No Activos):**
  - Animales con estado `VENDIDO`, `FALLECIDO`, `ROBADO`, `PERDIDO`, `SACRIFICADO`, `DESCARTADO` o `BAJA` **jamás aparecerán como puntos en el mapa ni en la lista de animales activos de los potreros**.
  - Si un usuario intenta forzar el traslado de un animal inactivo, el sistema rechazará la solicitud con error HTTP 400.
- **RF-032 (Alerta No Bloqueante de Capacidad):** CUANDO la cantidad de animales en el potrero destino tras el movimiento supere su `capacidad_cabezas`, EL SISTEMA mostrará una advertencia destacada en amarillo:
  *"Advertencia: El potrero destino tiene una capacidad recomendada de X cabezas y pasará a tener Y cabezas. ¿Desea continuar de todos modos?"*
  El usuario podrá continuar si confirma deliberadamente la sobrecarga.

### 4.8. Historial, Trazabilidad y Anulaciones
- **RF-033 (Comprobante Correlativo de Movimiento):** Cada operación de traslado generará un comprobante único correlativo e inmutable con formato `MOV-GAN-YYYYMM-XXXX` (ej: `MOV-GAN-202611-0001`).
- **RF-034 (Historial en Perfil 360° del Animal):** En la Ficha Perfil 360° del animal (pestaña *Procedencia & Historial*), se desplegará la cronología completa de todos los potreros por los que ha transitado, indicando fecha, potrero origen, potrero destino, motivo y responsable.
- **RF-035 (Historial del Potrero):** Cada potrero mantendrá su bitácora cronológica de entradas y salidas de ganado.
- **RF-036 (Anulación de Movimiento):** EL SISTEMA permitirá anular un movimiento confirmado si no existen movimientos posteriores incompatibles para los animales involucrados. La anulación devolverá los animales a su potrero anterior y registrará el suceso en la Bitácora de Auditoría.

---

## 5. Requisitos no funcionales

- **RNF-01 (Rendimiento del Mapa y Renderizado):** El renderizado de los polígonos y de hasta 1.000 puntos de ganado sobre el mapa satelital deberá ejecutarse a no menos de 60 FPS sin bloquear el hilo principal de la interfaz de usuario, empleando capas optimizadas de Canvas / SVG en Leaflet.
- **RNF-02 (Cero Costo de APIs Cartográficas):** No se utilizarán servicios de pago por consumo (como Google Maps Platform o Mapbox comercial) que requieran tarjetas de crédito corporativas. Se utilizarán teselas satelitales estándar Open Geospatial (Esri World Imagery) de acceso público y confiable.
- **RNF-03 (Consistencia Transaccional ACID):** Todo movimiento de ganado (sea individual o de 50 cabezas) se ejecutará bajo una transacción atómica con nivel de aislamiento serializable o consistente, actualizando simultáneamente el comprobante, el detalle, los animales y la bitácora.
- **RNF-04 (Auditoría Integral en Bitácora con Zona Horaria Bolivia UTC-4):** Toda creación de potrero, edición de polígono, movimiento de ganado o anulación se asentará de forma inmediata e inmutable en la tabla `bitacora` con fecha y hora oficial de Bolivia (`America/La_Paz`, UTC-4).
- **RNF-05 (Diseño Responsivo Multi-Dispositivo):**
  - **Escritorio / Laptop (>= 1024px):** Disposición de pantalla dividida con mapa satelital amplio al centro/izquierda y panel lateral colapsable de potreros y animales a la derecha.
  - **Tablets y Móviles (< 1024px):** El mapa satelital ocupará el 100% del viewport; el panel de detalles y las listas de animales se desplegarán mediante hojas inferiores deslizables (*bottom sheets*) o modales táctiles adaptados.

---

## 6. Modelo de datos y arquitectura de persistencia

### 6.1. Tabla `potrero`
Representa cada división territorial o instalación física del predio.

```sql
CREATE TABLE potrero (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,               -- POT-0001, COR-0001, etc.
    nombre VARCHAR(100) NOT NULL,                     -- Potrero 1, Corral de Manejo, etc.
    tipo_area VARCHAR(40) DEFAULT 'POTRERO' NOT NULL, -- POTRERO, CORRAL, CUARENTENA, MATERNIDAD, OTRO
    superficie_ha NUMERIC(10, 2) NULL,                -- Superficie calculada en hectáreas
    capacidad_cabezas INT DEFAULT 50 NOT NULL,         -- Capacidad recomendada de cabezas
    color_hex VARCHAR(20) DEFAULT '#10b981' NOT NULL,  -- Color del polígono (#10b981, #3b82f6, etc.)
    poligono_geojson TEXT NOT NULL,                   -- GeoJSON Geometry (Polygon / MultiPolygon)
    centroide_lat NUMERIC(10, 6) NULL,                -- Latitud del centro para centrado y etiquetas
    centroide_lng NUMERIC(10, 6) NULL,                -- Longitud del centro para centrado y etiquetas
    estado VARCHAR(20) DEFAULT 'ACTIVO' NOT NULL,     -- ACTIVO, INACTIVO
    observaciones TEXT NULL,
    usuario_registro_ci VARCHAR(30) REFERENCES usuario(ci) ON DELETE SET NULL,
    fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC-4') NOT NULL,
    fecha_actualizacion TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC-4') NOT NULL
);

CREATE INDEX idx_potrero_codigo ON potrero(codigo);
CREATE INDEX idx_potrero_nombre ON potrero(nombre);
CREATE INDEX idx_potrero_tipo_area ON potrero(tipo_area);
CREATE INDEX idx_potrero_estado ON potrero(estado);
```

### 6.2. Modificación a la tabla `animal` (Enlace Relacional)
Se agrega la clave foránea `potrero_id` vinculando al potrero actual:

```sql
ALTER TABLE animal ADD COLUMN potrero_id INT NULL REFERENCES potrero(id) ON DELETE SET NULL;
CREATE INDEX idx_animal_potrero_id ON animal(potrero_id);

-- Regla de sincronización:
-- animal.ubicacion se mantiene sincronizada con potrero.nombre
```

### 6.3. Tabla `movimiento_ganado` (Cabecera)
Representa cada operación formal de traslado de animales.

```sql
CREATE TABLE movimiento_ganado (
    id SERIAL PRIMARY KEY,
    numero_comprobante VARCHAR(50) UNIQUE NOT NULL,      -- MOV-GAN-202611-0001
    fecha_movimiento DATE NOT NULL,                      -- Fecha del traslado
    potrero_origen_id INT NOT NULL REFERENCES potrero(id) ON DELETE RESTRICT,
    potrero_destino_id INT NOT NULL REFERENCES potrero(id) ON DELETE RESTRICT,
    tipo_operacion VARCHAR(30) DEFAULT 'MANUAL' NOT NULL,-- ARRASTRE_MAPA, MANUAL_INDIVIDUAL, MANUAL_GRUPAL
    cantidad_animales INT NOT NULL,                      -- Cantidad de cabezas trasladas
    motivo VARCHAR(100) NULL,                            -- Rotación, Engorde, Destete, etc.
    responsable VARCHAR(150) NULL,                       -- Nombre o cargo del responsable
    observaciones TEXT NULL,
    estado VARCHAR(20) DEFAULT 'CONFIRMADO' NOT NULL,    -- CONFIRMADO, ANULADO
    motivo_anulacion TEXT NULL,
    usuario_ci VARCHAR(30) REFERENCES usuario(ci) ON DELETE SET NULL,
    fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC-4') NOT NULL
);

CREATE INDEX idx_movimiento_comprobante ON movimiento_ganado(numero_comprobante);
CREATE INDEX idx_movimiento_fecha ON movimiento_ganado(fecha_movimiento);
CREATE INDEX idx_movimiento_origen ON movimiento_ganado(potrero_origen_id);
CREATE INDEX idx_movimiento_destino ON movimiento_ganado(potrero_destino_id);
CREATE INDEX idx_movimiento_estado ON movimiento_ganado(estado);
```

### 6.4. Tabla `movimiento_ganado_detalle`
Renglones con cada animal participante del movimiento.

```sql
CREATE TABLE movimiento_ganado_detalle (
    id SERIAL PRIMARY KEY,
    movimiento_id INT NOT NULL REFERENCES movimiento_ganado(id) ON DELETE CASCADE,
    animal_id INT NOT NULL REFERENCES animal(id) ON DELETE RESTRICT,
    numero_arete VARCHAR(50) NULL,
    codigo_interno VARCHAR(50) NOT NULL,
    potrero_origen_id INT NOT NULL,
    potrero_destino_id INT NOT NULL
);

CREATE INDEX idx_mov_detalle_movimiento ON movimiento_ganado_detalle(movimiento_id);
CREATE INDEX idx_mov_detalle_animal ON movimiento_ganado_detalle(animal_id);
```

---

## 7. Endpoints de la API REST

Todos los endpoints se alojan bajo el prefijo `/api/ganaderia`:

| Método | Endpoint | Permiso Requerido | Descripción |
|---|---|---|---|
| `GET` | `/potreros` | `GANADERIA_VER` | Lista todos los potreros/corrales con sus polígonos GeoJSON, área y cantidad de animales activos. |
| `POST` | `/potreros` | `GANADERIA_EDITAR` | Crea un nuevo potrero o corral con su polígono delimitado y capacidad. |
| `GET` | `/potreros/{id}` | `GANADERIA_VER` | Obtiene el detalle de un potrero y la lista de todos sus animales presentes. |
| `PUT` | `/potreros/{id}` | `GANADERIA_EDITAR` | Actualiza datos y/o vértices del polígono de un potrero existente. |
| `PATCH` | `/potreros/{id}/desactivar` | `GANADERIA_EDITAR` | Desactiva un potrero (únicamente si tiene 0 animales activos). |
| `GET` | `/mapa-distribucion` | `GANADERIA_VER` | Devuelve en 1 sola consulta optimizada los potreros delimitados y todos los animales activos con sus coordenadas internas calculadas. |
| `POST` | `/movimientos` | `GANADERIA_CREAR` | Registra un movimiento (por arrastre en mapa o selección de lote) y actualiza la ubicación de los animales. |
| `GET` | `/movimientos` | `GANADERIA_VER` | Historial paginado de movimientos con filtros por fecha, potrero origen/destino y motivo. |
| `GET` | `/movimientos/{id}` | `GANADERIA_VER` | Consulta el comprobante y detalle de un movimiento específico. |
| `POST` | `/movimientos/{id}/anular` | `GANADERIA_EDITAR` | Anula un movimiento revirtiendo la ubicación de los animales de forma segura. |
| `GET` | `/animales/{id}/historial-movimientos` | `GANADERIA_VER` | Cronología de traslados de un animal particular para su Ficha Perfil 360°. |

---

## 8. Casos límite y reglas de excepción

- **CE-01 (Animal sin arete físico):** Si un animal aún no tiene arete colocado (ej: ternero o cría recién nacida), el punto en el mapa y la confirmación de arrastre lo identificarán claramente por su código inmutable `GAN-XXXX` y su sexo/raza.
- **CE-02 (Arrastre fuera de potrero):** Si el operador suelta el punto del animal en un área del mapa satelital que no corresponde a ningún polígono registrado, el marcador regresará suavemente a su posición original mediante animación y no se ejecutará ninguna petición a la base de datos.
- **CE-03 (Potrero de destino inactivo):** Si un potrero fue dado de baja o marcado como inactivo, no podrá ser seleccionado como destino ni en el mapa ni en el selector manual.
- **CE-04 (Concurrencia de movimientos simultáneos):** Si dos usuarios intentan mover el mismo animal al mismo tiempo desde terminales distintas, el bloqueo a nivel de fila (`SELECT ... FOR UPDATE`) procesará el primer traslado y rechazará el segundo con una notificación amigable: *"El animal GAN-XXXX ya ha sido trasladado recientemente por otro usuario. La vista se actualizará automáticamente."*
- **CE-05 (Reversión o anulación que genera inconsistencias):** Si se intenta anular un movimiento de hace 15 días, pero uno de los animales involucrados ya fue trasladado posteriormente a un tercer potrero o vendido, la anulación directa será rechazada para evitar saltos temporales ilógicos en la trazabilidad.

---

## 9. Criterios de aceptación y checklist de finalización

- [ ] **Acceso en Sidebar:** El botón `Gestión de Potreros y Movimientos` aparece ubicado en el menú lateral exactamente entre `Registro / Identificación del Ganado` y `Bitácora de Auditoría`.
- [ ] **Carga del Mapa Satelital:** El mapa carga satélite nítido de Esri World Imagery sin errores de consola ni requerimiento de claves API externas.
- [ ] **Encuadre Automático:** Al ingresar, el mapa ajusta automáticamente su zoom para encuadrar todos los potreros del predio.
- [ ] **Nombres Libres de Potreros:** Es posible crear y editar potreros con cualquier nombre libre (ej: `Potrero 1`, `Corral de Manejo`, `Potrero Don Felipe`), sin restricción a "A, B, C, D".
- [ ] **Tipos de Área:** Es posible registrar tanto potreros de pastoreo como corrales de manejo, maternidad y cuarentena.
- [ ] **Delimitación y Edición de Polígonos:** Las herramientas de dibujo permiten trazar y luego mover vértices de los polígonos sobre el mapa.
- [ ] **Distribución Automática de Puntos:** Los animales asignados a un potrero aparecen como puntos individuales distribuidos visualmente dentro de su área poligonal.
- [ ] **Zoom Progresivo:** Al alejarse se aprecian nombres y conteo total de cabezas; al acercarse se visualizan los animales individuales con arete y código.
- [ ] **Tooltip y Perfil 360°:** Hacer clic en un animal muestra su tarjeta flotante y permite abrir su Perfil 360°.
- [ ] **Movimiento por Arrastre (Drag & Drop):** Es posible arrastrar un animal de un potrero a otro, abriéndose la ventana de confirmación antes de impactar en la base de datos.
- [ ] **Movimiento por Lote:** Es posible marcar varios animales de un potrero y trasladarlos juntos mediante formulario manual.
- [ ] **Sincronización Bidireccional:** El traslado actualiza atómicamente `animal.potrero_id` y `animal.ubicacion`.
- [ ] **Compatibilidad con Datos Existentes:** Los animales ya registrados en la BD con `Potrero 1` y `CORRAL DE MANEJO` se vinculan automáticamente a sus potreros respectivos.
- [ ] **Animales Vendidos o Dados de Baja:** No aparecen en el mapa satelital pero conservan su historial de ubicaciones previas.
- [ ] **Alerta de Capacidad:** Si el destino excede su capacidad de cabezas, se muestra una alerta visual permitiendo confirmación deliberada.
- [ ] **Historial y Comprobantes:** Cada movimiento genera su comprobante correlativo `MOV-GAN-YYYYMM-XXXX`.
- [ ] **Auditoría en Bitácora:** Todos los movimientos se asientan en la tabla `bitacora` con hora oficial de Bolivia (UTC-4).
- [ ] **Responsividad Móvil y Táctil:** El mapa y los paneles funcionan fluidamente tanto en pantallas de escritorio como en tablets y smartphones.
