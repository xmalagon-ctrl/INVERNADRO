import time

class Luces:
    def __init__(self, led, luces_led, tiempoDeCalibracion):
        self.led = led
        self.luces_led = luces_led
        
        self.estado_luces_leds = False 
        self.ultimo_cambio = time.ticks_ms()
        
        # Iniciamos directo en la etapa de incubación
        self.etapa = "incubacion"
        self.inicio_incubacion = time.ticks_ms() + tiempoDeCalibracion

    def actualizar(self):
        tiempo_actual = time.ticks_ms()
        
        # === ETAPA 1: INCUBACIÓN ===
        if self.etapa == "incubacion":
            # Durante la incubación el led indicativo queda encendido (valor 1) y las luces led apagadas(valor 1)
            self.led.value(1)       
            self.luces_led.value(1)
            
            # Simulamos 10 segundos de incubación de forma no bloqueante
            # (El while True principal sigue corriendo libremente mientras se cumple este tiempo)
            if time.ticks_diff(tiempo_actual, self.inicio_incubacion) >= 10000:  #EDITAR EL TIEMPO DE INCUBACION
                self.etapa = "fructificacion"
                self.ultimo_cambio = tiempo_actual # Sincroniza el reloj para el parpadeo
                print("--- PASANDO A ETAPA DE FRUCTIFICACIÓN ---")
        
        # === ETAPA 2: FRUCTIFICACIÓN ===
        elif self.etapa == "fructificacion":
            self.led.value(0)
            # Control de parpadeo cada 5 segundos
            if time.ticks_diff(tiempo_actual, self.ultimo_cambio) >= 5000: #EDITAR EL TIEMPO DE FRUCTIFICACION
                self.estado_luces_leds = not self.estado_luces_leds
                
                if self.estado_luces_leds:
                    self.luces_led.value(0)
                    print("LED encendido (Fructificación)")
                else:
                    self.luces_led.value(1)
                    print("LED apagado (Fructificación)")
                    
                self.ultimo_cambio = tiempo_actual
    
    def obtener_etapa(self):
        if self.etapa == "incubacion":
            return "INCUBACION"
        else:
            return "FRUCTIFICACION"



    

