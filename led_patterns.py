import math
import random
from machine import Pin
from neopixel import NeoPixel
import uasyncio as asyncio

COLORS = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "pink": (255, 20, 147),
    "magenta": (255, 0, 255),
    "purple": (128, 0, 128),
    "blue": (0, 0, 255),
    "cyan": (0, 255, 255),
    "teal": (0, 128, 128),
    "green": (0, 255, 0),
    "yellow": (255, 255, 0),
    "orange": (255, 165, 0),
    "warm": (255, 223, 180)
}

NUM_LEDS = 180
NEOPIXEL_LEDS_PIN = 2
np = NeoPixel(Pin(NEOPIXEL_LEDS_PIN), NUM_LEDS)

def color_wheel(pos):
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)

async def rainbow(brightness=100, speed=20):
    """Displays a cycling rainbow effect across all LEDs."""
    brightness = max(0, min(brightness, 100)) / 100  # Normalize brightness to 0-1 scale
    
    for j in range(256):
        for i in range(NUM_LEDS):
            color = color_wheel((i + j) & 255)
            adjusted_color = tuple(int(c * brightness) for c in color)
            np[i] = adjusted_color
        np.write()
        await asyncio.sleep_ms(speed)
        
async def rainbow_cycle(brightness=100, speed=20):
    brightness = max(0, min(brightness, 100)) / 100  # Normalize brightness to 0-1 scale
    
    while True:
        for j in range(256):
            for i in range(NUM_LEDS):
                color = color_wheel((int(i * 256 / NUM_LEDS) + j) & 255)
                adjusted_color = tuple(int(c * brightness) for c in color)
                np[i] = adjusted_color
            np.write()
            await asyncio.sleep_ms(speed)
        
async def rainbow_solid(brightness=100, speed=20):
    brightness = max(0, min(brightness, 100)) / 100  # Normalize brightness to 0-1 scale
    
    while True:
        for j in range(256):
            color = color_wheel(j)  # Get the color for this step in the wheel
            adjusted_color = tuple(int(c * brightness) for c in color)
            np.fill(adjusted_color)  # Set all LEDs to the same color
            np.write()
            await asyncio.sleep_ms(speed)
        
async def theatre_chase(color, brightness=100, speed=100):
    brightness = max(0, min(brightness, 100)) / 100  # Normalize brightness to 0-1 scale
    adjusted_color = tuple(int(c * brightness) for c in color)  # Adjust color for brightness
    
    while True:
        # Theatre chase effect with the specified color
        for _ in range(10):  # Number of cycles for the chase effect
            for q in range(3):  # Three steps in the chase pattern
                for i in range(0, NUM_LEDS, 3):
                    np[i + q] = adjusted_color  # Set every third LED to the color
                np.write()
                await asyncio.sleep_ms(speed)
                for i in range(0, NUM_LEDS, 3):
                    np[i + q] = (0, 0, 0)  # Turn off every third LED after each cycle
                
async def fade_in_out(color, brightness=100, speed=20):
    brightness = max(0, min(brightness, 100)) / 100  # Normalize brightness to 0-1 scale

    while True:
        # Fade in
        for level in range(0, 101):  # From 0% to 100%
            adjusted_color = tuple(int(c * (level / 100) * brightness) for c in color)
            np.fill(adjusted_color)
            np.write()
            await asyncio.sleep_ms(speed)
        
        # Fade out
        for level in range(100, -1, -1):  # From 100% to 0%
            adjusted_color = tuple(int(c * (level / 100) * brightness) for c in color)
            np.fill(adjusted_color)
            np.write()
            await asyncio.sleep_ms(speed)
        
async def color_wipe(color, brightness=100, speed=50):
    brightness = max(0, min(brightness, 100)) / 100  # Normalize brightness to 0-1 scale
    adjusted_color = tuple(int(c * brightness) for c in color)  # Adjust color for brightness
    
    while True:
        # Wipe forward
        for i in range(NUM_LEDS):
            np[i] = adjusted_color
            np.write()
            await asyncio.sleep_ms(speed)
        
        # Clear LEDs
        for i in range(NUM_LEDS):
            np[i] = (0, 0, 0)
            np.write()
            await asyncio.sleep_ms(speed)

async def breathe(color, brightness=100, speed=20):
    max_brightness = max(0, min(brightness, 100)) / 100  # Normalize brightness to 0-1 scale

    while True:
        # Fade in
        for level in range(0, 101):  # 0% to 100%
            adjusted_brightness = (math.sin(level * math.pi / 100 - math.pi / 2) + 1) / 2 * max_brightness
            adjusted_color = tuple(int(c * adjusted_brightness) for c in color)
            np.fill(adjusted_color)
            np.write()
            await asyncio.sleep_ms(speed)

        # Fade out
        for level in range(100, -1, -1):  # 100% to 0%
            adjusted_brightness = (math.sin(level * math.pi / 100 - math.pi / 2) + 1) / 2 * max_brightness
            adjusted_color = tuple(int(c * adjusted_brightness) for c in color)
            np.fill(adjusted_color)
            np.write()
            await asyncio.sleep_ms(speed)


async def sparkle(color, brightness=100, speed=50, sparkle_count=15, fade_speed=50):
    brightness = max(0, min(brightness, 100)) / 100  # Normalize brightness to 0-1 scale
    adjusted_color = tuple(int(c * brightness) for c in color)  # Adjust color for brightness

    while True:
        # Turn off all LEDs initially
        np.fill((0, 0, 0))
        
        # Randomly select LEDs to sparkle
        sparkle_indices = set()
        while len(sparkle_indices) < sparkle_count:
            sparkle_indices.add(random.randint(0, NUM_LEDS - 1))
        
        for i in sparkle_indices:
            np[i] = adjusted_color  # Set selected LEDs to the sparkle color
        np.write()
        
        # Brief delay to show sparkles
        await asyncio.sleep_ms(speed)
        
        # Fade out sparkles by turning them off
        for i in sparkle_indices:
            np[i] = (0, 0, 0)
        np.write()
        
        # Delay to control sparkle refresh rate
        await asyncio.sleep_ms(fade_speed)
        
async def fire(brightness=100, cooldown=55, heat_increment=40, speed=30):
    brightness = max(0, min(brightness, 100)) / 100  # Normalize brightness to 0-1 scale
    heat = [0] * NUM_LEDS  # Initialize heat array for each LED

    while True:
        # Step 1: Cool down every cell a little
        for i in range(NUM_LEDS):
            cooldown_amount = random.randint(0, ((cooldown * 10) // NUM_LEDS) + 2)
            heat[i] = max(0, heat[i] - cooldown_amount)

        # Step 2: Heat drifts upward
        for i in range(NUM_LEDS - 1, 1, -1):
            heat[i] = (heat[i - 1] + heat[i - 2] + heat[i - 2]) // 3

        # Step 3: Ignite new sparks near the bottom
        if random.randint(0, 255) < heat_increment:
            spark_index = random.randint(0, 7)
            heat[spark_index] = min(255, heat[spark_index] + random.randint(160, 255))

        # Step 4: Map heat to color with brightness adjustment and display
        for i in range(NUM_LEDS):
            base_color = heat_to_color(heat[i])
            adjusted_color = tuple(int(c * brightness) for c in base_color)
            np[i] = adjusted_color
        np.write()

        # Control flame animation speed
        await asyncio.sleep_ms(speed)

def heat_to_color(heat):
    # Convert heat values to color (red-yellow-white gradient)
    if heat <= 85:
        return (heat * 3, 0, 0)  # Red tones
    elif heat <= 170:
        return (255, (heat - 85) * 3, 0)  # Yellow tones
    else:
        return (255, 255, (heat - 170) * 3)  # White tones
    
async def meteor_rain(color, brightness=100, meteor_size=15, trail_decay=0.7, speed=50):
    brightness = max(0, min(brightness, 100)) / 100  # Normalize brightness to 0-1 scale
    adjusted_color = tuple(int(c * brightness) for c in color)  # Adjust color for brightness

    while True:
        # Clear LEDs
        np.fill((0, 0, 0))

        # Move the meteor across the strip
        for start in range(NUM_LEDS + meteor_size):
            # Fade all LEDs slightly to create trailing effect
            for i in range(NUM_LEDS):
                np[i] = tuple(int(c * trail_decay) for c in np[i])
            
            # Set the LEDs for the meteor
            for j in range(meteor_size):
                if 0 <= start - j < NUM_LEDS:
                    np[start - j] = adjusted_color

            np.write()
            await asyncio.sleep_ms(speed)

def color_fill(color, brightness=100):
    adjusted_brightness = max(0, min(brightness, 100)) / 100  # Clamp brightness to 0-100 and normalize
    adjusted_color = tuple(int(c * adjusted_brightness) for c in color)
    np.fill(adjusted_color)
    np.write()

def leds_off():
    np.fill((0, 0, 0))
    np.write()
