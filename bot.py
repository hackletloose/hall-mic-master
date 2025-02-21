import asyncio
import os
from api_client import APIClient
from dotenv import load_dotenv
import logging

load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')
API_BASE_URL = os.getenv('API_BASE_URL')
SLEEPTIMER = int(os.getenv('SLEEPTIMER', '2'))
TARGET_ROLES = ['officer', 'armycommander', 'spotter', 'tankcommander']
MESSAGE_CONTENT = os.getenv('MESSAGE_CONTENT')
TARGET_TIME = int(os.getenv('TARGET_TIME', '10'))
START_TIME = int(os.getenv('START_TIME', '90'))

async def zeit_holen(api_client):
    gamestate = await api_client.get_gamestate()
    if gamestate and 'result' in gamestate:
        raw_time_remaining = gamestate['result']['raw_time_remaining']
        if raw_time_remaining == "0:00:00":
            return None
        global hours, minutes, seconds
        hours, minutes, seconds = map(int, raw_time_remaining.split(':'))
        total_seconds = hours * 3600 + minutes * 60 + seconds
        return total_seconds
    else:
        logging.error("ERROR getting current gamestate")
        return None

async def send_notifications():
    api_client = APIClient(API_BASE_URL, API_TOKEN)
    messages_sent = False
    
    try:
        while True:
            time_remaining = await zeit_holen(api_client)
            if time_remaining is None:
                print("Spiel läuft nicht, es werden keine Nachrichten gesendet.")
                messages_sent = False
                await asyncio.sleep(SLEEPTIMER * 60)
                continue
            if time_remaining < (START_TIME - TARGET_TIME) * 60:
                    messages_sent = False
                    time_remaining_min = time_remaining / 60
                    print(f"Spiel läuft noch {hours}:{minutes}:{seconds}. Dementsprechend wird keine Nachricht versendet.")
                    await asyncio.sleep(SLEEPTIMER * 60)
            else:
                wait_time = time_remaining - (START_TIME - TARGET_TIME) * 60
                print(f"Spiel gestartet: Warte {wait_time} Sekunden bis zur Nachrichtenzustellung.")
                await asyncio.sleep(wait_time)
                print("Nachrichten werden gesendet!")
                await notify_roles(api_client)
                messages_sent = True
        else:
            await asyncio.sleep(SLEEPTIMER * 60)
    finally:
        await api_client.close_session()

async def notify_roles(api_client):
    players_data = await api_client.get_detailed_players()

    if players_data and 'result' in players_data:
        for player_id, player_info in players_data['result']['players'].items():
            role = player_info.get('role', '').lower()
            if role in TARGET_ROLES:
                player_id = player_info.get('player_id')
                player_name = player_info.get('name')
                await api_client.do_message_player(player_name, player_id, MESSAGE_CONTENT)
                print(f"Nachricht gesendet an {player_name} | (Rolle: {role})")
    else:
        print("FEHLER beim Aktualisieren der Spielerliste. Kein Spieler gefunden.")

if __name__ == "__main__":
    asyncio.run(send_notifications())
