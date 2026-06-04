# Confirmaciones en ARVIS

ARVIS v0.2.2 agrega acciones pendientes para manejar pedidos riesgosos sin ejecutarlos automaticamente.

## Que es una accion pendiente

Una accion pendiente es un pedido del usuario que ARVIS detecta como riesgoso y guarda para confirmacion explicita. La accion queda registrada con:

- ID unico.
- Fecha y hora de creacion.
- Mensaje original.
- Intencion detectada.
- Herramienta solicitada, si existe.
- Parametros.
- Nivel de riesgo.
- Estado.

Los estados posibles son:

- `pending`
- `confirmed`
- `cancelled`
- `expired`
- `blocked`

## Cuando ARVIS pide confirmacion

ARVIS pide confirmacion para acciones como:

- Borrar archivos.
- Mover archivos.
- Sobrescribir documentos.
- Enviar mensajes.
- Instalar programas.
- Cerrar aplicaciones.
- Cambiar configuraciones sensibles.
- Acceder a carpetas no autorizadas.
- Subir informacion a internet.

En v0.2.2 no existen herramientas reales para borrar, mover, enviar mensajes o ejecutar comandos libres. Por eso una confirmacion no ejecuta esas acciones: solo registra la confirmacion y responde que falta una herramienta segura implementada.

## Como confirmar

Ejemplos:

```text
confirmo
si, confirmar
confirmar accion
confirmar accion 3
ejecutar accion pendiente 3
```

Si hay una sola accion pendiente, ARVIS puede usar esa. Si hay varias, pide el ID.

## Como cancelar

Ejemplos:

```text
cancelar
cancelar accion
cancelar accion 3
no, cancelar
cancelar pendiente 3
```

## Expiracion

Las acciones pendientes vencen despues del tiempo configurado en:

```json
{
  "pending_action_expiration_minutes": 10
}
```

Si una accion vencio, ARVIS no la ejecuta y pide solicitarla nuevamente.

## Por que no se ejecutan comandos libres

Ejecutar comandos libres podria borrar datos, instalar software, exfiltrar informacion o modificar configuraciones sensibles. ARVIS solo ejecuta herramientas seguras definidas por codigo, con lista blanca y permisos revisables.

Confirmar una accion no significa permiso total. La accion vuelve a pasar por permisos y solo se ejecuta si existe una herramienta segura implementada.
