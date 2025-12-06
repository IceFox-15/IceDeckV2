"""
Advanced KMK Configuration for IceDeck V2
Includes proper matrix scanning, encoder handling, and display integration
"""

import board
import digitalio
import rotaryio
import busio
import time
from kmk.keys import KC
from kmk.keyboard import Keyboard
from kmk.extensions.media_keys import MediaKeys

# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================

# Matrix dimensions
MATRIX_ROWS = 3
MATRIX_COLS = 3

# Debounce time (in milliseconds)
DEBOUNCE_MS = 20

# Encoder configuration
ENCODER_ENABLED = True
DISPLAY_ENABLED = True

# ============================================================================
# GPIO PIN DEFINITIONS
# ============================================================================

# Row pins (set as inputs)
ROW_PINS = [board.GP26, board.GP27, board.GP28]

# Column pins (set as outputs)
COL_PINS = [board.GP1, board.GP2, board.GP4]

# I2C pins for display
I2C_SCL = board.GP7
I2C_SDA = board.GP6

# Rotary encoder pins
ENC_A_PIN = board.GP3
ENC_B_PIN = board.GP29
ENC_SW_PIN = board.GP0

# ============================================================================
# MATRIX SCANNER CLASS
# ============================================================================

class MatrixScanner:
    """Scans a keyboard matrix and detects key presses"""
    
    def __init__(self, row_pins, col_pins, debounce_ms=20):
        self.row_pins = row_pins
        self.col_pins = col_pins
        self.debounce_ms = debounce_ms
        self.num_rows = len(row_pins)
        self.num_cols = len(col_pins)
        
        # Initialize row pins as inputs
        self.rows = []
        for pin in row_pins:
            row = digitalio.DigitalInOut(pin)
            row.direction = digitalio.Direction.INPUT
            row.pull = digitalio.Pull.DOWN
            self.rows.append(row)
        
        # Initialize column pins as outputs
        self.cols = []
        for pin in col_pins:
            col = digitalio.DigitalInOut(pin)
            col.direction = digitalio.Direction.OUTPUT
            col.value = False
            self.cols.append(col)
        
        # Track key states
        self.key_states = [[False] * self.num_cols for _ in range(self.num_rows)]
        self.last_press_time = [[0] * self.num_cols for _ in range(self.num_rows)]
        
        print(f"[MATRIX] Initialized {self.num_rows}x{self.num_cols} matrix")
    
    def scan(self):
        """
        Scan the matrix and return list of pressed keys
        Returns: [(row, col), ...] list of currently pressed keys
        """
        pressed_keys = []
        current_time = time.monotonic() * 1000  # Convert to ms
        
        for col_idx, col_pin in enumerate(self.cols):
            # Set this column HIGH
            col_pin.value = True
            
            # Small delay for signal to settle
            time.sleep(0.0001)
            
            # Read all rows
            for row_idx, row_pin in enumerate(self.rows):
                is_pressed = row_pin.value
                
                # Debounce logic
                if is_pressed and not self.key_states[row_idx][col_idx]:
                    # Key just pressed
                    if current_time - self.last_press_time[row_idx][col_idx] > self.debounce_ms:
                        self.key_states[row_idx][col_idx] = True
                        self.last_press_time[row_idx][col_idx] = current_time
                        pressed_keys.append((row_idx, col_idx))
                
                elif not is_pressed and self.key_states[row_idx][col_idx]:
                    # Key just released
                    if current_time - self.last_press_time[row_idx][col_idx] > self.debounce_ms:
                        self.key_states[row_idx][col_idx] = False
            
            # Set this column LOW
            col_pin.value = False
        
        return pressed_keys

# ============================================================================
# ENCODER CLASS
# ============================================================================

class EncoderController:
    """Handles rotary encoder input"""
    
    def __init__(self, a_pin, b_pin, switch_pin):
        try:
            self.encoder = rotaryio.IncrementalEncoder(a_pin, b_pin)
            self.last_position = 0
            
            self.switch = digitalio.DigitalInOut(switch_pin)
            self.switch.direction = digitalio.Direction.INPUT
            self.switch.pull = digitalio.Pull.UP
            self.last_switch_state = True
            
            self.enabled = True
            print("[ENCODER] Successfully initialized")
        except Exception as e:
            print(f"[ENCODER] Initialization failed: {e}")
            self.enabled = False
    
    def update(self):
        """Update encoder state and return (rotation_direction, button_pressed)"""
        if not self.enabled:
            return (0, False)
        
        rotation = 0
        button_pressed = False
        
        try:
            # Check rotation
            current_position = self.encoder.position
            if current_position > self.last_position:
                rotation = 1  # Clockwise
                self.last_position = current_position
            elif current_position < self.last_position:
                rotation = -1  # Counter-clockwise
                self.last_position = current_position
            
            # Check button
            current_switch = self.switch.value
            if not current_switch and self.last_switch_state:
                button_pressed = True
                self.last_switch_state = current_switch
            elif current_switch and not self.last_switch_state:
                self.last_switch_state = current_switch
        
        except Exception as e:
            print(f"[ENCODER] Update error: {e}")
        
        return (rotation, button_pressed)

# ============================================================================
# DISPLAY CLASS
# ============================================================================

class DisplayController:
    """Handles SSD1306 display updates"""
    
    def __init__(self, scl_pin, sda_pin):
        try:
            self.i2c = busio.I2C(scl_pin, sda_pin)
            
            # Try to import and initialize display
            import adafruit_ssd1306
            self.display = adafruit_ssd1306.SSD1306_I2C(128, 32, self.i2c)
            self.enabled = True
            
            # Clear display
            self.display.fill(0)
            self.display.show()
            
            print("[DISPLAY] SSD1306 initialized successfully")
        
        except ImportError:
            print("[DISPLAY] adafruit_ssd1306 library not found")
            self.enabled = False
        except Exception as e:
            print(f"[DISPLAY] Initialization failed: {e}")
            self.enabled = False
    
    def show_startup(self):
        """Display startup message"""
        if not self.enabled:
            return
        
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            image = Image.new('1', (128, 32))
            draw = ImageDraw.Draw(image)
            
            draw.rectangle((0, 0, 127, 31), outline=0, fill=0)
            draw.text((20, 12), "IceDeck V2", fill=1)
            
            self.display.image(image)
            self.display.show()
        except Exception as e:
            print(f"[DISPLAY] Startup display failed: {e}")
    
    def show_time(self):
        """Display current time"""
        if not self.enabled:
            return
        
        try:
            from PIL import Image, ImageDraw, ImageFont
            import time as time_module
            
            image = Image.new('1', (128, 32))
            draw = ImageDraw.Draw(image)
            
            # Get current time
            current_time = time_module.localtime()
            time_str = f"{current_time.tm_hour:02d}:{current_time.tm_min:02d}:{current_time.tm_sec:02d}"
            
            # Try to use a larger font, fall back to default
            try:
                font = ImageFont.truetype("/lib/fonts/DejaVuSansMono.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            # Draw border
            draw.rectangle((0, 0, 127, 31), outline=1, fill=0)
            
            # Draw time centered
            draw.text((25, 8), time_str, font=font, fill=1)
            
            self.display.image(image)
            self.display.show()
        except Exception as e:
            print(f"[DISPLAY] Time display failed: {e}")
    
    def show_status(self, layer, encoder_val, last_key=None):
        """Display current status"""
        if not self.enabled:
            return
        
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            image = Image.new('1', (128, 32))
            draw = ImageDraw.Draw(image)
            
            # Draw border
            draw.rectangle((0, 0, 127, 31), outline=1, fill=0)
            
            # Draw info
            draw.text((2, 2), f"L:{layer} V:{encoder_val}", fill=1)
            if last_key:
                draw.text((2, 12), f"Key: {last_key}", fill=1)
            
            self.display.image(image)
            self.display.show()
        except Exception as e:
            print(f"[DISPLAY] Status update failed: {e}")

# ============================================================================
# KEYBOARD SETUP
# ============================================================================

# Create keyboard instance
keyboard = Keyboard()

# Add media keys extension
keyboard.extensions.append(MediaKeys())

# Define keymaps
keyboard.keymap = [
    # Layer 0 - Media Controls
    # Top row: Skip Back, Play/Pause, Skip Forward
    # Mid row: Brightness Down, Empty, Brightness Up
    # Bot row: Mute Discord, Deafen Discord, Quick Open Discord
    (
        KC.MEDIA_PREV_TRACK,    KC.MEDIA_PLAY_PAUSE,    KC.MEDIA_NEXT_TRACK,
        KC.BRIGHTNESS_DOWN,     KC.NO,                  KC.BRIGHTNESS_UP,
        KC.LCTRL(KC.LALT(KC.M)),  KC.LCTRL(KC.LALT(KC.D)),  KC.LCTRL(KC.LALT(KC.SLASH)),
    ),
]

# ============================================================================
# INITIALIZE COMPONENTS
# ============================================================================

# Initialize matrix scanner
matrix_scanner = MatrixScanner(ROW_PINS, COL_PINS, DEBOUNCE_MS)

# Initialize encoder
encoder = EncoderController(ENC_A_PIN, ENC_B_PIN, ENC_SW_PIN)

# Initialize display
display = DisplayController(I2C_SCL, I2C_SDA)

# Variables for display updates
current_layer = 0
current_encoder_value = 0
last_key_pressed = None
last_update_time = time.monotonic()

# ============================================================================
# MAIN KEYBOARD LOOP
# ============================================================================

def main():
    global current_layer, current_encoder_value, last_key_pressed, last_update_time
    
    print("\n" + "="*60)
    print("IceDeck V2 - KMK Firmware")
    print("="*60)
    print("Keyboard initialized. Waiting for input...\n")
    
    display.show_startup()
    time.sleep(1)
    
    # Main loop
    last_time_update = time.monotonic()
    
    while True:
        # Update time display every 1 second
        current_time_check = time.monotonic()
        if current_time_check - last_time_update >= 1.0:
            display.show_time()
            last_time_update = current_time_check
        
        # Scan matrix
        pressed_keys = matrix_scanner.scan()
        
        for row, col in pressed_keys:
            # Calculate key index in the flat keymap
            key_idx = row * MATRIX_COLS + col
            
            # Get key from current layer
            if current_layer < len(keyboard.keymap):
                key = keyboard.keymap[current_layer][key_idx]
                keyboard.write(key)
                
                last_key_pressed = f"{key}"
                print(f"[KEY] Row {row}, Col {col} -> {key}")
                
                # Update display briefly
                display.show_status(current_layer, current_encoder_value, last_key_pressed)
                # Return to time after 2 seconds
                last_time_update = current_time_check - 0.8
        
        # Handle encoder
        if ENCODER_ENABLED:
            rotation, button_pressed = encoder.update()
            
            if rotation > 0:
                # Clockwise - Volume Up
                keyboard.write(KC.AUDIO_VOL_UP)
                current_encoder_value += 1
                print(f"[ENCODER] Volume UP: {current_encoder_value}")
            
            elif rotation < 0:
                # Counter-clockwise - Volume Down
                keyboard.write(KC.AUDIO_VOL_DOWN)
                current_encoder_value -= 1
                print(f"[ENCODER] Volume DOWN: {current_encoder_value}")
            
            if button_pressed:
                # Mute the whole system
                keyboard.write(KC.AUDIO_MUTE)
                print(f"[ENCODER] Button pressed - System mute toggle")
                display.show_status(0, current_encoder_value, "MUTE")
                last_time_update = current_time_check - 0.8
        
        # Small delay to prevent CPU spinning
        time.sleep(0.001)

# ============================================================================
# RUN FIRMWARE
# ============================================================================

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Keyboard interrupted")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
