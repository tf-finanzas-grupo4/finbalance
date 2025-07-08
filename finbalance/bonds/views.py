from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Bond
from django.utils import timezone
from decimal import Decimal, getcontext
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import base64
from io import BytesIO

def generar_grafico_recuperacion(flujos):
    # Preparar datos
    periodos = [f['periodo'] for f in flujos]
    saldo_pendiente = [float(f['saldo']) for f in flujos]
    recuperado = [float(flujos[0]['saldo'] - f['saldo']) for f in flujos]  # Diferencia desde el inicial
    
    # Crear gráfico
    plt.figure(figsize=(10, 5))
    plt.plot(periodos, saldo_pendiente, label="Saldo Pendiente", color='red', marker='o')
    plt.plot(periodos, recuperado, label="Dinero Recuperado", color='green', marker='o')
    
    # Personalizar
    plt.title("Recuperación de Capital")
    plt.xlabel("Periodos")
    plt.ylabel("Monto ($)")
    plt.grid(True)
    plt.legend()
    plt.xticks(periodos)
    
    # Convertir a imagen base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    
    return base64.b64encode(image_png).decode('utf-8')

def calcular_vna(tasa_descuento, flujos):
    """Calcula el Valor Neto Actual (VNA) similar a la función de Excel"""
    vna = Decimal('0')
    for periodo, flujo in enumerate(flujos, start=1):
        vna += flujo / (1 + tasa_descuento)**periodo
    return vna

# bonds/views.py
@login_required
def bond_list(request):
    bonds = Bond.objects.all().order_by('-fecha_registro')
    return render(request, 'bonds/list.html', {'bonds': bonds})

@login_required
def bond_create(request):
    if request.method == 'POST':
        try:
            # Convertir el valor de plazo de gracia a booleano
            tiene_plazo_gracia = request.POST.get('tiene_plazo_gracia') == 'si'
            
            bond = Bond(
                valor_nominal=Decimal(request.POST['valor_nominal']),
                valor_comercial=Decimal(request.POST['valor_comercial']),
                num_anios=int(request.POST['num_anios']),
                frecuencia_cupon=int(request.POST['frecuencia_cupon']),
                dias_por_anio=int(request.POST['dias_por_anio']),
                tipo_tasa_interes=request.POST['tipo_tasa_interes'],
                capitalizacion=int(request.POST['capitalizacion']) if request.POST['tipo_tasa_interes'] == 'nominal' else None,
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
                tiene_plazo_gracia=tiene_plazo_gracia,
                periodos_gracia=int(request.POST.get('periodos_gracia', 0)) if tiene_plazo_gracia else None,
                tipo_gracia=request.POST.get('tipo_gracia') if tiene_plazo_gracia else None,
                metodo_amortizacion='Francés',
                fecha_registro=timezone.now()
            )
            bond.save()
            return redirect('bonds:list')
            
        except Exception as e:
            print(f"Error al crear bono: {str(e)}")
            return render(request, 'bonds/create.html', {
                'error': f"Error al crear el bono: {str(e)}",
                'form_data': request.POST
            })
    
    return render(request, 'bonds/create.html')


@login_required
def bond_detail(request, bond_id):
    getcontext().prec = 12
    bond = get_object_or_404(Bond, id=bond_id)
    
    try:
        # === PARTE 1: Variables base ===
        tasa = Decimal(str(bond.tasa_interes)) / Decimal('100')
        tasa_descuento = Decimal(str(bond.tasa_anual_descuento)) / Decimal('100')
        frecuencia = bond.frecuencia_cupon
        valor_nominal = Decimal(str(bond.valor_nominal))
        valor_comercial = Decimal(str(bond.valor_comercial))
        num_anios = bond.num_anios
        impuesto_renta = Decimal(str(bond.impuesto_renta)) / Decimal('100')
        num_pagos = frecuencia * num_anios
        periodos_gracia = bond.periodos_gracia if bond.tiene_plazo_gracia else 0

        # === PARTE 2: Tasas periódicas ===
        if bond.tipo_tasa_interes == 'nominal':
            tasa_periodica = tasa / frecuencia
            tasa_descuento_periodica = tasa_descuento / frecuencia
        else:
            tasa_periodica = (Decimal('1') + tasa)**(Decimal('1')/frecuencia) - Decimal('1')
            tasa_descuento_periodica = (Decimal('1') + tasa_descuento)**(Decimal('1')/frecuencia) - Decimal('1')

        tea = ((Decimal('1') + tasa_periodica)**frecuencia - Decimal('1')) * Decimal('100')
        tep = tasa_periodica * Decimal('100')
        cok_periodo = tasa_descuento_periodica * Decimal('100')

        # === PARTE 3: Cuota fija del método francés ===
        factor = (Decimal('1') - (Decimal('1') + tasa_periodica)**Decimal(-num_pagos)) / tasa_periodica
        cuota = valor_nominal / factor

        # === PARTE 4: Costos iniciales ===
        def calcular_costos(tipo):
            return sum([
                getattr(bond, f'porcentaje_{nombre}') * (Decimal('1') if getattr(bond, f'tipo_{nombre}') in [tipo, 'ambos'] else Decimal('0'))
                for nombre in ['estructuracion', 'colocacion', 'flotacion', 'cavali']
            ]) / Decimal('100') * valor_comercial

        costes_emisor = calcular_costos('emisor')
        costes_bonista = calcular_costos('bonista')

        # === PARTE 5: Flujos ===
        saldo = valor_nominal
        flujos = []
        flujos_bonista = []
        flujos_emisor = [valor_comercial - costes_emisor]
        flujos_emisor_con_escudo = [valor_comercial - costes_emisor]
        duracion_numerador = valor_presente_total = convexidad_numerador = Decimal('0')

        for t in range(1, num_pagos + 1):
            en_gracia = t <= periodos_gracia

            if en_gracia:
                if bond.tipo_gracia == 'total':
                    interes = amortizacion = cuota_periodo = Decimal('0')
                elif bond.tipo_gracia == 'parcial':
                    interes = saldo * tasa_periodica
                    amortizacion = Decimal('0')
                    cuota_periodo = interes
                else:
                    interes = saldo * tasa_periodica
                    amortizacion = Decimal('0')
                    cuota_periodo = interes
                    saldo += interes
            else:
                interes = saldo * tasa_periodica
                cuota_periodo = cuota
                amortizacion = cuota - interes

            interes_neto = interes * (Decimal('1') - impuesto_renta)
            escudo = interes * impuesto_renta
            flujo_bonista = amortizacion + interes_neto
            flujo_emisor = -cuota_periodo
            flujo_emisor_con_escudo = flujo_emisor + escudo

            # === Agregar prima al último periodo ===
            prima = Decimal('0')
            if t == num_pagos and bond.porcentaje_prima:
                prima = valor_nominal * bond.porcentaje_prima / Decimal('100')
                flujo_bonista += prima  # 👈 Aquí sí se suma correctamente
                flujos_emisor[-1] -= prima  # 👈 El emisor paga más al final
                flujos_emisor_con_escudo[-1] -= prima

            flujos_bonista.append(flujo_bonista)
            flujos_emisor.append(flujo_emisor)
            flujos_emisor_con_escudo.append(flujo_emisor_con_escudo)

            factor_actualizacion = Decimal('1') / (Decimal('1') + tasa_descuento_periodica)**t
            vp_flujo = flujo_bonista * factor_actualizacion

            if not en_gracia or bond.tipo_gracia != 'total':
                saldo -= amortizacion

            duracion_numerador += vp_flujo * t
            valor_presente_total += vp_flujo
            convexidad_numerador += vp_flujo * t * (t + 1)

            flujos.append({
                'periodo': t,
                'cuota': cuota_periodo,
                'interes': interes,
                'amortizacion': amortizacion,
                'saldo': saldo if saldo > 0 else Decimal('0'),
                'vp_flujo': vp_flujo,
                'flujo_bonista': flujo_bonista,
                'flujo_emisor': flujo_emisor,
                'prima': prima,
                'escudo': escudo,
                'flujo_emisor_con_escudo': flujo_emisor_con_escudo,
                'factor_actualizacion': factor_actualizacion,
                'fa_x_plazo': factor_actualizacion * t,
                'en_gracia': en_gracia,
                'tipo_gracia': bond.tipo_gracia if en_gracia else None,
            })

        # === PARTE 6: Indicadores finales ===
        def calcular_tir(flujos):
            tasa = Decimal('0.1')
            for _ in range(100):
                vna = sum(cf / (1 + tasa)**i for i, cf in enumerate(flujos))
                derivada = sum(-i * cf / (1 + tasa)**(i + 1) for i, cf in enumerate(flujos))
                if abs(vna) < Decimal('0.0001') or derivada == 0:
                    break
                tasa -= vna / derivada
            return tasa

        tir_emisor = calcular_tir(flujos_emisor)
        tcea_emisor = ((Decimal('1') + tir_emisor)**frecuencia - Decimal('1')) * Decimal('100')

        tir_emisor_escudo = calcular_tir(flujos_emisor_con_escudo)
        tcea_emisor_escudo = ((Decimal('1') + tir_emisor_escudo)**frecuencia - Decimal('1')) * Decimal('100')

        trea_bonista = ((Decimal('1') + tasa_descuento_periodica)**frecuencia - Decimal('1')) * Decimal('100')
        
        
        
        precio_actual = calcular_vna(tasa_descuento_periodica, flujos_bonista) - calcular_vna(tasa_descuento_periodica, flujos_bonista) + valor_comercial + costes_bonista
        utilidad = precio_actual - (valor_comercial + costes_bonista) 


        duracion = (duracion_numerador / valor_presente_total) / frecuencia
        duracion_modificada = duracion / (Decimal('1') + tasa_descuento_periodica)
        convexidad = (convexidad_numerador / (valor_presente_total * (Decimal('1') + tasa_descuento_periodica)**2)) / (frecuencia**2)
        total_ratios = duracion + convexidad

        periodo_nombre = {
            12: 'Mensual', 6: 'Bimestral', 4: 'Trimestral',
            3: 'Cuatrimestral', 2: 'Semestral', 1: 'Anual'
        }.get(frecuencia, 'Periódica')

        grafico_recuperacion = generar_grafico_recuperacion(flujos)

        return render(request, 'bonds/detail.html', {
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
            'precio_teorico': valor_presente_total,
            'tasa_periodica': tasa_periodica * Decimal('100'),
            'periodos_gracia': periodos_gracia,
            'grafico_recuperacion': grafico_recuperacion,
        })
    

    except Exception as e:
        return render(request, 'bonds/error.html', {
            'error': f"Error en cálculos: {str(e)}",
            'bond': bond
        })
    
    
    