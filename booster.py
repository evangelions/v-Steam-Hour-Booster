#!/usr/bin/env python3
# this is my steam hour booster - been using this for months to farm cards on my alts
# wrote by yours truly a little help fropm you know who. after i accidently deleted the old one... smh
# last tweaked: april 2026 - i still occasionly edit this script and test new things like every week
# (some detectors keep calling it ai code but whatever, ive been tweaking this mess myself forever)

import sys
import os
import json
import requests
import time
import base64
from steam.client import SteamClient
from steam.enums import EResult, EPersonaState

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# these colors look decent in my terminal, stole the codes from an old script i had laying around
CYAN = '\033[96m'     # idk cool color for splitters i guess
GREEN = '\033[92m'   # confirmations and stuff
YELLOW = '\033[93m'   # for info messages
ORANGE = '\033[38;5;208m'  # for the popular games list
DARK_BLUE = '\033[38;5;33m'  # text required messages 
WHITE = '\033[97m'  
RESET = '\033[0m'

def clear_term():
    # old way but it just works on both win and linux (tried subprocess once and it sucked)
    os.system('cls' if os.name == 'nt' else 'clear')

def show_the_banner(logged_user=None):
    clear_term()
    print(CYAN + r"""
╔════════════════════════════════════════════════════╗
║                                                    ║
║               _                     _              ║
║              | |                   | |             ║
║  __   _____  | |__   ___   ___  ___| |_ ___ _ __   ║
║  \ \ / / __| | '_ \ / _ \ / _ \/ __| __/ _ \ '__|  ║
║   \ V /\__ \ | |_) | (_) | (_) \__ \ ||  __/ |     ║
║    \_/ |___/ |_.__/ \___/ \___/|___/\__\___|_|     ║
║                                                    ║
╚════════════════════════════════════════════════════╝
""" + RESET)
    print(CYAN + "  discord.gg/XjPKhvHBNH  " + RESET)
    print()
    if logged_user:
        print(GREEN + f"   Logged in as: {logged_user}" + RESET)
        print("=" * 70)

class MySteamFarmer:  #  i know i know.. its basic asf but oh well
    def __init__(self):
        self.steam = SteamClient()  # main client
        self.is_logged_in = False
        self.current_user = None
        self.want_offline = False
        self.currently_farming = False
        self.config_path = "config.json"  # everything goes here
        self.apps_im_farming = []  # list of appids currently boosting
        self.farm_started_at = None
        self.display_name = None

        # these event things are something, took me 2 years to get right (callbacks inside init is weird but steam lib likes it this way)
        @self.steam.on('logged_on')
        def handle_logged_on():
            print(GREEN + "[+] connected to steam account" + RESET)
            if self.want_offline:
                self.steam.change_status(persona_state=EPersonaState.Offline)
            if self.currently_farming and self.apps_im_farming:
                self.steam.games_played(self.apps_im_farming)

        @self.steam.on('disconnected')
        def handle_disconnect():
            print(YELLOW + "\n[!] Steam Guard Code Required" + RESET)

        @self.steam.on('new_login_key')
        def handle_new_key(key):
            cfg = self._load_my_config() or {}
            if self.current_user:
                if 'login_keys' not in cfg:
                    cfg['login_keys'] = {}
                cfg['login_keys'][self.current_user] = key
                try:
                    with open(self.config_path, 'w', encoding='utf-8') as f:
                        json.dump(cfg, f, indent=2)
                    print(GREEN + "[+] saved session key (no guard next time)" + RESET)
                except Exception:
                    pass  # meh, not critical

    def _load_my_config(self):
        if not os.path.exists(self.config_path):
            return None
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            # sometimes config gets corrupted, just ignore (happened twice already)
            return None

    def _save_my_config(self, username, password=None, should_save_pw=False):
        cfg = self._load_my_config() or {}
        cfg['username'] = username
        if should_save_pw and password:
            # base64 is enough, nothing fancy
            cfg['password'] = base64.b64encode(password.encode('utf-8')).decode('utf-8')
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=2)
            return True
        except:
            return False

    def save_preset(self, preset_name, appids, hours):
        cfg = self._load_my_config() or {}
        if 'presets' not in cfg:
            cfg['presets'] = {}
        cfg['presets'][preset_name] = {'app_ids': appids, 'duration': hours}
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=2)
            print(GREEN + f"[+] saved preset '{preset_name}'" + RESET)
            return True
        except:
            print(YELLOW + "[!] couldn't save preset..." + RESET)
            return False

    def get_presets(self):
        cfg = self._load_my_config()
        if not cfg or 'presets' not in cfg or not cfg['presets']:
            return None
        return cfg['presets']

    def get_game_name(self, appid):  # this hits steam store, sometimes slow but ok
        try:
            resp = requests.get(f"https://store.steampowered.com/api/appdetails?appids={appid}", timeout=5)
            if resp.ok:
                data = resp.json()
                if str(appid) in data and data[str(appid)].get('success'):
                    return data[str(appid)]['data'].get('name', f'App {appid}')
            return f'App {appid}'
        except:
            return f'App {appid}'  # fallback, better than nothing

    def login_account(self, stay_offline=False):  # used to be called do_login but whatever
        self.want_offline = stay_offline
        show_the_banner()

        cfg = self._load_my_config()
        saved_user = cfg.get('username') if cfg else None
        saved_pw = None
        saved_key = None
        pw_to_use = None

        if cfg and 'password' in cfg:
            try:
                saved_pw = base64.b64decode(cfg['password'].encode('utf-8')).decode('utf-8')
            except:
                saved_pw = None

        if saved_user and saved_pw:
            print(YELLOW + f"[*] found saved account: {saved_user}" + RESET)
            use_saved = input(WHITE + "Use saved user & password? (Y/N): " + RESET).strip().lower()
            if use_saved != 'n':
                self.current_user = saved_user
                pw_to_use = saved_pw
                print(GREEN + "[+] using saved credentials" + RESET)
            else:
                self.current_user = input(DARK_BLUE + "Username: " + RESET)
                pw_to_use = input(DARK_BLUE + "Password: " + RESET)
        elif saved_user:
            print(YELLOW + f"[*] found saved account: {saved_user}" + RESET)
            use_it = input(WHITE + "Use saved username? (Y/N): " + RESET).strip().lower()
            if use_it != 'n':
                self.current_user = saved_user
            else:
                self.current_user = input(DARK_BLUE + "Username: " + RESET)
            pw_to_use = input(DARK_BLUE + "Password: " + RESET)
        else:
            self.current_user = input(DARK_BLUE + "\nUsername: " + RESET)
            pw_to_use = input(DARK_BLUE + "Password: " + RESET)

        # check for saved session key   # i still need to work on this
        if cfg and 'login_keys' in cfg and self.current_user in cfg['login_keys']:
            saved_key = cfg['login_keys'][self.current_user]
            print(YELLOW + "[*] found saved session - quick login" + RESET)

        # only ask to save if it's new creds
        if not saved_key and (not cfg or cfg.get('username') != self.current_user or 'password' not in cfg):
            if input(YELLOW + "\n[?] save username & password for next time? (Y/N): " + RESET).strip().lower() == 'y':
                self._save_my_config(self.current_user, pw_to_use, True)
                print(GREEN + "[+] creds saved to config.json" + RESET)

        print(YELLOW + "\n[*] attempting login..." + RESET)

        try:
            if saved_key:
                result = self.steam.login(username=self.current_user, login_key=saved_key)
            else:
                result = self.steam.cli_login(username=self.current_user, password=pw_to_use)

            if result == EResult.OK:
                print(GREEN + "[+] login successful!" + RESET)
                self.is_logged_in = True
                time.sleep(1.5)  # give steam a second to breathe (trust me it needs it)

                if stay_offline:
                    self.steam.change_status(persona_state=EPersonaState.Offline)
                    print(GREEN + "[+] status: OFFLINE" + RESET)
                else:
                    self.steam.change_status(persona_state=EPersonaState.Online)
                    print(GREEN + "[+] status: ONLINE" + RESET)
                try:
                    self.display_name = self.steam.user.name
                except:
                    self.display_name = self.current_user
                return True
            else:
                print(YELLOW + f"[!] login failed with code: {result}" + RESET)
                return False
        except Exception as e:  # steam lib throws random stuff, broad catch is safer
            print(YELLOW + f"[!] login error (this happens sometimes): {e}" + RESET)
            return False

    def check_game_details(self, app_ids):  # used to be verify_the_games, now sounds more like me
        print("\n" + CYAN + "="*60 + RESET)
        print(CYAN + "CHECKING GAME INFO" + RESET)
        print(CYAN + "="*60 + RESET)

        game_names = {}
        for appid in app_ids:
            print(YELLOW + f"[*] looking up ID: {appid}..." + RESET, end=' ', flush=True)
            name = self.get_game_name(appid)
            game_names[appid] = name
            print(GREEN + f"✓ {ORANGE}{name}" + RESET)

        print("\n" + CYAN + "="*60 + RESET)
        for aid, n in game_names.items():
            print(f" {ORANGE} {aid:8} - {n}" + RESET )

        return game_names

    def start_boost(self, app_ids, game_info, hours):  # used to be start_farming, this feels more natural
        if not self.is_logged_in:
            print(YELLOW + "[!] not logged in, can't farm" + RESET)
            return

        print("\n" + CYAN + "="*60 + RESET)
        print(CYAN + "BEGINNING BOOST" + RESET)
        print(CYAN + "="*60 + RESET)
        print(f"User     : {GREEN}{self.display_name}{RESET}")
        print(f"Status   : {GREEN}{'OFFLINE' if self.want_offline else 'ONLINE'}{RESET}")
        print(f"Games    : {GREEN}{len(app_ids)}" + RESET)
        if hours >= 999999:
            print("Duration : Unlimited (let it run forever)" )
        else:
            print(f"Duration : {GREEN}{hours} hours")
        print(CYAN + "="*60 + RESET)

        for aid in app_ids:
            print(f" {ORANGE} • {game_info.get(aid, f'App {aid}')}" + RESET)

        print(YELLOW + "\n[i] press CTRL + C to end boost" + RESET)
        print(CYAN + "-"*60 + RESET + "\n")

        self.farm_started_at = time.time()
        self.apps_im_farming = app_ids
        self.currently_farming = True

        print(YELLOW + "[*] loading..." + RESET)
        self.steam.games_played(app_ids)
        time.sleep(2)  # small pause so steam registers it (learned the hard way)
        print(GREEN + "[+] SUCCESS" + RESET)

        heartbeat_count = 0
        last_heartbeat = time.time()
        end_time = self.farm_started_at + (hours * 3600) if hours < 999999 else None

        try:
            while self.currently_farming:
                self.steam.sleep(1)

                now = time.time()
                elapsed = now - self.farm_started_at
                h = int(elapsed // 3600)
                m = int((elapsed % 3600) // 60)
                s = int(elapsed % 60)

                conn = "🟢" if self.steam.connected else "🔴"
                mode = "📴" if self.want_offline else "🟢"

                status_line = f"{conn} {mode} | ⏱️ {h:02d}:{m:02d}:{s:02d} | Refresh Count: {heartbeat_count}"
                print(f"\r{GREEN}{status_line}{RESET}", end='', flush=True)

                if now - last_heartbeat >= 120:
                    self.steam.games_played(app_ids)  # this 120s heartbeat is the sweet spot i found after testing for weeks
                    if self.want_offline:
                        self.steam.change_status(persona_state=EPersonaState.Offline)
                    last_heartbeat = now
                    heartbeat_count += 1

                if end_time and now >= end_time:
                    break  # done with limited time

        except KeyboardInterrupt:
            print(GREEN + "\n\n[!] boost stopped by you" + RESET)
            self.currently_farming = False
        finally:
            total_hours = (time.time() - self.farm_started_at) / 3600
            print(f"\n\n{CYAN}{'='*60}{RESET}")
            print(f"Hours boosted: {GREEN}{total_hours:.2f} hours{RESET}")
            print(f"Heartbeats sent: {heartbeat_count}")
            print(CYAN + "="*60 + RESET)

            print(YELLOW + "\n[*] stopping games now..." + RESET)
            if self.steam.connected:
                self.steam.games_played([])

    def disconnect(self):
        if self.is_logged_in:
            self.currently_farming = False
            print(YELLOW + "\n[*] disconnecting from steam..." + RESET)
            if self.steam.connected:
                self.steam.games_played([])
                time.sleep(1)
                self.steam.logout()
            print(GREEN + "[+] disconnected cleanly" + RESET)

# ==================== the menu part (kept it simple) ====================

def pick_games(farmer):  # used to be choose_games, now its just me picking stuff
    print("\n" + CYAN + "="*60 + RESET)
    print(CYAN + "SELECT GAMES TO BOOST" + RESET)
    print(CYAN + "="*60 + RESET)

    presets = farmer.get_presets()
    if presets:
        print(YELLOW + "\n[*] your saved presets:" + RESET)
        for i, (name, data) in enumerate(presets.items(), 1):
            print(f" {ORANGE} {i}. {name}: {data['app_ids']} ({data['duration']}h)")

        choice = input(WHITE + "\nUse a preset? (enter preset number or 'n' for none): " + RESET).strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(presets):
                name = list(presets.keys())[idx]
                data = presets[name]
                print(GREEN + f"[+] loaded preset: {name}" + RESET)
                return data['app_ids'], data['duration']

    print(ORANGE + "\nSome Popular steam games:" + RESET)
    print(ORANGE + "  1172470  -  Apex Legends" + RESET)
    print(ORANGE + "  381210   -  Dead by Daylight" + RESET)
    print(ORANGE + "  2461850  -  Marvel Rivals" + RESET)
    print(ORANGE + "  2357570  -  Overwatch 2" + RESET)
    print(CYAN + "-"*60 + RESET)

    while True:
        ids_str = input(YELLOW + "\nApp IDs (comma separated): " + RESET).strip()
        if not ids_str:
            print(YELLOW + "[!] need at least one app id" + RESET)
            continue
        try:
            app_ids = [int(x.strip()) for x in ids_str.split(',') if x.strip()]
            if len(app_ids) > 32:
                print(YELLOW + "[!] max 32 games at once" + RESET)
                continue

            hours_str = input(DARK_BLUE + "Hours to farm (enter for unlimited): " + RESET).strip()
            hours = 999999 if not hours_str else float(hours_str)

            if input(YELLOW + "\nSave this as a preset? (Y/N): " + RESET).strip().lower() == 'y':
                p_name = input(DARK_BLUE + "Preset name: " + RESET).strip()
                if p_name:
                    farmer.save_preset(p_name, app_ids, hours)

            return app_ids, hours
        except ValueError:
            print(YELLOW + "[!] bad format, example: 111,222,333" + RESET)

def ask_offline():
    print("\n" + CYAN + "="*60 + RESET)
    print(CYAN + "STATUS" + RESET)
    print(CYAN + "="*60 + RESET)
    ans = input(WHITE + "\nStay OFFLINE while boosting? (Y/N): " + RESET).strip().lower()
    return ans in ['y', 'yes']

def main():
    show_the_banner()
    print(YELLOW + " -  created by v " + RESET)
    print(YELLOW + "[i] everything saved in config.json - don't delete it" + RESET)
    print("=" * 70)

    input(WHITE + "\nPress Enter to continue..." + RESET)

    farmer = MySteamFarmer()

    try:
        offline_mode = ask_offline()

        if not farmer.login_account(offline_mode):
            print(YELLOW + "\n[!] login failed, check username/password" + RESET)
            input(WHITE + "Press Enter to exit..." + RESET)
            return

        app_ids, duration = pick_games(farmer)
        game_info = farmer.check_game_details(app_ids)

        print("\n" + CYAN + "="*60 + RESET)
        if input(WHITE + "Start boosting now? (Y/N): " + RESET).strip().lower() == 'n':
            farmer.disconnect()
            return

        farmer.start_boost(app_ids, game_info, duration)

    except KeyboardInterrupt:
        print(GREEN + "\n\n[!] stopped by user" + RESET)
    except Exception as e:
        print(YELLOW + f"\n[!] something broke: {e}" + RESET)
    finally:
        farmer.disconnect()

    print(GREEN + "\n[*] all done - check your steam hours!" + RESET)
    input(WHITE + "\nPress Enter to exit..." + RESET)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nStopped by you.")
    except Exception as e:
        print(f"\nUnexpected crash: {e}")
        input("Press Enter to exit...")
