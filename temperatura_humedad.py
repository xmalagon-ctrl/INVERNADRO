from machine import Pin, I2C
import time

# --- 1. Configuración de Pines ---
i2c = I2C(0, scl=Pin(19), sda=Pin(18))
sensor_addr = 0x44

# Relés
rele_calefactor = Pin(32, Pin.OUT)   # IN2 (12V) - NC
rele_nebulizador = Pin(15, Pin.OUT)  # IN1 (5V)  - NO
ven_entrada = Pin(25, Pin.OUT)       # LED Rojo
ven_salida = Pin(33, Pin.OUT)        # LED Azul

# --- CONFIGURACIÓN INICIAL (LÓGICA INVERSA) ---
# En Lógica Inversa: value(1) = Reposo / value(0) = Activado (Clic)

# Nebulizador (NO): Enviamos 1 para que NO haga clic (se queda abierto/apagado)
rele_nebulizador.value(1) 

# Calefactor (NC): Enviamos 0 para obligarlo a hacer clic (abre el circuito para que arranque APAGADO)
rele_calefactor.value(0)  

ven_entrada.value(0)
ven_salida.value(0)

# --- 2. Definición de Fases de Cultivo ---
fases_orellana = {
    "Inoculacion":    {"t_min": 20.0, "t_max": 26.0, "h_min": 80.0, "h_max": 85.0},
    "Incubacion":     {"t_min": 24.0, "t_max": 26.0, "h_min": 80.0, "h_max": 85.0},
    "Fructificacion": {"t_min": 15.5, "t_max": 18.5, "h_min": 87.0, "h_max": 93.0}
}

fase_actual = "Fructificacion" 

def leer_sht3x():
    try:
        i2c.writeto(sensor_addr, b'\x24\x00')
        time.sleep(0.1) 
        data = i2c.readfrom(sensor_addr, 6)
        temp_raw = (data[0] << 8) | data[1]
        t = -45 + (175 * temp_raw / 65535)
        hum_raw = (data[3] << 8) | data[4]
        h = 100 * hum_raw / 65535
        return t, h
    except Exception as e:
        return None, None

print(f"Iniciando Prueba - Fase: {fase_actual}")

while True:
    t, h = leer_sht3x()

    if t is not None and h is not None:
        limites = fases_orellana[fase_actual]
        estado_t = ""
        estado_h = ""

        # --- Lógica de Control de Temperatura ---
        if t < limites["t_min"]:
            # Calentando: Queremos que el NC deje pasar corriente (estado natural). Enviamos 1 (Reposo).
            rele_calefactor.value(1)
            ven_entrada.value(1)
            ven_salida.value(0)
            estado_t = "Calentando"
            
        elif t > limites["t_max"]:
            # Enfriando: Queremos que el NC corte la corriente (activar bobina). Enviamos 0 (Clic).
            rele_calefactor.value(0)
            ven_entrada.value(1)
            ven_salida.value(1)
            estado_t = "Enfriando"
            
        else:
            # Ideal: Apagar calefactor. Enviamos 0 (Clic) para mantener abierto el NC.
            rele_calefactor.value(0)
            ven_entrada.value(0)
            ven_salida.value(0)
            estado_t = "Rango Ideal"

        # --- Lógica de Control de Humedad ---
        if h < limites["h_min"]:
            # Nebulizando: Queremos cerrar el NO (activar bobina). Enviamos 0 (Clic).
            rele_nebulizador.value(0)
            estado_h = "Nebulizando"
            
        elif h > limites["h_max"]:
            # Humedad alta: Apagar nebulizador. Enviamos 1 (Reposo).
            rele_nebulizador.value(1)
            estado_h = "Humedad Alta"
            
        else:
            # Ideal: Apagar nebulizador. Enviamos 1 (Reposo).
            rele_nebulizador.value(1)
            estado_h = "Rango Ideal"

        print(f"T: {t:.1f}°C [{estado_t}] | H: {h:.1f}% [{estado_h}]")

    time.sleep(3)
