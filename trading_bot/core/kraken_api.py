import aiohttp
import hashlib
import hmac
import base64
import urllib.parse
import time
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

class KrakenREST:
    def __init__(self, api_key, api_secret, base_url):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url

    def _get_signature(self, urlpath, data, nonce):
        postdata = urllib.parse.urlencode(data)
        encoded = (str(nonce) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()
        mac = hmac.new(base64.b64decode(self.api_secret), message, hashlib.sha512)
        return base64.b64encode(mac.digest()).decode()

    async def _request(self, method, endpoint, data=None, is_private=True):
        if data is None: data = {}
        
        headers = {}
        if is_private:
            path = f"/0/private/{endpoint}"
            # If private endpoint, add auth
            if self.api_key and self.api_secret:
                nonce = str(int(time.time() * 1000))
                data['nonce'] = nonce
                headers['API-Key'] = self.api_key
                headers['API-Sign'] = self._get_signature(path, data, nonce)
        else:
            path = f"/0/public/{endpoint}"
        
        url = f"{self.base_url}{path}"
        
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, data=data, headers=headers) as resp:
                response = await resp.json()
                if response.get('error'):
                    # Kraken returns errors as a list, e.g., ['EQuery:Unknown asset pair']
                    raise Exception(f"Kraken API Error: {response['error']}")
                return response['result']

    async def get_ohlc(self, pair, interval=1):
        """
        Public Endpoint: Get OHLC data
        interval: 1, 5, 15, 30, 60, 240, 1440, 10080, 21600
        """
        data = {
            "pair": pair,
            "interval": interval
        }
        return await self._request("GET", "OHLC", data, is_private=False)

    async def get_ticker(self, pair):
        """Public Endpoint: Get Ticker Info"""
        data = {"pair": pair}
        return await self._request("GET", "Ticker", data, is_private=False)

    async def add_order(self, pair, side, type, volume):
        """Private Endpoint: Create Order"""
        data = {
            "pair": pair,
            "ordertype": type,
            "type": side,
            "volume": volume
        }
        return await self._request("POST", "AddOrder", data, is_private=True)


class KrakenWS:
    def __init__(self, ws_url, callback_func):
        self.ws_url = ws_url
        self.callback = callback_func
        self.running = False

    async def connect_and_stream(self, symbols, interval=1):
        self.running = True
        while self.running:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(self.ws_url) as ws:
                        logger.info(f"Connected to Kraken WS v2: {self.ws_url}")
                        
                        # Subscribe to OHLC
                        subscribe_msg = {
                            "method": "subscribe",
                            "params": {
                                "channel": "ohlc",
                                "symbol": symbols,
                                "interval": interval
                            }
                        }
                        await ws.send_json(subscribe_msg)
                        
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                await self.callback(data)
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                break
            except Exception as e:
                logger.error(f"WS Connection lost: {e}, retrying in 5s...")
                await asyncio.sleep(5)