import machine
import time
from machine import Pin, I2C
from lcd_i2c import LCD

class Pantalla:
    
    def __init__(self, scl, sda):
        self.scl = scl
        self.sda = sda
        self.i2c = None
        self.direccion_lcd = None
        self.lcd = None
    
    def configuracion(self):
        self.i2c = I2C(0, scl=Pin(self.scl), sda=Pin(self.sda), freq=400000)
        print("Escaneando bus I2C...")
        direcciones = self.i2c.scan()
        if not direcciones:
            print("¡No se detectó ningún dispositivo I2C! Revisa cables.")
        else:
            self.direccion_lcd = direcciones[0]
            print(f"Dispositivo I2C encontrado en: {hex(self.direccion_lcd)}")
            
            try:
                # === INICIALIZACIÓN ===
                self.lcd = LCD(self.direccion_lcd, 20, 4, 0, self.i2c)
                self.lcd.begin()
                self.lcd.clear()
                print("¡Pantalla LCD inicializada con éxito!")
                self.lcd.backlight()
                
                # Mensaje inicial
                self.lcd.set_cursor(0, 1)
                self.lcd.print("Pantalla lista")
                
            except Exception as e:
                print(f"Error en la ejecución: {e}")
                
    def mostrarEnPantalla(self, columna0, mensaje0, columna1, mensaje1, columna2, mensaje2, columna3, mensaje3):
        if self.lcd is None:
            print("Error: la pantalla no está configurada. Llama primero a configuracion().")
            return
        
        self.lcd.clear()
        self.lcd.backlight()
        
        self.lcd.set_cursor(columna0, 0)
        self.lcd.print(mensaje0)
        
        self.lcd.set_cursor(columna1, 1)
        self.lcd.print(mensaje1)
        
        self.lcd.set_cursor(columna2, 2)
        self.lcd.print(mensaje2)
        
        self.lcd.set_cursor(columna3, 3)
        self.lcd.print(mensaje3)
