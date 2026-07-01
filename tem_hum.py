from machine import Pin, I2C
import time

class Tem_Hum:
    def __init__(self, scl_clima=5, sda_clima=4, ven_entrada =None, ven_salida = None, rele_calefactor = None, rele_nebulizador = None, address=0x44 ):
        # Configuración I2C para el SHT3x
        self.i2c = I2C(0, scl=Pin(scl_clima), sda=Pin(sda_clima))
        self.sensor_addr = address
        
        # Relés y Ventiladores
        self.rele_calefactor = rele_calefactor
        self.rele_nebulizador = rele_nebulizador
        self.ven_entrada = ven_entrada
        self.ven_salida = ven_salida
        
        # Todo inicia apagado 
        self.rele_calefactor.value(1)
        self.rele_nebulizador.value(1)
        self.ven_entrada.value(1)
        self.ven_salida.value(1)
        
        # Rangos por defecto 
        self.t_min = 24.0
        self.t_max = 26.0
        self.h_min = 80.0
        self.h_max = 85.0
        
        # Variables de almacenamiento interno para no perder la lectura
        self.temperatura_actual = None
        self.humedad_actual = None
        
        # Control de tiempo asíncrono
        self.ultimo_muestreo = time.ticks_ms()
        self.estado_t = "Inicializando"
        self.estado_h = "Inicializando"
        self.inicio_calentamiento = time.ticks_ms()

    def cambiar_limites(self, t_min, t_max, h_min, h_max):
        """Permite al main actualizar los rangos óptimos según la etapa actual."""
        self.t_min = t_min
        self.t_max = t_max
        self.h_min = h_min
        self.h_max = h_max

    def _leer_sht3x(self):
        """Intenta realizar la lectura del protocolo I2C de forma segura."""
        try:
            self.i2c.writeto(self.sensor_addr, b'\x24\x00')
            # Volvemos a sleep estándar o aumentamos a 150ms para dar tiempo al hardware
            time.sleep(0.15) 
            data = self.i2c.readfrom(self.sensor_addr, 6)
            
            temp_raw = (data[0] << 8) | data[1]
            t = -45 + (175 * temp_raw / 65535)
            
            hum_raw = (data[3] << 8) | data[4]
            h = 100 * hum_raw / 65535
            return round(t, 1), round(h, 1)
        except Exception as e:
            # Imprimir el error real en consola ayuda muchísimo a saber qué falló
            print(f"Error en I2C SHT3x: {e}")
            return None, None

    def actualizar(self):
        """Ejecuta la lógica de control del clima cada 3 segundos y devuelve el estado actual."""
        tiempo_actual = time.ticks_ms()
        
        if self.estado_h == "Inicializando" and self.estado_t == "Inicializando":
            if time.ticks_diff(tiempo_actual, self.inicio_calentamiento) >= 10000: #MODIFICAR TIEMPO DEPENDIENDO DE CALIBRACION
                self.estado_h = "OK"
                self.estado_t = "OK"
            return self.temperatura_actual, self.humedad_actual, self.estado_t, self.estado_h
        
        # Monitoreo activo cada 2 segundos
        if time.ticks_diff(tiempo_actual, self.ultimo_muestreo) >= 2000:
            t, h = self._leer_sht3x()
            self.ultimo_muestreo = tiempo_actual
            
            if t is not None and h is not None:
                # Guardamos en la memoria interna de la clase
                self.temperatura_actual = t
                self.humedad_actual = h

                # --- Lógica de Control de Temperatura ---
                if t < self.t_min:
                    self.rele_calefactor.value(0) # ENCENDIDO
                    self.ven_entrada.value(0)
                    self.ven_salida.value(1)
                    self.estado_t = "CAL"
                elif t > self.t_max:
                    self.rele_calefactor.value(1) # APAGADO
                    self.ven_entrada.value(0)
                    self.ven_salida.value(0)
                    self.estado_t = "ENF"
                else:
                    self.rele_calefactor.value(1)
                    self.ven_entrada.value(1)
                    self.ven_salida.value(1)
                    self.estado_t = "OK"

                # --- Lógica de Control de Humedad ---
                if h < self.h_min:
                    self.rele_nebulizador.value(0) # ENCENDIDO
                    self.estado_h = "ACT"
                elif h > self.h_max:
                    self.rele_nebulizador.value(1) # APAGADO
                    self.ven_entrada.value(0)
                    self.ven_salida.value(0)
                    self.estado_h = "ALTA"
                else:
                    self.rele_nebulizador.value(1)
                    self.estado_h = "OK"
                    
                    
        return self.temperatura_actual, self.humedad_actual, self.estado_t, self.estado_h
                    
        
