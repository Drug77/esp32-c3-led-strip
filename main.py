import binascii, micropython
import led_patterns
import uasyncio as asyncio
from ble_uart import BLEUART
from machine import Pin
from settings import SETTINGS_FILE, DEFAULT_SETTINGS, load_settings, save_settings, hash_settings
from threadsafe_queue import ThreadSafeQueue

BLE_NAME = "ESP32-C3 Neopixels"
LED_INDICATOR_PIN = 3

# Mode constants
MODE_ON = "on"
MODE_OFF = "off"
MODE_COLOR = "color"
MODE_RAINBOW = "rainbow"
MODE_RAINBOW_CYCLE = "rainbow_cycle"
MODE_RAINBOW_SOLID = "rainbow_solid"
MODE_THEATRE_CHASE = "theatre_chase"
MODE_FADE_IN_OUT = "fade_in_out"
MODE_COLOR_WIPE = "color_wipe"
MODE_BREATHE = "breathe"
MODE_SPARKLE = "sparkle"
MODE_FIRE = "fire"
MODE_METEOR_RAIN = "meteor_rain"

# Tuple of all modes
MODES = (
    MODE_ON,
    MODE_OFF,
    MODE_COLOR,
    MODE_RAINBOW,
    MODE_RAINBOW_CYCLE,
    MODE_RAINBOW_SOLID,
    MODE_THEATRE_CHASE,
    MODE_FADE_IN_OUT,
    MODE_COLOR_WIPE,
    MODE_BREATHE,
    MODE_SPARKLE,
    MODE_FIRE,
    MODE_METEOR_RAIN,
)

EFFECTS = (
    MODE_RAINBOW,
    MODE_RAINBOW_CYCLE,
    MODE_RAINBOW_SOLID,
    MODE_THEATRE_CHASE,
    MODE_FADE_IN_OUT,
    MODE_COLOR_WIPE,
    MODE_BREATHE,
    MODE_SPARKLE,
    MODE_FIRE,
    MODE_METEOR_RAIN,
)

COLOR_REQUIRED = (
    MODE_THEATRE_CHASE,
    MODE_FADE_IN_OUT,
    MODE_COLOR_WIPE,
    MODE_BREATHE,
    MODE_SPARKLE,
    MODE_METEOR_RAIN,
)

COMMAND_RESET = "reset"
COMMAND_SAVE = "save"
COMMAND_MODE = "mode"
COMMAND_INFO = "info"

COMMANDS = (
    COMMAND_RESET,
    COMMAND_SAVE,
    COMMAND_MODE,
    COMMAND_INFO
)

class BleLedController:
    def __init__(self):
        self.led = Pin(LED_INDICATOR_PIN, Pin.OUT)
        self.led.off()
        self.settings = load_settings()
        self.settings_hash = hash_settings(self.settings)
        self.ble_message_queue = ThreadSafeQueue(3)
        self.ble = BLEUART(name=BLE_NAME, queue=self.ble_message_queue, led=self.led)
        self.last_ble_command = None
        self.is_change = False
    
    def notify(self, msg):
        self.ble.write(msg)
    
    def parse_command(self, cmd):
        cmd = cmd.lower()
        
        if cmd in COMMANDS:
            old_mode = self.settings["mode"]
            is_change = old_mode != cmd
            self.settings["mode"] = cmd 
            self.settings["old-mode"] = old_mode
            return is_change
            
        if cmd in MODES:
            is_change = self.settings["mode"] != cmd
            self.settings["mode"] = cmd
            return is_change

        if cmd in led_patterns.COLORS:
            is_change = self.settings["mode"] != cmd
            self.settings["mode"] = MODE_COLOR
            self.settings["color"] = cmd
            return is_change
        
        # Check if cmd is a brightness value (0% to 100%)
        if cmd.endswith("%"):
            try:
                val = int(cmd[:-1].strip())  # Remove '%' and convert to integer
                if 0 <= val <= 100:
                    self.settings["brightness"] = val
                    self.notify(f"Brightness set to {val}%")
                    return True
                else:
                    self.notify("Brightness value must be between 0% and 100%.")
                    return False
            except ValueError:
                self.notify("Invalid brightness value.")
                return False
            
        # Check if cmd is a speed value (20 to 1000)
        try:
            val = int(cmd.strip())  # Convert to integer directly
            if 20 <= val <= 1000:
                self.settings["speed"] = val
                self.notify(f"Speed set to {val}")
                return True
            else:
                self.notify("Speed value must be between 20 and 1000.")
                return False
        except ValueError:
            pass

        self.notify("Unknown command.")
        return False
    
    def is_settings_change(self):
        current_settings_hash = hash_settings(self.settings)
        return current_settings_hash != self.settings_hash

    def send_current_settings(self):
        mode = self.settings.get("mode")
        color = self.settings.get("color")
        brightness = self.settings.get("brightness")
        speed = self.settings.get("speed")

        msg = """
Mode: {}
Color: {}
Brightness: {}
Speed: {}
""".format(
            mode, color, brightness, speed
        ).strip()
        self.notify(msg)

    def send_info(self):
        default_settings_hash = binascii.hexlify(hash_settings(DEFAULT_SETTINGS))

        current_settings = self.settings
        current_settings_hash = binascii.hexlify(hash_settings(current_settings))

        saved_settings = load_settings()
        saved_settings_hash = binascii.hexlify(hash_settings(current_settings))

        info = {
            "Bluetooth name": BLE_NAME,
            "Number of LEDs": led_patterns.NUM_LEDS,
            "Indicator LED pin": LED_INDICATOR_PIN,
            "Neopixel LEDs pin": led_patterns.NEOPIXEL_LEDS_PIN,
            "Settings file": SETTINGS_FILE,
            "Default settings": DEFAULT_SETTINGS,
            "Default settings hash": default_settings_hash,
            "Current settings": current_settings,
            "Current settings hash": current_settings_hash,
            "Saved settings": saved_settings,
            "Saved settings hash": saved_settings_hash,
            "Need to save new settings?": "Yes" if self.is_settings_change() else "No",
            "Last recieved BLE command": self.last_ble_command,
            "Last BLE command changed current settings?": "Yes" if self.is_change else "No"
        }

        for k, v in info.items():
            k = k if k.endswith("?") else k + ":"
            self.notify("{} {}".format(k, v))
            
    def restore_old_mode_or(self, mode):
        # Restore the previous mode if "old-mode" exists
        if "old-mode" in self.settings:
            old_mode = self.settings["old-mode"]
            self.settings["mode"] = old_mode
            del self.settings["old-mode"]  # Remove "old-mode" from settings
            self.notify(f"Mode restored to {old_mode}.")
            return old_mode
        else:
            return mode
    
    async def neopixels(self):
        mode = self.settings.get("mode")
        color = self.settings.get("color")
        color_rgb = led_patterns.COLORS.get(color)
        brightness = self.settings.get("brightness")
        speed = self.settings.get("speed")
        
        led_patterns.leds_off()
        
        if mode == COMMAND_SAVE:
            mode = self.restore_old_mode_or(mode)
            save_settings(self.settings)
            self.notify("Settings saved.")

        elif mode == COMMAND_RESET:
            self.settings = DEFAULT_SETTINGS.copy()
            self.settings_hash = hash_settings(self.settings)
            self.notify("Reset to default settings.")
            
        elif mode == COMMAND_MODE:
            mode = self.restore_old_mode_or(mode)
            self.send_current_settings()
        
        elif mode == COMMAND_INFO:
            mode = self.restore_old_mode_or(mode)
            self.send_info()
        
        if mode == MODE_OFF:
            led_patterns.leds_off()
        
        elif mode == MODE_ON:
            led_patterns.color_fill(led_patterns.COLORS["white"], brightness)

        elif mode == MODE_COLOR and color in led_patterns.COLORS.keys():
            color = color_rgb
            led_patterns.color_fill(color, brightness)
            
        elif mode in EFFECTS:
            # Check if color is required and use default if not specified
            color = color_rgb if mode in COLOR_REQUIRED else None
            # Retrieve the function dynamically from led_patterns and call with required params
            effect_func = getattr(led_patterns, mode)
            
            # Call effect with brightness and color if required
            if color:
                await effect_func(color=color, brightness=brightness, speed=speed)
            else:
                await effect_func(brightness=brightness, speed=speed)
        
        else:
            self.notify("Unknown mode or settings error.")

        await asyncio.sleep(0)
    
    async def run(self):
        neopixel_task = None
        
        while True:
            if not self.ble_message_queue.empty():
                # Await and process messages from the queue
                msg = await self.ble_message_queue.get()
                self.last_ble_command = msg

                is_change = self.parse_command(msg)
                self.is_change = is_change
            
                # Blink led 3 times if settings have changed
                for _ in range(3 if self.is_change else 2):
                    self.led.off()
                    await asyncio.sleep(0.3)
                    self.led.on()
                    await asyncio.sleep(0.3)

                if is_change:
                    self.send_current_settings()
                    
                if neopixel_task is not None:
                    neopixel_task.cancel()
                    await asyncio.sleep(0)

                neopixel_task = asyncio.create_task(self.neopixels())
                
            if neopixel_task is None:
                neopixel_task = asyncio.create_task(self.neopixels())
                
            await asyncio.sleep(0)

if __name__ == "__main__":
    micropython.alloc_emergency_exception_buf(100)
    
    ble_led_controller = BleLedController()
    asyncio.run(ble_led_controller.run())
