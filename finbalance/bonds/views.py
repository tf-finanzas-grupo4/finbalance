from django.shortcuts import render, redirect, get_object_or_404
from .models import Bond
from django.utils import timezone
from decimal import Decimal, getcontext
import math
from datetime import timedelta, datetime

def bond_list(request):
    bonds = Bond.objects.all().order_by('-fecha_emision')
    return render(request, 'bonds/list.html', {'bonds': bonds})

def bond_create(request):
    if request.method == 'POST':
        try:
            # Validación y conversión de datos
            valor_nominal = Decimal(request.POST['valor_nominal'])
            valor_comercial = Decimal(request.POST['valor_comercial'])
            num_anios = int(request.POST['num_anios'])
            frecuencia_cupon = int(request.POST['frecuencia_cupon'])
            dias_por_anio = int(request.POST['dias_por_anio'])
            tipo_tasa_interes = request.POST['tipo_tasa_interes']
            capitalizacion = int(request.POST.get('capitalizacion', 0))
            tasa_interes = Decimal(request.POST['tasa_interes'])
            tasa_anual_descuento = Decimal(request.POST['tasa_anual_descuento'])
            impuesto_renta = Decimal(request.POST['impuesto_renta'])
            fecha_emision = request.POST['fecha_emision']
            porcentaje_prima = Decimal(request.POST.get('porcentaje_prima', '0.00'))
            porcentaje_estructuracion = Decimal(request.POST.get('porcentaje_estructuracion', '0.00'))
            porcentaje_colocacion = Decimal(request.POST.get('porcentaje_colocacion', '0.00'))
            porcentaje_flotacion = Decimal(request.POST.get('porcentaje_flotacion', '0.00'))
            porcentaje_cavali = Decimal(request.POST.get('porcentaje_cavali', '0.00'))

            # Crear nuevo bono con validación
            bond = Bond(
                valor_nominal=valor_nominal,
                valor_comercial=valor_comercial,
                num_anios=num_anios,
                frecuencia_cupon=frecuencia_cupon,
                dias_por_anio=dias_por_anio,
                tipo_tasa_interes=tipo_tasa_interes,
                capitalizacion=capitalizacion,
                tasa_interes=tasa_interes,
                tasa_anual_descuento=tasa_anual_descuento,
                impuesto_renta=impuesto_renta,
                fecha_emision=fecha_emision,
                porcentaje_prima=porcentaje_prima,
                porcentaje_estructuracion=porcentaje_estructuracion,
                porcentaje_colocacion=porcentaje_colocacion,
                porcentaje_flotacion=porcentaje_flotacion,
                porcentaje_cavali=porcentaje_cavali,
                metodo_amortizacion='Francés',
            )
            bond.full_clean()
            bond.save()
            
            return redirect('bonds:list')
            
        except Exception as e:
            error_msg = f"Error al crear el bono: {str(e)}"
            return render(request, 'bonds/create.html', {
                'error': error_msg,
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
        dias_por_anio = bond.dias_por_anio
        
        # Cálculo del número total de períodos
        num_pagos = frecuencia * num_anios
        
        # Tasa periódica según tipo de tasa
        if bond.tipo_tasa_interes == 'nominal':
            tasa_periodica = tasa / frecuencia
        else:  # efectiva
            tasa_periodica = (Decimal('1') + tasa)**(Decimal('1')/frecuencia) - Decimal('1')
        
        # Tasa periódica de descuento
        tasa_descuento_periodica = tasa_descuento / frecuencia
        
        # 1. Cálculo de la cuota constante (Método Francés)
        factor = (Decimal('1') - (Decimal('1') + tasa_periodica)**Decimal(-num_pagos)) / tasa_periodica
        cuota = valor_nominal / factor
        
        # 2. Cálculo de TCEA
        tcea = ((Decimal('1') + tasa_periodica)**frecuencia - Decimal('1')) * Decimal('100')
        
        # 3. Cálculo de TREA (considerando impuestos)
        trea = tcea * (Decimal('1') - bond.impuesto_renta/Decimal('100'))
        
        # 4. Generar tabla de amortización
        flujos = []
        saldo = valor_nominal
        duracion_numerador = Decimal('0')
        valor_presente_total = Decimal('0')
        
        for t in range(1, num_pagos + 1):
            interes = saldo * tasa_periodica
            cuota_periodo = cuota
            amortizacion = cuota - interes
            
            # Aplicar impuesto a la renta
            interes_neto = interes * (Decimal('1') - bond.impuesto_renta/Decimal('100'))
            cuota_neto = amortizacion + interes_neto
            
            saldo -= amortizacion
            
            # Valor presente del flujo
            vp_flujo = cuota_neto / ((Decimal('1') + tasa_descuento_periodica)**t)
            duracion_numerador += vp_flujo * t
            valor_presente_total += vp_flujo
            
            flujos.append({
                'periodo': t,
                'cuota': round(cuota_periodo, 2),
                'interes': round(interes, 2),
                'interes_neto': round(interes_neto, 2),
                'amortizacion': round(amortizacion, 2),
                'saldo': round(saldo, 2) if saldo > Decimal('0') else Decimal('0'),
                'vp_flujo': round(vp_flujo, 2)
            })
        
        # 5. Cálculo de Duración (Macaulay)
        duracion = duracion_numerador / valor_presente_total / frecuencia
        
        # 6. Duración Modificada
        duracion_modificada = duracion / (Decimal('1') + tasa_descuento_periodica)
        
        # 7. Convexidad
        convexidad_numerador = Decimal('0')
        for t in range(1, num_pagos + 1):
            vp_flujo = flujos[t-1]['vp_flujo']
            convexidad_numerador += vp_flujo * Decimal(t) * Decimal(t + 1)
        
        convexidad = convexidad_numerador / (valor_presente_total * (Decimal('1') + tasa_descuento_periodica)**2) / frecuencia**2
        
        # 8. Precio Teórico
        precio_teorico = valor_presente_total
        
        # 9. Costos iniciales
        costos_iniciales = (
            bond.porcentaje_prima + 
            bond.porcentaje_estructuracion + 
            bond.porcentaje_colocacion + 
            bond.porcentaje_flotacion + 
            bond.porcentaje_cavali
        ) / Decimal('100') * valor_nominal
        
        # 10. VAN y TIR (simplificado)
        van = valor_presente_total - valor_comercial - costos_iniciales
        tir = tasa_descuento * Decimal('100')  # Simplificación
        
        context = {
            'bond': bond,
            'flujos': flujos,
            'cuota': round(cuota, 2),
            'tcea': round(tcea, 2),
            'trea': round(trea, 2),
            'duracion': round(duracion, 4),
            'duracion_modificada': round(duracion_modificada, 4),
            'convexidad': round(convexidad, 6),
            'precio_teorico': round(precio_teorico, 2),
            'tasa_periodica': round(tasa_periodica * 100, 4),
            'costos_iniciales': round(costos_iniciales, 2),
            'van': round(van, 2),
            'tir': round(tir, 2),
        }
        
        return render(request, 'bonds/detail.html', context)
        
    except Exception as e:
        return render(request, 'bonds/error.html', {
            'error': f"Error en cálculos: {str(e)}",
            'bond': bond
        })