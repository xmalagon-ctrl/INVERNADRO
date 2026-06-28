from machine import Pin, ADC
import time
from pantalla import Pantalla
from luces import Luces
from co2 import SensorCO2
from tem_hum import Tem_Hum

#FUNCIONES
def fotoResistor():
         
    valor_1 = ldr_1.read()
    valor_2 = ldr_2.read()
    #print(f"LDR: {valor_1}, {valor_2}, {valor_3}")#SOLO DESCOMENTAR EN  CASOS ESPECIFICOS, PARA QUE NO SE ESTE IMPRIMIENDO TANTA INFORMACION EN CONSOLA
    #SE DEBE MODIFICAR EL RANGO DE OSCURIDAD, DEPENDIENDO DE CALIBRACION EN CAJA
    if valor_1 <= 1500 and valor_2 <= 1500: # ESTA OSCURO 
        return "Luces Apagadas"
    else:
        return "Luces Encendidas"
        

# PINES
luces_led = Pin(26, Pin.OUT)
led = Pin(13, Pin.OUT)
#FOTORESISTENCIAS
ldr_1= ADC (Pin(14))
ldr_2= ADC (Pin(27))
#PANTALLA
scl_pan = 22
sda_pan = 21
#VENTILADORES
ven_entrada_global = Pin(25, Pin.OUT)
ven_salida_global = Pin(33, Pin.OUT)
#CALEFACTOR
calefactor = Pin(32, Pin.OUT)
#NEUBULIZADOR
nebulizador = Pin(12, Pin.OUT)
#CONFIGURACION DEL RANGO DE LECTRURA
ldr_1.atten(ADC.ATTN_11DB)
ldr_2.atten(ADC.ATTN_11DB)


#OBJETOS
sistema_pantalla = Pantalla( scl_pan, sda_pan)
sistema_iluminacion = Luces(led, luces_led, 10000) #SE DEBE DE EDITAR EL TIEMPO DE CALIBRACION PARA QUE LAS ETAPAS INICIEN SOLO CUANDO TERMINE DE CALIBRAR EL INVERNADERO
#SE DEBE MODIFICAR UMBRAL INICIAL, DEPENDIENDO DE CALIBRACION EN CAJA
sistema_co2 = SensorCO2(pin_sensor=35,pin_vent1=ven_entrada_global, pin_vent2=ven_salida_global, umbral_inicial=25.0)
sistema_clima = Tem_Hum(scl_clima=19, sda_clima=18, ven_entrada =ven_entrada_global, ven_salida = ven_salida_global, rele_calefactor =calefactor, rele_nebulizador = nebulizador)



luces_led.value(1) #se inica las luces apagadas
sistema_pantalla.configuracion()

print("--- Iniciando Monitoreo del Invernadero ---")

# Variables globales de visualización para la pantalla LCD mientras se calibra 
ppm_actual = "Calibrando..." 
temperatura = "T:--- "
humedad = "H:---"
estado_Co2 = "Estabilizando"

#ESTO ES PARA QUE LA PANTALLA NO ESTE IMPRIMIENDO LOS MENSAJES CADA VES QUE SE REPITA EL BUCLE, Y NO GENERE PICOS DE VOLTAJE
ultimo_tiempo_pantalla = time.ticks_ms()

# BUCLE PRINCIPAL 
while True:
    ppm_medido = sistema_co2.actualizar()
    temp, hum, est_t, est_h = sistema_clima.actualizar()
    
    
    # Actualizar valores locales en memoria si hay lecturas nuevas
    if ppm_medido is not None:
        ppm_actual = f"{ppm_medido} ppm"
        
    if temp is not None and hum is not None:
        temperatura = f"{temp}C"
        humedad = f"{hum}%"

    
    #HASTA QUE NO TERMINE DE CALIBRAR NO EMPIEZA LAS ETAPAS
    if sistema_co2.estado_actual == "Estabilizando": 
        # Actualizar pantalla de calibración de forma no bloqueante cada 1 segundo
        if time.ticks_diff(time.ticks_ms(), ultimo_tiempo_pantalla) >= 1000: #SE PUEDE MODIFICAR CUANDO SE HAGA CALIBRACIONES
            sistema_pantalla.mostrarEnPantalla(0, "", 0, "CALIBRANDO...", 0, "INVERNADERO", 0, "")      
            ultimo_tiempo_pantalla = time.ticks_ms()    
    else:
        #DIVISION DE ETAPAS
        sistema_iluminacion.actualizar()
        etapa = sistema_iluminacion.obtener_etapa()
        estado_luces = fotoResistor()
        estado_Co2 = sistema_co2.estado_actual 
    
        if "incubacion" in etapa:
            sistema_co2.cambiar_umbral(25.0)  #EDITAR UMBRAL DEPENDIENDO DE CALIBRACION Y DE ETAPA
            #EDITAR CLIMA DEPENDIENDO DE CALIBRACION, ORDEN:t_min, t_max, h_min, h_max
            sistema_clima.cambiar_limites(24.0, 26.0, 80.0, 85.0)
            
            # CHOQUE DE PRIORIDAD EN CO2 Y TEM_HUM YA QUE LOS DOS INTERFIEREN CON LOS VENTILADORES PUEDE TENER UN CHOQUE
            if est_t == "ENFRIANDO" or est_h == "ALTA" or (estado_Co2  == "C02 ALTO"):
                ven_entrada_global.value(0) # Se encienden si CUALQUIERA de los dos lo necesita
                ven_salida_global.value(0)
            else:
                ven_entrada_global.value(1) # Solo se apagan si NINGUNO los requiere
                ven_salida_global.value(1)
            
        elif "fructificacion" in etapa:
            sistema_co2.cambiar_umbral(20.0)  #EDITAR UMBRAL DEPENDIENDO DE CALIBRACION Y DE ETAPA
            #EDITAR CLIMA DEPENDIENDO DE CALIBRACION, ORDEN:t_min, t_max, h_min, h_max
            sistema_clima.cambiar_limites(15.5, 18.5, 87.0, 93.0)
            
            
            
             # CHOQUE DE PRIORIDAD  CON VENTILADORES
            if est_t == "ENFRIANDO" or est_h == "ALTA"or (estado_Co2  == "C02 ALTO"):
                ven_entrada_global.value(0) # Se encienden si CUALQUIERA de los dos lo necesita
                ven_salida_global.value(0)
            else:
                ven_entrada_global.value(1) # Solo se apagan si NINGUNO los requiere
                ven_salida_global.value(1)
           
           
        #IMRESION EN PANTALLA (Cada 500ms)
        if time.ticks_diff(time.ticks_ms(), ultimo_tiempo_pantalla) >= 500:
            if "final" in etapa:
                #SE APAGA TODO
                ven_entrada_global.value(1) 
                ven_salida_global.value(1)
                calefactor.value(1)
                nebulizador.value(1)
                luces_led.value(1)
                sistema_pantalla.mostrarEnPantalla(0, "", 0, "YA PUEDES COSECHAR", 0, "TUS ORELLANAS", 0, "")
                print("--- PROCESO FINALIZADO: Saliendo del bucle principal ---")
                break #ROMPE EL BUCLE PRINCIPAL
            else:
                # Fila 1: etapa | Fila 2: estado_luces | Fila 3: clima_actual | Fila 4: ppm_actual
                sistema_pantalla.mostrarEnPantalla(0, etapa, 0, estado_luces, 0,"T:{est_t}  H:{est_h}", 0, estado_Co2)
                ultimo_tiempo_pantalla = time.ticks_ms() # Reinicia el temporizador de la pantalla
           
    #SOLO DESCOMENTAR EN  CASOS ESPECIFICOS, PARA QUE NO SE ESTE IMPRIMIENDO TANTA INFORMACION EN CONSOLA
    print(f"{estado_Co2} ,{ppm_actual} | H: {est_h}, {humedad} |T: {est_t}, {temperatura}")    
    time.sleep_ms(10)
