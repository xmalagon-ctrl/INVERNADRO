
# invernadero_final.py
# MicroPython para ESP32
# MQ-135 en GPIO34 — Módulo relé HW-316 en GPIO26
# Ro calibrado = 3.55 kΩ (12h de calibración)
 
from machine import ADC, Pin
import time
import math
 
# ── Pines ──────────────────────────────────────────
sensor = ADC(Pin(34))
sensor.atten(ADC.ATTN_11DB)    # Rango 0–3.3V
sensor.width(ADC.WIDTH_12BIT)  # Resolución 0–4095
 
# Módulo HW-316 es activo en LOW
# LOW  = relé ON  → ventilador encendido
# HIGH = relé OFF → ventilador apagado
ventitador_1 = Pin(25, Pin.OUT)
ventitador_2 = Pin(33, Pin.OUT)
ventitador_1.value(1)  # Apagado al inicio (HIGH = OFF en HW-316)
ventitador_2.value(1)
 
# ── Calibración ────────────────────────────────────
Ro = 3.55   # kΩ — calibrado con 12h de datos reales
RL = 10.0   # kΩ — resistencia de carga del módulo
 
# ── Umbrales CO2 para hongos orejanas ──────────────
UMBRAL_ADVERTENCIA = 25   # ppm — ventilador ON
UMBRAL_CRITICO     = 60  # ppm — nivel peligroso
 
# ── Estado ─────────────────────────────────────────
ventilador_on = False
 
# ── Funciones ──────────────────────────────────────
def leer_voltaje():
    """Promedia 10 lecturas para reducir ruido."""
    total = sum(sensor.read() for _ in range(10))
    return (total / 10) * (3.3 / 4095.0)
 
def calcular_ppm(voltaje):
    """Convierte voltaje a ppm de CO2."""
    if voltaje <= 0.01:
        return 0.0
    Rs    = ((3.3 - voltaje) / voltaje) * RL
    ratio = Rs / Ro
    ppm   = 116.6020682 * math.pow(ratio, -2.769034857)
    return round(ppm, 1)
 
def controlar_ventilador(ppm):
    """Enciende o apaga el relé según CO2. HW-316 activo en LOW."""
    global ventilador_on
 
    if ppm >= UMBRAL_ADVERTENCIA and not ventilador_on:
        ventitador_1.value(0)          # LOW = relé ON
        ventitador_2.value(0)
        ventilador_on = True
        print(">>> VENTILADOR ENCENDIDO <<<")
 
    elif ppm < UMBRAL_ADVERTENCIA and ventilador_on:
        ventitador_1.value(1)          # HIGH = relé OFF
        ventitador_2.value(1)  
        ventilador_on = False
        print(">>> VENTILADOR APAGADO <<<")
 
def imprimir_estado(ppm):
    """Imprime el estado actual en el monitor serial."""
    if ppm >= UMBRAL_CRITICO:
        nivel = "CRITICO"
    elif ppm >= UMBRAL_ADVERTENCIA:
        nivel = "ADVERTENCIA"
    else:
        nivel = "Normal"
 
    vent = "ON" if ventilador_on else "OFF"
    print(f"CO2: {ppm:7.1f} ppm | {nivel:13} | Ventilador: {vent}")
 
# ── Inicio ─────────────────────────────────────────
print("========================================")
print("   Invernadero Orejanas — Sistema CO2")
print("========================================")
print(f"  Ro calibrado:       {Ro} kΩ")
print(f"  Umbral advertencia: {UMBRAL_ADVERTENCIA} ppm")
print(f"  Umbral critico:     {UMBRAL_CRITICO} ppm")
print("========================================")
 
# Calentamiento 30 segundos
print("Estabilizando sensor...")
for i in range(30, 0, -5):
    print(f"  {i}s...")
    time.sleep(5)
print("Sensor listo. Iniciando monitoreo...\n")
 
# ── Bucle principal ────────────────────────────────
while True:
    voltaje = leer_voltaje()
    ppm     = calcular_ppm(voltaje)
 
    controlar_ventilador(ppm)
    imprimir_estado(ppm)
 
    time.sleep(2)