import aiohttp
import logging

class APIClient:
    def __init__(self, base_url, api_token):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_token}"}
        self.session = None

    async def create_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)

    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def login(self, username, password):
        await self.create_session()
        url = f'{self.base_url}/api/login'
        data = {'username': username, 'password': password}
        async with self.session.post(url, json=data) as response:
            if response.status != 200:
                text = await response.text()
                logging.error(f"Fehler beim Login: {response.status}, Antwort: {text}")
                return False
            return True

    async def get_players_fast(self):
        url = f'{self.base_url}/api/get_players_fast'
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logging.error(f"Error fetching fast players data: {e}")
            return None

    async def do_message_player(self, player_name, player_id, message):
        url = f'{self.base_url}/api/message_player'
        data = {
            "player_name": player_name,
            "player_id": player_id,
            "message": message
        }
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.post(url, json=data) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logging.error(f"Error sending message to player {player}: {e}")
            return None

    async def get_detailed_players(self):
        url = f'{self.base_url}/api/get_detailed_players'
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logging.error(f"Error fetching detailed players data: {e}")
            return None
            
    async def get_gamestate(self):
        url = f'{self.base_url}/api/get_gamestate'
        try:
            await self.create_session()
            async with self.session.get(url) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logging.error(f"Error fetching gamestate: {e}")
            return None
            
