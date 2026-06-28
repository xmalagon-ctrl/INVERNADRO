from machine import ADC, Pin
import time
import math

class SensorCO2:
    def __init__(self, pin_sensor, pin_vent1=None, pin_vent2=None, umbral_inicial=25.0):
        # Hardware
        self.sensor = ADC(Pin(pin_sensor))
        self.sensor.atten(ADC.ATTN_11DB)
        self.sensor.width(ADC.WIDTH_12BIT)
        
        self.vent1 = pin_vent1
        self.vent2 = pin_vent2
        self.vent1.value(1)  # Apagado (HIGH = OFF)
        self.vent2.value(1)
        
        # Calibración
        self.Ro = 3.55   
        self.RL = 10.0   
        
        # Umbral dinámico único
        self.umbral_ventilacion = umbral_inicial
        
        # Control de tiempos
        self.ventilador_on = False
        self.ultimo_muestreo = time.ticks_ms()
        self.estado_actual = "Estabilizando"
        self.inicio_calentamiento = time.ticks_ms()

    def cambiar_umbral(self, nuevo_umbral):
        """Permite modificar el umbral dinámicamente desde el main según la etapa."""
        self.umbral_ventilacion = nuevo_umbral

    def _leer_voltaje(self):
        total = sum(self.sensor.read() for _ in range(10))
        return (total / 10) * (3.3 / 4095.0)

    def _calcular_ppm(self, voltaje):
        if voltaje <= 0.01:
            return 0.0
        Rs = ((3.3 - voltaje) / voltaje) * self.RL
        ratio = Rs / self.Ro
        ppm = 116.6020682 * math.pow(ratio, -2.769034857)
        return round(ppm, 1)

    def actualizar(self):
        tiempo_actual = time.ticks_ms()

        # Calentamiento inicial
        if self.estado_actual == "Estabilizando":
            if time.ticks_diff(tiempo_actual, self.inicio_calentamiento) >= 10000: #MODIFICAR TIEMPO DEPENDIENDO DE CALIBRACION
                self.estado_actual = "C02 ESTABLE"
                print("-> [CO2] Calentamiento finalizado. Monitoreo activo.")
            return None

        # Monitoreo activo cada 2 segundos
        if time.ticks_diff(tiempo_actual, self.ultimo_muestreo) >= 2000: #MODIFICAR TIEMPO DEPENDIENDO DE CALIBRACION
            voltaje = self._leer_voltaje()
            #print(f"-> [DEBUG] Voltaje real en Pin 35: {voltaje} V")#para saber si le esta entrando voltaje 
            ppm = self._calcular_ppm(voltaje)
            
            # Control de los relés
            if ppm >= self.umbral_ventilacion and not self.ventilador_on:
                self.vent1.value(0)  # LOW = relé ON
                self.vent2.value(0)
                self.ventilador_on = True
                self.estado_actual = "C02 ALTO"
                print(f">>> VENTILADOR ENCENDIDO (CO2: {ppm} ppm >= Umbral: {self.umbral_ventilacion}) <<<")
            elif ppm < self.umbral_ventilacion and self.ventilador_on:
                self.vent1.value(1)  # HIGH = relé OFF
                self.vent2.value(1)  
                self.ventilador_on = False
                self.estado_actual = "C02 ESTABLE"
                print(f">>> VENTILADOR APAGADO (CO2: {ppm} ppm < Umbral: {self.umbral_ventilacion}) <<<")
                
            self.ultimo_muestreo = tiempo_actual
            return ppm
            
        return None 
