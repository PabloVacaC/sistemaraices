# Especificación de Requisitos de Software (SRS) — Gestión de Planillas, Pagos, Anticipos y Liquidación Salarial

---

## 1. Contexto y objetivo

El sistema **SISTEMAS RAÍCES** incorpora y consolida la gestión integral del ciclo salarial de los trabajadores a través de dos módulos interconectados: **Planilla** y **Pagos y Anticipos**.

El objetivo central es proveer una plataforma automatizada, auditable y transparente para la administración de haberes, entregas de anticipos quincenales, liquidaciones finales de fin de mes y el cierre formal de planillas por período mensual. El sistema garantiza la trazabilidad histórica, el cálculo matemático exacto sin inconsistencias, la emisión inmutable de comprobantes correlativos oficiales (vales de anticipo y liquidaciones), el bloqueo de períodos cerrados y una experiencia fluida tanto en computadoras de escritorio como en dispositivos móviles.

---

## 2. Usuarios y actores

- **Usuario Responsable de Pagos / Planilla:** Administra los períodos salariales, registra entregas de anticipos, liquida pagos de quincena (día 18) y sueldos restantes (día 5), emite comprobantes oficiales, anula movimientos erróneos con justificación y ejecuta el cierre de planillas.
- **Trabajador:** Beneficiario del haber mensual, solicitante de anticipos salariales y receptor de los vales y comprobantes de pago digitales o impresos.
- **Administrador / Auditor:** Revisa la bitácora de auditoría de movimientos salariales, verifica el libro de pagos y supervisa la consistencia financiera.
- **Sistema:** Controla el ciclo de vida de los períodos (abierto/cerrado), ejecuta las reglas de corte por fecha (día 18 y día 5), calcula en tiempo real los saldos disponibles, genera numeración correlativa única e inmutable y bloquea modificaciones en períodos cerrados.

---

## 3. Historias de usuario

### Submódulo de Planillas y Períodos
- **H1:** Como usuario responsable, quiero acceder al módulo Planilla desde el menú principal para consultar y administrar las planillas salariales mensuales.
- **H2:** Como usuario responsable, quiero visualizar automáticamente el período del mes actual para operar directamente sobre la planilla vigente.
- **H3:** Como usuario responsable, quiero consultar planillas de meses anteriores para revisar la información histórica y liquidaciones pasadas.
- **H4:** Como usuario responsable, quiero que cada planilla conserve los datos salariales congelados de su período para que aumentos posteriores de sueldo no alteren cálculos históricos.
- **H5:** Como usuario responsable, quiero cerrar una planilla cuando concluya el ciclo de pagos para impedir modificaciones o adiciones accidentales.
- **H6:** Como usuario responsable, quiero recibir advertencias antes de cerrar una planilla con pagos o saldos pendientes para evitar omisiones involuntarias.
- **H7:** Como usuario responsable, quiero que los trabajadores inactivos o retirados conserven su historial en los períodos en que trabajaron para mantener trazabilidad legal.

### Submódulo de Pagos y Anticipos
- **H8:** Como usuario responsable, quiero seleccionar un trabajador y visualizar en tarjetas claras su Sueldo Base Mensual, sus anticipos recibidos, la quincena de referencia y su Saldo Salarial Estimado con su fórmula matemática transparente.
- **H9:** Como usuario responsable, quiero registrar anticipos salariales antes del día 18 para que se computen automáticamente como adelanto de la primera quincena.
- **H10:** Como usuario responsable, quiero que los anticipos registrados a partir del día 19 se clasifiquen como "Anticipos posteriores al día 18" para que no alteren la quincena (ya vencida) y se descuenten directamente en la liquidación final.
- **H11:** Como usuario responsable, quiero que el sistema me impida registrar un anticipo si el monto supera el saldo salarial disponible real del trabajador (restando anticipos previos y quincenas pagadas).
- **H12:** Como usuario responsable, quiero generar un Vale Oficial de Anticipo correlativo e inmutable (`ANT-YYYYMM-XXXX`) que detalle el sueldo base, la lista ordenada de anticipos, el estado de la quincena (con el importe descontado si ya fue pagada) y el saldo salarial estimado resultante.
- **H13:** Como usuario responsable, quiero gestionar en una sola tabla de control los pagos de quincena (día 18) y las liquidaciones de sueldo restante (día 5), con la columna de acción accesible entre el trabajador y su sueldo base.
- **H14:** Como usuario responsable, quiero pagar la quincena con el monto sugerido automático, o registrar una constancia de revisión en Bs 0.00 si el trabajador ya cubrió la quincena con anticipos previos.
- **H15:** Como usuario responsable, quiero liquidar el sueldo restante de fin de mes descontando exactamente el total de anticipos y los pagos parciales/quincena efectuados, pudiendo agregar bonos o ajustes auditables.
- **H16:** Como usuario responsable o trabajador, quiero imprimir en formato ticket/PDF o compartir vía WhatsApp el comprobante oficial de anticipo o liquidación desde cualquier dispositivo (móvil o PC).

---

## 4. Requisitos funcionales (Criterios de aceptación en EARS)

### Gestión de Períodos y Planillas

#### RF-1. Acceso y ubicación del módulo
CUANDO el usuario navegue en la barra de navegación lateral, EL SISTEMA DEBERÁ mostrar los accesos diferenciados para los módulos Planilla y Pagos y Anticipos.

#### RF-2. Selección automática del período vigente
CUANDO el usuario ingrese a cualquiera de los módulos salariales, EL SISTEMA DEBERÁ cargar de forma predeterminada el período correspondiente al mes y año en curso (o el período abierto más reciente si el actual no existe).

#### RF-3. Navegación histórica de períodos
CUANDO el usuario cambie el período seleccionado en el selector superior, EL SISTEMA DEBERÁ recargar todos los indicadores, tablas de anticipos, listas de pagos y liquidaciones asociadas exclusivamente a dicho período.

#### RF-4. Inmutabilidad de haberes básicos históricos
CUANDO se modifique el sueldo base mensual en la ficha de un trabajador, EL SISTEMA DEBERÁ aplicar el nuevo sueldo únicamente a períodos futuros o abiertos, sin alterar los sueldos base ni cálculos registrados en liquidaciones de períodos anteriores.

#### RF-5. Advertencia por pendientes al cerrar período
CUANDO el usuario solicite el cierre formal de una planilla o período salarial, EL SISTEMA DEBERÁ verificar si existen trabajadores con saldo pendiente de cobro o anticipos sin conciliar, y mostrar una ventana modal de advertencia detallando las obligaciones pendientes antes de exigir confirmación.

#### RF-6. Bloqueo de operaciones en períodos cerrados
MIENTRAS un período salarial se encuentre en estado `CERRADO`, EL SISTEMA NO DEBERÁ permitir:
- Registrar nuevos anticipos.
- Registrar pagos de quincena o liquidaciones.
- Modificar montos, fechas o conceptos de pagos existentes.
- Anular comprobantes de dicho período.

#### RF-7. Exclusión y retención de trabajadores inactivos
CUANDO un trabajador sea dado de baja en el módulo de personal, EL SISTEMA DEBERÁ excluirlo de las listas operativas de nuevos períodos, conservando intactos todos sus comprobantes, liquidaciones y registros históricos en los períodos donde estuvo activo.

---

### Módulo de Pagos y Anticipos

#### RF-8. Estructura modular y pestañas operativas
EL SISTEMA DEBERÁ organizar el módulo de Pagos y Anticipos en 4 vistas claramente accesibles:
1. **Panel General:** Cuadro de mando con KPIs financieros del mes (Total anticipos, Total sueldos pagados, Liquidaciones completadas vs pendientes, Dinero entregado vs pendiente).
2. **Registrar Anticipo:** Búsqueda rápida de trabajadores, resumen salarial en tarjetas y emisión de vales de anticipo.
3. **Pagos Parciales & Liquidación:** Matriz de control del personal con cálculo automático de quincenas (día 18) y liquidación de sueldo restante (día 5).
4. **Historial & Movimientos:** Libro diario cronológico de operaciones salariales por trabajador con opción de reimpresión y anulación auditada.

#### RF-9. Regla de corte de primera quincena (Día 18)
CUANDO se registre un anticipo cuya fecha de entrega sea menor o igual al día 18 del mes del período:
- EL SISTEMA DEBERÁ acumular dicho importe dentro de la métrica `Anticipos hasta Día 18`.
- EL SISTEMA DEBERÁ computarlo contra la `Quincena de Referencia` (fijada por defecto en Bs 1,000.00).

#### RF-10. Regla de anticipos posteriores al Día 18
CUANDO se registre un anticipo con fecha de entrega posterior al día 18 (día 19 en adelante):
- EL SISTEMA DEBERÁ clasificarlo bajo la métrica `Anticipos después del Día 18`.
- EL SISTEMA NO DEBERÁ restar este importe de la diferencia de quincena, acumulándolo directamente para su descuento en la liquidación final de sueldo.

#### RF-11. Cálculo y sugerencia de Quincena
EL SISTEMA DEBERÁ calcular dinámicamente la diferencia de quincena según la fórmula:
$$\text{Diferencia Quincena} = \text{Quincena Referencial (Bs 1,000.00)} - \text{Anticipos hasta Día 18}$$
- SI $\text{Anticipos hasta Día 18} < \text{Bs 1,000.00}$, ENTONCES EL SISTEMA DEBERÁ mostrar la diferencia positiva como monto sugerido a pagar en quincena.
- SI $\text{Anticipos hasta Día 18} \ge \text{Bs 1,000.00}$, ENTONCES EL SISTEMA DEBERÁ mostrar `Superó en Bs [Excedente]` y sugerir un importe de Bs 0.00 para la quincena.

#### RF-12. Registro de pago de quincena y constancia de revisión
CUANDO el usuario efectúe el pago de quincena desde la tabla de control:
- EL SISTEMA DEBERÁ permitir registrar un pago efectivo (`PAGO_QUINCENA`) por el monto acordado.
- SI la quincena ya fue cubierta por anticipos, EL SISTEMA DEBERÁ permitir registrar una constancia de revisión (`REVISION_QUINCENA`) por importe Bs 0.00.
- En ambos casos, EL SISTEMA DEBERÁ actualizar el estado de la quincena del trabajador a `LIQUIDADA`.

#### RF-13. Validación estricta de saldo disponible para anticipos
CUANDO el usuario ingrese el monto a solicitar en la entrega de un anticipo:
- EL SISTEMA DEBERÁ calcular el saldo salarial disponible real:
  $$\text{Saldo Disponible} = \text{Sueldo Base Mensual} + \text{Ajustes} - \text{Total Anticipos Previos} - \text{Total Pagos Realizados (Quincena / Parciales)}$$
- SI el monto solicitado supera el `Saldo Disponible`, ENTONCES EL SISTEMA DEBERÁ bloquear la confirmación del anticipo y mostrar una alerta impidiendo sobregirar el haber del trabajador.

#### RF-14. Bloqueo de anticipos a trabajadores liquidados
SI la liquidación de un trabajador para el período seleccionado ya se encuentra en estado `LIQUIDADO`, ENTONCES EL SISTEMA NO DEBERÁ permitir el registro de nuevos anticipos para dicho período.

#### RF-15. Liquidación salarial final de sueldo restante (Día 5)
CUANDO el usuario proceda a liquidar el sueldo de fin de mes de un trabajador:
- EL SISTEMA DEBERÁ presentar el desglose matemático:
  - (+) Sueldo Base Mensual
  - (-) Total Anticipos acumulados del período
  - (-) Pagos de Quincena y pagos parciales previos
  - (+/-) Ajustes o bonos adicionales editables
  - (=) Saldo Restante a Liquidar
- EL SISTEMA DEBERÁ permitir registrar pago inmediato (Efectivo, Transferencia, Cheque) o generar la liquidación en estado `PENDIENTE` o `PARCIAL`.
- CUANDO el saldo restante llegue a Bs 0.00, EL SISTEMA DEBERÁ cambiar el estado de la liquidación a `LIQUIDADO`.

---

### Comprobantes Oficiales y Vales

#### RF-16. Generación de numeración correlativa inmutable
EL SISTEMA DEBERÁ generar números de comprobante únicos, correlativos y no reutilizables con la estructura:
- Vales de Anticipo: `ANT-YYYYMM-XXXX` (ej. `ANT-202610-0019`)
- Liquidaciones Salariales: `LIQ-YYYYMM-XXXX` (ej. `LIQ-202610-0004`)
- Pagos Parciales / Quincena: `PAG-YYYYMM-XXXX` (ej. `PAG-202610-0013`)

#### RF-17. Desglose detallado en el Vale de Anticipo
CUANDO se genere o visualice un comprobante de anticipo (`ANT`), EL SISTEMA DEBERÁ mostrar una tarjeta limpia y legible con:
1. Encabezado institucional: "SISTEMAS RAÍCES - Gestión Empresarial y Recursos", número correlativo y fecha.
2. Datos de filiación: Trabajador, CI, Cargo, Área, Período Salarial.
3. Importe entregado destacado con el método de pago (Efectivo, Transferencia, etc.).
4. Cuadro "Estado y Desglose Salarial del Anticipo" conteniendo:
   - Sueldo Base Mensual enmarcado.
   - Lista cronológica ordenada de anticipos del período: Primer Anticipo (fecha, monto), Segundo Anticipo (fecha, monto), etc.
   - Total Anticipos acumulados.
   - Estado de la Quincena:
     - Si está liquidada: badge `LIQUIDADA` junto con el importe descontado `(- Bs X,XXX.XX)`.
     - Si no está liquidada: badge `PENDIENTE`.
   - Saldo Salarial Estimado Tras Anticipo:
     $$\text{Saldo Estimado} = \max(0, \text{Sueldo Base} + \text{Ajustes} - \text{Total Anticipos Acumulados} - \text{Quincena/Pagos Realizados})$$
5. Notas de pie de página: Observaciones registradas.
6. Bloque de firmas: "Entregado por (Nombre y CI de quien autorizó)" y "Recibí Conforme (Trabajador)".

#### RF-18. Desglose en Comprobante de Liquidación / Pago
CUANDO se emita o visualice un comprobante de liquidación o pago salarial (`LIQ` / `PAG`), EL SISTEMA DEBERÁ desglosar:
- Sueldo Base Mensual.
- (-) Total Anticipos descontados.
- (-) Quincena pagada previamente.
- (+/-) Otros Ajustes / Bonos.
- (=) Monto Liquidado / Entregado en la operación.
- Saldo Salarial Restante posterior a la operación.

#### RF-19. Exportación, Impresión y Compartir por WhatsApp
CUANDO el usuario visualice cualquier comprobante oficial en pantalla, EL SISTEMA DEBERÁ proveer:
- Botón **Imprimir / PDF:** Genera una versión limpia optimizada para impresoras térmicas de 80mm o formato carta PDF.
- Botón **Compartir por WhatsApp:** Genera el mensaje formateado con los datos clave del comprobante listo para enviar al trabajador vía WhatsApp Web o app móvil.
- Botón **Cerrar:** Cierra la vista modal regresando a la pantalla anterior sin perder el estado de búsqueda.

---

### Usabilidad, Auditoría y Diseño Responsivo

#### RF-20. Diseño responsivo para dispositivos móviles
CUANDO el usuario acceda desde un teléfono inteligente o pantalla con ancho menor a 768px:
- EL SISTEMA DEBERÁ apilar las columnas y cards verticalmente.
- Los botones de cierre y acciones de los modales de comprobante DEBERÁN permanecer siempre visibles y accesibles en pantalla.
- La tabla de control de pagos parciales DEBERÁ contar con scroll horizontal fluido manteniendo visible la identidad del trabajador.

#### RF-21. Ubicación ergonómica de acciones en tabla de pagos
EL SISTEMA DEBERÁ situar la columna `Acción` (botones de "Pagar Quincena", "Liquidar Sueldo", "Historial") inmediatamente después del nombre del trabajador y antes del Sueldo Base, permitiendo que el operador ejecute pagos rápidos sin necesidad de desplazar la tabla hacia la derecha en pantallas pequeñas o medianas.

#### RF-22. Bitácora de auditoría y anulación
CUANDO se anule una operación de anticipo o liquidación:
- EL SISTEMA DEBERÁ solicitar obligatoriamente un motivo de anulación justificado.
- EL SISTEMA DEBERÁ registrar el evento en la bitácora de auditoría inmutable (`accion="ANULAR"`, usuario autenticado, fecha/hora y motivo).
- EL SISTEMA DEBERÁ revertir los saldos salariales acumulados y marcar el comprobante con estado `ANULADO`.

---

## 5. Requisitos no funcionales (RNF)

- **RNF-1. Consistencia Financiera y Precisión Decimal:** Todas las operaciones de anticipos, quincenas, liquidaciones y saldos pendientes deben calcularse utilizando tipos numéricos de precisión fija (`Decimal` con 2 decimales en backend y redondeo bancario estándar), evitando inconsistencias de redondeo flotante.
- **RNF-2. Integridad Transaccional (ACID):** El registro de un anticipo o pago junto con la actualización de la liquidación y la inserción en bitácora de auditoría deben ejecutarse dentro de una misma transacción atómica de base de datos; ante cualquier fallo, se debe revertir el 100% de la operación (`rollback`).
- **RNF-3. Rendimiento en Lote ($O(1)$ consultas):** La pantalla de Gestión de Pagos Parciales y Liquidación no debe realizar consultas N+1 en la base de datos; la consolidación de todos los trabajadores, anticipos y pagos del período debe resolverse mediante consultas optimizadas con `joinedload` e índices compuestos.
- **RNF-4. Idempotencia e Inmutabilidad de Comprobantes:** Los números correlativos (`ANT-...`, `LIQ-...`, `PAG-...`) generados no pueden ser reasignados ni reutilizados, garantizando validez jurídica y contable.
- **RNF-5. Seguridad y Roles:** Las operaciones de registro de pagos, liquidación y anulación requieren autenticación obligatoria mediante token JWT activo con rol de administrador o responsable de planilla.

---

## 6. Casos límite contemplados y resueltos

1. **Trabajador con anticipos mayores a la quincena (Superó Quincena):**
   - El sistema no prohíbe los anticipos previos, pero al momento del corte (día 18) marca el excedente en rojo y sugiere pago de quincena en Bs 0.00. Permite registrar una constancia formal de revisión (`REVISION_QUINCENA`) en Bs 0.00 para certificar que el período fue revisado.
2. **Anticipo solicitado después de haber cobrado la quincena:**
   - Si la quincena ya fue liquidada (ej. Bs 1,000.00 pagados) y el trabajador pide un anticipo de Bs 100.00 el día 30: el vale de anticipo muestra la quincena como `LIQUIDADA (- Bs 1,000.00)` y el saldo salarial estimado resta tanto los anticipos acumulados como los Bs 1,000.00 de la quincena ya cobrada.
3. **Solicitud de anticipo que excede el saldo restante:**
   - Si el sueldo base es Bs 3,500.00, ya recibió Bs 2,000.00 en anticipos y Bs 1,000.00 en quincena, su saldo disponible es Bs 500.00. Si intenta solicitar Bs 600.00, el sistema rechaza la operación informando que excede el saldo disponible restante.
4. **Período completamente liquidado:**
   - Si un trabajador ya tiene liquidación final en estado `LIQUIDADO` (saldo restante Bs 0.00), el sistema bloquea cualquier solicitud de anticipo adicional en ese mes.
5. **Cierre de período con trabajadores pendientes:**
   - Si el responsable intenta cerrar el período salarial mientras existen saldos pendientes, el sistema muestra una advertencia informativa explícita exigiendo confirmación consciente del usuario.

---

## 7. Fuera de alcance

- Declaración impositiva y generación automática de planillas tributarias oficiales para el Servicio de Impuestos Nacionales (formulario RC-IVA planilla tributaria V4), lo cual corresponde a un submódulo contable externo.
- Conexión bancaria directa (APIs bancarias SWIFT/ACH) para dispersión automática de fondos en cuentas bancarias.
- Procesamiento de retenciones judiciales externas no registradas previamente como descuentos salariales.

---

## 8. Criterios de finalización y aceptación

- [x] El módulo Planilla y el módulo Pagos y Anticipos están operativos e integrados con el selector de períodos salariales mensuales.
- [x] La regla de corte del Día 18 categoriza correctamente los anticipos anteriores y posteriores al día 18.
- [x] El flujo de pago de quincena sugiere montos automáticos y admite constancias de revisión en Bs 0.00.
- [x] El cálculo de la liquidación final (día 5) descuenta con exactitud matemática el sueldo base, anticipos, quincena y ajustes.
- [x] Los comprobantes oficiales de anticipo (`ANT`) y liquidación (`LIQ`/`PAG`) muestran el desglose salarial, estados y firmas.
- [x] El comprobante de anticipo descuenta la quincena liquidada en el `Saldo Salarial Estimado Tras Anticipo`.
- [x] El sistema bloquea nuevos anticipos que superen el saldo disponible o pertenezcan a períodos cerrados o liquidados.
- [x] La columna Acción en la tabla de control de pagos está situada entre Trabajador y Sueldo Base y es responsiva en móviles.
- [x] Todas las pruebas unitarias y de integración de backend y compilación de frontend (`npm run build`) se ejecutan con éxito.

---

## 9. Registro de decisiones arquitectónicas

| ID | Decisión | Justificación |
|---|---|---|
| ADR-001 | Regla del Día 18 como corte de Quincena | Se alinea con el régimen laboral operativo de la empresa, donde los anticipos hasta el día 18 amortizan la quincena fija referencial de Bs 1,000.00 y los posteriores se difieren al fin de mes. |
| ADR-002 | Comprobantes inmutables con código alfanumérico | Permite auditoría física y digital inalterable con formato estándar `ANT-YYYYMM-XXXX` y `LIQ-YYYYMM-XXXX`. |
| ADR-003 | Descuento explícito de quincena en vales de anticipo posteriores | Evita que el trabajador o el cajero asuman que cuentan con el sueldo íntegro cuando la quincena ya fue desembolsada. |
| ADR-004 | Disposición ergonómica de botones de acción en tabla | Al ubicar los botones junto al nombre del trabajador, los operadores en campo que usan smartphones o tablets no tienen que realizar desplazamiento horizontal continuo. |
