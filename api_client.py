import aiohttp
import logging

class APIClient:
    """
    Ein asynchroner Client für API-Aufrufe.
    Nutzt eine einzige aiohttp.ClientSession pro Instanz,
    die über create_session() gestartet und über close_session() 
    wieder geschlossen wird.
    """
    def __init__(self, base_url, api_token):
        self.base_url = base_url
        self.api_token = api_token
        self.headers = {"Authorization": f"Bearer {api_token}"}
        self.session = None

    async def create_session(self):
        """
        Erstellt eine aiohttp.ClientSession, falls nicht bereits vorhanden.
        """
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)

    async def close_session(self):
        """
        Schließt die aiohttp.ClientSession, falls vorhanden.
        """
        if self.session:
            await self.session.close()
            self.session = None

    async def get_gamestate(self):
        """
        Ruft den aktuellen Gamestate (Zeit etc.) ab.
        """
        await self.create_session()
        url = f"{self.base_url}/api/get_gamestate"
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logging.error(f"Error fetching gamestate: {e}")
            return None

    async def get_players_fast(self):
        """
        Beispielmethode zum schnellen Abruf einer Spielerliste.
        """
        await self.create_session()
        url = f"{self.base_url}/api/get_players_fast"
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logging.error(f"Error fetching fast players data: {e}")
            return None

    async def get_detailed_players(self):
        """
        Detaillierte Infos zu allen Spielern abfragen.
        """
        await self.create_session()
        url = f"{self.base_url}/api/get_detailed_players"
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logging.error(f"Error fetching detailed players data: {e}")
            return None

    async def do_message_player(self, player_name, player_id, message):
        """
        Sendet eine Nachricht an einen bestimmten Spieler (player_id).
        """
        await self.create_session()
        url = f"{self.base_url}/api/message_player"
        data = {
            "player_name": player_name,
            "player_id": player_id,
            "message": message
        }
        try:
            async with self.session.post(url, json=data) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logging.error(f"Fehler beim Senden der Nachricht an {player_name}: {e}")
            return None
