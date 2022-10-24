from time import sleep
import psutil
import os
import subprocess
from subprocess import PIPE
import sys
import traceback
import platform
from enum import Enum
import pyautogui
import pyscreenshot
import utils
from games_actions import locate_and_click, locate_on_screen, click_on_element
from elements import AMDLinkElements, IconElements

if platform.system() == "Windows":
    import win32gui
    import win32con
    import win32clipboard

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


def set_dropdown_option(case, field_width, param_name):
    label_coords = locate_on_screen(AMDLinkElements.DROPDOWN_OPTIONS_LABELS[param_name].build_path())
    pyautogui.click(label_coords[0] + field_width, label_coords[1] + label_coords[3] / 2)
    locate_and_click(AMDLinkElements.DROPDOWN_OPTIONS_VALUES[param_name][case["server_params"][param_name]].build_path())


def configure_boolean_option(case, field_width, param_name):
    label_coords = locate_on_screen(AMDLinkElements.DROPDOWN_OPTIONS_LABELS[param_name].build_path())
    region = (int(label_coords[0] + field_width - 100), int(label_coords[1]), int(field_width), int(label_coords[3]))
    try:
        coords = locate_on_screen(AMDLinkElements.ENABLED.build_path(), region=region)
        value = True
    except:
        try:
            coords = locate_on_screen(AMDLinkElements.DISABLED.build_path(), region=region)
            value = False
        except:
            raise Exception("Can't determine boolean value")

    if value != case["server_params"][param_name]:
        click_on_element(coords)


def set_adrenalin_params(case):
    # calculate approximate width of option field as distance between AMD Link Server and Stream Resolution labels
    amd_link_coords = locate_on_screen(AMDLinkElements.AMD_LINK_SERVER.build_path())
    resolution_coords = locate_on_screen(AMDLinkElements.STREAM_RESOLUTION.build_path())

    field_width = (resolution_coords[0] - amd_link_coords[0]) / 2

    # select Resolution
    set_dropdown_option(case, field_width, "resolution")

    # select Video Encoding
    set_dropdown_option(case, field_width, "encoding_type")

    # configure Accept All Connections option
    configure_boolean_option(case, field_width, "accept_all_connections")

    # configure Use Encryption option
    configure_boolean_option(case, field_width, "use_encryption")


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
                    locate_on_screen(AMDLinkElements.ADRENALIN_ICON.build_path())
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

            locate_and_click(IconElements.ADRENALIN_ICON.build_path())
            win32gui.ShowWindow(window_hwnd, win32con.SW_MAXIMIZE)

            try:
                locate_on_screen(AMDLinkElements.HOME_ACTIVE.build_path())
                # open AMD Link tab
                coords = locate_on_screen(AMDLinkElements.AMD_LINK_STATUS.build_path())
                pyautogui.click(coords[0] + coords[2] - 5, coords[1] + coords[3] - 5)
            except:
                # AMD Link tab is already active
                pass

            try:
                # open enable AMD Link if it's required
                locate_on_screen(AMDLinkElements.ENABLE_AMD_LINK.build_path())
            except:
                pass

            try:
                locate_on_screen(AMDLinkElements.STOP_STREAMING_BUTTON.build_path(), delay=1)
                server_already_started = True
            except:
                server_already_started = False

            try:
                locate_on_screen(AMDLinkElements.PC_ICON.build_path())
                client_already_started = True
            except:
                client_already_started = False

            main_logger.info("Server is already started: {}".format(server_already_started))
            main_logger.info("Client is already started: {}".format(client_already_started))

            if client_already_started:
                locate_and_click(AMDLinkElements.START_STREAMING_BUTTON.build_path(), delay=1)

                socket.send("restart".encode("utf-8"))
            else:
                # receive game invite link
                coords = locate_on_screen(AMDLinkElements.LINK_GAME_INVITE_SERVER.build_path(), delay=1)
                click_on_element(coords)
                sleep(1)
                # sometimes first click not work
                click_on_element(coords)

                if case["server_params"]["streaming_mode"] == "multi_play":
                    link_coords = locate_on_screen(AMDLinkElements.MULTI_PLAY.build_path(), delay=1)
                else:
                    link_coords = locate_on_screen(AMDLinkElements.FULL_ACCESS.build_path(), delay=1)

                # sometimes click not work
                for i in range(3):
                    click_on_element(link_coords)
                    sleep(0.5)

                for i in range(40):
                    try:
                        if case["server_params"]["streaming_mode"] == "multi_play":
                            coords = locate_on_screen(AMDLinkElements.MULTI_PLAY_FRESH_LINK.build_path())
                        else:
                            coords = locate_on_screen(AMDLinkElements.FULL_ACCESS_FRESH_LINK.build_path())
                        break
                    except:
                        sleep(1)
                else:
                    raise Exception("Fresh invitation code wasn't detected")

                # sometimes click not work
                click_on_element(link_coords)
                sleep(0.5)
                click_on_element(link_coords)

                # copy invite code and close window with it
                locate_and_click(AMDLinkElements.COPY_TEXT.build_path(), delay=1)

                locate_and_click(AMDLinkElements.CLOSE_INVITE_CODE_WINDOW.build_path(), delay=1)

                sleep(1)
                pyautogui.moveTo(10, 10)
                sleep(2)

                if not server_already_started:
                    locate_and_click(AMDLinkElements.START_STREAMING_BUTTON.build_path(), delay=1)

                    set_adrenalin_params(case)

                if debug_screen_path:
                    # save debug screen
                    screen = pyscreenshot.grab()
                    screen = screen.convert("RGB")
                    screen.save(debug_screen_path)

                win32clipboard.OpenClipboard()
                invite_code = win32clipboard.GetClipboardData()
                win32clipboard.CloseClipboard()

                main_logger.info(f"Sending invite code: {invite_code}")

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

        main_logger.info(f"Received invite code: {invite_code}")

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
                        locate_on_screen(AMDLinkElements.AMD_LINK_ICON.build_path())
                        break
                    except:
                        sleep(1)
                else:
                    raise Exception("AMD Link tool window wasn't found")
                
                # connect to server
                locate_and_click(AMDLinkElements.CONNECT_TO_PC.build_path(), delay=1)

                locate_and_click(AMDLinkElements.LINK_GAME_INVITE_CLIENT.build_path(), delay=1)

                # focus AMD Link window
                sleep(0.5)
                locate_and_click(AMDLinkElements.SUBMIT_CONNECT_DISABLED.build_path(), delay=1)

                # type invite code and press submit button
                sleep(0.5)
                pyautogui.write(invite_code)
                sleep(1)

                # sometimes click not work
                locate_and_click(AMDLinkElements.SUBMIT_CONNECT.build_path(), delay=1)
                sleep(1)
                try:
                    locate_and_click(AMDLinkElements.SUBMIT_CONNECT.build_path())
                except:
                    pass

                sleep(2)

                # check that submit button was clicked
                try:
                    locate_on_screen(AMDLinkElements.SUBMIT_CONNECT.build_path())
                    submit_button_found = True
                except:
                    submit_button_found = False

                if submit_button_found:
                    raise Exception("Submit button wasn't clicked. Invite code could be invalid / outdated or connection could't be established")

                try:
                    # skip optimizations and start streaming
                    locate_and_click(AMDLinkElements.SKIP_OPTIMIZATION.build_path(), delay=1)
                except:
                    pass

                if case['server_params']['streaming_mode'] == 'full_access':
                    try:
                        locate_and_click(AMDLinkElements.START_STREAMING.build_path(), delay=1)
                    except:
                        # Start Streaming button can be hovered
                        locate_and_click(AMDLinkElements.START_STREAMING_2.build_path(), delay=1)

                sleep(5)

            # apply full screen
            try:
                locate_and_click(AMDLinkElements.APPLY_FULL_SCREEN.build_path(), delay=1)
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
            return close_streaming_sdk(execution_type, case, process, tool_path=tool_path)
        elif streaming_type == StreamingType.AMD_LINK:
            return close_streaming_amd_link(execution_type, case, process)
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


def close_streaming_amd_link(execution_type, case, process):
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

            locate_and_click(IconElements.ADRENALIN_ICON.build_path())
            win32gui.ShowWindow(window_hwnd, win32con.SW_MAXIMIZE)

            # make a click on Adrenalin tool
            locate_and_click(AMDLinkElements.ADRENALIN_ICON.build_path(), delay=1)

            locate_and_click(AMDLinkElements.STOP_STREAMING_BUTTON.build_path(), delay=1)

        elif execution_type == "client":
            subprocess.call("taskkill /f /im AMDLink.exe", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
            sleep(3)

        main_logger.info("Finish closing")

        return None
    else:
        main_logger.info("Keep StreamingSDK instance")

    return process
