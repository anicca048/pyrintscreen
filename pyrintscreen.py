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

import sys

# Make sure the right version of python is being used.
try:
    assert sys.version_info >= (3, 0, 0), "python version error"
except AssertionError:
    print("error: python3 is required to run this program!")
    exit(1)

import argparse
from PIL import Image
import pyautogui
import pytesseract
from pynput.keyboard import Controller, Listener, Key
import cv2
import numpy
from queue import Queue
from time import sleep
from random import randint

WIN32_TESSERACT_V4_PATH = r'C:\Program Files\Tesseract-OCR\tesseract'

# Removes unwanted characters from string.
def get_valid_chars(text, alpha, numeric, whitespace, symbols):
    # String to hold valid chars.
    valid_str = ""
    
    # Add any valid chars to string.
    for ch in text:
        if alpha and ch.isalpha():
            valid_str += ch
        elif numeric and ch.isdigit():
            valid_str += ch
        elif whitespace and ch.isspace():
            valid_str += ch
        elif symbols and (ord(ch) > 32 and ord(ch) < 48):
            valid_str += ch
    
    # Return allowed values in OCR string.
    return valid_str

# Takes screenshot, converts specific region to text with OCR, and types it.
def get_image_text(image):
    # Convert screenshot to string with OCR.
    image_text = pytesseract.image_to_string(image)
    
    # Return OCR data.
    return image_text

# Get region of the screen as image.
def get_screen_region_image(selected_region):
    # Test for invalid setting on tuple.
    if selected_region == (0, 0, 0, 0):
        raise SystemError("invalid selected screen bounds for OCR")
    
    # Get screenshot.
    screen_image = pyautogui.screenshot()
    
    # Crop screenshot to selected region.
    region_image = screen_image.crop(box=selected_region)
    
    return region_image

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
    global draw_start, draw_redraw, draw_finish, ix, iy, fx, fy
    
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
    
    # Very basic invalid selection test.
    if (ix < 1) or (iy < 1) or (fx < 1) or (fy < 1):
        return (0, 0, 0, 0)
    elif (ix == fx) and (iy == fy):
        return (0, 0, 0, 0)
    
    return (ix, iy, fx, fy)

# Key released handler.
def on_key_release(key):
    global key_queue, bind_list
    
    # Check if key is in bind list and add it to the queue.
    if key in bind_list:
        key_queue.put(key)

# Entry point funciton, and keybind handler.
def main(alpha, numeric, whitespace, symbols, fast_typing):
    global key_queue, bind_list
    
    # Setup keybind defs and def list.
    bind_sel_scr_region = Key.f4
    bind_ocr_to_scr = Key.f8
    bind_exit_prog = Key.f9
    
    bind_list = {bind_sel_scr_region, bind_ocr_to_scr, bind_exit_prog}
    
    # Disable anti bot detection timing if requested.
    if fast_typing:
        anti_detection = False
    else:
        anti_detection = True
    
    # Init allowed chars for OCR (alpha, numeric, whitespace, symbols).
    allowed_chars = (alpha, numeric, whitespace, symbols)
    
    # Set tesseract binary location incase it's not in path (if on Windows OS).
    if sys.platform == "win32":
        pytesseract.pytesseract.tesseract_cmd = WIN32_TESSERACT_V4_PATH
    
    print("\nStarting initial screen region selection.")
    
    # Get region of screen to use.
    selected_region = user_select_screen_region()
    
    print("Starting keybind listner.")
    
    # Create key queue for key bind processing.
    key_queue = Queue()
    
    # Create key listner thread and join it (ignore multithreading).
    key_listner = Listener(on_release = on_key_release)
    key_listner.start()
    
    # Create keyboard writer for OCR data.
    key_writer = Controller()
    
    print("Listening for keybinds.\n")
    
    # Main event loop.
    while True:
        # Get key from queue.
        key = key_queue.get()
        
        # Handle screen region reselect.
        if key == bind_sel_scr_region:
            print("\tRunning: screen region selection.")
            selected_region = user_select_screen_region()
        # Handle OCR to screen.
        elif key == bind_ocr_to_scr:
            print("\tRunning: OCR to screen.")
            
            # Get targeted screen text (numbers only).
            screen_text = ""
            
            try:
                screen_text = get_image_text(get_screen_region_image(selected_region))
            except SystemError:
                print("Error: selected screen region is invalid!\n"
                    + "Please reselect the screen region.", file=sys.stderr)
            
            # Remove unwanted chars from OCR output.
            filtered_text = get_valid_chars(screen_text, allowed_chars[0],
                                            allowed_chars[1], allowed_chars[2],
                                            allowed_chars[3])
            
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
        # Handle script exit.
        elif key == bind_exit_prog:
            print("\nExiting.")
            break
    
    # Thread cleanup.
    key_listner.stop()
    key_listner.join()

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
    
    # Set default allowed OCR value type.
    if not args.value_type:
        args.value_type = "numeric"
    
    # Check for valid arguments, and run program.
    if not args.value_type in {"alpha", "numeric", "alphanumeric"}:
        parser.print_help(sys.stderr)
        exit(1)
    else:
        main(alpha = (True if args.value_type != "numeric" else False),
             numeric = (True if args.value_type != "alpha" else False),
             whitespace = (True if args.whitespace else False),
             symbols = (True if args.symbols else False),
             fast_typing = (True if args.fast_typing else False))
