from django.db import models
from django.utils import timezone

class Bond(models.Model):
    # Opciones para campos de selección
    FRECUENCIA_PAGOS_CHOICES = [
        (12, 'Mensual (12 pagos/año)'),
        (6, 'Bimestral (6 pagos/año)'),
        (4, 'Trimestral (4 pagos/año)'),
        (3, 'Cuatrimestral (3 pagos/año)'),
        (2, 'Semestral (2 pagos/año)'),
        (1, 'Anual (1 pago/año)'),
    ]
    
    TIPO_GRACIA_CHOICES = [
        ('ninguno', 'Ninguno'),
        ('total', 'Total (solo intereses)'),
        ('parcial', 'Parcial (sin pagos)'),
    ]
    
    # Campos principales
    valor_nominal = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        verbose_name="Valor Nominal"
    )
    moneda = models.CharField(
        max_length=3,
        choices=[('PEN', 'Soles'), ('USD', 'Dólares'), ('EUR', 'Euros')],
        verbose_name="Moneda"
    )
    gastos = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        verbose_name="Gastos"
    )
    tasa_interes = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Tasa de Interés (%)"
    )
    tipo_tasa = models.CharField(
        max_length=20,
        choices=[('nominal', 'Nominal'), ('efectiva', 'Efectiva')],
        verbose_name="Tipo de Tasa"
    )
    capitalizacion = models.IntegerField(
        null=True, 
        blank=True,
        verbose_name="Capitalización"
    )
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(verbose_name="Fecha de Fin")
    
    # Campos modificados/agregados
    tipo_periodo_gracia = models.CharField(
        max_length=10,
        choices=TIPO_GRACIA_CHOICES,
        default='ninguno',
        verbose_name="Tipo de Período de Gracia"
    )
    duracion_gracia = models.IntegerField(
        default=0,
        verbose_name="Duración de Gracia (meses)"
    )
    metodo_amortizacion = models.CharField(
        max_length=50, 
        default='Francés',
        verbose_name="Método de Amortización"
    )
    frecuencia_pagos = models.IntegerField(
        choices=FRECUENCIA_PAGOS_CHOICES,
        verbose_name="Frecuencia de Pagos"
    )
    precio_mercado = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100.00,
        verbose_name="Precio de Mercado (%)"
    )
    fecha_registro = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha de Registro"
    )

    class Meta:
        verbose_name = "Bono"
        verbose_name_plural = "Bonos"
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"Bono {self.id} - {self.valor_nominal} {self.moneda} ({self.fecha_inicio.year}-{self.fecha_fin.year})"

    # Método para calcular la fecha final del período de gracia
    def fecha_fin_gracia(self):
        if self.tipo_periodo_gracia == 'ninguno' or self.duracion_gracia == 0:
            return None
        return self.fecha_inicio + timezone.timedelta(days=30*self.duracion_gracia)