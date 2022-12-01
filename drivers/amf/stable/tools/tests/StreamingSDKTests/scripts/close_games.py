import argparse
import subprocess
import platform


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--game_name', required=True)

    args = parser.parse_args()

    if args.game_name == "LoL":
        subprocess.call("taskkill /f /im \"LeagueClient.exe\"", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        subprocess.call("taskkill /f /im \"League of Legends.exe\"", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    elif args.game_name == "HeavenDX9" or args.game_name == "HeavenDX11" or args.game_name == "HeavenOpenGL":
        if platform.system() == "Windows":
            subprocess.call("taskkill /f /im \"browser_x86.exe\"", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
            subprocess.call("taskkill /f /im \"Heaven.exe\"", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        else:
            subprocess.call("pkill \"browser_x64\"", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
            subprocess.call("pkill \"heaven_x64\"", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    elif args.game_name == "ValleyDX9" or args.game_name == "ValleyDX11" or args.game_name == "ValleyOpenGL":
        if platform.system() == "Windows":
            subprocess.call("taskkill /f /im \"browser_x86.exe\"", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
            subprocess.call("taskkill /f /im \"Valley.exe\"", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        else:
            subprocess.call("pkill \"browser_x64\"", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
            subprocess.call("pkill \"valley_x64\"", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    elif args.game_name == "Dota2DX11" or args.game_name == "Dota2Vulkan":
        subprocess.call("taskkill /f /im \"dota2.exe\"", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    elif args.game_name == "CSGO":
        subprocess.call("taskkill /f /im \"csgo.exe\"", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    elif args.game_name == "PUBG":
        subprocess.call("taskkill /f /im \"TslGame.exe\"", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
