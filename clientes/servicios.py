from clientes.modelos.cliente import Cliente, EstadoCliente


def activar_cliente(cliente: Cliente) -> Cliente:
    cliente.estado = EstadoCliente.ACTIVO
    cliente.save(update_fields=["estado", "actualizado_en"])
    return cliente


def suspender_cliente(cliente: Cliente) -> Cliente:
    cliente.estado = EstadoCliente.SUSPENDIDO
    cliente.save(update_fields=["estado", "actualizado_en"])
    return cliente
