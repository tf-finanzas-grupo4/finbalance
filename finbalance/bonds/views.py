from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Bond
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_DOWN
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import math
from datetime import datetime, timedelta

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
def bond_delete(request, pk):
    bond = get_object_or_404(Bond, pk=pk)
    if request.method == 'POST':
        bond.delete()
        return redirect('bonds:list')  # Redirige a la lista de bonos
    return render(request, 'bonds/bond_confirm_delete.html', {'bond': bond})

def calculate_bond_metrics(bond):
    """
    Calcula todas las métricas financieras para un bono usando el método francés
    """
    # Cálculos básicos
    periodos_por_anio = bond.frecuencia_cupon
    total_periodos = bond.num_anios * periodos_por_anio
    dias_capitalizacion = bond.dias_por_anio // periodos_por_anio
    
    # Convertir a float para cálculos matemáticos
    tasa_interes = float(bond.tasa_interes)
    tasa_descuento = float(bond.tasa_anual_descuento)
    valor_comercial = float(bond.valor_comercial)  # ← AGREGAR ESTA LÍNEA
    
    # Cálculo de tasas
    if bond.tipo_tasa_interes == 'efectiva':
        tea = tasa_interes / 100
    else:  # nominal
        capitalizacion = bond.capitalizacion or 1
        tea = (1 + (tasa_interes / 100) / capitalizacion) ** capitalizacion - 1
    
    # Tasa efectiva por periodo
    tep = (1 + tea) ** (1 / periodos_por_anio) - 1
    
    # COK (Costo de oportunidad del capital)
    cok_anual = tasa_descuento / 100
    cok_periodo = (1 + cok_anual) ** (1 / periodos_por_anio) - 1
    
    # Cálculo de costes
    costes_data = calculate_costes(bond)
    costes_bonista = costes_data['bonista']
    
    # Generar flujos de caja
    flujos = generate_cash_flows(bond, tep, total_periodos)
    
    # Cálculo del precio actual (valor presente)
    precio_actual = calculate_present_value(flujos, cok_periodo)
    
   # Cálculo de duración y convexidad (ahora devuelve 4 valores)
    duracion, convexidad, duracion_modificada, total_ratios = calculate_duration_convexity(flujos, cok_periodo, periodos_por_anio)
    
    # Cálculo de TCEAs y TREA
    tcea_emisor = calculate_tcea_emisor(bond, flujos, costes_data)
    tcea_emisor_escudo = calculate_tcea_emisor_escudo(bond, flujos, costes_data)
    trea_bonista = calculate_trea_bonista(bond, flujos, costes_data)
    
    # Utilidad/Pérdida (ahora ambos son float)
    utilidad = -float(bond.valor_comercial) - costes_bonista + precio_actual
    
    
    return {
        'bond': bond,
        'periodos_por_anio': periodos_por_anio,
        'periodo_nombre': get_periodo_name(periodos_por_anio),
        'dias_capitalizacion': dias_capitalizacion,
        'tea': tea * 100,
        'tep': tep * 100,
        'cok_periodo': cok_periodo * 100,
        'flujos': flujos,
        'precio_actual': precio_actual,
        'utilidad': utilidad,
        'duracion': duracion,
        'convexidad': convexidad,
        'duracion_modificada': duracion_modificada,
        'total_ratios': total_ratios,  # Usar el valor calculado
        'tcea_emisor': tcea_emisor * 100,
        'tcea_emisor_escudo': tcea_emisor_escudo * 100,
        'trea_bonista': trea_bonista * 100,
        'costes_emisor': costes_data['emisor'],
        'costes_bonista': costes_data['bonista'],
    }

def calculate_costes(bond):
    """
    Calcula los costes iniciales del emisor y bonista
    """
    valor_comercial = float(bond.valor_comercial)
    
    costes_emisor = 0
    costes_bonista = 0
    
    
    # Estructuración
    estr_pct = float(bond.porcentaje_estructuracion or 0)
    estr_monto = (estr_pct / 100) * valor_comercial
    if bond.tipo_estructuracion == 'emisor':
        costes_emisor += estr_monto
    elif bond.tipo_estructuracion == 'bonista':
        costes_bonista += estr_monto
    elif bond.tipo_estructuracion == 'ambos':
        costes_emisor += estr_monto
        costes_bonista += estr_monto
    
    # Colocación
    coloc_pct = float(bond.porcentaje_colocacion or 0)
    coloc_monto = (coloc_pct / 100) * valor_comercial
    if bond.tipo_colocacion == 'emisor':
        costes_emisor += coloc_monto
    elif bond.tipo_colocacion == 'bonista':
        costes_bonista += coloc_monto
    elif bond.tipo_colocacion == 'ambos':
        costes_emisor += coloc_monto 
        costes_bonista += coloc_monto 
    
    # Flotación
    flot_pct = float(bond.porcentaje_flotacion or 0)
    flot_monto = (flot_pct / 100) * valor_comercial
    if bond.tipo_flotacion == 'emisor':
        costes_emisor += flot_monto
    elif bond.tipo_flotacion == 'bonista':
        costes_bonista += flot_monto
    elif bond.tipo_flotacion == 'ambos':
        costes_emisor += flot_monto 
        costes_bonista += flot_monto 
    
    # Cavali
    cavali_pct = float(bond.porcentaje_cavali or 0)
    cavali_monto = (cavali_pct / 100) * valor_comercial
    if bond.tipo_cavali == 'emisor':
        costes_emisor += cavali_monto
    elif bond.tipo_cavali == 'bonista':
        costes_bonista += cavali_monto
    elif bond.tipo_cavali == 'ambos':
        costes_emisor += cavali_monto 
        costes_bonista += cavali_monto 
    
    return {
        'emisor': costes_emisor,
        'bonista': costes_bonista
    }

def generate_cash_flows(bond, tep, total_periodos):
    """
    Genera los flujos de caja usando el método francés
    """
    flujos = []
    valor_nominal = float(bond.valor_nominal)
    prima_pct = float(bond.porcentaje_prima or 0)
    # La prima se calcula como porcentaje del valor nominal y se paga en el último período
    prima_total = (prima_pct / 100) * valor_nominal
    
    # Verificar si hay periodo de gracia
    periodos_gracia = 0
    if bond.tiene_plazo_gracia:
        periodos_gracia = bond.periodos_gracia or 0
    
    # Cálculo de la cuota constante (método francés)
    if bond.tiene_plazo_gracia and bond.tipo_gracia == 'total':
        # Periodo de gracia total: no se paga ni interés ni capital
        periodos_pago = total_periodos - periodos_gracia
        if periodos_pago > 0:
            cuota_constante = (valor_nominal * tep) / (1 - (1 + tep) ** -periodos_pago)
        else:
            cuota_constante = 0
    elif bond.tiene_plazo_gracia and bond.tipo_gracia == 'parcial':
        # Periodo de gracia parcial: solo se paga interés
        periodos_pago = total_periodos - periodos_gracia
        if periodos_pago > 0:
            cuota_constante = (valor_nominal * tep) / (1 - (1 + tep) ** -periodos_pago)
        else:
            cuota_constante = 0
    else:
        # Sin periodo de gracia
        cuota_constante = (valor_nominal * tep) / (1 - (1 + tep) ** -total_periodos)
    
    saldo_pendiente = valor_nominal
    
    for periodo in range(1, total_periodos + 1):
        # Cálculo de interés
        interes = saldo_pendiente * tep
        
        # Determinar tipo de periodo
        if periodo <= periodos_gracia:
            if bond.tipo_gracia == 'total':
                # Periodo de gracia total
                cuota = 0
                amortizacion = 0
                # El interés se capitaliza
                saldo_pendiente += interes
                interes_mostrado = 0
            else:  # parcial
                # Periodo de gracia parcial
                cuota = interes
                amortizacion = 0
                interes_mostrado = interes
        else:
            # Periodo normal
            cuota = cuota_constante
            amortizacion = cuota - interes
            saldo_pendiente -= amortizacion
            interes_mostrado = interes
        
        # Ajustar último periodo para evitar saldo residual
        if periodo == total_periodos and saldo_pendiente > 0.01:
            amortizacion += saldo_pendiente
            cuota = interes_mostrado + amortizacion
            saldo_pendiente = 0
        
        # Asignar prima
        prima_periodo = prima_total if periodo == total_periodos else 0
        
        # Prima mostrada
        if periodo == total_periodos:
            prima_mostrada = (prima_pct / 100) * amortizacion
        else:
            prima_mostrada = 0
        
        flujos.append({
            'periodo': periodo,
            'cuota': round(cuota, 2),
            'interes': round(interes_mostrado, 2),
            'amortizacion': round(amortizacion, 2),
            'saldo': round(saldo_pendiente, 2),
            'prima': round(prima_mostrada, 2),
            'prima_calculo': round(prima_periodo, 2)
        })
    
    return flujos

def calculate_present_value(flujos, cok_periodo):
    """
    Calcula el valor presente de los flujos de caja
    """
    valor_presente = 0
    for flujo in flujos:
        prima_real = flujo.get('prima_calculo', flujo['prima'])
        flujo_total = flujo['cuota'] + prima_real
        valor_presente += flujo_total / ((1 + cok_periodo) ** flujo['periodo'])
    
    return valor_presente

def calculate_duration_convexity(flujos, cok_periodo, periodos_por_anio):
    """
    Calcula la duración y convexidad del bono
    """
    # Inicializar variables
    duracion_numerador = Decimal('0')
    valor_presente_total = Decimal('0')
    convexidad_numerador = Decimal('0')
    
    for flujo in flujos:
        prima_real = flujo.get('prima_calculo', flujo['prima'])
        flujo_total = Decimal(str(flujo['cuota'])) + Decimal(str(prima_real))
        factor_actualizacion = Decimal('1') / (Decimal('1') + Decimal(str(cok_periodo))) ** Decimal(str(flujo['periodo']))
        vp_flujo = flujo_total * factor_actualizacion
        
        duracion_numerador += vp_flujo * Decimal(str(flujo['periodo']))
        valor_presente_total += vp_flujo
        convexidad_numerador += vp_flujo * Decimal(str(flujo['periodo'])) * (Decimal(str(flujo['periodo'])) + Decimal('1'))
    
    # Cálculo de duración (en años)
    duracion = (duracion_numerador / valor_presente_total) / Decimal(str(periodos_por_anio))
    
    # Duración modificada
    duracion_modificada = duracion / (Decimal('1') + Decimal(str(cok_periodo)))
    
    # Convexidad (en años)
    convexidad = (convexidad_numerador / (valor_presente_total * (Decimal('1') + Decimal(str(cok_periodo)))**2)) / (Decimal(str(periodos_por_anio))**2)
    
    # Total ratios
    total_ratios = duracion + convexidad
    
    return float(duracion), float(convexidad), float(duracion_modificada), float(total_ratios)

def calculate_tcea_emisor(bond, flujos, costes_data):
    """
    Calcula la TCEA del emisor
    """
    # Flujo inicial (ingreso neto para el emisor)
    flujo_inicial = float(bond.valor_comercial) - costes_data['emisor']
    
    # Flujos futuros (egresos para el emisor)
    flujos_futuros = []
    for flujo in flujos:
        prima_real = flujo.get('prima_calculo', flujo['prima'])
        flujo_total = flujo['cuota'] + prima_real
        flujos_futuros.append(-flujo_total)  # Negativo porque son egresos
    
    # Usar método de Newton-Raphson para encontrar la TIR
    tir = newton_raphson_tir([flujo_inicial] + flujos_futuros)
    
    # Convertir a tasa anual
    periodos_por_anio = len(flujos) / bond.num_anios
    tcea = (1 + tir) ** periodos_por_anio - 1
    
    return tcea

def calculate_tcea_emisor_escudo(bond, flujos, costes_data):
    """
    Calcula la TCEA del emisor considerando el escudo fiscal
    """
    # Flujo inicial
    flujo_inicial = float(bond.valor_comercial) - costes_data['emisor']
    
    # Flujos futuros con escudo fiscal
    flujos_futuros = []
    impuesto_renta = float(bond.impuesto_renta or 0)
    
    for flujo in flujos:
        interes_bruto = flujo['interes']
        escudo_fiscal = interes_bruto * (impuesto_renta / 100)
        interes_neto = interes_bruto - escudo_fiscal
        prima_real = flujo.get('prima_calculo', flujo['prima'])
        flujo_total = interes_neto + flujo['amortizacion'] + prima_real
        flujos_futuros.append(-flujo_total)
    
    # Calcular TIR
    tir = newton_raphson_tir([flujo_inicial] + flujos_futuros)
    
    # Convertir a tasa anual
    periodos_por_anio = len(flujos) / bond.num_anios
    tcea = (1 + tir) ** periodos_por_anio - 1
    
    return tcea

def calculate_trea_bonista(bond, flujos, costes_data):
    """
    Calcula la TREA del bonista
    """
    # Flujo inicial (egreso para el bonista)
    flujo_inicial = -(float(bond.valor_comercial) + costes_data['bonista'])
    
    # Flujos futuros (ingresos para el bonista)
    flujos_futuros = []
    for flujo in flujos:
        prima_real = flujo.get('prima_calculo', flujo['prima'])
        flujo_total = flujo['cuota'] + prima_real
        flujos_futuros.append(flujo_total)
    
    # Calcular TIR
    tir = newton_raphson_tir([flujo_inicial] + flujos_futuros)
    
    # Convertir a tasa anual
    periodos_por_anio = len(flujos) / bond.num_anios
    trea = (1 + tir) ** periodos_por_anio - 1
    
    return trea

def newton_raphson_tir(flujos):
    """
    Calcula la TIR usando el método de Newton-Raphson
    """
    # Estimación inicial
    r = 0.1
    tolerance = 1e-10
    max_iterations = 100
    
    for _ in range(max_iterations):
        # Calcular VPN y su derivada
        vpn = 0
        vpn_derivada = 0
        
        for t, flujo in enumerate(flujos):
            vpn += flujo / ((1 + r) ** t)
            if t > 0:
                vpn_derivada -= t * flujo / ((1 + r) ** (t + 1))
        
        # Verificar convergencia
        if abs(vpn) < tolerance:
            break
        
        # Actualizar estimación
        if vpn_derivada != 0:
            r_new = r - vpn / vpn_derivada
        else:
            break
        
        # Verificar convergencia en la tasa
        if abs(r_new - r) < tolerance:
            break
        
        r = r_new
    
    return r

def get_periodo_name(periodos_por_anio):
    """
    Obtiene el nombre del periodo según la frecuencia
    """
    periodo_names = {
        1: 'anual',
        2: 'semestral',
        3: 'cuatrimestral',
        4: 'trimestral',
        6: 'bimestral',
        12: 'mensual',
        360: 'diario'
    }
    return periodo_names.get(periodos_por_anio, 'período')

@login_required
def bond_detail(request, bond_id):
    """
    Vista para mostrar el detalle del bono con todos los cálculos
    """
    bond = get_object_or_404(Bond, id=bond_id)
    context = calculate_bond_metrics(bond)
    return render(request, 'bonds/detail.html', context)