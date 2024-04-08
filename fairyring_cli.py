import argparse
import asyncio
import websockets
import json
import requests
import dotenv
import os


class FairyringCLI:
    def __init__(self):
        dotenv.load_dotenv()
        self.websocket_url = os.getenv("websocket_url")
        self.rpc_url = os.getenv("rpc_url")
        self.slack_webhook_url = os.getenv("slack_webhook_url")

    async def subscribe_to_aggregated_key(self):
        async with websockets.connect(self.websocket_url) as websocket:
            query = {"jsonrpc": "2.0", "method": "subscribe",
                     "params": ["tm.event='Tx' AND keyshare-aggregated EXISTS"], "id": 1}

            await websocket.send(json.dumps(query))

            async for message in websocket:
                data = json.loads(message)
                if data["result"] != {}:
                    alert_message = ("height: " + data["result"]["events"]["tx.height"][0] + "\ndata: " +
                                     data["result"]["events"]["keyshare-aggregated.data"][0])
                    requests.post(self.slack_webhook_url, json={'text': alert_message})

    async def subscribe_to_transfer(self, address, amount):
        async with websockets.connect(self.websocket_url) as websocket:
            sender_query = {"jsonrpc": "2.0", "method": "subscribe", "params": [
                "tm.event='Tx' AND transfer.sender='{}' AND transfer.amount>{}".format(address, amount)], "id": 1}
            recipient_query = {"jsonrpc": "2.0", "method": "subscribe", "params": [
                "tm.event='Tx' AND transfer.recipient='{}' AND transfer.amount>{}".format(address, amount)], "id": 1}
            await websocket.send(json.dumps(sender_query))
            await websocket.send(json.dumps(recipient_query))

            async for message in websocket:
                data = json.loads(message)
                if data["result"] != {}:
                    events = data["result"]["data"]["value"]["TxResult"]["result"]["events"]
                    for event in events:
                        if event["type"] == "transfer":
                            amount_attr = next(attr for attr in event["attributes"] if attr["key"] == "amount")
                            amount_value = amount_attr["value"]
                            if int(amount_value[:-6]) > amount:
                                alert_message = ("height: " + data["result"]["events"]["tx.height"][0] +
                                                 "\nhash: " + data["result"]["events"]["tx.hash"][0] +
                                                 "\nsender: " +
                                                 (next(
                                                     attr for attr in event["attributes"] if attr["key"] == "sender"))[
                                                     "value"] +
                                                 "\nrecipient: " +
                                                 (next(attr for attr in event["attributes"] if
                                                       attr["key"] == "recipient"))[
                                                     "value"] +
                                                 "\namount: " + amount_value
                                                 )
                                requests.post(self.slack_webhook_url, json={'text': alert_message})

    async def subscribe_to_encrypted_tx(self, tx_hash):
        target_height = None
        creator = None
        index = None
        query_url = f"{self.rpc_url}/tx?hash=0x{tx_hash}"
        response = requests.get(query_url)
        if response.status_code == 200:
            tx_result = response.json()["result"]["tx_result"]

            if tx_result["code"] == 0:
                for event in tx_result["events"]:
                    if event["type"] == "new-encrypted-tx-submitted":
                        for attr in event["attributes"]:
                            if attr["key"] == "target-height":
                                target_height = attr["value"]
                                print(f"Target height: {target_height}")
                            elif attr["key"] == "creator":
                                creator = attr["value"]
                                print(f"creator: {creator}")
                            elif attr["key"] == "index":
                                index = attr["value"]
                                print(f"index: {index}")
                        break
            else:
                print(f"Transaction failed with code {tx_result['code']}")
        else:
            print("Transaction not found")
            return
        if target_height is not None:
            async with websockets.connect(self.websocket_url) as websocket:
                query = {"jsonrpc": "2.0", "method": "subscribe",
                         "params": [
                             "tm.event='NewBlock' AND executed-encrypted-tx.target-height='{}' AND executed-encrypted-tx.creator='{}' AND executed-encrypted-tx.index='{}'".format(
                                 target_height, creator, index)], "id": 1}
                await websocket.send(json.dumps(query))
                async for message in websocket:
                    data = json.loads(message)
                    if data["result"] != {}:
                        alert_message = "The encrypted transaction is executed now."
                        requests.post(self.slack_webhook_url, json={'text': alert_message})
                        break
        else:
            print("It is not an encrypted transaction")

    async def run(self):
        parser = argparse.ArgumentParser(description='Fairyring CLI')
        subparsers = parser.add_subparsers(dest='command', required=True)

        subparsers.add_parser('subscribe_aggregated_key', help='Subscribe to aggregated key events')

        transfer_parser = subparsers.add_parser('subscribe_transfer',
                                                help='Subscribe to transfer events for an address and minimum amount')
        transfer_parser.add_argument('address', help='Address to monitor')
        transfer_parser.add_argument('amount', type=int, help='Minimum amount to trigger an alert, unit: ufairy')

        encrypted_tx_parser = subparsers.add_parser('subscribe_encrypted_tx',
                                                    help='Subscribe to encrypted transaction execution')
        encrypted_tx_parser.add_argument('tx_hash', help='Encrypted transaction hash')

        args = parser.parse_args()

        if args.command == 'subscribe_aggregated_key':
            await self.subscribe_to_aggregated_key()
        elif args.command == 'subscribe_transfer':
            await self.subscribe_to_transfer(args.address, args.amount)
        elif args.command == 'subscribe_encrypted_tx':
            await self.subscribe_to_encrypted_tx(args.tx_hash)


if __name__ == "__main__":
    cli = FairyringCLI()
    asyncio.run(cli.run())
