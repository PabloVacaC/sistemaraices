# SPEC-004.md — Gestión Agrícola

## Contexto y objetivo

El módulo de Agricultura permitirá gestionar las áreas agrícolas de un establecimiento mediante un mapa satelital interactivo. El usuario podrá delimitar parcelas mediante polígonos, conocer automáticamente su superficie en hectáreas y gestionar el ciclo agrícola de cada área, desde la preparación del terreno hasta la cosecha. El objetivo es ofrecer una herramienta visual, sencilla e intuitiva para registrar las actividades agrícolas, controlar el avance de los cultivos y consultar el historial de campañas, sin incorporar funcionalidades complejas que dificulten la demostración inicial del sistema.

## Usuarios / actores

- Administrador del establecimiento.
- Encargado agrícola.
- Usuario autorizado para gestionar las áreas y actividades agrícolas.

## Historias de usuario

**H1:** Como encargado agrícola, quiero visualizar el establecimiento en un mapa satelital para identificar y gestionar visualmente mis áreas de cultivo.

**H2:** Como encargado agrícola, quiero delimitar áreas agrícolas mediante polígonos para conocer la superficie de cada parcela.

**H3:** Como encargado agrícola, quiero crear un ciclo agrícola para cada área para controlar las actividades realizadas durante una campaña.

**H4:** Como encargado agrícola, quiero registrar las actividades de cada fase para conocer el avance del cultivo.

**H5:** Como encargado agrícola, quiero consultar el historial de ciclos de cada área para conocer los cultivos y resultados de campañas anteriores.

---

# Requisitos funcionales

## RF-1 — Visualización del mapa

CUANDO el usuario ingrese al módulo de Agricultura, EL SISTEMA deberá mostrar un mapa satelital interactivo del establecimiento.

EL SISTEMA deberá permitir:

- Acercar y alejar el mapa (zoom).
- Desplazarse por el mapa.
- Visualizar las áreas agrícolas delimitadas.
- Seleccionar un área para consultar su información.
- Visualizar las áreas mediante polígonos.

## RF-2 — Delimitación de áreas agrícolas

CUANDO el usuario cree una nueva área agrícola, EL SISTEMA deberá permitir dibujar un polígono sobre el mapa.

EL SISTEMA deberá:

- Permitir agregar puntos para delimitar el área.
- Permitir modificar los puntos del polígono.
- Permitir eliminar puntos durante la edición.
- Calcular automáticamente la superficie delimitada en hectáreas.
- Permitir guardar el área.
- Permitir asignar un nombre o identificador al área.

SI el polígono no es válido o no posee una superficie calculable, ENTONCES EL SISTEMA deberá impedir su guardado e informar al usuario.

## RF-3 — Gestión de áreas agrícolas

CUANDO el usuario seleccione un área agrícola, EL SISTEMA deberá mostrar:

- Nombre o identificador.
- Superficie en hectáreas.
- Estado actual.
- Cultivo actual, si existe.
- Campaña actual, si existe.
- Fase actual del ciclo agrícola, si existe.

EL SISTEMA deberá permitir editar el nombre del área y su delimitación geográfica.

Las áreas agrícolas deberán mantenerse independientemente de los ciclos agrícolas que se realicen sobre ellas.

## RF-4 — Gestión de ciclos agrícolas

CUANDO el usuario cree un ciclo agrícola sobre un área, EL SISTEMA deberá permitir registrar:

- Área agrícola.
- Cultivo.
- Campaña o temporada agrícola.
- Fecha de inicio.
- Superficie utilizada.

EL SISTEMA deberá permitir iniciar nuevos ciclos sobre áreas que hayan sido utilizadas en campañas anteriores.

EL SISTEMA deberá conservar el historial de ciclos anteriores de cada área.

SI un área ya posee un ciclo activo, ENTONCES EL SISTEMA deberá informar al usuario antes de permitir crear otro ciclo activo sobre la misma área.

## RF-5 — Fases del ciclo agrícola

EL SISTEMA deberá organizar cada ciclo agrícola en las siguientes cuatro fases:

1. Preparación del terreno.
2. Siembra.
3. Fumigación y manejo del cultivo.
4. Cosecha.

EL SISTEMA deberá mostrar visualmente la fase actual del ciclo y su avance.

---

## RF-6 — Fase 1: Preparación del terreno

CUANDO el usuario ingrese a la fase de Preparación del terreno, EL SISTEMA deberá mostrar las siguientes actividades:

- Arado.
- Rastra.
- Rolo.

EL SISTEMA deberá permitir registrar cada actividad con:

- Fecha.
- Tipo de actividad.
- Estado: Pendiente o Completada.

EL SISTEMA deberá mostrar el progreso de la fase mediante un indicador visual.

Ejemplo:

- Arado: Completado.
- Rastra: Completado.
- Rolo: Pendiente.

Progreso: 2 de 3 actividades completadas.

EL SISTEMA deberá permitir actualizar el estado de cada actividad.

## RF-7 — Fase 2: Siembra

CUANDO el usuario ingrese a la fase de Siembra, EL SISTEMA deberá permitir registrar:

- Cultivo.
- Variedad o híbrido.
- Fecha de siembra.
- Superficie sembrada.

EL SISTEMA deberá permitir registrar cultivos como:

- Soya.
- Maíz.
- Sorgo.
- Trigo.
- Otros cultivos.

EL SISTEMA deberá permitir seleccionar un cultivo existente o registrar uno nuevo si corresponde.

## RF-8 — Fase 3: Fumigación y manejo del cultivo

EL SISTEMA deberá permitir registrar múltiples actividades durante el desarrollo del ciclo agrícola.

Las actividades disponibles deberán incluir:

- Fumigación.
- Herbicidas.
- Insecticidas.
- Fungicidas.
- Fertilización.
- Aplicación foliar.

Cada registro deberá contener:

- Fecha.
- Tipo de actividad.
- Producto utilizado.
- Cantidad aplicada.
- Observación opcional.

EL SISTEMA deberá mostrar las actividades registradas en forma de listado cronológico.

EL SISTEMA deberá permitir agregar nuevos registros durante toda la fase de desarrollo del cultivo.

## RF-9 — Fase 4: Cosecha

CUANDO el usuario ingrese a la fase de Cosecha, EL SISTEMA deberá permitir registrar:

- Fecha de inicio de cosecha.
- Fecha de finalización, opcional.
- Cultivo cosechado.
- Superficie cosechada.
- Cantidad producida.

EL SISTEMA deberá permitir registrar cosechas realizadas durante varios días.

EL SISTEMA deberá calcular automáticamente el rendimiento por hectárea cuando se disponga de la superficie y la cantidad producida.

EL SISTEMA deberá permitir finalizar el ciclo agrícola cuando el usuario confirme que la cosecha ha concluido.

## RF-10 — Estado visual de las áreas

EL SISTEMA deberá mostrar visualmente el estado de cada área agrícola mediante colores o indicadores.

Los estados deberán representar, como mínimo:

- Sin ciclo activo.
- Preparación del terreno.
- Siembra.
- Desarrollo del cultivo.
- Cosecha.
- Ciclo finalizado.

Los colores deberán permitir identificar rápidamente el estado de cada área desde el mapa.

## RF-11 — Historial agrícola

CUANDO el usuario consulte un área agrícola, EL SISTEMA deberá permitir visualizar los ciclos agrícolas anteriores.

Cada ciclo histórico deberá mostrar:

- Cultivo.
- Campaña.
- Fecha de inicio.
- Fases realizadas.
- Actividades registradas.
- Datos de cosecha, cuando existan.
- Rendimiento, cuando pueda calcularse.

EL SISTEMA deberá conservar la información de ciclos finalizados.

## RF-12 — Navegación y visualización

EL SISTEMA deberá permitir consultar las áreas agrícolas desde el mapa y acceder a sus detalles.

La información del ciclo agrícola deberá presentarse de forma sencilla, organizada por fases.

EL SISTEMA deberá priorizar una interfaz visual clara que permita realizar una demostración del funcionamiento del módulo sin requerir capacitación extensa.

---

# Requisitos no funcionales

## RNF-1 — Usabilidad

La interfaz deberá ser sencilla, intuitiva y visual.

Las operaciones principales deberán poder realizarse con pocos pasos.

## RNF-2 — Diseño adaptable

La interfaz deberá adaptarse a:

- Computadoras.
- Tablets.
- Dispositivos móviles.

## RNF-3 — Rendimiento

El mapa y las áreas agrícolas deberán cargar de forma fluida.

La consulta y actualización de actividades no deberá generar retrasos perceptibles durante el uso normal.

## RNF-4 — Integridad de información

Los ciclos agrícolas, actividades y registros de cosecha deberán mantenerse vinculados al área correspondiente.

La edición de un área no deberá eliminar su historial agrícola.

## RNF-5 — Persistencia

Los datos de áreas, ciclos y actividades deberán almacenarse permanentemente y estar disponibles cuando el usuario vuelva a ingresar al módulo.

---

# Casos límite

- Un área no posee un polígono válido.
- El usuario intenta guardar un área sin nombre.
- El usuario intenta crear un ciclo sin seleccionar cultivo.
- El usuario intenta crear un segundo ciclo activo sobre un área que ya posee uno.
- Un área tiene una superficie de 0 hectáreas o un polígono inválido.
- El usuario registra una actividad sin fecha.
- El usuario registra una cantidad de producto igual a cero o negativa.
- El usuario registra una cosecha sin superficie.
- El usuario finaliza un ciclo sin registrar cosecha.
- El usuario modifica el polígono de un área que posee ciclos históricos.
- El usuario consulta un área que todavía no posee ciclos agrícolas.
- El usuario abandona el formulario sin guardar los cambios.

---

# Fuera de alcance

En esta primera versión NO se incluirán:

- Gestión avanzada de maquinaria agrícola.
- Gestión de combustible.
- Gestión de mano de obra.
- Control de costos agrícolas detallado.
- Integración automática con inventario de productos.
- Integración automática con contabilidad.
- Planificación avanzada de cultivos.
- Predicción de rendimiento mediante inteligencia artificial.
- Sensores IoT.
- Monitoreo meteorológico automático.
- Imágenes satelitales históricas.
- Análisis de índices vegetativos.
- Riego automatizado.
- Gestión avanzada de semillas e insumos.
- Trazabilidad comercial de la producción.
- Gestión de contratos de venta agrícola.

La estructura deberá permitir incorporar estas funcionalidades posteriormente sin necesidad de rediseñar completamente el módulo.

---

# Criterios de finalización

- El usuario puede visualizar el establecimiento mediante un mapa satelital.
- El usuario puede crear, editar y visualizar áreas agrícolas mediante polígonos.
- La superficie de cada área se calcula automáticamente.
- El usuario puede crear ciclos agrícolas sobre las áreas.
- El ciclo posee las cuatro fases definidas.
- El usuario puede registrar y actualizar las actividades de preparación.
- El usuario puede registrar los datos de siembra.
- El usuario puede registrar actividades de fumigación y manejo del cultivo.
- El usuario puede registrar datos de cosecha.
- El sistema muestra el estado y avance del ciclo.
- El usuario puede consultar el historial agrícola de cada área.
- La información permanece almacenada después de cerrar y volver a abrir el sistema.
- La interfaz funciona correctamente en computadora, tablet y móvil.
- El flujo principal puede realizarse completamente durante una demostración.

---

# Dudas abiertas

[NECESITA ACLARACIÓN] ¿El sistema deberá permitir que un ciclo agrícola utilice solamente una parte del área delimitada, o inicialmente siempre se utilizará toda la superficie del área?

[NECESITA ACLARACIÓN] ¿La cantidad cosechada deberá registrarse en kilogramos, toneladas o permitir seleccionar la unidad?

[NECESITA ACLARACIÓN] ¿Las actividades de preparación del terreno (Arado, Rastra y Rolo) serán obligatorias para completar la fase o podrán omitirse?

[NECESITA ACLARACIÓN] ¿El usuario podrá marcar manualmente una fase como finalizada, o el sistema deberá avanzar automáticamente cuando se completen las actividades requeridas?

[NECESITA ACLARACIÓN] ¿Las áreas agrícolas podrán dividirse, unirse o cambiar su delimitación después de haber registrado ciclos históricos?
