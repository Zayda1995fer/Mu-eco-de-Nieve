
from machine import Pin, I2C, ADC, PWM
from servo import Servo
from time import sleep
from ssd1306 import SSD1306_I2C
from dht import DHT22
import math
from esp8266_i2c_lcd import I2cLcd

# Constantes
GAMMA_CORRECTION = 0.7
RESISTOR_LDR = 50  

# Pines para botones y LEDs
led_main = Pin(16, Pin.OUT)
led_aux1 = Pin(17, Pin.OUT)
led_aux2 = Pin(23, Pin.OUT)
btn_on = Pin(19, Pin.IN, Pin.PULL_UP)
btn_off = Pin(18, Pin.IN, Pin.PULL_UP)
btn_toggle = Pin(4, Pin.IN, Pin.PULL_UP)

# Configuración I2C para pantalla OLED y LCD
I2C_ADDRESS_LCD = 0x27 
LCD_ROWS = 4
LCD_COLS = 20
i2c_oled = I2C(0, scl=Pin(22), sda=Pin(21))
i2c_lcd = I2C(1, scl=Pin(33), sda=Pin(32), freq=400000)
lcd_display = I2cLcd(i2c_lcd, I2C_ADDRESS_LCD, LCD_ROWS, LCD_COLS)

sensor_dht22 = DHT22(Pin(27))  
oled_display = SSD1306_I2C(128, 64, i2c_oled)

# Pines LED RGB
rgb_led_red = Pin(12, Pin.OUT)
rgb_led_green = Pin(13, Pin.OUT)

# Pines Servo Motor
servo_motor = Servo(Pin(15))

# Estado de los LEDs
main_led_state = False
toggle_led_state = False

# Configuración del sensor de luz (LDR)
ldr_sensor = ADC(Pin(26))
ldr_sensor.atten(ADC.ATTN_11DB)
ldr_sensor.width(ADC.WIDTH_12BIT)
light_led = Pin(14, Pin.OUT)

# Funciones para controlar los LEDs
def toggle_led(pin):
    global toggle_led_state
    toggle_led_state = not toggle_led_state
    led_aux2.value(toggle_led_state)

def turn_on_leds(pin):
    global main_led_state
    main_led_state = True
    led_main.value(main_led_state)
    led_aux1.value(main_led_state)

def turn_off_leds(pin):
    global main_led_state
    main_led_state = False
    led_main.value(main_led_state)
    led_aux1.value(main_led_state)

# Asignación de interrupciones a los botones
btn_on.irq(trigger=Pin.IRQ_FALLING, handler=turn_on_leds)
btn_off.irq(trigger=Pin.IRQ_FALLING, handler=turn_off_leds)
btn_toggle.irq(trigger=Pin.IRQ_FALLING, handler=toggle_led)

# Función para el indicador de temperatura
def temperature_indicator(temp):
    if temp < 30:
        rgb_led_red.value(0)
        rgb_led_green.value(1)
    else:
        rgb_led_red.value(1)
        rgb_led_green.value(0)

# Calculo del nivel de luz en lux
def calculate_lux_value(analog_read):
    voltage = analog_read / 4095.0 * 3.3
    resistance = 2000 * voltage / (1 - voltage / 3.3)
    lux = math.pow(RESISTOR_LDR * 1e3 * math.pow(10, GAMMA_CORRECTION) / resistance, (1 / GAMMA_CORRECTION)) / 1.808
    return lux

# Bucle principal
while True:
    sensor_dht22.measure()
    temperature = sensor_dht22.temperature()
    humidity = sensor_dht22.humidity()
    
    # Actualizar pantalla OLED
    oled_display.fill(0)
    oled_display.text("T: %3.1f grados" % temperature, 10, 13)
    oled_display.text("H: %3.1f%% humedad" % humidity, 10, 40)
    
    # Actualizar pantalla LCD
    lcd_display.clear()
    lcd_display.putstr("T: %3.1f grados" % temperature)
    lcd_display.move_to(0, 1)
    lcd_display.putstr("H: %3.1f%% humedad" % humidity)

    # Mensaje de alerta de temperatura alta
    if temperature > 50:
        lcd_display.move_to(0, 2)
        lcd_display.putstr("TEMPERATURA ALTA")
        oled_display.text("TEMPERA ALTA", 10, 25)
    else:
        oled_display.text("", 10, 25)
    
    oled_display.show()

    # Control del indicador de temperatura
    temperature_indicator(temperature)

    # Control del servo motor
    if temperature > 30:
        servo_motor.move(90)
    else:
        servo_motor.move(0)

    # Leer nivel de luz del LDR
    analog_light_value = ldr_sensor.read()
    lux_level = calculate_lux_value(analog_light_value)
    print("Lux:", lux_level)

    # Control del LED de luz
    if lux_level < 1000:
        light_led.value(1)
    else:
        light_led.value(0)

    sleep(1)
