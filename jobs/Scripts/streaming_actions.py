from time import sleep
import psutil
import os
import subprocess
from subprocess import PIPE
import sys
import traceback
import platform
import win32clipboard
from enum import Enum
import pyautogui
import pyscreenshot
import utils
from streaming_actions import locate_and_click, locate_on_screen, click_on_element
from elements import AMDLinkElementLocation

if platform.system() == "Windows":
    import win32gui
    import win32con

ROOT_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir))
sys.path.append(ROOT_PATH)
from jobs_launcher.core.config import main_logger


class StreamingType(Enum):
    SDK = 1
    AMD_LINK = 2
    WEB = 3


def start_streaming(execution_type, streaming_type=StreamingType.SDK, script_path=None, case=None, socket=None, debug_screen_path=None):
    main_logger.info("Start StreamingSDK {}".format(execution_type))

    if streaming_type == StreamingType.SDK:
        if not script_path:
            raise ValueError("Script path is required to launch Streaming SDK")

        return start_streaming_sdk(execution_type, script_path)
    elif streaming_type == StreamingType.AMD_LINK:
        if not case:
            raise ValueError("Case is required to launch AMD Link")
        if not socket:
            raise ValueError("Socket is required to launch AMD Link")

        return start_streaming_amd_link(execution_type, case, socket, debug_screen_path=debug_screen_path)
    else:
        raise ValueError(f"Unknown StreamingSDK type: {streaming_type}")


def start_streaming_sdk(execution_type, script_path):
    if platform.system() == "Windows":
        process = psutil.Popen(script_path, stdout=PIPE, stderr=PIPE, shell=True)
    else:
        process = psutil.Popen(f"xterm -e {script_path}", stdout=PIPE, stderr=PIPE, shell=True)

    return process


def set_dropdown_option(case, field_width, label_image_name, param_name):
    label_coords = locate_on_screen(AMDLinkElementLocation.DROPDOWN_OPTIONS_LABELS[label_image_name])
    pyautogui.click(label_coords[0] + field_width, label_coords[1] + label_coords[3] / 2)
    locate_and_click(AMDLinkElementLocation.DROPDOWN_OPTIONS_VALUES[label_image_name][param_name], main_logger)


def configure_boolean_option(case, field_width, label_image_name, param_name):
    label_coords = locate_on_screen(AMDLinkElementLocation.DROPDOWN_OPTIONS_LABELS[label_image_name])
    region = (int(label_coords[0] + field_width - 100), int(label_coords[1]), int(field_width), int(label_coords[3]))
    try:
        coords = locate_on_screen(AMDLinkElementLocation.ENABLED, region=region)
        value = True
    except:
        try:
            coords = locate_on_screen(AMDLinkElementLocation.DISABLED, region=region)
            value = False
        except:
            raise Exception("Can't determine boolean value")

    if value != case['server_params'][param_name]:
        click_on_element(coords, main_logger)


def set_adrenalin_params(case):
    # calculate approximate width of option field as distance between AMD Link Server and Stream Resolution labels
    amd_link_coords = locate_on_screen(AMDLinkElementLocation.AMD_LINK_SERVER)
    resolution_coords = locate_on_screen(AMDLinkElementLocation.STREAM_RESOLUTION)

    field_width = (resolution_coords[0] - amd_link_coords[0]) / 2

    # select Resolution
    set_dropdown_option(case, field_width, "stream_resolution", "resolution")

    # select Video Encoding
    set_dropdown_option(case, field_width, "video_encoding_type", "encoding_type")

    # configure Accept All Connections option
    configure_boolean_option(case, field_width, "accept_all_connections", "accept_all_connections")

    # configure Use Encryption option
    configure_boolean_option(case, field_width, "use_encryption", "use_encryption")


def start_streaming_amd_link(execution_type, case, socket, debug_screen_path=None):
    if execution_type == "server":
        client_already_started = False

        try:
            pyautogui.hotkey("alt", "tab")
            sleep(1)
            pyautogui.hotkey("win", "m")
            sleep(1)

            script_path = "C:\\JN\\Adrenalin.lnk"
            process = psutil.Popen(script_path, stdout=PIPE, stderr=PIPE, shell=True)

            # wait AMD Adrenalin window opening
            for i in range(10):
                try:
                    locate_on_screen(AMDLinkElementLocation.ADRENALIN_ICON)
                    break
                except:
                    sleep(1)
            else:
                raise Exception("Adrenalin tool window wasn't found")

            window_hwnd = None

            for window in pyautogui.getAllWindows():
                if "AMD Software: Adrenalin" in window.title:
                    window_hwnd = window._hWnd
                    break

            if not window_hwnd:
                raise Exception("Adrenalin tool window wasn't found")

            win32gui.ShowWindow(window_hwnd, win32con.SW_MAXIMIZE)

            try:
                locate_on_screen(AMDLinkElementLocation.HOME_ACTIVE)
                # open AMD Link tab
                coords = locate_on_screen(AMDLinkElementLocation.AMD_LINK_STATUS)
                pyautogui.click(coords[0] + coords[2] - 5, coords[1] + coords[3] - 5)
            except:
                # AMD Link tab is already active
                pass

            try:
                # open enable AMD Link if it's required
                locate_on_screen(AMDLinkElementLocation.ENABLE_AMD_LINK)
            except:
                pass

            try:
                locate_on_screen(AMDLinkElementLocation.STOP_STREAMING_BUTTON, delay=1)
                server_already_started = True
            except:
                server_already_started = False

            try:
                locate_on_screen(AMDLinkElementLocation.PC_ICON)
                client_already_started = True
            except:
                client_already_started = False

            if client_already_started:
                locate_on_screen(AMDLinkElementLocation.START_STREAMING_BUTTON, delay=1)

                socket.send("restart".encode("utf-8"))
            else:
                # receive game invite link
                coords = locate_on_screen(AMDLinkElementLocation.LINK_GAME_INVITE_SERVER, delay=1)
                click_on_element(coords, main_logger)
                sleep(1)
                # sometimes first click not work
                click_on_element(coords, main_logger)

                if case["server_params"]["streaming_mode"] == "multi_play":
                    coords = locate_on_screen(AMDLinkElementLocation.MULTI_PLAY, delay=1)
                else:
                    coords = locate_on_screen(AMDLinkElementLocation.FULL_ACCESS, delay=1)

                # first click - make full acess active, second click - select full access, third click - click on code to display copy button + one additional click (sometimes first click not work)
                for i in range(4):
                    click_on_element(coords, main_logger)
                    sleep(1)

                for i in range(40):
                    try:
                        if case["server_params"]["streaming_mode"] == "multi_play":
                            coords = locate_on_screen(AMDLinkElementLocation.MULTI_PLAY_FRESH_LINK)
                        else:
                            coords = locate_on_screen(AMDLinkElementLocation.FULL_ACCESS_FRESH_LINK)
                        break
                    except:
                        sleep(1)
                else:
                    raise Exception("Fresh invitation code wasn't detected")

                # copy invite code and close window with it
                locate_and_click(AMDLinkElementLocation.COPY_TEXT, main_logger, delay=1)

                locate_and_click(AMDLinkElementLocation.CLOSE_INVITE_CODE_WINDOW, main_logger, delay=1)

                sleep(1)
                pyautogui.moveTo(10, 10)
                sleep(2)

                if not server_already_started:
                    locate_and_click(AMDLinkElementLocation.START_STREAMING_BUTTON, main_logger, delay=1)

                    set_adrenalin_params(case)

                if debug_screen_path:
                    # save debug screen
                    screen = pyscreenshot.grab()
                    screen = screen.convert("RGB")
                    screen.save(debug_screen_path)

                win32clipboard.OpenClipboard()
                invite_code = win32clipboard.GetClipboardData()
                win32clipboard.CloseClipboard()

                socket.send(invite_code.encode("utf-8"))
        except Exception as e:
            socket.send("failed".encode("utf-8"))
            raise e

        # wait answer from client
        while True:
            try:
                answer = socket.recv(1024).decode("utf-8")
                break
            except Exception as e:
                sleep(0.1)
                continue

        if answer != "done":
            raise Exception("Failed to open AMD Link on client side")
    else:
        # wait invite code
        invite_code = socket.recv(1024).decode("utf-8")

        if invite_code == "failed":
           raise Exception("Failed to receive invite code on server side") 

        try:
            pyautogui.hotkey("alt", "tab")
            sleep(1)
            pyautogui.hotkey("win", "m")
            sleep(1)

            script_path = "C:\\JN\\AMDLink.lnk"
            process = psutil.Popen(script_path, stdout=PIPE, stderr=PIPE, shell=True)

            if invite_code != "restart":
                # wait AMD Link window opening
                for i in range(10):
                    try:
                        locate_on_screen(AMDLinkElementLocation.AMD_LINK_ICON)
                        break
                    except:
                        sleep(1)
                else:
                    raise Exception("AMD Link tool window wasn't found")
                
                # connect to server
                locate_and_click(AMDLinkElementLocation.CONNECT_TO_PC, main_logger, delay=1)

                locate_and_click(AMDLinkElementLocation.LINK_GAME_INVITE_CLIENT, main_logger, delay=1)

                # type invite code and press submit button
                sleep(1)
                pyautogui.write(invite_code)

                locate_and_click(AMDLinkElementLocation.SUBMIT_CONNECT, main_logger, delay=1)

                sleep(1)

                try:
                    # skip optimizations and start streaming
                    locate_and_click(AMDLinkElementLocation.SKIP_OPTIMIZATION, main_logger, delay=1)
                except:
                    pass

                if case['server_params']['streaming_mode'] == 'full_access':
                    try:
                        locate_and_click(AMDLinkElementLocation.START_STREAMING, main_logger, delay=1)
                    except:
                        # Start Streaming button can be hovered
                        locate_and_click(AMDLinkElementLocation.START_STREAMING_2, main_logger, delay=1)

                sleep(5)

            # apply full screen
            try:
                locate_and_click(AMDLinkElementLocation.APPLY_FULL_SCREEN, main_logger, delay=1)
            except:
                pass

            socket.send("done".encode("utf-8"))
        except Exception as e:
            socket.send("failed".encode("utf-8"))
            raise e

    return process


def close_streaming(execution_type, case, process, tool_path=None, streaming_type=StreamingType.SDK):
    try:
        if streaming_type == StreamingType.SDK:
            return close_streaming_sdk(execution_type, case, process, tool_path=None)
        elif streaming_type == StreamingType.AMD_LINK:
            return close_streaming_amd_link(execution_type, case, process, tool_path=None)
        else:
            raise ValueError(f"Unknown StreamingSDK type: {streaming_type}")
    except Exception as e:
        main_logger.error("Failed to close Streaming SDK process. Exception: {}".format(str(e)))
        main_logger.error("Traceback: {}".format(traceback.format_exc()))

        return None


def close_streaming_sdk(execution_type, case, process, tool_path=None):
    if utils.should_case_be_closed(execution_type, case):
        # close the current Streaming SDK process
        main_logger.info("Start closing")

        if platform.system() == "Windows":
            if process is not None:
                utils.close_process(process)

            # additional try to kill Streaming SDK server/client (to be sure that all processes are closed)
            subprocess.call("taskkill /f /im RemoteGameClient.exe", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
            subprocess.call("taskkill /f /im RemoteGameServer.exe", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)

            if execution_type == "server":
                crash_window = win32gui.FindWindow(None, "RemoteGameServer.exe")
            else:
                crash_window = win32gui.FindWindow(None, "RemoteGameClient.exe")

            if crash_window:
                main_logger.info("Crash window was found. Closing it...")
                win32gui.PostMessage(crash_window, win32con.WM_CLOSE, 0, 0)
        else:
            if process is not None and tool_path is not None:
                os.system("sudo pkill -9 -f \"^{}\"".format(os.path.abspath(tool_path)))

        main_logger.info("Finish closing")

        return None
    else:
        main_logger.info("Keep StreamingSDK instance")

    return process


def close_streaming_amd_link(execution_type, case, process, tool_path=None):
    if utils.should_case_be_closed(execution_type, case):
        # close the current Streaming SDK process
        main_logger.info("Start closing") 

        if execution_type == "server":
            # wait closing on client
            sleep(3)

            pyautogui.hotkey("alt", "tab")
            sleep(1)
            pyautogui.hotkey("win", "m")
            sleep(5)

            script_path = "C:\\JN\\Adrenalin.lnk"
            process = psutil.Popen(script_path, stdout=PIPE, stderr=PIPE, shell=True)

            window_hwnd = None

            for window in pyautogui.getAllWindows():
                if "AMD Software: Adrenalin" in window.title:
                    window_hwnd = window._hWnd
                    break

            if not window_hwnd:
                raise Exception("Adrenalin tool window wasn't found")

            win32gui.ShowWindow(window_hwnd, win32con.SW_MAXIMIZE)

            # make a click on Adrenalin tool
            locate_and_click(AMDLinkElementLocation.ADRENALIN_ICON, main_logger, delay=1)

            locate_and_click(AMDLinkElementLocation.STOP_STREAMING_BUTTON, main_logger, delay=1)

        elif execution_type == "client":
            subprocess.call("taskkill /f /im AMDLink.exe", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
            sleep(3)

        main_logger.info("Finish closing")

        return None
    else:
        main_logger.info("Keep StreamingSDK instance")

    return process
