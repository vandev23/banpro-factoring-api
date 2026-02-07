from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from clientes.modelos import Cliente
from core.rut import es_rut_valido, normalizar_rut
from facturas.modelos import Factura, EstadoFactura


def _hoy() -> date:
    return date.today()


FACTURAS_SEED = [
    # (cliente_rut, numero_factura, rut_deudor, razon_social_deudor, monto, dias_hasta_venc)
    ("12.345.678-5", "F-1001", "76.543.210-3", "Deudor Uno SpA", Decimal("1500000.00"), 30),
    ("12.345.678-5", "F-1002", "77.777.777-7", "Deudor Dos Ltda", Decimal("2500000.00"), 45),
    ("11.111.111-1", "F-2001", "76.543.210-3", "Deudor Uno SpA", Decimal("900000.00"), 20),
    ("11.111.111-1", "F-2002", "88.888.888-8", "Deudor Tres SpA", Decimal("3000000.00"), 60),
    ("9.876.543-3", "F-3001", "99.999.999-9", "Deudor Cuatro SpA", Decimal("1200000.00"), 15),
]


class Command(BaseCommand):
    help = "Seed de facturas para entorno local/desarrollo (requiere clientes existentes)"

    def add_arguments(self, parser):
        parser.add_argument("--solo-disponibles", action="store_true", help="Crea solo facturas disponibles")
        parser.add_argument("--reset", action="store_true", help="Elimina todas las facturas antes de sembrar")

    def handle(self, *args, **options):
        solo_disponibles = options["solo_disponibles"]
        reset = options["reset"]

        self.stdout.write("🌱 Seed de facturas...")

        # Validación previa: clientes deben existir
        faltantes = []
        for cliente_rut, *_ in FACTURAS_SEED:
            if not Cliente.objects.filter(rut=normalizar_rut(cliente_rut)).exists():
                faltantes.append(cliente_rut)

        if faltantes:
            raise CommandError(
                "Faltan clientes para sembrar facturas. Ejecuta primero seed_clientes. "
                f"Clientes faltantes: {', '.join(faltantes)}"
            )

        with transaction.atomic():
            if reset:
                Factura.objects.all().delete()
                self.stdout.write("  🧹 Facturas eliminadas (reset)")

            hoy = _hoy()

            for cliente_rut, numero, rut_deudor_raw, razon_deudor, monto, dias in FACTURAS_SEED:
                if not es_rut_valido(rut_deudor_raw):
                    raise CommandError(f"RUT deudor inválido en seed: {rut_deudor_raw}")

                cliente = Cliente.objects.get(rut=normalizar_rut(cliente_rut))

                rut_deudor = normalizar_rut(rut_deudor_raw)

                # Regla: rut_deudor != rut_cliente
                if normalizar_rut(cliente.rut) == rut_deudor:
                    raise CommandError(f"Seed inválido: rut_deudor igual al rut del cliente ({cliente.rut})")

                fecha_emision = hoy - timedelta(days=5)
                fecha_vencimiento = hoy + timedelta(days=int(dias))

                # Regla: vencimiento > emision
                if fecha_vencimiento <= fecha_emision:
                    raise CommandError(f"Seed inválido: vencimiento no es posterior a emisión para {numero}")

                factura, created = Factura.objects.get_or_create(
                    cliente=cliente,
                    numero_factura=numero,
                    defaults={
                        "rut_deudor": rut_deudor,
                        "razon_social_deudor": razon_deudor,
                        "monto_total": monto,
                        "fecha_emision": fecha_emision,
                        "fecha_vencimiento": fecha_vencimiento,
                        "estado": EstadoFactura.DISPONIBLE,
                    },
                )

                if not solo_disponibles:
                    # Para tener data variada, marcamos 1 pagada y 1 anulada (si existen)
                    if numero.endswith("01"):
                        factura.estado = EstadoFactura.PAGADA
                        factura.save(update_fields=["estado", "actualizado_en"])
                    if numero.endswith("02"):
                        factura.estado = EstadoFactura.ANULADA
                        factura.save(update_fields=["estado", "actualizado_en"])

                if created:
                    self.stdout.write(f"  ✅ Factura creada: {factura.numero_factura} ({cliente.rut})")
                else:
                    self.stdout.write(f"  ↩️  Factura ya existe: {factura.numero_factura} ({cliente.rut})")

        self.stdout.write(self.style.SUCCESS("✔ Seed de facturas finalizado"))
