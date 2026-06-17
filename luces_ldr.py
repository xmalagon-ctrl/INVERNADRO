import time
from machine import Pin, ADC

#DECLARACION DE PINES
luces_led = Pin(26, Pin.OUT)
led = Pin(13, Pin.OUT)
ldr_1= ADC (Pin(12)) #DECLARA COMO ENTRADA ANALOGICA
ldr_2= ADC (Pin(14))
ldr_3= ADC (Pin(27))
ldr_1.atten(ADC.ATTN_11DB) #CONFIGURACION DEL RANGO DE LECTRURA
ldr_2.atten(ADC.ATTN_11DB)
ldr_3.atten(ADC.ATTN_11DB)


luces_led.value(1)
led.value(1)   
for segundo in range(15, 0, -1):
    print(f"Esperando... {segundo} segundos restantes")
    time.sleep(1)

print("Espera terminada..")

# BUCLE PRINCIPAL
while True:
    led.value(0)
    
    luces_led.value(0)
    print("LED encendido")
    time.sleep(8)

    luces_led.value(1)
    print("LED apagado")
    time.sleep(8)

'''
valor_1 = ldr_1.read()
valor_2 = ldr_2.read()
valor_3 = ldr_3.read()
print(f"LDR: {valor_1}, {valor_2}, {valor_3}")
if valor_1 <= 1500 and valor_2 <= 1500 and valor_3 <= 1500: # ESTA OSCURO POR ENDE ENCIENDE LAS LUCES
    print("Luces LED encendidas")
    led.value(0)
else :
    print("Luces LED apagadas")
    led.value(1)
'''




    

