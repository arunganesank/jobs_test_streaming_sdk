from time import sleep
import psutil
import os
from glob import glob
import zipfile
import subprocess
from subprocess import PIPE, STDOUT
import shlex
import sys
import traceback
from shutil import copyfile
from datetime import datetime
import pyautogui
import pyshark
import json
import multiprocessing
import platform
from threading import Thread
from PIL import Image
from grayArtifacts import check_artifacts
from streaming_actions import StreamingType
from elements import *

if platform.system() == "Windows":
    import win32api
    import win32gui
    import win32con
    import pydirectinput

ROOT_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir))
sys.path.append(ROOT_PATH)
from jobs_launcher.core.config import main_logger


GRAY_ARTIFACTS_LOCK = multiprocessing.Lock()


def close_game(game_name):
    if platform.system() == "Windows":
        edge_x = win32api.GetSystemMetrics(0)
        edge_y = win32api.GetSystemMetrics(1)
    else:
        process = subprocess.Popen("xdpyinfo | awk '/dimensions/{print $2}'", stdout=PIPE, shell=True)
        stdout, stderr = process.communicate()
        edge_x, edge_y = stdout.decode("utf-8").strip().split("x")
        edge_x = int(edge_x)
        edge_y = int(edge_y)

    center_x = edge_x / 2
    center_y = edge_y / 2

    if game_name == "lol":
        pydirectinput.keyDown("esc")
        sleep(0.1)
        pydirectinput.keyUp("esc")

        sleep(2)

        pyautogui.moveTo(center_x - 360, center_y + 335)
        sleep(0.2)
        pyautogui.mouseDown()
        sleep(0.2)
        pyautogui.mouseUp()
        sleep(0.2)
        pyautogui.mouseDown()
        sleep(0.2)
        pyautogui.mouseUp()

        sleep(1)

        pyautogui.moveTo(center_x - 130, center_y - 50)
        sleep(0.2)
        pyautogui.mouseDown()
        sleep(0.2)
        pyautogui.mouseUp()

        sleep(3)


def close_game_process(game_name):
    try:
        games_processes = {
            "heavendx9": ["browser_x86.exe", "Heaven.exe"],
            "heavendx11": ["browser_x86.exe", "Heaven.exe"],
            "heavenopengl": ["browser_x86.exe", "Heaven.exe"],
            "valleydx9": ["browser_x86.exe", "Valley.exe"],
            "valleydx11": ["browser_x86.exe", "Valley.exe"],
            "valleyopengl": ["browser_x86.exe", "Valley.exe"],
            "borderlands3": ["Borderlands3.exe"],
            "apexlegends": ["r5apex.exe"],
            "valorant": ["VALORANT-Win64-Shipping.exe"],
            "lol": ["LeagueClient.exe", "League of Legends.exe"],
            "csgo": ["csgo.exe"],
            "dota2dx11": ["dota2.exe"],
            "dota2vulkan": ["dota2.exe"],
        }

        if game_name in games_processes:
            processes_names = games_processes[game_name]

            for process in psutil.process_iter():
                if process.name() in processes_names:
                    process.kill()
                    main_logger.info("Target game process found. Close it")

    except Exception as e:
        main_logger.error("Failed to close game process. Exception: {}".format(str(e)))
        main_logger.error("Traceback: {}".format(traceback.format_exc()))


def make_window_minimized(window):
    try:
        win32gui.ShowWindow(window, 2)
    except Exception as e:
        main_logger.error("Failed to make window minized: {}".format(str(e)))
        main_logger.error("Traceback: {}".format(traceback.format_exc()))


def locate_on_screen(template, scale=False, tries=3, delay=0, **kwargs):
    coords = None
    if not "confidence" in kwargs:
        if scale:
            kwargs["confidence"] = 0.75
            # pyautogui locateOnScreen doesn't consider scale of elements
            # scale screenshots of elements with a small step to pick up the necessary scale
            # screenshots of elements made on 2k resolution (16:9). Screenshots are supported for up to 4k (16:10 and 16:9) resolution or down to full hd (16:10 and 16:9) resolution
            scale_up = win32api.GetSystemMetrics(0) >= 2560
        else:
            kwargs["confidence"] = 0.95

    while not coords and tries > 0 and kwargs["confidence"] > 0:
        with Image.open(os.path.abspath(os.path.join(os.path.dirname(__file__), template))) as img:
            if scale:
                scaling_try = 0
                # Examples
                # scale up 10 times -> 2560 * 150% = 3840;  (4k 16:9)
                # scale up 12 times -> 2560 * 160% = 4096 (4k 16:10)
                # scale down 5 times -> 2560 * 75% = 1920 (full hd 16:9 or full hd 19:10)
                max_scaling_tries = 12 if scale_up else 5
                while not coords and max_scaling_tries > scaling_try:
                    # change size with step in 5% of width and height
                    if scale_up:
                        image = img.resize((int(img.width + img.width * scaling_try * 5 / 100), int(img.height + img.height * scaling_try * 5 / 100)))
                    else:
                        image = img.resize((int(img.width - img.width * scaling_try * 5 / 100), int(img.height - img.height * scaling_try * 5 / 100)))
                    scaling_try += 1
            else:
                coords = pyautogui.locateOnScreen(img, **kwargs)

        tries -= 1
        kwargs["confidence"] -= 0.07

        if not coords and delay:
            sleep(delay)
    if not coords:
        raise Exception("No such element on screen")
    return (coords[0], coords[1], coords[2], coords[3])


# do click on center with flexible offsets
def click_on_element(coords, x_offset=0, y_offset=0):
    pyautogui.click(coords[0] + coords[2] / 2 + x_offset, coords[1] + coords[3] / 2 + y_offset)
    main_logger.info("Click at x = {}, y = {}".format(x, y))


# Function return protocol type(tcp\udp) from server keys in case
def getTransportProtocol(case):
    current_protocol = "tcp"
    if "-protocol udp" in case["server_keys"].lower():
        current_protocol = "udp"
    return current_protocol


def locate_and_click(template, scale=False, tries=3, delay=0, x_offset=0, y_offset=0, **kwargs):
    coords = locate_on_screen(template, scale=scale, tries=tries, delay=delay, **kwargs)
    x = coords[0] + coords[2] / 2 + x_offset
    y = coords[1] + coords[3] / 2 + y_offset
    main_logger.info("Click at x = {}, y = {}".format(x, y))
    pyautogui.click(x, y)


def prepare_game(game_name, game_launcher):
    pyautogui.moveTo(1, 1)
    pyautogui.hotkey("win", "m")

    if game_name == "heavendx9" or game_name == "heavendx11" or game_name == "heavenopengl":
        sleep(6)

        coords = locate_on_screen(HeavenElementLocation.API_LABEL)
        click_on_element(coords, x_offset=50)

        if game_name == "heavendx11":
            click_on_element(coords, x_offset=50, y_offset=15)
        elif game_name == "heavendx9":
            click_on_element(coords, x_offset=50, y_offset=30)
        else:
            click_on_element(coords, x_offset=50, y_offset=45)

        locate_and_click(ValleyElementLocation.RUN_BUTTON)

        sleep(20)
    if game_name == "valleydx9" or game_name == "valleydx11" or game_name == "valleyopengl":
        sleep(6)

        coords = locate_on_screen(ValleyElementLocation.API_LABEL)
        click_on_element(coords, x_offset=50)

        if game_name == "heavendx11":
            click_on_element(coords, x_offset=50, y_offset=15)
        elif game_name == "heavendx9":
            click_on_element(coords, x_offset=50, y_offset=30)
        else:
            click_on_element(coords, x_offset=50, y_offset=45)

        locate_and_click(ValleyElementLocation.RUN_BUTTON)

        sleep(20)
    elif self.game_name == "valorant":
        sleep(60)
        click("380", "edge_-225")
        sleep(1)
        click("360", "210")
        sleep(60)

        # do opening of lobby twice to avoid ads
        click("center_0", "25")
        sleep(3)

        press_keys("esc")

        click("center_0", "25")
        sleep(3)

        click("center_-300", "edge_-95")
        sleep(3)

        click("center_0", "center_225")
        sleep(30)

        click("center_-260", "center_-55")
        sleep(2)
        click("center_0", "center_110")
    elif game_name == "lol":
        # TODO: check find Play button and click on it
        sleep(90)
        click("center_-15", "center_-160", self.logger)
        sleep(1)
        locate_and_click(LoLElementLocation.PLAY_BUTTON, tries=4, delay=15)
        sleep(1)
        locate_and_click(LoLElementLocation.TRAINING)
        sleep(1)
        locate_and_click(LoLElementLocation.PRACTICE_TOOL)
        sleep(1)
        locate_and_click(LoLElementLocation.CONFIRM_BUTTON)
        sleep(1)
        locate_and_click(LoLElementLocation.START_GAME_ACTIVE)
        sleep(1)
        locate_and_click(LoLElementLocation.MALPHITE_ICON)
        sleep(1)
        locate_and_click(LoLElementLocation.LOCK_IN_BUTTON)
        sleep(45)
        click("center_0", "center_0")
        press_keys("shift+x ctrl+shift+i shift+y:17 ctrl+e ctrl+r")
    elif game_name == "dota2dx11" or game_name == "dota2vulkan":
        sleep(30)
        click("center_0", "center_0")
        press_keys("esc")
        sleep(5)
        press_keys("esc")
        sleep(1)

        # click on arcade to disable lighting from Dota2 logo
        locate_and_click(Dota2ElementLocation.ARCADE, scale=True)
        sleep(1)
        locate_and_click(Dota2ElementLocation.SETTINGS_BUTTON, scale=True)
        sleep(1)
        locate_and_click(Dota2ElementLocation.VIDEO_TAB, scale=True)
        sleep(1)
        locate_and_click(Dota2ElementLocation.RENDER_API_SELECTION, scale=True)
        sleep(1)
        if game_name == "dota2dx11":
            locate_and_click(Dota2ElementLocation.RENDER_API_DX11_OPTION, scale=True)
        else:
            locate_and_click(Dota2ElementLocation.RENDER_API_VULKAN_OPTION, scale=True)
        sleep(1)
        press_keys("esc")
        sleep(3)
        locate_and_click(Dota2ElementLocation.EXIT_BUTTON, scale=True)
        sleep(1)
        locate_and_click(Dota2ElementLocation.YES_BUTTON, scale=True)
        sleep(1)

        psutil.Popen(game_launcher, stdout=PIPE, stderr=PIPE, shell=True)
        sleep(15)
        press_keys("esc")
        sleep(5)
        press_keys("esc")
        sleep(1)

        locate_and_click(Dota2ElementLocation.ARCADE, scale=True)
        sleep(1)
        locate_and_click(Dota2ElementLocation.HEROES, scale=True)
        sleep(1)
        pyautogui.typewrite("sand king")
        press_keys("enter")
        sleep(1)
        locate_and_click(Dota2ElementLocation.DEMO_HERO, scale=True)
        sleep(15)
        locate_and_click(Dota2ElementLocation.FREE_SPELLS, scale=True)
        sleep(1)
        locate_and_click(Dota2ElementLocation.LVL_MAX, scale=True)
        sleep(1)
    elif game_name == "csgo":
        sleep(30)
        press_keys("esc")
        sleep(3)
        press_keys("esc")
        sleep(3)
        click("center_-919", "center_-394", self.logger)
        sleep(1)
        click("center_-710", "center_-406", self.logger)
        sleep(1)
        click("center_-718", "center_-223", self.logger)
        sleep(1)
        click("center_-4", "center_-86", self.logger)
        sleep(1)
        click("center_700", "center_492", self.logger)
        sleep(1)
        click("center_142", "center_112", self.logger)
        sleep(20)
        press_keys("w_3")

        # enter commands to csgo console
        commands = [
            "`",
            "sv_cheats 1",
            "give weapon_deagle",
            "give weapon_molotov",
            "sv_infinite_ammo 1",
            "`"
        ]
        for command in commands:
            if command != "`":
                keyboard.write(command)
            else:
                pydirectinput.press("`")
            sleep(0.5)
            pydirectinput.press("enter")


def press_keys(keys_string):
    keys = keys_string.split()

    # press keys one by one
    # possible formats
    # * space - press space
    # * space_10 - press space down for 10 seconds
    # * space+shift - press space and shift
    # * space+shift:10 - press space and shift 10 times
    for i in range(len(keys)):
        key = keys[i]

        duration = 0

        if "_" in key:
            parts = key.split("_")
            key = parts[0]
            duration = int(parts[1])

        main_logger.info("Press: {}. Duration: {}".format(key, duration))

        if duration == 0:
            times = 1

            if ":" in key:
                parts = key.split(":")
                key = parts[0]
                times = int(parts[1])

            keys_to_press = key.split("+")

            for i in range(times):
                for key_to_press in keys_to_press:
                    pydirectinput.keyDown(key_to_press)

                sleep(0.1)

                for key_to_press in keys_to_press:
                    pydirectinput.keyUp(key_to_press)

                sleep(0.5)
        else:
            keys_to_press = key.split("+")

            for key_to_press in keys_to_press:
                pydirectinput.keyDown(key_to_press)

            sleep(duration)

            for key_to_press in keys_to_press:
                pydirectinput.keyUp(key_to_press)

        # if it isn't the last key - make a delay
        if i != len(keys) - 1:
            if "enter" in key:
                sleep(2)
            else:
                sleep(1)


def click(x_description, y_description, delay = 0.2):
    if platform.system() == "Windows":
        edge_x = win32api.GetSystemMetrics(0)
        edge_y = win32api.GetSystemMetrics(1)
    else:
        process = subprocess.Popen("xdpyinfo | awk '/dimensions/{print $2}'", stdout=PIPE, shell=True)
        stdout, stderr = process.communicate()
        edge_x, edge_y = stdout.decode("utf-8").strip().split("x")
        edge_x = int(edge_x)
        edge_y = int(edge_y)

    if "center_" in x_description:
        x = edge_x / 2 + int(x_description.replace("center_", ""))
    elif "edge_" in x_description:
        x = edge_x + int(x_description.replace("edge_", ""))
    else:
        x = int(x_description)

    if "center_" in y_description:
        y = edge_y / 2 + int(y_description.replace("center_", ""))
    elif "edge_" in y_description:
        y = edge_y + int(y_description.replace("edge_", ""))
    else:
        y = int(y_description)

    main_logger.info("Click at x = {}, y = {}".format(x, y))

    pyautogui.moveTo(x, y)
    sleep(delay)
    pyautogui.click()


def make_game_foreground(game_name):
    if "heaven" in game_name.lower():
        icon_path = IconElementLocation.HEAVEN.build_path()
    elif "valley" in game_name.lower():
        icon_path = IconElementLocation.VALLEY.build_path()
    elif "valorant" in game_name.lower():
        icon_path = IconElementLocation.VALORANT.build_path()
    elif "lol" in game_name.lower():
        icon_path = IconElementLocation.LOL.build_path()
    elif "dota2" in game_name.lower():
        icon_path = IconElementLocation.DOTA2.build_path()
    elif "csgo" in game_name.lower():
        icon_path = IconElementLocation.CSGO.build_path()
    else:
        main_logger.error(f"Unknown game: {game_name}")
        return

    # sometimes first click on app can be ignored
    for i in range(2):
        try:
            locate_and_click(icon_path)
            sleep(4)
        except:
            main_logger.info(f"Icon wasn't detected. Skip making game foreground (try #{i})")
            break
