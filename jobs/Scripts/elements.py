import os


class ElementLocation:
    def __init__(self, location, element_name):
        self.location = location
        self.element_name = element_name

    def build_path(self):
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Elements", self.location, self.element_name) + ".png")


class GameElementLocation(ElementLocation):
    def __init__(self, game_name, element_name):
        super().__init__(os.path.join("Games", game_name), element_name)


class CSGOElementLocation(GameElementLocation):
    def __init__(self, element_name):
        super().__init__("CSGO", element_name)


class CSGOElements:
    PLAY_BUTTON = CSGOElementLocation("play_button")
    MODE_SELECTION = CSGOElementLocation("mode_selection")
    WORKSHOP_MAPS = CSGOElementLocation("workshop_maps")
    TRAINING_MAP = CSGOElementLocation("training_map")
    SELECT_MAP_BUTTON = CSGOElementLocation("select_map_button")
    GO_BUTTON = CSGOElementLocation("go_button")


class Dota2ElementLocation(GameElementLocation):
    def __init__(self, element_name):
        super().__init__("Dota2", element_name)


class Dota2Elements:
    ARCADE = Dota2ElementLocation("arcade")
    DEMO_HERO = Dota2ElementLocation("demo_hero")
    EXIT_BUTTON = Dota2ElementLocation("exit_button")
    FREE_SPELLS = Dota2ElementLocation("free_spells")
    HEROES = Dota2ElementLocation("heroes")
    LVL_MAX = Dota2ElementLocation("lvl_max")
    RENDER_API_SELECTION = Dota2ElementLocation("render_api_selection")
    RENDER_API_DX11_OPTION = Dota2ElementLocation("rendering_api_dx11_option")
    RENDER_API_VULKAN_OPTION = Dota2ElementLocation("rendering_api_vulkan_option")
    SETTINGS_BUTTON = Dota2ElementLocation("settings_button")
    VIDEO_TAB = Dota2ElementLocation("video_tab")
    YES_BUTTON = Dota2ElementLocation("yes_button")


class HeavenElementLocation(GameElementLocation):
    def __init__(self, element_name):
        super().__init__("Heaven", element_name)



class HeavenElements:
    API_LABEL = HeavenElementLocation("api_label")
    RUN_BUTTON = HeavenElementLocation("run_button")


class LoLElementLocation(GameElementLocation):
    def __init__(self, element_name):
        super().__init__("LoL", element_name)


class LoLElements:
    CONFIRM_BUTTON = LoLElementLocation("confirm_button")
    LOCK_IN_BUTTON = LoLElementLocation("lock_in_button")
    MALPHITE_ICON = LoLElementLocation("malphite_icon")
    PLAY_BUTTON = LoLElementLocation("play_button")
    PRACTICE_TOOL = LoLElementLocation("practice_tool")
    START_GAME = LoLElementLocation("start_game")
    START_GAME_ACTIVE = LoLElementLocation("start_game_active")
    TRAINING_BUTTON = LoLElementLocation("training_button")


class ValleyElementLocation(GameElementLocation):
    def __init__(self, element_name):
        super().__init__("Valley", element_name)


class ValleyElements:
    API_LABEL = ValleyElementLocation("api_label")
    RUN_BUTTON = ValleyElementLocation("run_button")


class IconElementLocation(ElementLocation):
    def __init__(self, element_name):
        super().__init__("Icons", element_name)


class IconElements:
    CSGO = IconElementLocation("CSGO")
    DOTA2 = IconElementLocation("Dota2")
    HEAVEN = IconElementLocation("Heaven")
    LATENCY_TOOL = IconElementLocation("LatencyTool")
    LOL = IconElementLocation("LoL")
    VALLEY = IconElementLocation("Valley")
    VALORANT = IconElementLocation("Valorant")


class AMDLinkElementLocation(ElementLocation):
    def __init__(self, element_name):
        super().__init__("AMDLink", element_name)


class AMDLinkElements:
    RESOLUTION_2K = ValorantElementLocation("2k")
    RESOLUTION_4K = ValorantElementLocation("4k")
    RESOLUTION_480P = ValorantElementLocation("480p")
    RESOLUTION_720P = ValorantElementLocation("720p")
    RESOLUTION_1080P = ValorantElementLocation("1080p")
    ACCEPT_ALL_CONNECTIONS = ValorantElementLocation("accept_all_connections")
    ADRENALIN_ICON = ValorantElementLocation("adrenalin_icon")
    AMD_LINK_ICON = ValorantElementLocation("amd_link_icon")
    AMD_LINK_SERVER = ValorantElementLocation("amd_link_server")
    AMD_LINK_STATUS = ValorantElementLocation("amd_link_status")
    APPLY_FULL_SCREEN = ValorantElementLocation("apply_full_screen")
    AVC = ValorantElementLocation("avc")
    CLOSE_INVITE_CODE_WINDOW = ValorantElementLocation("close_invite_code_window")
    CONNECT_TO_PC = ValorantElementLocation("connect_to_pc")
    COPY_TEXT = ValorantElementLocation("copy_text")
    DISABLED = ValorantElementLocation("disabled")
    DISCONNECT_BUTTON = ValorantElementLocation("disconnect_button")
    ENABLE_AMD_LINK = ValorantElementLocation("enable_amd_link")
    ENABLED = ValorantElementLocation("enabled")
    FULL_ACCESS = ValorantElementLocation("full_access")
    FULL_ACCESS_FRESH_LINK = ValorantElementLocation("full_access_fresh_link")
    HEVC = ValorantElementLocation("hevc")
    HOME_ACTIVE = ValorantElementLocation("home_active")
    LINK_GAME_INVITE_CLIENT = ValorantElementLocation("link_game_invite_client")
    LINK_GAME_INVITE_SERVER = ValorantElementLocation("link_game_invite_server")
    MULTI_PLAY = ValorantElementLocation("multi_play")
    MULTI_PLAY_FRESH_LINK = ValorantElementLocation("multi_play_fresh_link")
    PC_ICON = ValorantElementLocation("pc_icon")
    SKIP_OPTIMIZATION = ValorantElementLocation("skip_optimization")
    START_STREAMING = ValorantElementLocation("start_streaming")
    START_STREAMING_2 = ValorantElementLocation("start_streaming_2")
    START_STREAMING_BUTTON = ValorantElementLocation("start_streaming_button")
    STOP_STREAMING_BUTTON = ValorantElementLocation("stop_streaming_button")
    STREAM_RESOLUTION = ValorantElementLocation("stream_resolution")
    SUBMIT_CONNECT = ValorantElementLocation("submit_connect")
    USE_ENCRYPTION = ValorantElementLocation("use_encryption")
    VIDEO_ENCODING_TYPE = ValorantElementLocation("video_encoding_type")

    DROPDOWN_OPTIONS_LABELS = {
        "stream_resolution": AMDLinkElementLocation.STREAM_RESOLUTION,
        "video_encoding_type": AMDLinkElementLocation.VIDEO_ENCODING_TYPE,
        "amd_link_server": AMDLinkElementLocation.AMD_LINK_SERVER,
        "accept_all_connections": AMDLinkElementLocation.ACCEPT_ALL_CONNECTIONS,
        "use_encryption": AMDLinkElementLocation.USE_ENCRYPTION
    }

    DROPDOWN_OPTIONS_VALUES = {
        "stream_resolution": {
            "2k": AMDLinkElementLocation.RESOLUTION_2K,
            "4k": AMDLinkElementLocation.RESOLUTION_4K,
            "480p": AMDLinkElementLocation.RESOLUTION_480P,
            "720p": AMDLinkElementLocation.RESOLUTION_720P,
            "1080p": AMDLinkElementLocation.RESOLUTION_1080P
        },

        "video_encoding_type": {
            "avc": AMDLinkElementLocation.AVC,
            "hevc": AMDLinkElementLocation.HEVC
        }
    }
