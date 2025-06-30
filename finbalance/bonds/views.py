from django.shortcuts import render, redirect, get_object_or_404
from .models import Bond
from django.utils import timezone
from decimal import Decimal, getcontext
import math
from datetime import timedelta

def bond_list(request):
    bonds = Bond.objects.all().order_by('-fecha_registro')
    return render(request, 'bonds/list.html', {'bonds': bonds})

def bond_create(request):
    if request.method == 'POST':
        try:
            # Validación y conversión de datos
            valor_nominal = Decimal(request.POST['valor_nominal'])
            tasa_interes = Decimal(request.POST['tasa_interes'])
            frecuencia_pagos = int(request.POST['frecuencia_pagos'])
            duracion_gracia = int(request.POST.get('duracion_gracia', 0))
            tipo_gracia = request.POST.get('tipo_periodo_gracia', 'ninguno')

            # Crear nuevo bono con validación
            bond = Bond(
                valor_nominal=valor_nominal,
                moneda=request.POST['moneda'],
                gastos=Decimal(request.POST.get('gastos', '0.00')),
                tasa_interes=tasa_interes,
                tipo_tasa=request.POST['tipo_tasa'],
                capitalizacion=int(request.POST.get('capitalizacion', 0)),
                fecha_inicio=request.POST['fecha_inicio'],
                fecha_fin=request.POST['fecha_fin'],
                tipo_periodo_gracia=tipo_gracia,
                duracion_gracia=duracion_gracia,
                metodo_amortizacion='Francés',
                frecuencia_pagos=frecuencia_pagos,
                precio_mercado=Decimal(request.POST.get('precio_mercado', '100.00')),
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
        frecuencia = bond.frecuencia_pagos
        valor_nominal = Decimal(str(bond.valor_nominal))
        
        # Cálculo del período de gracia en meses
        meses_gracia = bond.duracion_gracia if bond.tipo_periodo_gracia != 'ninguno' else 0
        
        # Cálculo del número total de períodos (incluyendo gracia si aplica)
        plazo_total = (bond.fecha_fin - bond.fecha_inicio).days / 365.25
        num_pagos_total = math.ceil(frecuencia * plazo_total)
        num_pagos_normales = num_pagos_total - math.ceil(meses_gracia * frecuencia / 12)
        
        # Tasa periódica
        tasa_periodica = tasa / frecuencia
        
        # 1. Cálculo de la cuota constante (Método Francés)
        if num_pagos_normales > 0:
            factor = (Decimal('1') - (Decimal('1') + tasa_periodica)**Decimal(-num_pagos_normales)) / tasa_periodica
            cuota = valor_nominal / factor
        else:
            cuota = Decimal('0')
        
        # 2. Cálculo de TCEA
        tcea = ((Decimal('1') + tasa_periodica)**frecuencia - Decimal('1')) * Decimal('100')
        
        # 3. Cálculo de TREA (asumiendo reinversión)
        trea = tcea
        
        # 4. Generar tabla de amortización con período de gracia
        flujos = []
        saldo = valor_nominal
        duracion_numerador = Decimal('0')
        valor_presente_total = Decimal('0')
        
        # Período de gracia (si aplica)
        periodo_gracia = math.ceil(meses_gracia * frecuencia / 12)
        for t in range(1, num_pagos_total + 1):
            if t <= periodo_gracia:
                # Período de gracia
                if bond.tipo_periodo_gracia == 'total':
                    interes = saldo * tasa_periodica
                    cuota_periodo = interes
                    amortizacion = Decimal('0')
                else:
                    interes = Decimal('0')
                    cuota_periodo = Decimal('0')
                    amortizacion = Decimal('0')
            else:
                # Períodos normales
                interes = saldo * tasa_periodica
                cuota_periodo = cuota
                amortizacion = cuota - interes
            
            saldo -= amortizacion
            vp_flujo = cuota_periodo / ((Decimal('1') + tasa_periodica)**t)
            duracion_numerador += vp_flujo * t
            valor_presente_total += vp_flujo
            
            flujos.append({
                'periodo': t,
                'tipo': 'Gracia' if t <= periodo_gracia else 'Normal',
                'cuota': round(cuota_periodo, 2),
                'interes': round(interes, 2),
                'amortizacion': round(amortizacion, 2),
                'saldo': round(saldo, 2) if saldo > Decimal('0') else Decimal('0'),
                'vp_flujo': round(vp_flujo, 2)
            })
        
        # 5. Cálculo de Duración (Macaulay)
        duracion = duracion_numerador / valor_presente_total / frecuencia
        
        # 6. Duración Modificada
        duracion_modificada = duracion / (Decimal('1') + tasa_periodica)
        
        # 7. Convexidad
        convexidad_numerador = Decimal('0')
        for t in range(1, num_pagos_total + 1):
            vp_flujo = flujos[t-1]['vp_flujo']
            convexidad_numerador += vp_flujo * Decimal(t) * Decimal(t + 1)
        
        convexidad = convexidad_numerador / (valor_presente_total * (Decimal('1') + tasa_periodica)**2) / frecuencia**2
        
        # 8. Precio Teórico
        precio_teorico = valor_presente_total
        
        context = {
            'bond': bond,
            'flujos': flujos,
            'cuota_normal': round(cuota, 2) if num_pagos_normales > 0 else 0,
            'tcea': round(tcea, 2),
            'trea': round(trea, 2),
            'duracion': round(duracion, 4),
            'duracion_modificada': round(duracion_modificada, 4),
            'convexidad': round(convexidad, 6),
            'precio_teorico': round(precio_teorico, 2),
            'tasa_periodica': round(tasa_periodica * 100, 4),
            'periodos_gracia': periodo_gracia,
            'periodos_normales': num_pagos_normales,
        }
        
        return render(request, 'bonds/detail.html', context)
        
    except Exception as e:
        return render(request, 'bonds/error.html', {
            'error': f"Error en cálculos: {str(e)}",
            'bond': bond
        })