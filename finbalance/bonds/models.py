from django.db import models
from django.utils import timezone

class Bond(models.Model):
    # Opciones para campos de selección
    FRECUENCIA_CUPON_CHOICES = [
        (12, 'Mensual (12 pagos/año)'),
        (6, 'Bimestral (6 pagos/año)'),
        (4, 'Trimestral (4 pagos/año)'),
        (3, 'Cuatrimestral (3 pagos/año)'),
        (2, 'Semestral (2 pagos/año)'),
        (1, 'Anual (1 pago/año)'),
    ]
    
    DIAS_ANIO_CHOICES = [
        (360, '360 días'),
        (365, '365 días'),
    ]
    
    TIPO_TASA_CHOICES = [
        ('nominal', 'Nominal'),
        ('efectiva', 'Efectiva'),
    ]
    
    # Campos principales del formulario
    valor_nominal = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        verbose_name="Valor Nominal"
    )
    
    valor_comercial = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Valor Comercial"
    )
    
    num_anios = models.IntegerField(
        verbose_name="Nº de Años"
    )
    
    frecuencia_cupon = models.IntegerField(
        choices=FRECUENCIA_CUPON_CHOICES,
        verbose_name="Frecuencia del cupón"
    )
    
    dias_por_anio = models.IntegerField(
        choices=DIAS_ANIO_CHOICES,
        verbose_name="Días por Año"
    )
    
    tipo_tasa_interes = models.CharField(
        max_length=10,
        choices=TIPO_TASA_CHOICES,
        verbose_name="Tipo de Tasa de Interés"
    )
    
    capitalizacion = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Capitalización"
    )
    
    tasa_interes = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Tasa de interés (%)"
    )
    
    tasa_anual_descuento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Tasa anual de descuento (%)"
    )
    
    impuesto_renta = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Impuesto a la Renta (%)"
    )
    
    fecha_emision = models.DateField(
        verbose_name="Fecha de Emisión"
    )
    
    # Costos/Gastos iniciales
    porcentaje_prima = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="% Prima"
    )
    
    porcentaje_estructuracion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="% Estructuración"
    )
    
    porcentaje_colocacion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="% Colocación"
    )
    
    porcentaje_flotacion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="% Flotación"
    )
    
    porcentaje_cavali = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="% CAVALI"
    )
    
    # Campos del sistema
    metodo_amortizacion = models.CharField(
        max_length=50,
        default='Francés',
        verbose_name="Método de Amortización"
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
        return f"Bono {self.id} - {self.valor_nominal} ({self.fecha_emision.year})"

    # Método para calcular costos iniciales totales
    def costos_iniciales(self):
        return (
            self.porcentaje_prima +
            self.porcentaje_estructuracion +
            self.porcentaje_colocacion +
            self.porcentaje_flotacion +
            self.porcentaje_cavali
        ) / 100 * self.valor_nominal