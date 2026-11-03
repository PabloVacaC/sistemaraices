analiza la arquitectura sin romper nada 
# Spec NNN — <Nombre de la funcionalidad>

## Contexto y objetivo
<Qué problema resuelve y por qué merece la pena. Un párrafo.>
ahora  quiero crear una nueva columna que va a estar al final despues de Líquido Pagable. lo que tendra ahi sera el excedente de Líquido Pagable digamos si yo tengo que que pagar un monto en Líquido Pagable actualmente no puedo pagarle mas ahora si podre ejemplo si el sueldo final es 2000 yo puedo pagarle 3000 y ahora si va a ir ir a la nueva columna que quiero crear la nueva columna se llamara anticipo para el siguiente mes, entonces cuando yo tenga que pagar 2000 de sueldo y le pago 3000 en el ticket saldra cuanto le pague pero en Líquido Pagable quedara lo que se tenia que haber dado , y abajo de eso me marcara como comentario el restante digamos 2000 que es el monto y debajo de eso 1000 como comentario que se le dio eso y el ticket si o si tiene que tener cuanto se le pago en la liquidacion de sueldo ahora ese restante ira a la nueva columna anticipo para el siguiente mes y ese anticipo para el siguiente mes mandara como primer anticipo. a Anticipo Rider y Otros Anticipos, ese restante es como primer anticipo ademas en mi boton cerrar planilla tengo Monto Otros Gastos (Bs) ahi es donde tiene que ir anticipos para el siguiente mes. 

## Usuarios / actores
<Quién lo usa.>
usuario del sistema. 

## Historias de usuario
- H1: Como <rol> quiero <acción> para <beneficio>.

## Requisitos funcionales (criterios de aceptación en EARS)
- RF-1: CUANDO Líquido Pagable sea un monto yo puedo sobrepasar ese monto  <evento>, EL SISTEMA me debe mostrar un ticket de cuanto le esoy dando pero Líquido Pagable no deberia de cambiarme debe ser cuanto le tengo que dar.pero el restatante me aparecera como comentario debajo de ese monto, andemas se ira a la nueva columna anticipo para el siguiente mes se ca a esa nueva columna y tambien se ira a la siguiente planilla como primer anticipo a la columna Anticipo Rider y Otros Anticipos con una opservacion que se le dice que es un anticpo que se le pago el dia del sueldo <respuesta> (salida/resultado esperado).


## Requisitos no funcionales
<Solo los que apliquen: rendimiento, seguridad, plataformas, idioma...>

## Casos límite
<Vacíos, duplicados, datos corruptos, límites, concurrencia...>

## Fuera de alcance
<Lo que explícitamente NO se hace en esta iteración.>

## Criterios de finalización
<Ej.: todos los RF con test en verde + demo manual del flujo principal.>

## Dudas abiertas
- si tienes dudas o ambiguedades preguntame antes de implementar  <duda>