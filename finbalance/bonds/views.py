from django.shortcuts import render, redirect, get_object_or_404
from .models import Bond
from django.utils import timezone
from decimal import Decimal, getcontext
from datetime import date
from math import pow

def bond_list(request):
    bonds = Bond.objects.all().order_by('-fecha_registro')
    return render(request, 'bonds/list.html', {'bonds': bonds})

def bond_create(request):
    if request.method == 'POST':
        try:
            # Validar que los campos requeridos estén presentes
            if not request.POST.get('valor_nominal'):
                raise ValueError("El valor nominal es requerido")
                
            # Crear nuevo bono con los datos del formulario
            Bond.objects.create(
                valor_nominal=request.POST['valor_nominal'],  # Usar [] en lugar de get() para campos requeridos
                moneda=request.POST['moneda'],
                gastos=request.POST.get('gastos', 0),
                tasa_interes=request.POST['tasa_interes'],
                tipo_tasa=request.POST['tipo_tasa'],
                capitalizacion=request.POST.get('capitalizacion'),
                fecha_inicio=request.POST['fecha_inicio'],
                fecha_fin=request.POST['fecha_fin'],
                periodo_gracia=request.POST.get('periodo_gracia'),
                frecuencia_pagos=request.POST['frecuencia_pagos'],
                precio_mercado=request.POST.get('precio_mercado', 100.00),  # Valor por defecto
            )
            return redirect('bonds:list')
        except (ValueError, KeyError) as e:
            # Manejar errores de validación
            return render(request, 'bonds/create.html', {'error': str(e)})
    
    return render(request, 'bonds/create.html')

def bond_detail(request, bond_id):
    # Configuración de precisión decimal
    getcontext().prec = 10
    
    bond = get_object_or_404(Bond, id=bond_id)
    
    try:
        # Conversión segura a Decimal
        tasa = Decimal(str(bond.tasa_interes)) / Decimal('100')
        frecuencia = int(bond.frecuencia_pagos)
        valor_nominal = Decimal(str(bond.valor_nominal))
        precio_mercado = Decimal(str(bond.precio_mercado)) / Decimal('100') if bond.precio_mercado else Decimal('1')
        
        # Cálculo de períodos
        años = (bond.fecha_fin.year - bond.fecha_inicio.year)
        meses = (bond.fecha_fin.month - bond.fecha_inicio.month)
        num_pagos = frecuencia * años + (frecuencia * meses // 12)
        tasa_periodica = tasa / frecuencia
        
        # 1. Cálculo de la cuota constante (Método Francés)
        factor = (Decimal('1') - (Decimal('1') + tasa_periodica)**Decimal(-num_pagos)) / tasa_periodica
        cuota = valor_nominal / factor
        
        # 2. Cálculo de TCEA
        tcea = ((Decimal('1') + tasa_periodica)**frecuencia - Decimal('1')) * Decimal('100')
        
        # 3. Cálculo de TREA (asumiendo reinversión a misma tasa)
        trea = tcea  # Puede ajustarse según condiciones específicas
        
        # 4. Cálculo de Duración (Macaulay Duration)
        flujos = []
        saldo = valor_nominal
        duracion_numerador = Decimal('0')
        valor_presente_total = Decimal('0')
        
        for t in range(1, num_pagos + 1):
            interes = saldo * tasa_periodica
            amortizacion = cuota - interes
            flujo = cuota
            saldo -= amortizacion
            
            vp_flujo = flujo / ((Decimal('1') + tasa_periodica)**t)
            duracion_numerador += vp_flujo * t
            valor_presente_total += vp_flujo
            
            flujos.append({
                'periodo': t,
                'cuota': round(cuota, 2),
                'interes': round(interes, 2),
                'amortizacion': round(amortizacion, 2),
                'saldo': round(saldo, 2) if saldo > Decimal('0') else Decimal('0'),
                'vp_flujo': round(vp_flujo, 2)
            })
        
        duracion = duracion_numerador / valor_presente_total / frecuencia
        
        # 5. Duración Modificada
        duracion_modificada = duracion / (Decimal('1') + tasa_periodica)
        
        # 6. Convexidad
        convexidad_numerador = Decimal('0')
        for t in range(1, num_pagos + 1):
            vp_flujo = flujos[t-1]['vp_flujo']
            convexidad_numerador += vp_flujo * Decimal(t) * Decimal(t + 1)
        
        convexidad = convexidad_numerador / (valor_presente_total * (Decimal('1') + tasa_periodica)**2) / frecuencia**2
        
        # 7. Precio Máximo (Valor Presente)
        precio_maximo = valor_presente_total
        
        context = {
            'bond': bond,
            'flujos': flujos,
            'cuota': round(cuota, 2),
            'tcea': round(tcea, 2),
            'trea': round(trea, 2),
            'duracion': round(duracion, 4),
            'duracion_modificada': round(duracion_modificada, 4),
            'convexidad': round(convexidad, 4),
            'precio_maximo': round(precio_maximo, 2),
            'tasa_periodica': round(tasa_periodica * Decimal('100'), 2),
            'num_pagos': num_pagos,
        }
        
        return render(request, 'bonds/detail.html', context)
        
    except Exception as e:
        return render(request, 'bonds/error.html', {'error': str(e)})

def generar_tabla_amortizacion(bond):
    tasa_periodica = bond.tasa_interes / 100 / bond.frecuencia_pagos
    num_pagos = bond.frecuencia_pagos * ((bond.fecha_fin.year - bond.fecha_inicio.year) * 12 + bond.fecha_fin.month - bond.fecha_inicio.month) // 12
    factor = (1 - pow(1 + Decimal(tasa_periodica), -num_pagos)) / Decimal(tasa_periodica)
    cuota = bond.valor_nominal / factor
    
    tabla = []
    saldo = bond.valor_nominal
    
    for periodo in range(1, num_pagos + 1):
        interes = saldo * Decimal(tasa_periodica)
        amortizacion = cuota - interes
        saldo -= amortizacion
        
        tabla.append({
            'periodo': periodo,
            'cuota': round(cuota, 2),
            'interes': round(interes, 2),
            'amortizacion': round(amortizacion, 2),
            'saldo': round(saldo, 2) if saldo > 0 else 0
        })
    
    return tabla