from django.db import models
from django.utils import timezone

class Bond(models.Model):
    valor_nominal = models.DecimalField(max_digits=15, decimal_places=2)
    moneda = models.CharField(max_length=3)
    gastos = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tasa_interes = models.DecimalField(max_digits=5, decimal_places=2)
    tipo_tasa = models.CharField(max_length=20)
    capitalizacion = models.IntegerField(null=True, blank=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    periodo_gracia = models.DateField(null=True, blank=True)
    metodo_amortizacion = models.CharField(max_length=50, default='Francés')
    frecuencia_pagos = models.IntegerField()
    precio_mercado = models.DecimalField(max_digits=5, decimal_places=2)
    fecha_registro = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Bono {self.id} - {self.valor_nominal} {self.moneda}"