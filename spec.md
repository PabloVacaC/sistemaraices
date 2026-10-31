# ESPECIFICACIÓN DE REQUISITOS DE SOFTWARE (SRS)
## SISTEMAS RAÍCES — Gestión de Planillas, Pagos, Anticipos y Liquidación Salarial

**Versión:** 1.0  
**Estado:** Especificación funcional propuesta para revisión y desarrollo.  
**Sistema:** SISTEMAS RAÍCES — Gestión Empresarial y Recursos.

---

# 1. Contexto y objetivo

El sistema SISTEMAS RAÍCES incorporará un módulo de Planilla integrado con el módulo existente de Pagos y Anticipos, con el propósito de administrar el ciclo salarial mensual de los trabajadores, desde el cálculo de sus haberes hasta el registro de anticipos, descuentos, pagos de quincena y liquidaciones de sueldo.

El sistema permitirá consultar planillas por mes y año, calcular los salarios de acuerdo con los días trabajados, registrar múltiples anticipos y descuentos mediante ítems dinámicos, controlar los pagos pendientes, conservar el historial laboral y salarial, emitir comprobantes y cerrar formalmente los períodos mensuales. Se garantizará que los movimientos se contabilicen una sola vez, que los cambios salariales no alteren períodos históricos y que las planillas cerradas permanezcan bloqueadas. La interfaz será interactiva, de manera que el usuario pueda agregar, consultar y administrar los movimientos directamente desde la planilla, sin tener que volver a escribir los datos del trabajador.

# 2. Usuarios y actores

## 2.1. Usuario responsable de Planilla y Pagos

Es el usuario encargado de administrar el ciclo salarial.

Podrá:

- Consultar y gestionar planillas mensuales.
- Revisar los datos de los trabajadores.
- Registrar anticipos y descuentos.
- Registrar los pagos de quincena.
- Consultar las sugerencias de pago.
- Modificar el importe de quincena que decida pagar.
- Registrar liquidaciones y pagos parciales.
- Consultar saldos pendientes y negativos.
- Emitir comprobantes.
- Consultar períodos anteriores.
- Cerrar planillas.
- Consultar el historial de movimientos.

## 2.2. Administrador o auditor

Será responsable de supervisar las operaciones salariales y consultar los registros de auditoría, de acuerdo con sus permisos.

Podrá revisar las operaciones registradas, las anulaciones justificadas y el historial de los movimientos.

## 2.3. Trabajador

Es el beneficiario del salario.

Sus datos laborales se obtendrán del registro existente en el sistema. El trabajador podrá recibir comprobantes de anticipos, pagos de quincena y liquidaciones mediante los mecanismos habilitados.

No se presupone que el trabajador pueda modificar directamente la planilla.

## 2.4. Sistema

Será responsable de calcular los importes, gestionar los períodos, conservar los datos históricos, controlar los estados de las planillas, actualizar los totales y evitar la duplicación de movimientos.

---

# 3. Historias de usuario

## 3.1. Gestión de planillas

- **H1:** Como usuario responsable, quiero acceder al módulo Planilla desde el menú principal para gestionar los salarios de los trabajadores.
- **H2:** Como usuario responsable, quiero visualizar automáticamente el período mensual actual para trabajar en la planilla correspondiente.
- **H3:** Como usuario responsable, quiero consultar meses anteriores para revisar o completar las operaciones de planillas que todavía estén abiertas.
- **H4:** Como usuario responsable, quiero visualizar todos los trabajadores activos que correspondan al período para conocer sus importes salariales.
- **H5:** Como usuario responsable, quiero que los datos laborales se recuperen del registro del trabajador para evitar introducirlos nuevamente.
- **H6:** Como usuario responsable, quiero que cada planilla conserve los importes salariales de su período para evitar modificaciones históricas involuntarias.
- **H7:** Como usuario responsable, quiero cerrar una planilla después de revisar sus cálculos y pendientes para impedir modificaciones posteriores.

## 3.2. Gestión interactiva de anticipos y descuentos

- **H8:** Como usuario responsable, quiero agregar varios anticipos mediante ítems dinámicos dentro de la planilla para registrar todas las entregas realizadas a un trabajador.
- **H9:** Como usuario responsable, quiero agregar varios descuentos mediante ítems independientes para registrar diferentes deducciones.
- **H10:** Como usuario responsable, quiero que los totales se actualicen automáticamente al agregar o modificar un movimiento para conocer el saldo real del trabajador.
- **H11:** Como usuario responsable, quiero registrar anticipos superiores al saldo disponible cuando sea necesario, recibiendo una advertencia antes de confirmar.
- **H12:** Como usuario responsable, quiero que los anticipos entregados entre los días 1 y 5 se incorporen a la planilla siguiente para mantener correctamente separados los períodos.
- **H13:** Como usuario responsable, quiero consultar las fechas, conceptos e importes de cada movimiento para mantener un historial detallado.

## 3.3. Quincenas y liquidaciones

- **H14:** Como usuario responsable, quiero que el sistema sugiera el importe de quincena a pagar considerando los anticipos anteriores al corte.
- **H15:** Como usuario responsable, quiero poder modificar el importe sugerido de quincena para registrar el pago que realmente decida realizar.
- **H16:** Como usuario responsable, quiero calcular el líquido pagable descontando los anticipos, los descuentos y la quincena para conocer el importe restante.
- **H17:** Como usuario responsable, quiero visualizar los saldos negativos para identificar los casos que necesitan regularización.
- **H18:** Como usuario responsable, quiero registrar pagos pendientes o parciales para controlar las obligaciones salariales todavía no completadas.
- **H19:** Como usuario responsable, quiero generar comprobantes de las operaciones para disponer de evidencia de los importes entregados.

---

# 4. Requisitos funcionales (criterios de aceptación en EARS)

# 4.1. Gestión de períodos y planillas

## RF-1. Ubicación del módulo

CUANDO el usuario acceda al menú principal, EL SISTEMA DEBERÁ mostrar el módulo Planilla ubicado entre Inventario y Pagos y Anticipos.

## RF-2. Selección del período actual

CUANDO el usuario ingrese al módulo Planilla, EL SISTEMA DEBERÁ seleccionar inicialmente el período correspondiente al mes y año actuales.

## RF-3. Selector de períodos

CUANDO el usuario seleccione otro mes y año, EL SISTEMA DEBERÁ cargar la información correspondiente exclusivamente a la planilla seleccionada.

El selector deberá permitir consultar tanto períodos anteriores como períodos existentes del año actual.

## RF-4. Cambio automático de mes

CUANDO comience un nuevo mes, EL SISTEMA DEBERÁ mostrar el nuevo período al ingresar al módulo, sin impedir que el usuario regrese a los meses anteriores.

EL SISTEMA DEBERÁ permitir continuar trabajando en planillas anteriores mientras permanezcan abiertas.

## RF-5. Conservación de períodos históricos

EL SISTEMA DEBERÁ conservar los registros de cada período, incluyendo los trabajadores asociados, los haberes básicos, los días trabajados, los anticipos, los descuentos, las quincenas, los pagos y los estados de cierre.

## RF-6. Datos salariales históricos

CUANDO se modifique el haber básico de un trabajador, EL SISTEMA DEBERÁ utilizar el nuevo importe para los períodos que correspondan, sin modificar los importes históricos ya registrados en períodos anteriores.

## RF-7. Unicidad de la planilla mensual

EL SISTEMA DEBERÁ mantener una única planilla por mes y año, salvo que una decisión posterior de negocio establezca expresamente otra modalidad.

## RF-8. Estado de la planilla

EL SISTEMA DEBERÁ manejar, como mínimo, los siguientes estados:

- **ABIERTA:** permite registrar y modificar movimientos autorizados.
- **CERRADA:** permite consultar los datos históricos, pero no modificar los registros del período.

---

# 4.2. Tabla principal de Planilla

## RF-9. Estructura visual de la planilla

CUANDO el usuario ingrese al módulo, EL SISTEMA DEBERÁ mostrar una tabla con las siguientes columnas, respetando el orden definido:

1. Numeración.
2. Nombre completo.
3. Cargo.
4. Área.
5. Fecha de ingreso.
6. Haber básico.
7. Días trabajados del período.
8. Total ganado.
9. Pago de quincena.
10. Pago de anticipos.
11. Total de anticipos y descuentos.
12. Anticipos para el período siguiente.
13. Líquido pagable.

La interfaz deberá mantener una estructura tabular similar a la planilla de referencia proporcionada por el usuario.

## RF-10. Numeración de trabajadores

EL SISTEMA DEBERÁ enumerar consecutivamente a los trabajadores que correspondan a la planilla seleccionada.

La numeración será visual y no deberá confundirse con el identificador interno del trabajador.

## RF-11. Recuperación de datos del trabajador

CUANDO se cargue una planilla, EL SISTEMA DEBERÁ recuperar del registro del trabajador los siguientes datos:

- Nombre completo.
- Cargo.
- Área.
- Fecha de ingreso correspondiente al período laboral.
- Haber básico aplicable al período.

EL SISTEMA NO DEBERÁ exigir que el usuario vuelva a escribir estos datos en cada planilla.

## RF-12. Trabajadores activos

CUANDO se cargue una planilla, EL SISTEMA DEBERÁ mostrar los trabajadores activos que correspondan al período seleccionado.

Los trabajadores que se encuentren inactivos no deberán aparecer en las nuevas planillas de períodos en los que no estuvieron activos.

Los trabajadores que hayan trabajado durante un período anterior deberán conservar su información histórica en dicho período.

## RF-13. Interactividad de la tabla

CUANDO el usuario interactúe con las columnas de anticipos, descuentos, quincena o liquidación, EL SISTEMA DEBERÁ permitir consultar el detalle correspondiente y ejecutar las operaciones autorizadas desde la interfaz.

Los importes resumidos de la tabla deberán estar vinculados a sus registros individuales.

EL SISTEMA NO DEBERÁ tratar los totales resumidos como movimientos independientes de los ítems que los componen.

## RF-14. Actualización automática de importes

CUANDO el usuario registre, modifique o anule un movimiento permitido en una planilla abierta, EL SISTEMA DEBERÁ actualizar los totales afectados y recalcular el líquido pagable.

---

# 4.3. Días trabajados y total ganado

## RF-15. Cálculo automático de días trabajados

CUANDO se genere o actualice el registro salarial de un trabajador, EL SISTEMA DEBERÁ calcular los días trabajados del período a partir de las fechas de inicio y fin de su actividad laboral, considerando los límites del período mensual.

El cálculo deberá considerar:

- La fecha de ingreso o inicio de actividad.
- El primer y último día del período mensual.
- La fecha de inactividad, cuando corresponda.
- Los días de actividad que correspondan a ese trabajador durante el período.

El día de ingreso y el último día de actividad se contabilizarán como días trabajados.

## RF-16. Modificación de días trabajados

CUANDO el usuario modifique manualmente los días trabajados, EL SISTEMA DEBERÁ permitir la modificación en una planilla abierta y recalcular el total ganado.

EL SISTEMA DEBERÁ validar que los días registrados sean un valor entero no negativo y que no excedan el límite mensual de 30 días utilizado por la fórmula salarial.

La modificación no deberá cambiar automáticamente los días registrados en una planilla cerrada.

## RF-17. Fórmula del total ganado

EL SISTEMA DEBERÁ calcular el total ganado mediante la siguiente fórmula:

**Total ganado = (Haber básico / 30) × Días trabajados**

El divisor será siempre 30, independientemente de que el mes calendario tenga 28, 29 o 31 días.

El resultado monetario deberá redondearse a dos decimales.

## RF-18. Primer período laboral

CUANDO un trabajador ingrese durante un mes, EL SISTEMA DEBERÁ calcular el total ganado proporcionalmente a los días trabajados desde su fecha de ingreso hasta el final del período, inclusive.

Ejemplo:

- Haber básico: Bs 3.500.
- Fecha de ingreso: día 15.
- Fin del período: día 30.
- Días trabajados: 16.

Total ganado = (3.500 / 30) × 16 = Bs 1.866,67.

## RF-19. Mes completo

CUANDO un trabajador tenga 30 días computables en el período, EL SISTEMA DEBERÁ calcular el total ganado como el haber básico mensual completo.

Ejemplo:

- Haber básico: Bs 3.500.
- Días trabajados: 30.
- Total ganado: Bs 3.500.

EL SISTEMA NO DEBERÁ mantener el cálculo proporcional del primer mes en los períodos completos siguientes.

## RF-20. Último período laboral

CUANDO un trabajador sea desactivado y tenga registrada su fecha de inactividad, EL SISTEMA DEBERÁ utilizar esa fecha como último día de actividad para calcular los días trabajados del período correspondiente.

Ejemplo:

- Haber básico: Bs 3.500.
- Último día de actividad: día 20.
- Días computables, suponiendo que estuvo activo desde el día 1: 20.
- Total ganado: Bs 2.333,33.

## RF-21. Conservación del haber básico del período

CUANDO se modifique el sueldo de un trabajador, EL SISTEMA DEBERÁ conservar el haber básico que corresponda a cada planilla histórica.

Los cambios posteriores no deberán recalcular automáticamente el total ganado de las planillas cerradas.

---

# 4.4. Gestión interactiva de anticipos

## RF-22. Registro de anticipos mediante ítems

CUANDO el usuario seleccione la columna Pago de anticipos de un trabajador, EL SISTEMA DEBERÁ mostrar el detalle de anticipos correspondiente a ese trabajador y período.

La interfaz deberá disponer de una acción visible, como **Agregar anticipo**, para registrar nuevos ítems.

Cada ítem deberá permitir registrar, como mínimo:

- Fecha de entrega.
- Importe en bolivianos.
- Concepto u observación.
- Método de pago, cuando corresponda.
- Estado del movimiento.

EL SISTEMA DEBERÁ permitir agregar tantos ítems como sean necesarios.

La interfaz no deberá limitarse a un único campo de anticipo por trabajador.

## RF-23. Edición y eliminación visual de ítems

MIENTRAS la planilla permanezca abierta, EL SISTEMA DEBERÁ permitir modificar los datos de los anticipos según los permisos del usuario.

Los movimientos confirmados no deberán desaparecer silenciosamente de la auditoría.

CUANDO un movimiento deba anularse, EL SISTEMA DEBERÁ conservar el registro histórico y aplicar el procedimiento de anulación correspondiente.

## RF-24. Total de anticipos

EL SISTEMA DEBERÁ calcular el total de anticipos de un trabajador mediante la suma de los ítems válidos que correspondan al período seleccionado.

**Total de anticipos = suma de los anticipos contabilizables del período.**

Los movimientos anulados no deberán formar parte del total vigente.

Los anticipos del período siguiente deberán mantenerse separados hasta que correspondan a la nueva planilla.

## RF-25. Anticipos anteriores al día 18

CUANDO se registre un anticipo con fecha de entrega anterior al pago de quincena del día 18, EL SISTEMA DEBERÁ incluirlo en el total de anticipos anteriores al corte.

Estos anticipos se utilizarán para calcular la sugerencia de quincena.

## RF-26. Anticipos posteriores al día 18

CUANDO se registre un anticipo posterior al corte de quincena, EL SISTEMA DEBERÁ incluirlo en el total de anticipos del período y considerarlo en el cálculo del líquido pagable.

EL SISTEMA NO DEBERÁ restar el anticipo posterior al corte de la quincena ya calculada o liquidada.

## RF-27. Anticipos superiores al saldo disponible

CUANDO el usuario registre un anticipo cuyo importe supere el saldo salarial disponible estimado, EL SISTEMA DEBERÁ mostrar una advertencia indicando el importe disponible y la diferencia que excede ese importe.

EL SISTEMA DEBERÁ permitir al usuario confirmar el anticipo a pesar de la advertencia.

EL SISTEMA NO DEBERÁ bloquear automáticamente la operación únicamente por superar el saldo estimado.

## RF-28. Anticipos después de liquidar

SI la liquidación de un trabajador ya está registrada como completada, ENTONCES EL SISTEMA DEBERÁ advertir al usuario si intenta registrar un nuevo anticipo para ese período.

EL SISTEMA DEBERÁ impedir que una operación se registre en un período cerrado.

La gestión de anticipos excepcionales posteriores a una liquidación completada deberá respetar las reglas de autorización que se definan para esa operación.

---

# 4.5. Gestión interactiva de descuentos

## RF-29. Registro de descuentos mediante ítems

CUANDO el usuario seleccione la columna Total de anticipos y descuentos, EL SISTEMA DEBERÁ permitir consultar los anticipos y descuentos que componen el importe.

La interfaz deberá disponer de una acción como **Agregar descuento**.

Cada descuento deberá permitir registrar, como mínimo:

- Fecha.
- Importe en bolivianos.
- Motivo o concepto.
- Observación opcional.
- Estado del movimiento.

EL SISTEMA DEBERÁ permitir agregar tantos descuentos como sean necesarios.

## RF-30. Cálculo de descuentos

EL SISTEMA DEBERÁ sumar los descuentos válidos registrados para el trabajador en el período.

Ejemplo:

- Descuento por daño de equipo: Bs 100.
- Segundo descuento: Bs 50.
- Total descuentos: Bs 150.

## RF-31. Total de anticipos y descuentos

EL SISTEMA DEBERÁ calcular automáticamente:

**Total de anticipos y descuentos = total de anticipos del período + total de descuentos del período.**

Ejemplo:

- Anticipos: Bs 1.000.
- Descuentos: Bs 100.
- Total de anticipos y descuentos: Bs 1.100.

EL SISTEMA DEBERÁ actualizar el importe al agregar, modificar o anular un movimiento permitido.

## RF-32. Trazabilidad de descuentos

CUANDO se registre un descuento, EL SISTEMA DEBERÁ conservar su concepto, fecha e importe para que el usuario pueda identificar su origen.

EL SISTEMA NO DEBERÁ reemplazar el detalle de los descuentos por un único importe agregado.

---

# 4.6. Pago de quincena

## RF-33. Quincena de referencia

EL SISTEMA DEBERÁ utilizar Bs 1.000 como importe de referencia de la quincena, permitiendo que el usuario registre un importe diferente cuando corresponda.

El pago de quincena se realizará normalmente el día 18.

## RF-34. Cálculo de la quincena sugerida

EL SISTEMA DEBERÁ calcular la sugerencia de quincena de acuerdo con la siguiente fórmula:

**Quincena sugerida = máximo entre cero y (Bs 1.000 − anticipos anteriores al corte de quincena).**

Ejemplo:

- Quincena de referencia: Bs 1.000.
- Anticipos anteriores al corte: Bs 800.
- Quincena sugerida: Bs 200.

## RF-35. Anticipos iguales o superiores a la quincena

SI los anticipos anteriores al corte son iguales o superiores a Bs 1.000, ENTONCES EL SISTEMA DEBERÁ sugerir un pago de quincena de Bs 0.

EL SISTEMA DEBERÁ mostrar una advertencia cuando los anticipos superen la referencia de Bs 1.000.

## RF-36. Modificación del importe de quincena

CUANDO el usuario registre el pago de quincena, EL SISTEMA DEBERÁ permitir modificar el importe sugerido.

SI el importe registrado supera la sugerencia, ENTONCES EL SISTEMA DEBERÁ mostrar una advertencia y permitir que el usuario confirme el pago.

La sugerencia será informativa y no constituirá un límite obligatorio.

## RF-37. Registro del pago de quincena

CUANDO el usuario confirme un pago de quincena, EL SISTEMA DEBERÁ registrar el importe efectivamente pagado y actualizar la columna Pago de quincena.

El importe registrado deberá conservarse como un movimiento independiente de los anticipos.

## RF-38. Quincena sin desembolso

CUANDO el usuario revise la quincena y decida no realizar un pago porque los anticipos ya cubrieron o superaron el importe de referencia, EL SISTEMA DEBERÁ permitir registrar una constancia de revisión de Bs 0, siempre que no se registre un desembolso inexistente.

La constancia de revisión no deberá contabilizarse como dinero entregado.

## RF-39. Unicidad de pagos

EL SISTEMA DEBERÁ impedir que una misma operación de pago de quincena se registre dos veces por un reintento de la misma solicitud.

Los pagos adicionales reales deberán registrarse como operaciones independientes.

---

# 4.7. Anticipos para el período siguiente (días 1 al 5)

## RF-40. Registro de anticipos del período siguiente

CUANDO el usuario registre anticipos destinados al período siguiente durante los días 1 al 5, EL SISTEMA DEBERÁ permitir agregarlos como ítems independientes en la columna Anticipos para el período siguiente.

Cada ítem deberá conservar su fecha real, importe y concepto.

## RF-41. Cálculo del total de anticipos del período siguiente

EL SISTEMA DEBERÁ calcular la suma de todos los ítems registrados en la columna Anticipos para el período siguiente.

Ejemplo:

- Anticipo del día 3: Bs 500.
- Anticipo del día 4: Bs 100.
- Total para el período siguiente: Bs 600.

Si no existen movimientos, la columna podrá mostrar Bs 0.

## RF-42. Separación del período actual

MIENTRAS un anticipo esté registrado como correspondiente al período siguiente, EL SISTEMA NO DEBERÁ incluirlo en el total de anticipos ni en el líquido pagable del período actual.

## RF-43. Incorporación a la planilla siguiente

CUANDO se habilite la planilla siguiente, EL SISTEMA DEBERÁ incorporar los anticipos pendientes del período siguiente al detalle de anticipos de esa nueva planilla.

Los movimientos deberán conservar su fecha real de entrega y quedar vinculados al período en el que corresponde contabilizarlos.

## RF-44. Evitar la duplicación de anticipos

EL SISTEMA DEBERÁ garantizar que cada anticipo del período siguiente se incorpore una sola vez a la planilla correspondiente.

La consulta repetida de la planilla o el cambio de mes no deberán duplicar los movimientos.

## RF-45. Independencia del pago salarial anterior

CUANDO se registre un anticipo del período siguiente, EL SISTEMA NO DEBERÁ modificar el total ganado, los descuentos ni el líquido pagable de la planilla salarial anterior.

El hecho de que el sueldo de un período anterior se pague durante los primeros cinco días del mes siguiente no cambiará el período al que pertenece ese sueldo.

---

# 4.8. Cálculo del líquido pagable

## RF-46. Fórmula del líquido pagable

EL SISTEMA DEBERÁ calcular el líquido pagable de acuerdo con la siguiente fórmula:

**Líquido pagable = total ganado − total de anticipos y descuentos − pago de quincena.**

El cálculo utilizará los movimientos contabilizables correspondientes al período seleccionado.

## RF-47. Actualización del líquido pagable

CUANDO cambie el total ganado, el total de anticipos y descuentos o el pago de quincena, EL SISTEMA DEBERÁ recalcular automáticamente el líquido pagable.

## RF-48. Saldos negativos

SI el líquido pagable es inferior a cero, ENTONCES EL SISTEMA DEBERÁ mostrar el saldo negativo exacto con dos decimales.

EL SISTEMA NO DEBERÁ reemplazarlo automáticamente por cero ni trasladarlo sin autorización al período siguiente.

## RF-49. Regularización de saldos

CUANDO un trabajador tenga un saldo negativo de un período anterior, EL SISTEMA DEBERÁ conservar el registro histórico y permitir al usuario decidir si corresponde realizar una regularización posterior.

EL SISTEMA NO DEBERÁ descontar automáticamente el saldo negativo de una nueva planilla sin autorización.

## RF-50. Distinción entre saldo salarial y dinero pagado

EL SISTEMA DEBERÁ distinguir el líquido pagable calculado del dinero efectivamente entregado.

El importe pendiente de pago deberá poder consultarse independientemente del resultado de la fórmula salarial.

---

# 4.9. Desactivación y reactivación de trabajadores

## RF-51. Desactivación

CUANDO un trabajador sea desactivado, EL SISTEMA DEBERÁ registrar su fecha de inactividad y utilizarla como último día de actividad para el cálculo del período correspondiente.

## RF-52. Exclusión de períodos posteriores

CUANDO se genere una nueva planilla correspondiente a un período posterior a la inactividad del trabajador, EL SISTEMA DEBERÁ excluirlo de la lista operativa de trabajadores activos.

## RF-53. Conservación del historial

EL SISTEMA DEBERÁ conservar los datos, anticipos, descuentos, quincenas y liquidaciones de los períodos anteriores en los que el trabajador estuvo activo.

## RF-54. Reactivación

CUANDO se reactive a un trabajador, EL SISTEMA DEBERÁ registrar una nueva fecha de ingreso o inicio de actividad.

EL SISTEMA DEBERÁ conservar los períodos laborales anteriores, sin sobrescribir ni eliminar su historial.

## RF-55. Saldo pendiente al reactivar

CUANDO se reactive a un trabajador que tenga un saldo negativo anterior, EL SISTEMA DEBERÁ conservar ese saldo y permitir al usuario decidir si corresponde regularizarlo en la nueva planilla.

---

# 4.10. Liquidación del sueldo restante

## RF-56. Cálculo del sueldo restante

CUANDO el usuario consulte la liquidación salarial de un trabajador, EL SISTEMA DEBERÁ mostrar el desglose de los importes que intervienen en el cálculo:

- Total ganado del período.
- Total de anticipos.
- Total de descuentos.
- Pagos de quincena.
- Otros pagos o ajustes, si se habilitan.
- Líquido pagable.
- Importe efectivamente pagado.
- Saldo pendiente.

El total ganado deberá respetar el cálculo proporcional definido en los requisitos RF-15 a RF-21.

## RF-57. Pago de sueldo pendiente

EL SISTEMA DEBERÁ permitir registrar la liquidación del sueldo restante correspondiente a un período anterior, aunque el calendario ya se encuentre en un nuevo mes, siempre que la planilla a la que pertenece el pago siga abierta.

## RF-58. Pagos parciales

CUANDO el usuario registre un pago parcial de una liquidación, EL SISTEMA DEBERÁ conservar el importe pagado y recalcular el saldo pendiente de esa liquidación.

## RF-59. Estado de liquidación

EL SISTEMA DEBERÁ distinguir, como mínimo, los siguientes estados:

- **PENDIENTE:** no se ha completado el pago.
- **PARCIAL:** existe un pago, pero todavía queda saldo pendiente.
- **LIQUIDADO:** el importe correspondiente ha sido cubierto según los registros de pago.

EL SISTEMA NO DEBERÁ considerar liquidada una obligación únicamente porque el usuario haya abierto o revisado su detalle.

## RF-60. Métodos de pago

CUANDO se registre un pago, EL SISTEMA DEBERÁ permitir seleccionar el método de pago habilitado, por ejemplo, efectivo, transferencia o cheque.

El método elegido deberá quedar asociado al movimiento.

---

# 4.11. Módulo de Pagos y Anticipos

## RF-61. Estructura del módulo

EL SISTEMA DEBERÁ organizar el módulo Pagos y Anticipos en las siguientes vistas:

1. **Panel General.**
2. **Registrar Anticipo.**
3. **Pagos Parciales y Liquidación.**
4. **Historial y Movimientos.**

## RF-62. Panel General

CUANDO el usuario acceda al Panel General, EL SISTEMA DEBERÁ mostrar indicadores del período seleccionado, incluyendo:

- Total de anticipos.
- Total de sueldos pagados.
- Cantidad de liquidaciones completadas.
- Cantidad de liquidaciones pendientes.
- Dinero efectivamente entregado.
- Dinero pendiente de pago.

Los indicadores deberán calcularse a partir de los registros correspondientes al período.

## RF-63. Registrar anticipo

CUANDO el usuario seleccione un trabajador, EL SISTEMA DEBERÁ mostrar su información salarial y permitir registrar un anticipo mediante los campos definidos en RF-22.

La operación deberá estar vinculada a la planilla y al período correspondiente.

## RF-64. Pagos parciales y liquidación

EL SISTEMA DEBERÁ ofrecer una tabla de control del personal que permita consultar los importes de quincena, las liquidaciones y los saldos pendientes.

La tabla deberá facilitar el acceso a las acciones de pago y al historial del trabajador.

## RF-65. Historial y movimientos

EL SISTEMA DEBERÁ mostrar un historial cronológico de anticipos, descuentos, pagos de quincena, pagos parciales y liquidaciones.

Cada movimiento deberá poder consultarse por trabajador y período.

Las anulaciones deberán identificarse claramente y no deberán confundirse con movimientos vigentes.

## RF-66. Integración con Planilla

CUANDO el usuario registre una operación desde Pagos y Anticipos, EL SISTEMA DEBERÁ actualizar los totales de la planilla correspondiente.

CUANDO el usuario registre una operación desde Planilla, EL SISTEMA DEBERÁ reflejarla en el historial de Pagos y Anticipos.

Ambos módulos deberán consultar los mismos registros de movimientos, evitando mantener dos importes independientes para una misma operación.

---

# 4.12. Comprobantes oficiales

## RF-67. Numeración de comprobantes

EL SISTEMA DEBERÁ generar una numeración única y no reutilizable para los comprobantes.

Se utilizarán los siguientes formatos:

- Vales de anticipo: `ANT-YYYYMM-XXXX`.
- Liquidaciones salariales: `LIQ-YYYYMM-XXXX`.
- Pagos parciales y quincenas: `PAG-YYYYMM-XXXX`.

Los números de comprobante deberán conservarse aunque una operación sea anulada.

## RF-68. Vale de anticipo

CUANDO se emita un vale de anticipo, EL SISTEMA DEBERÁ mostrar:

1. Encabezado institucional de SISTEMAS RAÍCES.
2. Número de comprobante y fecha.
3. Nombre del trabajador.
4. Documento de identidad, si está registrado.
5. Cargo y área.
6. Período salarial correspondiente.
7. Importe entregado.
8. Método de pago.
9. Detalle de anticipos del período.
10. Total de anticipos contabilizables.
11. Estado de la quincena.
12. Observaciones.
13. Identificación de quien autorizó la entrega.
14. Espacio de conformidad del trabajador.

## RF-69. Saldo estimado en el comprobante

CUANDO se genere un comprobante de anticipo, EL SISTEMA DEBERÁ mostrar el saldo salarial estimado después de registrar la operación.

El cálculo deberá considerar el total ganado del período, los anticipos contabilizables, los descuentos y los pagos de quincena u otros pagos ya registrados, evitando duplicar importes.

EL SISTEMA NO DEBERÁ ocultar los saldos negativos mediante una restricción matemática de cero.

El saldo del comprobante será informativo y no sustituirá al cálculo definitivo del líquido pagable.

## RF-70. Comprobante de liquidación o pago

CUANDO se genere un comprobante de liquidación o pago, EL SISTEMA DEBERÁ mostrar:

- Haber básico del período.
- Total ganado.
- Total de anticipos.
- Total de descuentos.
- Quincena pagada.
- Otros ajustes autorizados.
- Líquido pagable.
- Importe entregado en la operación.
- Saldo restante.
- Estado de la liquidación.

## RF-71. Impresión y PDF

EL SISTEMA DEBERÁ permitir visualizar e imprimir los comprobantes y generar una versión PDF.

El diseño deberá ser legible y apropiado para impresión en formato carta y, cuando se habilite, en formato de ticket.

## RF-72. Compartir comprobantes

CUANDO el usuario visualice un comprobante, EL SISTEMA PODRÁ ofrecer una opción para compartirlo mediante WhatsApp Web, la aplicación móvil o los mecanismos disponibles.

El sistema preparará el comprobante o mensaje para que el usuario pueda revisar y completar el envío.

---

# 4.13. Auditoría y anulación de movimientos

## RF-73. Registro de auditoría

EL SISTEMA DEBERÁ registrar las operaciones salariales relevantes, incluyendo:

- Registro de anticipos.
- Registro de descuentos.
- Registro de pagos.
- Modificaciones autorizadas.
- Anulaciones.
- Cierre de planillas.

La bitácora deberá identificar al usuario, la fecha y hora, el tipo de operación y el motivo cuando corresponda.

## RF-74. Anulación justificada

CUANDO el usuario solicite anular un movimiento, EL SISTEMA DEBERÁ exigir un motivo y registrar la operación en la bitácora.

El movimiento original deberá conservarse con estado ANULADO.

## RF-75. Recalcular después de una anulación

CUANDO se anule una operación en una planilla abierta, EL SISTEMA DEBERÁ recalcular los totales afectados utilizando únicamente los movimientos válidos.

## RF-76. Prohibición de anulación en períodos cerrados

MIENTRAS una planilla se encuentre cerrada, EL SISTEMA NO DEBERÁ permitir anular movimientos de ese período mediante las operaciones ordinarias.

Cualquier mecanismo excepcional de reapertura o corrección administrativa deberá definirse por separado y contar con autorización y auditoría.

---

# 5. Requisitos no funcionales

## RNF-1. Precisión monetaria

EL SISTEMA DEBERÁ utilizar tipos numéricos de precisión decimal para los importes monetarios, con dos decimales en los cálculos y resultados mostrados.

No deberán utilizarse cálculos monetarios basados exclusivamente en números binarios de punto flotante.

## RNF-2. Integridad transaccional

EL SISTEMA DEBERÁ guardar cada operación salarial y sus actualizaciones relacionadas dentro de una transacción consistente.

Si ocurre un error durante el registro, el sistema deberá evitar que el movimiento quede parcialmente guardado.

## RNF-3. Persistencia

EL SISTEMA DEBERÁ conservar los movimientos confirmados en la base de datos y permitir consultarlos después de cerrar o reiniciar la aplicación.

## RNF-4. Integridad de períodos

EL SISTEMA DEBERÁ mantener la relación entre cada movimiento y el período al que pertenece.

Los anticipos del período siguiente no deberán duplicarse ni contabilizarse en el período anterior.

## RNF-5. Seguridad

EL SISTEMA DEBERÁ verificar la autenticación y los permisos del usuario antes de permitir registrar movimientos, modificar planillas, emitir comprobantes o ejecutar cierres.

## RNF-6. Rendimiento

EL SISTEMA DEBERÁ cargar la tabla de trabajadores y sus totales mediante consultas optimizadas, evitando ejecutar innecesariamente una consulta independiente por cada trabajador y por cada movimiento.

## RNF-7. Interfaz interactiva

EL SISTEMA DEBERÁ permitir agregar múltiples ítems de anticipos y descuentos sin requerir un número fijo de filas.

Los totales deberán actualizarse al confirmar cada movimiento.

La interfaz deberá comunicar claramente cuándo un movimiento fue guardado, cuándo existe una advertencia y cuándo una operación no puede realizarse.

## RNF-8. Usabilidad y diseño responsivo

EL SISTEMA DEBERÁ mantener una interfaz comprensible en computadoras y pantallas más pequeñas.

La tabla podrá utilizar desplazamiento horizontal cuando sea necesario, sin ocultar las acciones principales ni perder la identificación del trabajador.

## RNF-9. Trazabilidad

EL SISTEMA DEBERÁ conservar la relación entre trabajadores, períodos laborales, planillas, movimientos y comprobantes.

## RNF-10. Consistencia entre módulos

EL SISTEMA DEBERÁ garantizar que Planilla y Pagos y Anticipos utilicen los mismos registros de anticipos, descuentos y pagos.

Una operación registrada en un módulo no deberá duplicarse al consultar el otro.

---

# 6. Casos límite

## CL-1. Trabajador que ingresa a mitad de mes

El sistema deberá calcular el total ganado proporcionalmente desde la fecha de ingreso, contando ese día como trabajado.

## CL-2. Trabajador que trabaja el mes completo

El sistema deberá calcular el total ganado con base en los 30 días computables.

## CL-3. Trabajador que deja de trabajar a mitad de mes

El sistema deberá utilizar la fecha de inactividad como último día trabajado y calcular el total ganado proporcionalmente.

## CL-4. Trabajador reactivado

El sistema deberá conservar el historial laboral anterior y registrar un nuevo período de actividad.

## CL-5. Cambio de sueldo

El sistema deberá conservar el haber básico histórico y utilizar el nuevo importe para los períodos que correspondan.

## CL-6. Anticipos superiores a Bs 1.000 antes de la quincena

El sistema deberá mostrar una quincena sugerida de Bs 0 y advertir cuánto superaron los anticipos la referencia.

## CL-7. Pago de quincena superior a la sugerencia

El sistema deberá mostrar una advertencia y permitir confirmar el importe que decida pagar el usuario.

## CL-8. Anticipo superior al saldo salarial disponible

El sistema deberá advertir cuánto excede el importe solicitado y permitir confirmar la operación.

## CL-9. Múltiples anticipos

El sistema deberá permitir registrar cualquier cantidad de anticipos y actualizar su total sin duplicar movimientos.

## CL-10. Múltiples descuentos

El sistema deberá permitir registrar cualquier cantidad de descuentos, conservar sus conceptos y actualizar el total correspondiente.

## CL-11. Saldo negativo

El sistema deberá mostrar el líquido pagable negativo y conservarlo para su revisión y regularización.

## CL-12. Anticipos de los días 1 al 5

El sistema deberá registrar estos anticipos en el período siguiente, sin modificar el total ganado ni el líquido pagable del período anterior.

## CL-13. Anticipo pendiente de incorporación

Si un anticipo del período siguiente todavía no se ha incorporado a la planilla correspondiente, el sistema deberá mantenerlo identificado para evitar perderlo.

La incorporación no deberá generar un segundo movimiento económico.

## CL-14. Cambio de mes con planilla anterior abierta

El sistema deberá mostrar el nuevo período y permitir regresar a la planilla anterior mientras permanezca abierta.

## CL-15. Cierre con pagos pendientes

El sistema deberá advertir los pagos pendientes y permitir que el usuario confirme el cierre.

## CL-16. Edición de planilla cerrada

El sistema deberá impedir las modificaciones ordinarias de una planilla cerrada.

## CL-17. Trabajador inactivo con saldo pendiente

El sistema deberá conservar su historial y permitir consultar sus obligaciones pendientes.

## CL-18. Reintento de una operación

El sistema deberá evitar que un mismo anticipo o pago se registre dos veces debido a un reintento técnico.

## CL-19. Dos usuarios operando simultáneamente

El sistema deberá proteger la integridad de los movimientos cuando dos usuarios intenten modificar o cerrar simultáneamente el mismo período.

## CL-20. Error durante el cierre

Si ocurre un error al cerrar una planilla, el sistema deberá evitar que el período quede en un estado inconsistente.

---

# 7. Fuera de alcance

Quedan fuera de esta especificación, salvo que se aprueben posteriormente:

- Declaraciones tributarias oficiales y generación automática de formularios fiscales.
- Conexión bancaria directa para ejecutar transferencias.
- Integración automática con servicios externos de nómina.
- Procesamiento automático de retenciones judiciales no registradas.
- Reapertura ordinaria de una planilla cerrada.
- Traslado automático de saldos negativos entre períodos.
- Modificación automática de planillas históricas por cambios posteriores en los trabajadores.
- Cálculo de beneficios laborales o conceptos adicionales que no hayan sido definidos.
- Descuentos automáticos de saldos negativos anteriores sin autorización.
- Acceso directo de los trabajadores a modificar su información salarial.

---

# 8. Criterios de finalización y aceptación

Los siguientes criterios deberán verificarse antes de considerar terminada la implementación.

- [ ] El módulo Planilla aparece entre Inventario y Pagos y Anticipos.
- [ ] El sistema muestra inicialmente el período actual.
- [ ] El selector permite consultar períodos anteriores.
- [ ] La tabla contiene las trece columnas especificadas.
- [ ] Los datos del trabajador se obtienen de sus registros existentes.
- [ ] Se muestran los trabajadores que corresponden al período.
- [ ] Los días trabajados se calculan automáticamente y pueden corregirse en planillas abiertas.
- [ ] El total ganado utiliza la fórmula haber básico dividido entre 30, multiplicado por los días trabajados.
- [ ] Los cambios salariales no alteran los períodos históricos.
- [ ] La planilla permite agregar múltiples anticipos mediante ítems.
- [ ] La planilla permite agregar múltiples descuentos mediante ítems.
- [ ] Los totales se actualizan al confirmar movimientos.
- [ ] Los anticipos superiores al saldo disponible generan una advertencia y pueden confirmarse.
- [ ] La quincena sugerida considera los anticipos anteriores al corte.
- [ ] El usuario puede modificar el importe sugerido de quincena.
- [ ] Los anticipos posteriores al corte no reducen una quincena ya calculada.
- [ ] Los anticipos de los días 1 al 5 se incorporan a la planilla siguiente una sola vez.
- [ ] El líquido pagable se calcula correctamente.
- [ ] Los saldos negativos permanecen visibles.
- [ ] La desactivación y reactivación de trabajadores conserva el historial.
- [ ] Las liquidaciones pueden quedar pendientes o parciales.
- [ ] Los comprobantes tienen numeración única y no reutilizable.
- [ ] Los movimientos anulados permanecen identificados en el historial.
- [ ] El cierre solicita confirmación y muestra advertencias de pendientes.
- [ ] Las planillas cerradas no permiten modificaciones ordinarias.
- [ ] Las operaciones se conservan después de reiniciar la aplicación.
- [ ] Las pruebas de backend, frontend e integridad de datos se completan satisfactoriamente.

---

# 9. Registro de decisiones de negocio

| ID | Decisión | Regla acordada |
|---|---|---|
| DB-001 | Período salarial | Una planilla corresponde a un mes y año. |
| DB-002 | Haber básico | Se conserva el importe histórico de cada período. |
| DB-003 | Cálculo salarial | Haber básico / 30 × días trabajados. |
| DB-004 | Días trabajados | Se calculan automáticamente y el usuario puede corregirlos en planillas abiertas. |
| DB-005 | Trabajadores inactivos | No aparecen en los períodos posteriores a su inactividad, pero conservan su historial. |
| DB-006 | Reactivación | Se registra una nueva fecha de ingreso sin eliminar los períodos laborales anteriores. |
| DB-007 | Quincena de referencia | Bs 1.000, con sugerencia calculada según los anticipos anteriores al corte. |
| DB-008 | Quincena modificable | El usuario puede registrar un importe superior a la sugerencia, previa advertencia. |
| DB-009 | Anticipos | Se permiten múltiples registros individuales por trabajador y período. |
| DB-010 | Descuentos | Se permiten múltiples registros individuales por trabajador y período. |
| DB-011 | Anticipos superiores al saldo | Se muestra una advertencia, pero se permite confirmar la operación. |
| DB-012 | Anticipos del 1 al 5 | Se registran para el período siguiente y se contabilizan una sola vez. |
| DB-013 | Líquido pagable | Total ganado − total de anticipos y descuentos − pago de quincena. |
| DB-014 | Saldo negativo | Se muestra y conserva para regularización. |
| DB-015 | Cierre de planilla | Requiere confirmación y muestra advertencias de pendientes. |
| DB-016 | Planilla cerrada | No permite modificaciones ordinarias. |
| DB-017 | Historial | Los movimientos y comprobantes anteriores se conservan. |
| DB-018 | Auditoría | Las anulaciones requieren motivo y registro de auditoría. |

---

# 10. Dudas abiertas y decisiones pendientes

Las siguientes cuestiones deberán resolverse antes de cerrar definitivamente el diseño técnico.

- **[NECESITA ACLARACIÓN] Creación de planillas:** determinar si la planilla del nuevo mes se crea automáticamente al cambiar el calendario o cuando el usuario ingresa por primera vez al período.
- **[NECESITA ACLARACIÓN] Reapertura excepcional:** definir si un administrador podrá autorizar la reapertura de una planilla cerrada mediante un procedimiento auditado.
- **[NECESITA ACLARACIÓN] Cambios salariales dentro de un período abierto:** determinar si un cambio del haber básico debe aplicarse a toda la planilla abierta o únicamente a los cálculos que todavía no hayan sido confirmados.
- **[NECESITA ACLARACIÓN] Fecha límite de quincena:** confirmar el tratamiento exacto de los anticipos entregados el día 18 cuando el pago de quincena todavía no se haya registrado.
- **[NECESITA ACLARACIÓN] Regularización de saldos negativos:** definir qué operación registrará la regularización y cómo se reflejará en el historial.
- **[NECESITA ACLARACIÓN] Anulación de anticipos con comprobante emitido:** definir el procedimiento de autorización y conservación del comprobante original.
- **[NECESITA ACLARACIÓN] Ajustes y bonos adicionales:** determinar si se incorporarán en una iteración posterior o si formarán parte de la primera versión.

---

# 11. Consideraciones para la implementación

La implementación deberá respetar las siguientes pautas:

1. Los movimientos salariales deberán almacenarse individualmente. Los totales de la tabla serán resultados calculados a partir de esos registros.
2. Los anticipos y descuentos deberán poder agregarse dinámicamente desde la interfaz mediante botones para añadir ítems.
3. Las operaciones realizadas desde Planilla y Pagos y Anticipos deberán actualizar los mismos registros.
4. Las planillas deberán conservar los datos históricos necesarios para reproducir sus cálculos.
5. El estado cerrado deberá comprobarse también en el backend, no solamente en la interfaz.
6. Las operaciones que modifiquen dinero deberán ejecutarse mediante transacciones consistentes.
7. Los cálculos monetarios deberán utilizar precisión decimal.
8. La interfaz deberá mostrar advertencias comprensibles y solicitar confirmación para las operaciones que lo requieran.
9. Los comprobantes deberán conservar su numeración original y el historial de sus anulaciones.
10. Antes de habilitar el sistema para uso real, deberán ejecutarse pruebas con trabajadores nuevos, trabajadores inactivos, múltiples anticipos, descuentos, quincenas, saldos negativos y cierres de planilla.

**Fin de la especificación funcional.**