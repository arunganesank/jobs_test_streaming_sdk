import os
from time import sleep, strftime, gmtime
import traceback
import pyautogui
import pyscreenshot
import json
from threading import Thread
from utils import *
from actions import *
from streaming_actions import start_streaming, StreamingType
import games_actions

if platform.system() == "Windows":
    from pyffmpeg import FFmpeg
    import win32api
    import pydirectinput

pyautogui.FAILSAFE = False
MC_CONFIG = get_mc_config()


# [Server action] send request to execute some cmd command on server
# [Result] wait answer from server. Answer must be 'done'
class ExecuteCMD(Action):
    def parse(self):
        self.action = self.params["action_line"]

    def execute(self):
        self.sock.send(self.action.encode("utf-8"))

    def analyze_result(self):
        self.wait_server_answer(analyze_answer = True, abort_if_fail = True)


# [Server action] send request to check what some window exists
# [Result] wait answer from server. Answer can be any
class CheckWindow(Action):
    def parse(self):
        self.action = self.params["action_line"]

    def execute(self):
        self.sock.send(self.action.encode("utf-8"))

    def analyze_result(self):
        self.wait_server_answer(analyze_answer = True, abort_if_fail = False)


# [Server action] send request to press some sequence of keys on server
# [Result] wait answer from server. Answer must be 'done'
class PressKeysServer(Action):
    def parse(self):
        self.action = self.params["action_line"]

    def execute(self):
        self.sock.send(self.action.encode("utf-8"))

    def analyze_result(self):
        self.wait_server_answer(analyze_answer = True, abort_if_fail = True)


# [Server action] send request to abort the current case execution
# [Result] wait answer from server. Answer can be any
class Abort(Action):
    def execute(self):
        self.sock.send("abort".encode("utf-8"))

    def analyze_result(self):
        self.wait_server_answer(analyze_answer = False, abort_if_fail = False)


# [Server action] send request to retry the current case execution
# [Result] wait answer from server. Answer can be any
class Retry(Action):
    def execute(self):
        self.sock.send("retry".encode("utf-8"))

    def analyze_result(self):
        self.wait_server_answer(analyze_answer = False, abort_if_fail = False)


# [Server action] send request to start the next test case
# [Result] wait answer from server. Answer can be any
class NextCase(Action):
    def execute(self):
        self.sock.send("next_case".encode("utf-8"))

        if self.params["args"].track_used_memory:
            track_used_memory(self.params["case"], "client")

    def analyze_result(self):
        self.wait_server_answer(analyze_answer = False, abort_if_fail = False)


class IPerf(Action):
    def execute(self):
        self.sock.send("iperf".encode("utf-8"))

        response = self.sock.recv(1024).decode("utf-8")

        self.logger.info("Server iperf answer: {}".format(response))

        # start iperf execution
        if response == "start":
            collect_iperf_info(self.params["args"], self.params["case"]["case"])
            self.params["iperf_executed"] = True
        else:
            # finish execution
            pass


# [Server action] send request to do click on server side
# [Result] wait answer from server. Answer must be 'done'
class ClickServer(Action):
    def parse(self):
        self.action = self.params["action_line"]

    def execute(self):
        self.sock.send(self.action.encode("utf-8"))

    def analyze_result(self):
        self.wait_server_answer(analyze_answer = True, abort_if_fail = True)


# [Server action] send request to start doing test actions on server side
# [Result] wait answer from server. Answer must be 'done'
class StartTestActionsServer(Action):
    def parse(self):
        self.action = self.params["action_line"]

    def execute(self):
        self.sock.send(self.action.encode("utf-8"))

    def analyze_result(self):
        self.wait_server_answer(analyze_answer = True, abort_if_fail = True)

# [Server action] send request to start microphone
# [Result] wait answer from server. Answer must be 'done'
class RecordMicrophone(Action):
    def parse(self):
        self.action = self.params["action_line"]

    def execute(self):
        self.sock.send(self.action.encode("utf-8"))

    def analyze_result(self):
        self.wait_server_answer(analyze_answer = True, abort_if_fail = True)

# [Client action] do screenshot
# This action triggers actions on server side in Multiconnection group
class MakeScreen(Action):
    def parse(self):
        self.action = self.params["action_line"]
        self.test_group = self.params["args"].test_group
        self.screen_path = self.params["screen_path"]
        self.screen_name = self.params["arguments_line"]
        self.current_image_num = self.params["current_image_num"]
        self.current_try = self.params["current_try"]
        self.client_type = self.params["client_type"]
        self.is_multiconnection = self.test_group in MC_CONFIG["android_client"] or self.test_group in MC_CONFIG["second_win_client"]
        self.case_json_path = self.params["case_json_path"]

    def execute(self):
        if not self.screen_name:
            make_screen(self.screen_path, None, self.current_try, self.logger)
        else:
            if self.is_multiconnection:
                self.sock.send(self.action.encode("utf-8"))

            make_screen(self.screen_path, self.case_json_path, self.current_try, self.logger, self.screen_name + self.client_type, self.current_image_num)
            self.params["current_image_num"] += 1


    def analyze_result(self):
        if self.screen_name and self.is_multiconnection:
            self.wait_server_answer(analyze_answer = True, abort_if_fail = True)


def make_screen(screen_path, case_json_path, current_try, logger, screen_name = "", current_image_num = 0):
    screen = pyscreenshot.grab()

    if screen_name:
        screen = screen.convert("RGB")
        screen.save(os.path.join(screen_path, "{:03}_{}_try_{:02}.jpg".format(current_image_num, screen_name, current_try + 1)))

        # Check artifacts
        if case_json_path is not None:
            check_artifacts_and_save_status(os.path.join(screen_path, "{:03}_{}_try_{:02}.jpg".format(current_image_num, screen_name, current_try + 1)), case_json_path, logger)


# [Client action] record video
# This action triggers actions on server side in Multiconnection group
class RecordVideo(Action):
    def parse(self):
        self.action = self.params["action_line"]
        self.test_group = self.params["args"].test_group
        self.audio_device_name = self.params["audio_device_name"]
        self.video_path = self.params["output_path"]
        self.video_name = self.params["case"]["case"] + self.params["client_type"]
        self.resolution = self.params["args"].screen_resolution
        self.duration = int(self.params["arguments_line"])
        self.is_multiconnection = self.test_group in MC_CONFIG["android_client"] or self.test_group in MC_CONFIG["second_win_client"]
        self.case_json_path = self.params["case_json_path"]
        self.recovery_clumsy = "recovery_client_clumsy" in self.params["case"] and self.params["case"]["recovery_client_clumsy"]

    def execute(self):
        if self.recovery_clumsy:
            self.logger.info("Recovery Streaming SDK work - close clumsy")
            close_clumsy()

        if "recovery_server_clumsy" in self.params["case"] and self.params["case"]["recovery_server_clumsy"]:
            self.sock.send("recovery_clumsy".encode("utf-8"))

        if self.is_multiconnection:
            self.sock.send(self.action.encode("utf-8"))

        video_full_path = os.path.join(self.video_path, self.video_name + ".mp4")
        time_flag_value = strftime("%H:%M:%S", gmtime(int(self.duration)))

        recorder = FFmpeg()
        self.logger.info("Start to record video")

        self.logger.info("-f gdigrab -video_size {resolution} -i desktop -f dshow -i audio=\"{audio_device_name}\" -t {time} -q:v 3 -pix_fmt yuv420p {video} -crf 32"
            .format(resolution=self.resolution, audio_device_name=self.audio_device_name, time=time_flag_value, video=video_full_path))

        recorder.options("-f gdigrab -video_size {resolution} -i desktop -f dshow -i audio=\"{audio_device_name}\" -t {time} -q:v 3 -pix_fmt yuv420p {video} -crf 32"
            .format(resolution=self.resolution, audio_device_name=self.audio_device_name, time=time_flag_value, video=video_full_path))

        self.logger.info("Finish to record video")

        check_artifacts_and_save_status(video_full_path, self.case_json_path, self.logger, obj_type="video")

    def analyze_result(self):
        if self.is_multiconnection:
            self.wait_server_answer(analyze_answer = True, abort_if_fail = True)


# [Client action] move mouse to the specified position
class Move(Action):
    def parse(self):
        parsed_arguments = parse_arguments(self.params["arguments_line"])
        self.x = parsed_arguments[0]
        self.y = parsed_arguments[1]

    def execute(self):
        self.logger.info("Move to x = {}, y = {}".format(self.x, self.y))
        pyautogui.moveTo(int(self.x), int(self.y))
        sleep(0.2)


# [Client action] do click on client side
class Click(Action):
    def execute(self):
        pyautogui.click()
        sleep(0.2)


# [Client action] execute sleep on client side
class DoSleep(Action):
    def parse(self):
        self.seconds = self.params["arguments_line"]

    def execute(self):
        sleep(int(self.seconds))


# [Client action] press some sequence of keys on client
class PressKeys(Action):
    def parse(self):
        parsed_arguments = parse_arguments(self.params["arguments_line"])
        self.keys_string = parsed_arguments[0]

    def execute(self):
        games_actions.press_keys(self.keys_string)


# [Client action] make sequence of screens with delay. It supports initial delay before the first test case
# Starts collecting of the traces if it's required
# This action triggers actions on server side in Multiconnection group
class SleepAndScreen(Action):
    def parse(self):
        self.action = self.params["action_line"]
        self.test_group = self.params["args"].test_group
        parsed_arguments = parse_arguments(self.params["arguments_line"])
        self.initial_delay = parsed_arguments[0]
        self.number_of_screens = parsed_arguments[1]
        self.delay = parsed_arguments[2]
        self.collect_traces = self.params["args"].collect_traces
        self.screen_path = self.params["screen_path"]
        self.screen_name = parsed_arguments[3]
        self.archive_path = self.params["archive_path"]
        self.archive_name = self.params["case"]["case"]
        self.collect_traces = self.params["args"].collect_traces
        self.current_image_num = self.params["current_image_num"]
        self.current_try = self.params["current_try"]
        self.client_type = self.params["client_type"]
        self.is_multiconnection = self.test_group in MC_CONFIG["android_client"] or self.test_group in MC_CONFIG["second_win_client"]
        self.case_json_path = self.params["case_json_path"]

    def execute(self):
        if "Encryption" in self.test_group:
            try:
                self.sock.send("encryption".encode("utf-8"))
                response = self.sock.recv(1024).decode("utf-8")
                self.logger.info("Server response for 'encryption' action: {}".format(response))

                compressing_thread = Thread(target=analyze_encryption, args=(self.params["case"], "client", self.params["transport_protocol"], \
                    "-encrypt" in self.params["case"]["server_keys"].lower(), self.params["messages"], self.params["args"].ip_address))
                compressing_thread.start()
            except Exception as e:
                self.logger.warning("Failed to validate encryption: {}".format(str(e)))
                self.logger.warning("Traceback: {}".format(traceback.format_exc()))

        if self.is_multiconnection:
            self.sock.send(self.action.encode("utf-8"))

        sleep(float(self.initial_delay))

        screen_number = 1

        while True:
            make_screen(self.screen_path, self.case_json_path, self.current_try, self.logger, self.screen_name + self.client_type, self.current_image_num)
            self.params["current_image_num"] += 1
            self.current_image_num = self.params["current_image_num"]
            screen_number += 1

            if screen_number > int(self.number_of_screens):
                break
            else:
                sleep(float(self.delay))

        if self.is_multiconnection:
            self.wait_server_answer(analyze_answer = True, abort_if_fail = True)

        try:
            self.sock.send("gpuview".encode("utf-8"))
            response = self.sock.recv(1024).decode("utf-8")
            self.logger.info("Server response for 'gpuview' action: {}".format(response))

            if self.collect_traces == "AfterTests":
                collect_traces(self.archive_path, self.archive_name + "_client.zip")
        except Exception as e:
            self.logger.warning("Failed to collect GPUView traces: {}".format(str(e)))
            self.logger.warning("Traceback: {}".format(traceback.format_exc()))


# [Client + Server action] record metrics on client and server sides
# [Result] wait answer from server. Answer must be 'done'
class RecordMetrics(Action):
    def parse(self):
        self.action = self.params["action_line"]

    def execute(self):
        if "used_memory" not in self.params["case"]:
            self.params["case"]["used_memory"] = []

        if self.params["args"].track_used_memory:
            track_used_memory(self.params["case"], "client")

        self.sock.send(self.action.encode("utf-8"))

    def analyze_result(self):
        self.wait_server_answer(analyze_answer = True, abort_if_fail = True)


def do_test_actions(game_name, logger):
    try:
        if game_name == "apexlegends":
            for i in range(40):
                pyautogui.press("q")
                sleep(1)

    except Exception as e:
        logger.error("Failed to do test actions: {}".format(str(e)))
        logger.error("Traceback: {}".format(traceback.format_exc()))


# [Client action] start doing test actions on client side
class StartTestActionsClient(Action):
    def parse(self):
        self.game_name = self.params["game_name"]

    def execute(self):
        gpu_view_thread = Thread(target=do_test_actions, args=(self.game_name.lower(), self.logger,))
        gpu_view_thread.daemon = True
        gpu_view_thread.start()


# [Client action] skip N next cases if the previous action was successfully done (e.g. skip actions to open game / benchmark if it's already opened)
class SkipIfDone(Action):
    def parse(self):
        self.commands_to_skip = self.params["arguments_line"]

    def execute(self):
        if self.state.prev_action_done:
            self.state.commands_to_skip += int(self.commands_to_skip)


# [Client + Server action] start Streaming SDK clients and server
# [Result] wait answer from server. Answer can be any
class StartStreaming(Action):
    def parse(self):
        self.action = self.params["action_line"]
        self.case = self.params["case"]
        self.args = self.params["args"]
        self.archive_path = self.params["archive_path"]
        self.archive_name = self.params["case"]["case"]
        self.script_path = self.params["script_path"]
        self.process = self.params["process"]
        self.game_name = self.params["game_name"]

    def execute(self):
        if self.args.streaming_type == StreamingType.AMD_LINK:
            self.sock.send(self.action.encode("utf-8"))

            should_collect_traces = (self.args.collect_traces == "BeforeTests")

            self.process = start_streaming(self.args, self.case, socket=self.sock)

            if should_collect_traces:
                collect_traces(self.archive_path, self.archive_name + "_client.zip")

            self.wait_server_answer(analyze_answer = True, abort_if_fail = True)
        else:
            if self.args.streaming_type == StreamingType.FULL_SAMPLES:
                self.sock.send(self.action.encode("utf-8"))

            # start client before server (default case)
            if "start_first" not in self.case or self.case["start_first"] != "server":
                if self.process is None:
                    should_collect_traces = (self.args.collect_traces == "BeforeTests")
                    pyautogui.moveTo(1, 1)
                    pyautogui.hotkey("win", "m")
                    self.process = start_streaming(self.args, self.case, script_path=self.script_path, socket=self.sock)

                    if should_collect_traces:
                        collect_traces(self.archive_path, self.archive_name + "_client.zip")
                    elif "start_first" in self.case and self.case["start_first"] == "client":
                        sleep(5)

            if self.args.streaming_type == StreamingType.SDK:
                self.sock.send(self.action.encode("utf-8"))

            self.wait_server_answer(analyze_answer = True, abort_if_fail = True)

            # start server before client
            if "start_first" not in self.case or self.case["start_first"] == "server":
                if self.process is None:
                    should_collect_traces = (self.args.collect_traces == "BeforeTests")
                    pyautogui.moveTo(1, 1)
                    pyautogui.hotkey("win", "m")
                    self.process = start_streaming(self.args, self.case, script_path=self.script_path, socket=self.sock)

                    if should_collect_traces:
                        collect_traces(self.archive_path, self.archive_name + "_client.zip")


# [Client + Server action] start benchmark/game if it isn't already opened
# [Result] wait answer from server. Answer must be 'done'
class OpenGame(Action):
    def parse(self):
        self.action = self.params["action_line"]

    def execute(self):
        self.sock.send(self.action.encode("utf-8"))
        self.wait_server_answer(analyze_answer = True, abort_if_fail = True)


# [Client + Server action] start Latency tool on client and server
class StartLatencyTool(Action):
    def parse(self):
        self.action = self.params["action_line"]
        self.args = self.params["args"]
        self.case = self.params["case"]
        self.tool_path = os.path.join(self.args.server_tool, "LatencyTestClient.exe")
        self.test_group = self.params["args"].test_group

    def execute(self):
        if "Latency" not in self.test_group:
            return

        self.process = start_latency_tool(self.args.execution_type, self.tool_path)

        self.sock.send(self.action.encode("utf-8"))

        self.wait_server_answer(analyze_answer = True, abort_if_fail = True)

        sleep(15)

        pyautogui.press("S")
