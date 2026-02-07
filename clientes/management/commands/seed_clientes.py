from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from clientes.modelos import Cliente, EstadoCliente
from core.rut import es_rut_valido, normalizar_rut


CLIENTES_SEED = [
    {
        "rut": "12.345.678-5",
        "razon_social": "Empresa Alpha SpA",
        "email": "alpha@empresa.cl",
        "estado": EstadoCliente.ACTIVO,
        "linea_credito": Decimal("10000000.00"),
    },
    {
        "rut": "11.111.111-1",
        "razon_social": "Empresa Beta Ltda",
        "email": "beta@empresa.cl",
        "estado": EstadoCliente.ACTIVO,
        "linea_credito": Decimal("5000000.00"),
    },
    {
        "rut": "9.876.543-3",
        "razon_social": "Empresa Gamma SpA",
        "email": "gamma@empresa.cl",
        "estado": EstadoCliente.SUSPENDIDO,
        "linea_credito": Decimal("20000000.00"),
    },
    {
        "rut": "26.271.832-8",
        "razon_social": "Empresa Nessa SpA",
        "email": "nessa@empresa.cl",
        "estado": EstadoCliente.SUSPENDIDO,
        "linea_credito": Decimal("20000000.00"),
    },
]


class Command(BaseCommand):
    help = "Seed de clientes para entorno local/desarrollo"

    def handle(self, *args, **options):
        self.stdout.write("🌱 Creando clientes de prueba...")

        with transaction.atomic():
            for data in CLIENTES_SEED:
                rut_raw = data["rut"]

                # ✅ Validación explícita
                if not es_rut_valido(rut_raw):
                    raise CommandError(f"RUT inválido en seed: {rut_raw}")

                rut = normalizar_rut(rut_raw)

                cliente, created = Cliente.objects.get_or_create(
                    rut=rut,
                    defaults={
                        "razon_social": data["razon_social"],
                        "email": data["email"],
                        "estado": data["estado"],
                        "linea_credito": data["linea_credito"],
                        "linea_disponible": data["linea_credito"],
                    },
                )

                if created:
                    self.stdout.write(f"  ✅ Cliente creado: {cliente.razon_social}")
                else:
                    self.stdout.write(f"  ↩️  Cliente ya existe: {cliente.razon_social}")

        self.stdout.write(self.style.SUCCESS("✔ Seed de clientes finalizado"))
