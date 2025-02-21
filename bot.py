# bot.py

import asyncio
import os
import logging
import json
from dotenv import load_dotenv
from typing import Optional

from api_client import APIClient

logging.basicConfig(level=logging.INFO)

class Config:
    """
    Kapselt die wichtigsten Konfigurationswerte und lädt
    die Sprachinhalte aus 'language.json'.
    """
    def __init__(self):
        # Lädt Umgebungsvariablen aus .env
        load_dotenv()

        # Basis-Einstellungen
        self.API_TOKEN = os.getenv('API_TOKEN')
        self.API_BASE_URL = os.getenv('API_BASE_URL')
        self.SLEEPTIMER = int(os.getenv('SLEEPTIMER', '2'))      # in Minuten
        self.TARGET_TIME = int(os.getenv('TARGET_TIME', '10'))   # Wann Nachrichten gesendet werden
        self.START_TIME = int(os.getenv('START_TIME', '90'))     # Ab wann das Spiel als "gestartet" gilt

        # Rollen (Standard-Officer etc., kann in der .env angepasst werden)
        roles_env = os.getenv('TARGET_ROLES', 'officer,armycommander,spotter,tankcommander')
        self.TARGET_ROLES = [r.strip().lower() for r in roles_env.split(',')]

        # Eigene Sprachvariable BOT_LANG statt systemweiter LANG
        # Fallback auf "en", falls BOT_LANG nicht gesetzt
        raw_lang = os.getenv('BOT_LANG', 'en')
        self.LANGUAGE = self._extract_lang_code(raw_lang)

        # language.json laden (inkl. Fallback auf 'en', falls unbekannter Code)
        self.lang_data = self._load_language_json()
        # Alle Strings für Logs, Meldungen etc.
        self.lang_strings = self.lang_data.get("strings", {})
        # Eigentlicher Nachrichten-Text an die Spieler
        self.MESSAGE_CONTENT = self.lang_data.get("message_content", "Default message")

    def _extract_lang_code(self, lang_str: str) -> str:
        """
        Extrahiert den ISO-Sprachcode (z.B. 'en', 'de') aus einer
        Variable wie 'en_US.utf-8' oder 'de_DE'.
        Fällt zurück auf 'en', wenn nichts Passendes gefunden wird.
        """
        if not lang_str:
            return 'en'
        lang_str = lang_str.lower()

        # Bei Unterstrich, Punkt oder Bindestrich splitten
        if '_' in lang_str:
            lang_str = lang_str.split('_')[0]
        elif '.' in lang_str:
            lang_str = lang_str.split('.')[0]
        elif '-' in lang_str:
            lang_str = lang_str.split('-')[0]

        if not lang_str:
            return 'en'
        return lang_str

    def _load_language_json(self) -> dict:
        """
        Lädt aus language.json den passenden Inhalt für self.LANGUAGE.
        Fällt auf Englisch ('en') zurück, wenn der Eintrag nicht gefunden wird.
        """
        try:
            with open("language.json", "r", encoding="utf-8") as f:
                all_langs = json.load(f)
        except Exception as e:
            logging.error(f"Fehler beim Lesen von language.json: {e}")
            return {
                "message_content": "Default message (language.json not found).",
                "strings": {}
            }

        if self.LANGUAGE in all_langs:
            return {
                "message_content": all_langs[self.LANGUAGE].get("message_content", "Default message"),
                "strings": all_langs[self.LANGUAGE]
            }
        else:
            # Fallback auf 'en'
            fallback_str = all_langs.get("en", {}).get("log_fallback_lang", "Fallback to en.")
            logging.warning(fallback_str.format(lang=self.LANGUAGE))
            return {
                "message_content": all_langs.get("en", {}).get("message_content", "Default message"),
                "strings": all_langs.get("en", {})
            }

def parse_time_remaining(raw_time: str, lang_strings: dict) -> Optional[int]:
    """
    Parst eine Zeitangabe im Format 'H:MM:SS' und gibt
    die Gesamtzahl der verbleibenden Sekunden zurück.
    Gibt None zurück, wenn die Zeit '0:00:00' ist oder das Format ungültig.
    """
    if not raw_time or raw_time == "0:00:00":
        return None
    try:
        hours, minutes, seconds = map(int, raw_time.split(':'))
        return hours * 3600 + minutes * 60 + seconds
    except ValueError:
        logging.error(lang_strings.get("log_time_format_error", "Unexpected time format").format(raw_time=raw_time))
        return None

async def get_time_remaining(api_client: APIClient, lang_strings: dict) -> Optional[int]:
    """
    Ruft den Gamestate ab und extrahiert die verbleibende Zeit in Sekunden.
    Gibt None zurück, wenn kein gültiger Gamestate vorliegt.
    """
    gamestate = await api_client.get_gamestate()
    if gamestate and 'result' in gamestate:
        raw_time = gamestate['result'].get('raw_time_remaining')
        return parse_time_remaining(raw_time, lang_strings)
    else:
        logging.error(lang_strings.get("log_get_gamestate_error", "No 'result' key in gamestate."))
        return None

async def notify_roles(api_client: APIClient, config: Config):
    """
    Sendet Nachrichten an alle Spieler, deren Rolle in config.TARGET_ROLES enthalten ist.
    Nutzt asyncio.gather, um die Requests asynchron (parallel) abzuschicken.
    """
    strings = config.lang_strings
    players_data = await api_client.get_detailed_players()

    if not players_data or 'result' not in players_data:
        logging.error(strings.get("log_player_list_error", "Error updating player list."))
        return

    players = players_data['result'].get('players', {})
    if not players:
        logging.error(strings.get("log_no_players_found", "No players found."))
        return

    tasks = []
    for _, player_info in players.items():
        role = player_info.get('role', '').lower()
        if role in config.TARGET_ROLES:
            p_id = player_info.get('player_id')
            p_name = player_info.get('name')
            if p_id and p_name:
                tasks.append(api_client.do_message_player(p_name, p_id, config.MESSAGE_CONTENT))
                logging.info(strings.get("log_messages_in_queue", "Message in queue.").format(
                    player_name=p_name, role=role
                ))

    if tasks:
        # Nachrichten an alle relevanten Spieler versenden
        await asyncio.gather(*tasks, return_exceptions=True)
        logging.info(strings.get("log_messages_sent_gather", "Messages sent."))
    else:
        logging.info(strings.get("log_no_roles_found", "No messages sent."))

async def send_notifications(config: Config):
    """
    Hauptfunktion, die den Ablauf steuert:
      - In einer Schleife den Gamestate abfragen
      - Prüfen, ob die Zeit für Nachrichten erreicht ist
      - Nachrichten verschicken
      - Warten, dann Schleife neu
    """
    api_client = APIClient(config.API_BASE_URL, config.API_TOKEN)
    await api_client.create_session()

    strings = config.lang_strings

    try:
        while True:
            time_remaining = await get_time_remaining(api_client, strings)

            if time_remaining is None:
                logging.info(strings.get("log_game_not_running", "Game not running."))
                await asyncio.sleep(config.SLEEPTIMER * 60)
                continue

            if time_remaining < (config.START_TIME - config.TARGET_TIME) * 60:
                minutes_left = time_remaining // 60
                seconds_left = time_remaining % 60
                logging.info(strings.get("log_game_time_remaining", "").format(
                    minutes=minutes_left,
                    seconds=seconds_left
                ))
                await asyncio.sleep(config.SLEEPTIMER * 60)
            else:
                # Warte, bis (START_TIME - TARGET_TIME) * 60 Sekunden erreicht ist
                wait_time = time_remaining - (config.START_TIME - config.TARGET_TIME) * 60
                logging.info(strings.get("log_game_started_waiting", "").format(wait_time=wait_time))
                await asyncio.sleep(wait_time)

                logging.info(strings.get("log_messages_sending_now", "Sending messages now!"))
                await notify_roles(api_client, config)

                logging.info(strings.get("log_run_until_next_cycle", "Will loop again soon."))
                await asyncio.sleep(config.SLEEPTIMER * 60)

    except asyncio.CancelledError:
        logging.info(strings.get("log_cancelled_error", "Async task cancelled."))
        raise
    finally:
        await api_client.close_session()
        logging.info(strings.get("log_client_session_closed", "ClientSession closed."))

def main():
    config = Config()
    strings = config.lang_strings

    try:
        asyncio.run(send_notifications(config))
    except KeyboardInterrupt:
        logging.info(strings.get("log_keyboard_interrupt", "KeyboardInterrupt detected. Shutting down."))
    except Exception as e:
        logging.exception(strings.get("log_unexpected_error", "Unexpected error").format(error=e))

if __name__ == "__main__":
    main()
