#!/usr/bin/env python3
'''
 MIT License

 Copyright (c) 2020 anicca048

 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:
 
 The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.
 
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 SOFTWARE.
'''
'''
 Keybinds
 ============================================
 F4: Select screen region.
 F8: Perform OCR and write text to screen.
 F9: Kill program.
'''

# Make sure the right version of python is being used.
try:
    import sys
    assert sys.version_info >= (3, 0, 0), "python version error"
except AssertionError:
    print("error: python3 is required to run this program!")
    exit(1)

import argparse

try:
    from PIL import Image
except ImportError:
    import Image

import pyautogui
import pytesseract
from pynput.keyboard import Controller, Listener, Key
import cv2
import numpy

from time import sleep
from random import randint

# Mouse callback function to draw rectangle.
def draw_rectangle(event, x, y, flags, param):
    global draw_start, draw_redraw, draw_finish, ix, iy, fx, fy
    
    # Start to draw rectangle.
    if event == cv2.EVENT_LBUTTONDOWN:
        draw_start = True
        ix, iy = x, y
    # Update rectangle based on movements.
    elif event == cv2.EVENT_MOUSEMOVE:
        if draw_start == True:
            fx, fy = x, y
            draw_redraw = True
    # Finish drawing rectangle.
    elif event == cv2.EVENT_LBUTTONUP:
        draw_start = False
        fx, fy = x, y
        draw_finish = True

# Allows the user to select bounds of the screen.
def user_select_screen_region():
    global selected_region, draw_start, draw_redraw, draw_finish, ix, iy, fx, fy
    
    # Vars for drawing rectangle.
    draw_start = False
    draw_redraw = False
    draw_finish = False
    
    ix, iy, fx, fy = -1, -1, -1, -1
    
    # Color vars (BGR).
    rect_color = (255, 255, 0)
    
    # Create screen image for window background.
    scrn_img = cv2.cvtColor(numpy.array(pyautogui.screenshot()),
                            cv2.COLOR_RGB2BGR)
    # Create copy of image wich will be used for overlay modification.
    ovrly_img = scrn_img
    
    # Create window.
    cv2.namedWindow("select_region", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("select_region", cv2.WND_PROP_FULLSCREEN,
                          cv2.WINDOW_FULLSCREEN)
    cv2.setMouseCallback("select_region", draw_rectangle)
    
    # Rectangle drawing loop.
    while(1):
        cv2.imshow("select_region", ovrly_img)
        cv2.waitKey(1)
        
        if draw_start and draw_redraw:
            ovrly_img = scrn_img
            cv2.rectangle(ovrly_img, (ix, iy), (fx, fy), rect_color, -1)
            draw_redraw = False
        elif draw_finish:
            ovrly_img = scrn_img
            cv2.rectangle(ovrly_img, (ix, iy), (fx, fy), rect_color, -1)
            draw_finish = False
            break
    
    # Window cleanup.
    cv2.destroyAllWindows()
    
    # Return position info as tuple.
    selected_region = (ix, iy, fx, fy)

# Removes unwanted characters from string.
def get_valid_chars(text):
    global alpha_supported, numeric_supported, whitespace_supported, symbols_supported
    
    # String to hold numeric chars.
    valid_str = ""
    
    # Add any numeric chars to string.
    for ch in text:
        if alpha_supported and ch.isalpha():
            valid_str += ch
        elif numeric_supported and ch.isdigit():
            valid_str += ch
        elif whitespace_supported and ch.isspace():
            valid_str += ch
        elif symbols_supported and (ord(ch) > 32 and ord(ch) < 48):
            valid_str += ch
    
    # Return numeric values.
    return valid_str

# Get region of the screen as image.
def get_screen_region_image():
    global selected_region
    
    # Get screenshot.
    screen_image = pyautogui.screenshot()
    
    # Crop screenshot to selected region.
    region_image = screen_image.crop(box=selected_region)
    
    return region_image

# Takes screenshot, converts specific region to text with OCR, and types it.
def get_image_text(image):    
    # Convert screenshot to string with OCR.
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'
    image_text = pytesseract.image_to_string(image)
    
    # Return OCR data.
    return image_text

# Key released hook.
def on_key_release(key_released):
    global anti_detection
    
    # Bind F8 to the screen read write functionality.
    if key_released == Key.f8:
        # Get targeted screen text (numbers only).
        screen_text = get_image_text(get_screen_region_image())
        filtered_text = get_valid_chars(screen_text)
        
        # Create keyboard writer.
        key_writer = Controller()
        
        # Write text to screen.
        if anti_detection:
            for c in filtered_text:
                key_writer.press(c)
                
                # Anti detection wait time between key press and release.
                reset_time = (float(randint(53, 67)) / 1000.0)
                sleep(reset_time)
                
                key_writer.release(c)
                
                # Anti detection wait time between key strokes.
                delay_time = (float(randint(53, 79)) / 1000.0)
                sleep(delay_time)
        else:
            key_writer.type(filtered_text)
    
    # Bind F4 to redraw screen region.
    elif key_released == Key.f4:
        user_select_screen_region()
    # Bind F9 to exit() to kill thread.
    elif key_released == Key.f9:
        exit(0)

# Entry point funciton.
def main(value_type, whitespace, symbols, fast_typing):
    global numeric_supported, alpha_supported, whitespace_supported, symbols_supported, anti_detection
    
    # Set allowed main characters for OCR result.
    if value_type == "alpha":
        alpha_supported = True
        numeric_supported = False
    elif value_type == "alphanumeric":
        alpha_supported, numeric_supported = True, True
    else:
        alpha_supported = False
        numeric_supported = True
    
    # Disable anti bot detection timing if requested.
    if fast_typing:
        anti_detection = False
    else:
        anti_detection = True
    
    # Set allowed additional characters for OCR result.
    whitespace_supported = whitespace
    symbols_supported = symbols
    
    # Get region of screen to use.
    user_select_screen_region()
    
    # Create key sniffer thread and join it.
    key_sniffer = Listener(on_release = on_key_release)
    key_sniffer.start()
    key_sniffer.join()

# Entry point guard.
if __name__ == "__main__":
    # Setup parser for command line arguments.
    parser = argparse.ArgumentParser(prog="pyrintscreen.py",
                       description="Tool to print chars from screen to screen.")
    
    # Add arguments to parser.
    parser.add_argument("-v", "--value_type",
                        help="supported types for OCR result <alpha || numeric "
                             + "|| alphanumeric> (numeric is default)")
    parser.add_argument("-w", "--whitespace", action="store_true",
                        help="allow whitespace in OCR result (off by default)")
    parser.add_argument("-s", "--symbols", action="store_true",
                        help="allow non alphanumeric symbols in OCR result "
                             + "(off by default)")
    parser.add_argument("-f", "--fast_typing", action="store_true",
                        help="type chars as fast as possible"
                             + "(by default anti bot detection timing is on)")
    
    # Fetch arguments from sys.argv[].
    args = parser.parse_args()
    
    # Check for valid arguments, and run program.
    if args.value_type and (args.value_type != "alpha"
                            and args.value_type != "numeric"
                            and args.value_type != "alphanumeric"):
        parser.print_help(sys.stderr)
        exit(1)
    else:
        main(value_type = (args.value_type if args.value_type else "numeric"),
             whitespace = (args.whitespace if args.whitespace else False),
             symbols = (args.symbols if args.symbols else False),
             fast_typing = (args.fast_typing if args.fast_typing else False))