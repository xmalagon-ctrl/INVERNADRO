from machine import Pin, ADC
import time
from pantalla import Pantalla
from luces import Luces
from co2 import SensorCO2

#FUNCIONES
def fotoResistor():
         
    valor_1 = ldr_1.read()
    valor_2 = ldr_2.read()
    valor_3 = ldr_3.read()
    #print(f"LDR: {valor_1}, {valor_2}, {valor_3}")#SOLO DESCOMENTAR EN  CASOS ESPECIFICOS, PARA QUE NO SE ESTE IMPRIMIENDO TANTA INFORMACION EN CONSOLA
    #SE DEBE MODIFICAR EL RANGO DE OSCURIDAD, DEPENDIENDO DE CALIBRACION EN CAJA
    if valor_1 <= 1500 and valor_2 <= 1500 and valor_3 <= 1500: # ESTA OSCURO 
        return "Luces Apagadas"
    else:
        return "Luces Encendidas"
        

# PINES
luces_led = Pin(26, Pin.OUT)
led = Pin(13, Pin.OUT)
#FOTORESISTENCIAS
ldr_1= ADC (Pin(12))
ldr_2= ADC (Pin(14))
ldr_3= ADC (Pin(27))
#PANTALLA
scl = Pin(22, Pin.OUT)
sda = Pin(21, Pin.OUT)
#CONFIGURACION DEL RANGO DE LECTRURA
ldr_1.atten(ADC.ATTN_11DB)
ldr_2.atten(ADC.ATTN_11DB)
ldr_3.atten(ADC.ATTN_11DB)

#OBJETOS
sistema_pantalla = Pantalla( scl, sda)
sistema_iluminacion = Luces(led, luces_led, 10000) #SE DEBE DE EDITAR EL TIEMPO DE CALIBRACION PARA QUE LAS ETAPAS INICIEN SOLO CUANDO TERMINE DE CALIBRAR EL INVERNADERO
#SE DEBE MODIFICAR UMBRAL INICIAL, DEPENDIENDO DE CALIBRACION EN CAJA
sistema_co2 = SensorCO2(pin_sensor=35, pin_vent1=25, pin_vent2=33, umbral_inicial=25.0)


luces_led.value(1) #se inica las luces apagadas
sistema_pantalla.configuracion()

print("--- Iniciando Monitoreo del Invernadero ---")

ppm_actual = "Calibrando..." #SE INICIALIZA ASI EL PPM (C02) MIENTRAS SE CALIBRA

# BUCLE PRINCIPAL (SW DEBE DE EDITAR LA CONDICION DEL BUCLE CUANDO YA TENGAMOS TODO EL CODIGO, PARA QUE NO QUEDE EN UN BUCLE INFINITO)
while True:
    
    ppm_medido = sistema_co2.actualizar()
    
    if ppm_medido is not None:  #SI DEVUELVE LECTURA REAL, ACTUALIZA VARIABLES DE CO2
        ppm_actual = f"{ppm_medido} ppm"
    
    if sistema_co2.estado_actual == "Estabilizando": #HASTA QUE NO TERMINE DE CALIBRAR NO EMPIEZA LAS ETPAS
        sistema_pantalla.mostrarEnPantalla(0, "", 0, "CALIBRANDO...", 0, "INVERNADERO", 0, "")      
    else:
        #DIVISION DE ETAPAS
        sistema_iluminacion.actualizar()
        etapa = sistema_iluminacion.obtener_etapa()
        estado_luces = fotoResistor()
    
        if "incubacion" in etapa:
            sistema_co2.cambiar_umbral(25.0)  #EDITAR UMBRAL DEPENDIENDO DE CALIBRACION Y DE ETAPA
            
            #RESTO DE CODIGO DE LAS DEMAS VARIABLES
            
            
        elif "fructificacion" in etapa:
            sistema_co2.cambiar_umbral(20.0)  #EDITAR UMBRAL DEPENDIENDO DE CALIBRACION Y DE ETAPA

            #RESTO DE CODIGO DE LAS DEMAS VARIABLES
           
        
        sistema_pantalla.mostrarEnPantalla(0, etapa, 0, estado_luces, 0, "HUMEDAD Y TEM", 0, f"CO2= {ppm_actual}") 
    print ( f"CO2= {ppm_actual}")#SOLO DESCOMENTAR EN  CASOS ESPECIFICOS, PARA QUE NO SE ESTE IMPRIMIENDO TANTA INFORMACION EN CONSOLA
    time.sleep_ms(10)
