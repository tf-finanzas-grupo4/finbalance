from django.shortcuts import render, redirect, get_object_or_404
from .models import Bond
from django.utils import timezone
from decimal import Decimal, getcontext
import math
from datetime import timedelta, datetime

def calcular_vna(tasa_descuento, flujos):
    """Calcula el Valor Neto Actual (VNA) similar a la función de Excel"""
    vna = Decimal('0')
    for periodo, flujo in enumerate(flujos, start=1):
        vna += flujo / (1 + tasa_descuento)**periodo
    return vna

# bonds/views.py
def bond_list(request):
    bonds = Bond.objects.all().order_by('-fecha_registro')
    return render(request, 'bonds/list.html', {'bonds': bonds})

def bond_create(request):
    if request.method == 'POST':
        try:
            # Crear nuevo bono con todos los campos
            bond = Bond(
                valor_nominal=Decimal(request.POST['valor_nominal']),
                valor_comercial=Decimal(request.POST['valor_comercial']),
                num_anios=int(request.POST['num_anios']),
                frecuencia_cupon=int(request.POST['frecuencia_cupon']),
                dias_por_anio=int(request.POST['dias_por_anio']),
                tipo_tasa_interes=request.POST['tipo_tasa_interes'],
                capitalizacion=int(request.POST['capitalizacion']),
                tasa_interes=Decimal(request.POST['tasa_interes']),
                tasa_anual_descuento=Decimal(request.POST['tasa_anual_descuento']),
                impuesto_renta=Decimal(request.POST['impuesto_renta']),
                fecha_emision=request.POST['fecha_emision'],
                porcentaje_prima=Decimal(request.POST.get('porcentaje_prima', 0)),
                tipo_prima=request.POST.get('tipo_prima', 'emisor'),
                porcentaje_estructuracion=Decimal(request.POST.get('porcentaje_estructuracion', 0)),
                tipo_estructuracion=request.POST.get('tipo_estructuracion', 'emisor'),
                porcentaje_colocacion=Decimal(request.POST.get('porcentaje_colocacion', 0)),
                tipo_colocacion=request.POST.get('tipo_colocacion', 'emisor'),
                porcentaje_flotacion=Decimal(request.POST.get('porcentaje_flotacion', 0)),
                tipo_flotacion=request.POST.get('tipo_flotacion', 'emisor'),
                porcentaje_cavali=Decimal(request.POST.get('porcentaje_cavali', 0)),
                tipo_cavali=request.POST.get('tipo_cavali', 'emisor'),
                metodo_amortizacion='Francés',
                fecha_registro=timezone.now()
            )
            bond.save()
            return redirect('bonds:list')  # Asegúrate que este nombre coincide con tu URL de lista
            
        except Exception as e:
            # Manejo de errores - puedes imprimir esto para debug
            print(f"Error al crear bono: {str(e)}")
            # Puedes retornar el formulario con los datos ingresados
            return render(request, 'bonds/create.html', {
                'error': f"Error al crear el bono: {str(e)}",
                'form_data': request.POST
            })
    
    return render(request, 'bonds/create.html')


def bond_detail(request, bond_id):
    getcontext().prec = 12
    bond = get_object_or_404(Bond, id=bond_id)
    
    try:
        # Conversión segura a Decimal
        tasa = Decimal(str(bond.tasa_interes)) / Decimal('100')
        tasa_descuento = Decimal(str(bond.tasa_anual_descuento)) / Decimal('100')
        frecuencia = bond.frecuencia_cupon
        valor_nominal = Decimal(str(bond.valor_nominal))
        valor_comercial = Decimal(str(bond.valor_comercial))
        num_anios = bond.num_anios
        impuesto_renta = Decimal(str(bond.impuesto_renta)) / Decimal('100')
        
        # Cálculo del número total de períodos
        num_pagos = frecuencia * num_anios
        
        # 1. Cálculo de tasas periódicas
        if bond.tipo_tasa_interes == 'nominal':
            tasa_periodica = tasa / frecuencia
            tasa_descuento_periodica = tasa_descuento / frecuencia
        else:  # efectiva
            tasa_periodica = (Decimal('1') + tasa)**(Decimal('1')/frecuencia) - Decimal('1')
            tasa_descuento_periodica = (Decimal('1') + tasa_descuento)**(Decimal('1')/frecuencia) - Decimal('1')
        
        # Tasa Efectiva Anual (TEA)
        tea = ((Decimal('1') + tasa_periodica)**frecuencia - Decimal('1')) * Decimal('100')
        
        # Tasa Efectiva Periódica (TEP)
        tep = tasa_periodica * Decimal('100')
        
        # COK periódico
        cok_periodo = tasa_descuento_periodica * Decimal('100')
        
        # 2. Cálculo de la cuota constante (Método Francés)
        factor = (Decimal('1') - (Decimal('1') + tasa_periodica)**Decimal(-num_pagos)) / tasa_periodica
        cuota = valor_nominal / factor
        
        # 3. Cálculo de costos iniciales
        costes_emisor = (
            bond.porcentaje_estructuracion * (Decimal('1') if bond.tipo_estructuracion == 'emisor' or bond.tipo_estructuracion == 'ambos' else Decimal('0')) +
            bond.porcentaje_colocacion * (Decimal('1') if bond.tipo_colocacion == 'emisor' or bond.tipo_colocacion == 'ambos' else Decimal('0')) +
            bond.porcentaje_flotacion * (Decimal('1') if bond.tipo_flotacion == 'emisor' or bond.tipo_flotacion == 'ambos' else Decimal('0')) +
            bond.porcentaje_cavali * (Decimal('1') if bond.tipo_cavali == 'emisor' or bond.tipo_cavali == 'ambos' else Decimal('0'))
        ) / Decimal('100') * valor_comercial
        
        costes_bonista = (
            bond.porcentaje_estructuracion * (Decimal('1') if bond.tipo_estructuracion == 'bonista' or bond.tipo_estructuracion == 'ambos' else Decimal('0')) +
            bond.porcentaje_colocacion * (Decimal('1') if bond.tipo_colocacion == 'bonista' or bond.tipo_colocacion == 'ambos' else Decimal('0')) +
            bond.porcentaje_flotacion * (Decimal('1') if bond.tipo_flotacion == 'bonista' or bond.tipo_flotacion == 'ambos' else Decimal('0')) +
            bond.porcentaje_cavali * (Decimal('1') if bond.tipo_cavali == 'bonista' or bond.tipo_cavali == 'ambos' else Decimal('0'))
        ) / Decimal('100') * valor_comercial
        
        # 4. Generar tabla de amortización
        flujos = []
        flujos_bonista = []
        saldo = valor_nominal
        duracion_numerador = Decimal('0')
        valor_presente_total = Decimal('0')
        
        for t in range(1, num_pagos + 1):
            interes = saldo * tasa_periodica
            cuota_periodo = cuota
            amortizacion = cuota - interes
            
            # Aplicar impuesto a la renta
            interes_neto = interes * (Decimal('1') - impuesto_renta)
            cuota_neto = amortizacion + interes_neto

            # Calcular flujo neto para el bonista (positivo = entrada)
            flujo_bonista = amortizacion + interes_neto
            flujos_bonista.append(flujo_bonista)  

            
            saldo -= amortizacion
            
            # Valor presente del flujo
            vp_flujo = cuota_neto / ((Decimal('1') + tasa_descuento_periodica)**t)
            duracion_numerador += vp_flujo * t
            valor_presente_total += vp_flujo
            
            flujos.append({
                'periodo': t,
                'cuota': cuota_periodo,
                'interes': interes,
                'amortizacion': amortizacion,
                'saldo': saldo if saldo > Decimal('0') else Decimal('0'),
                'vp_flujo': vp_flujo,
                'flujo_bonista': flujo_bonista  # <-- Añadir al diccionario de flujo
            })
        
        # 5. Cálculo de indicadores
        # Precio teórico
        precio_teorico = valor_presente_total
        
        # Precio actual y utilidad
        precio_actual = calcular_vna(tasa_descuento_periodica, flujos_bonista)

        utilidad = (-valor_comercial - costes_bonista) + precio_actual
        
        # Duración (Macaulay)
        duracion = duracion_numerador / valor_presente_total / frecuencia
        
        # Duración Modificada
        duracion_modificada = duracion / (Decimal('1') + tasa_descuento_periodica)
        
        # Convexidad
        convexidad_numerador = Decimal('0')
        for t in range(1, num_pagos + 1):
            vp_flujo = flujos[t-1]['vp_flujo']
            convexidad_numerador += vp_flujo * Decimal(t) * Decimal(t + 1)
        
        convexidad = convexidad_numerador / (valor_presente_total * (Decimal('1') + tasa_descuento_periodica)**2) / frecuencia**2
        
        # Total ratios
        total_ratios = duracion + convexidad
        
        # TCEA Emisor (sin escudo)
        tcea_emisor = ((Decimal('1') + tasa_periodica)**frecuencia - Decimal('1')) * Decimal('100')
        
        # TCEA Emisor con escudo (considera impuestos)
        tasa_periodica_escudo = tasa_periodica * (Decimal('1') - impuesto_renta)
        tcea_emisor_escudo = ((Decimal('1') + tasa_periodica_escudo)**frecuencia - Decimal('1')) * Decimal('100')
        
        # TREA Bonista
        trea_bonista = ((Decimal('1') + tasa_descuento_periodica)**frecuencia - Decimal('1')) * Decimal('100')
        
        # Nombre del período según frecuencia
        periodo_nombre = {
            12: 'Mensual',
            6: 'Bimestral',
            4: 'Trimestral',
            3: 'Cuatrimestral',
            2: 'Semestral',
            1: 'Anual'
        }.get(frecuencia, 'Periódica')
        
        context = {
            'bond': bond,
            'flujos': flujos,
            'flujos_bonista': flujos_bonista, 
            'periodos_por_anio': frecuencia,
            'periodo_nombre': periodo_nombre,
            'tea': tea,
            'tep': tep,
            'cok_periodo': cok_periodo,
            'costes_emisor': costes_emisor,
            'costes_bonista': costes_bonista,
            'precio_actual': precio_actual,
            'utilidad': utilidad,
            'duracion': duracion,
            'duracion_modificada': duracion_modificada,
            'convexidad': convexidad,
            'total_ratios': total_ratios,
            'tcea_emisor': tcea_emisor,
            'tcea_emisor_escudo': tcea_emisor_escudo,
            'trea_bonista': trea_bonista,
            'precio_teorico': precio_teorico,
            'tasa_periodica': tasa_periodica * Decimal('100'),
        }
        
        return render(request, 'bonds/detail.html', context)
        
    except Exception as e:
        return render(request, 'bonds/error.html', {
            'error': f"Error en cálculos: {str(e)}",
            'bond': bond
        })
        
    except Exception as e:
        return render(request, 'bonds/error.html', {
            'error': f"Error en cálculos: {str(e)}",
            'bond': bond
        })