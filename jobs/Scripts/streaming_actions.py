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
import utils

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


def start_streaming(execution_type, script_path, streaming_type=StreamingType.SDK, socket=None):
    main_logger.info("Start StreamingSDK {}".format(execution_type))

    if streaming_type == StreamingType.SDK:
        return start_streaming_sdk(execution_type, script_path)
    elif streaming_type == StreamingType.AMD_LINK:
        if not socket:
            raise ValueError("Socket is required to launch AMD Link")

        return start_streaming_amd_link(execution_type, socket)
    else:
        raise ValueError(f"Unknown StreamingSDK type: {streaming_type}")


def start_streaming_sdk(execution_type, script_path):
    if platform.system() == "Windows":
        process = psutil.Popen(script_path, stdout=PIPE, stderr=PIPE, shell=True)
    else:
        process = psutil.Popen(f"xterm -e {script_path}", stdout=PIPE, stderr=PIPE, shell=True)

    return process


def start_streaming_amd_link(execution_type, socket):
    if execution_type == "server":
        try:
            script_path = "C:\\JN\\Adrenalin.lnk"
            process = psutil.Popen(script_path, stdout=PIPE, stderr=PIPE, shell=True)

            # wait AMD Adrenaline window opening
            for i in range(10):
                try:
                    utils.locate_on_screen(os.path.join(os.path.dirname(__file__), "Elements", "AMDLink", "adrenalin_icon.png"))
                    break
                except:
                    sleep(1)
            else:
                raise Exception("Adrenaline tool window wasn't found")

            try:
                utils.locate_on_screen(os.path.join(os.path.dirname(__file__), "Elements", "AMDLink", "home_active.png"))
                # open AMD Link tab
                coords = utils.locate_on_screen(os.path.join(os.path.dirname(__file__), "Elements", "AMDLink", "amd_link_status.png"))
                pyautogui.click(coords[0] + coords[2] - 5, coords[1] + coords[3] - 5)
            except:
                # AMD Link tab is already active
                pass

            # receive game invite link
            coords = utils.locate_on_screen(os.path.join(os.path.dirname(__file__), "Elements", "AMDLink", "link_game_invite_server.png"), delay=1)
            utils.click_on_center_of(coords)

            coords = utils.locate_on_screen(os.path.join(os.path.dirname(__file__), "Elements", "AMDLink", "full_access.png"), delay=1)
            # first click - make full acess active, second click - select full access, third click - click on code to display copy button
            for i in range(3):
                utils.click_on_center_of(coords)
                sleep(1)

            # copy invite code and close window with it
            coords = utils.locate_on_screen(os.path.join(os.path.dirname(__file__), "Elements", "AMDLink", "copy_text.png"), delay=1)
            utils.click_on_center_of(coords)

            coords = utils.locate_on_screen(os.path.join(os.path.dirname(__file__), "Elements", "AMDLink", "cancel.png"), delay=1)
            utils.click_on_center_of(coords)

            win32clipboard.OpenClipboard()
            invite_code = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()

            socket.send(invite_code.encode("utf-8"))
        except Exception as e:
            socket.send("failed".encode("utf-8"))
            raise e

        # wait answer from client
        answer = sock.recv(1024).decode("utf-8")

        if answer != "done":
            raise Exception("Failed to open AMD Link on client side")
    else:
        # wait invite code
        invite_code = sock.recv(1024).decode("utf-8")

        if invite_code == "failed":
           raise Exception("Failed to receive invite code on server side") 

        try:
            script_path = "C:\\JN\\AMDLink.lnk"
            process = psutil.Popen(script_path, stdout=PIPE, stderr=PIPE, shell=True)

            # wait AMD Link window opening
            for i in range(10):
                try:
                    utils.locate_on_screen(os.path.join(os.path.dirname(__file__), "Elements", "AMDLink", "amd_link_icon.png"))
                    break
                except:
                    sleep(1)
            else:
                raise Exception("AMD Link tool window wasn't found")

            # connect to server
            coords = utils.locate_on_screen(os.path.join(os.path.dirname(__file__), "Elements", "AMDLink", "connect_to_pc.png"), delay=1)
            utils.click_on_center_of(coords)

            coords = utils.locate_on_screen(os.path.join(os.path.dirname(__file__), "Elements", "AMDLink", "link_game_invite_client.png"), delay=1)
            utils.click_on_center_of(coords)

            # type invite code and press submit button
            sleep(1)
            pyautogui.write(invite_code)

            coords = utils.locate_on_screen(os.path.join(os.path.dirname(__file__), "Elements", "AMDLink", "submit_connect.png"), delay=1)
            utils.click_on_center_of(coords)

            sleep(1)

            # skip optimizations and start streaming
            coords = utils.locate_on_screen(os.path.join(os.path.dirname(__file__), "Elements", "AMDLink", "skip_optimization.png"), delay=1)
            utils.click_on_center_of(coords)

            coords = utils.locate_on_screen(os.path.join(os.path.dirname(__file__), "Elements", "AMDLink", "start_streaming.png"), delay=1)
            utils.click_on_center_of(coords)

            sleep(5)

            # apply full screen
            coords = utils.locate_on_screen(os.path.join(os.path.dirname(__file__), "Elements", "AMDLink", "apply_full_screen.png"), delay=1)
            utils.click_on_center_of(coords)

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
                close_process(process)

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
            script_path = "C:\\JN\\Adrenalin.lnk"
            process = psutil.Popen(script_path, stdout=PIPE, stderr=PIPE, shell=True)

            # click on pc name and select disconnect
            coords = utils.locate_on_screen(os.path.join(os.path.dirname(__file__), "Elements", "AMDLink", "pc_icon.png"), delay=1)
            pyautogui.moveTo(coords[0] + coords[2] / 2, coords[1] + coords[3] / 2)
            time.sleep(1)
            pyautogui.click(button="right")
            time.sleep(1)
            pyautogui.click(button="right")

            coords = utils.locate_on_screen(os.path.join(os.path.dirname(__file__), "Elements", "AMDLink", "disconnect_button.png"), delay=1)
            utils.click_on_center_of(coords)

        main_logger.info("Finish closing")

        return None
    else:
        main_logger.info("Keep StreamingSDK instance")

    return process
