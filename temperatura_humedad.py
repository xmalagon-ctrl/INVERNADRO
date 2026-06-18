from machine import Pin
import time


class ClimaControl:

    # Rangos ideales por etapa de cultivo (Pleurotus / orellana)
    FASES = {
        "inoculacion":    {"t_min": 20.0, "t_max": 26.0, "h_min": 80.0, "h_max": 85.0},
        "incubacion":     {"t_min": 24.0, "t_max": 26.0, "h_min": 80.0, "h_max": 85.0},
        "fructificacion": {"t_min": 15.5, "t_max": 18.5, "h_min": 87.0, "h_max": 93.0},
    }

    def __init__(self, i2c, pin_calefactor, pin_nebulizador, pin_ven_entrada, pin_ven_salida,
                 direccion_sensor=0x44, intervalo_lectura_ms=3000, fase_inicial="incubacion"):
        self.i2c = i2c
        self.direccion_sensor = direccion_sensor

        # RELÉS Y VENTILADORES
        self.rele_calefactor = Pin(pin_calefactor, Pin.OUT)
        self.rele_nebulizador = Pin(pin_nebulizador, Pin.OUT)
        self.ven_entrada = Pin(pin_ven_entrada, Pin.OUT)
        self.ven_salida = Pin(pin_ven_salida, Pin.OUT)

        # ESTADO INICIAL (misma lógica inversa que el código original)
        # Nebulizador (NO): 1 = reposo / apagado
        self.rele_nebulizador.value(1)
        # Calefactor (NC): 0 = clic, abre el circuito -> arranca apagado
        self.rele_calefactor.value(0)
        self.ven_entrada.value(0)
        self.ven_salida.value(0)

        self.fase_actual = fase_inicial
        self.intervalo_lectura_ms = intervalo_lectura_ms
        self.ultima_lectura = time.ticks_ms()

        self.temperatura = None
        self.humedad = None
        self.estado_temperatura = "Sin datos"
        self.estado_humedad = "Sin datos"

    def cambiar_fase(self, fase):

        if fase in self.FASES:
            self.fase_actual = fase
        else:
            print(f"[CLIMA] Fase desconocida: {fase}")

    def _leer_sht3x(self):
        try:
            self.i2c.writeto(self.direccion_sensor, b'\x24\x00')
            time.sleep(0.1)  # tiempo de medición del sensor
            data = self.i2c.readfrom(self.direccion_sensor, 6)
            temp_raw = (data[0] << 8) | data[1]
            t = -45 + (175 * temp_raw / 65535)
            hum_raw = (data[3] << 8) | data[4]
            h = 100 * hum_raw / 65535
            return t, h
        except Exception as e:
            print(f"[CLIMA] Error leyendo SHT3x: {e}")
            return None, None

    def _controlar_temperatura(self, t, limites):
        if t < limites["t_min"]:
            # Calentando: dejamos el NC en reposo (pasa corriente)
            self.rele_calefactor.value(1)
            self.ven_entrada.value(1)
            self.ven_salida.value(0)
            return "Calentando"
        elif t > limites["t_max"]:
            # Enfriando: activamos el NC (corta corriente al calefactor)
            self.rele_calefactor.value(0)
            self.ven_entrada.value(1)
            self.ven_salida.value(1)
            return "Enfriando"
        else:
            self.rele_calefactor.value(0)
            self.ven_entrada.value(0)
            self.ven_salida.value(0)
            return "Rango Ideal"

    def _controlar_humedad(self, h, limites):
        if h < limites["h_min"]:
            self.rele_nebulizador.value(0)  # Activa el NO (clic)
            return "Nebulizando"
        elif h > limites["h_max"]:
            self.rele_nebulizador.value(1)  # Reposo
            return "Humedad Alta"
        else:
            self.rele_nebulizador.value(1)  # Reposo
            return "Rango Ideal"

    def actualizar(self):

        tiempo_actual = time.ticks_ms()
        if time.ticks_diff(tiempo_actual, self.ultima_lectura) < self.intervalo_lectura_ms:
            return None, None

        self.ultima_lectura = tiempo_actual
        t, h = self._leer_sht3x()

        if t is not None and h is not None:
            limites = self.FASES[self.fase_actual]
            self.estado_temperatura = self._controlar_temperatura(t, limites)
            self.estado_humedad = self._controlar_humedad(h, limites)
            self.temperatura = t
            self.humedad = h
            print(f"[CLIMA] T: {t:.1f}C [{self.estado_temperatura}] | H: {h:.1f}% [{self.estado_humedad}]")

        return self.temperatura, self.humedad

    def obtener_texto_pantalla(self):

        if self.temperatura is None or self.humedad is None:
            return "T/H: leyendo..."
        return f"T:{self.temperatura:.1f}C H:{self.humedad:.0f}%"
