from kmk.keys import KC

KEYMAPS = [
    (
        KC.MEDIA_PREV_TRACK, KC.MEDIA_PLAY_PAUSE, KC.MEDIA_NEXT_TRACK,
        KC.BRIGHTNESS_UP,    KC.NO,               KC.BRIGHTNESS_DOWN,
        KC.RCTRL(KC.M),      KC.RCTRL(KC.D),      KC.LCTRL(KC.LALT(KC.SLASH)),
    ),
]

def apply_keymap_to_keyboard(keyboard):
    keyboard.keymap = KEYMAPS
