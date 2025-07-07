from django.db import models
from django.utils import timezone
from decimal import Decimal

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
    
    TIPO_RESPONSABLE_CHOICES = [
        ('emisor', 'Emisor'),
        ('bonista', 'Bonista'),
        ('ambos', 'Ambos'),
    ]
    
    TIPO_GRACIA_CHOICES = [
        ('normal', 'Normal'),
        ('parcial', 'Parcial'),
        ('total', 'Total'),
    ]
    
    # Campos principales
    valor_nominal = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor Nominal")
    valor_comercial = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor Comercial")
    num_anios = models.IntegerField(verbose_name="Nº de Años")
    frecuencia_cupon = models.IntegerField(choices=FRECUENCIA_CUPON_CHOICES, verbose_name="Frecuencia del cupón")
    dias_por_anio = models.IntegerField(choices=DIAS_ANIO_CHOICES, verbose_name="Días por Año")
    tipo_tasa_interes = models.CharField(max_length=10, choices=TIPO_TASA_CHOICES, verbose_name="Tipo de Tasa de Interés")
    capitalizacion = models.IntegerField(choices=FRECUENCIA_CUPON_CHOICES, null=True, blank=True, verbose_name="Frecuencia de Capitalización")
    tasa_interes = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Tasa de interés (%)")
    tasa_anual_descuento = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Tasa anual de descuento (%)")
    impuesto_renta = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Impuesto a la Renta (%)")
    fecha_emision = models.DateField(verbose_name="Fecha de Emisión")
    
    # Plazo de gracia
    tiene_plazo_gracia = models.BooleanField(default=False, verbose_name="¿Tiene plazo de gracia?")
    periodos_gracia = models.IntegerField(null=True, blank=True, verbose_name="Nº Periodos de Gracia")
    tipo_gracia = models.CharField(max_length=10, choices=TIPO_GRACIA_CHOICES, null=True, blank=True, verbose_name="Tipo de Gracia")
    
    # Costos/Gastos iniciales
    porcentaje_prima = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="% Prima")
    tipo_prima = models.CharField(max_length=10, choices=TIPO_RESPONSABLE_CHOICES, default='emisor', verbose_name="Tipo Prima")
    porcentaje_estructuracion = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="% Estructuración")
    tipo_estructuracion = models.CharField(max_length=10, choices=TIPO_RESPONSABLE_CHOICES, default='emisor', verbose_name="Tipo Estructuración")
    porcentaje_colocacion = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="% Colocación")
    tipo_colocacion = models.CharField(max_length=10, choices=TIPO_RESPONSABLE_CHOICES, default='emisor', verbose_name="Tipo Colocación")
    porcentaje_flotacion = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="% Flotación")
    tipo_flotacion = models.CharField(max_length=10, choices=TIPO_RESPONSABLE_CHOICES, default='emisor', verbose_name="Tipo Flotación")
    porcentaje_cavali = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="% CAVALI")
    tipo_cavali = models.CharField(max_length=10, choices=TIPO_RESPONSABLE_CHOICES, default='emisor', verbose_name="Tipo CAVALI")
    
    # Campos del sistema
    metodo_amortizacion = models.CharField(max_length=50, default='Francés', verbose_name="Método de Amortización")
    fecha_registro = models.DateTimeField(default=timezone.now, verbose_name="Fecha de Registro")

    class Meta:
        verbose_name = "Bono"
        verbose_name_plural = "Bonos"
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"Bono {self.id} - {self.valor_nominal} ({self.fecha_emision.year})"

    def costos_iniciales(self, tipo):
        total = Decimal('0')
        campos = [
            ('porcentaje_prima', 'tipo_prima'),
            ('porcentaje_estructuracion', 'tipo_estructuracion'),
            ('porcentaje_colocacion', 'tipo_colocacion'),
            ('porcentaje_flotacion', 'tipo_flotacion'),
            ('porcentaje_cavali', 'tipo_cavali'),
        ]
        
        for campo_porcentaje, campo_tipo in campos:
            porcentaje = getattr(self, campo_porcentaje)
            tipo_responsable = getattr(self, campo_tipo)
            
            if tipo_responsable == tipo or tipo_responsable == 'ambos':
                total += porcentaje
        
        return (total / Decimal('100')) * self.valor_nominal

    @property
    def costos_emisor(self):
        return self.costos_iniciales('emisor')

    @property
    def costos_bonista(self):
        return self.costos_iniciales('bonista')
    
    @property
    def dias_capitalizacion(self):
        dias = {
            12: 30,     # Mensual
            6: 60,      # Bimestral
            4: 90,      # Trimestral
            3: 120,     # Cuatrimestral
            2: 180,     # Semestral
            1: 360      # Anual
        }
        return dias.get(self.capitalizacion, 30)