#!/usr/bin/env python
import re
import asyncio
from websockets.asyncio.client import connect
import requests
import json
import random
import urllib.parse
from bs4 import BeautifulSoup
import concurrent.futures

# URL‑encode the ticket token
TOKEN = urllib.parse.quote_plus("ticket{KittySnoopy8202n25:PeqCf1U31VM902bX23aKjOXjr9XMQTIqRs-eExaKF0eNBaVM}")
print("Encoded token:", TOKEN)

# Convert a two-character card code (e.g. "sa", "dk") to its deck number (1–52)
def c2n(c):
    return {
        "s": 0,
        "h": 1,
        "c": 2,
        "d": 3,
    }[c[0].lower()] * 13 + {
        "a": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
        "x": 10,
        "j": 11,
        "q": 12,
        "k": 13,
    }[c[1].lower()]

# --- INITIAL HTTP REQUEST ---

with requests.Session() as s:
    r = s.get("https://sevenelbee-ru1ooth5oor5.shellweplayaga.me/")
    # Extract CSRF token from meta tag
    csrf_token = re.search('<meta name="csrf-token" content="([^"]*)">', r.text).group(1)
    #print("Extracted CSRF token:", csrf_token)
    # Print cookies for debugging
    cookies = s.cookies.get_dict()
    #print("Session Cookies:", cookies)
    _seven_el_bee_key = cookies["_seven_el_bee_key"]
    # Build a cookie header dictionary for the websocket connection
    cookie = {"Cookie": f"_seven_el_bee_key={_seven_el_bee_key}"}
    # Extract the LiveView div (its id, session, and static tokens)
    x = re.search(
        '<div id="([^"]*)" data-phx-main data-phx-session="([^"]*)" data-phx-static="([^"]*)"><header>',
        r.text
    )
    id, data_phx_session, data_phx_static = x.group(1), x.group(2), x.group(3)
    #print("Extracted LiveView id:", id)
    #print("Extracted session:", data_phx_session)
    #print("Extracted static token:", data_phx_static)

# Global variables for LiveView protocol message sequencing.
message_index = None
message_id = None

# --- HELPER FUNCTIONS ---

# Send a message over the websocket and await a reply.
async def act(ws, msg):
    await ws.send(json.dumps(msg))
    m = await ws.recv()
    #print("Received:", json.dumps(json.loads(m), indent=4))
    return m


def parse_available_cards(message):
    try:
        data = json.loads(message)
        #print("Parsed message:", data)
        available_cards = set()
        if isinstance(data, list) and len(data) >= 5:
            if data[3] == "phx_reply" and data[4].get("status") == "ok":
                diff = data[4].get("response", {}).get("diff", {})
                if diff and '0' in diff and '2' in diff['0'] and 'd' in diff['0']['2']:
                    for change_list in diff['0']['2']['d']:
                        for change in change_list:
                            if isinstance(change, dict) and '1' in change:
                                match = re.search(r'data-card="([^"]*)"', change['1'])
                                if match:
                                    available_cards.add(match.group(1).lower())
                    #print("Available cards to choose from:", available_cards)
                    return available_cards
        return set()
    except Exception as e:
        print("Error parsing available cards:", e)
        return set()

# --- LIVEVIEW MESSAGES ---

async def start(ws, csrf_token, data_phx_session, data_phx_static):
    global message_index, message_id
    #print("Starting LiveView connection...")
    #print("sending phx_join")
    msg = [
        "4",
        str(message_index),
        f"lv:{message_id}",
        "phx_join",
        {
            "url": "https://sevenelbee-ru1ooth5oor5.shellweplayaga.me/",
            "params": {
                "_csrf_token": csrf_token,
                "_track_static": [
                    "https://sevenelbee-ru1ooth5oor5.shellweplayaga.me/assets/css/app.css",
                    "https://sevenelbee-ru1ooth5oor5.shellweplayaga.me/assets/js/app.js"
                ],
                "_mounts": 0,
                "_mount_attempts": 0
            },
            "session": data_phx_session,
            "static": data_phx_static
        }
    ]
    m = await act(ws, msg)
    message_index += 1
    return m

async def token_event(ws, token):
    global message_index, message_id

    msg = [
        "4",
        str(message_index),
        f"lv:{message_id}",
        "event",
        {"type": "form", "event": "present_ticket", "value": f"ticket={token}"}
    ]
    #print("Sending token event:", msg)
    m = await act(ws, msg)
    message_index += 1
    return m

async def heartbeat(ws):
    global message_index, message_id
    msg = [None, str(message_index), "phoenix", "heartbeat", {}]
    m = await act(ws, msg)
    message_index += 1
    return m

async def init(ws, csrf_token, id, data_phx_session, data_phx_static, token):
    global message_index, message_id
    message_id = id
    message_index = 4
    await start(ws, csrf_token, data_phx_session, data_phx_static)
    message_index = 8
    await token_event(ws, token)
    await heartbeat(ws)

async def deal(ws):
    global message_index, message_id
    msg = [
        "4",
        str(message_index),
        f"lv:{message_id}",
        "event",
        {"type": "click", "event": "deal", "value": {"value": ""}}
    ]
    #print("Sending deal event:", msg)
    m = await act(ws, msg)
    message_index += 1
    return m

async def guess(ws, card_code):
    global message_index, message_id
    msg = [
        "4",
        str(message_index),
        f"lv:{message_id}",
        "event",
        {"type": "click", "event": "propose_card", "value": {"deck-number": str(c2n(card_code)), "value": ""}}
    ]
    #print("Sending guess event:", msg)
    m = await act(ws, msg)
    message_index += 1
    return m

# --- MAIN COROUTINE ---
async def do():
    # Connect to the websocket using the proper URL with query parameters; pass the cookie header.
    ws_url = (
        f"wss://sevenelbee-ru1ooth5oor5.shellweplayaga.me/live/websocket"
        f"?_csrf_token={csrf_token}"
        f"&_track_static%5B0%5D=https%3A%2F%2Fsevenelbee-ru1ooth5oor5.shellweplayaga.me%2Fassets%2Fcss%2Fapp.css"
        f"&_track_static%5B1%5D=https%3A%2F%2Fsevenelbee-ru1ooth5oor5.shellweplayaga.me%2Fassets%2Fjs%2Fapp.js"
        f"&_mounts=0&_mount_attempts=0&_live_referer=undefined&vsn=2.0.0"
    )
    print("Constructed WebSocket URL:", ws_url)
    async with connect(ws_url, additional_headers=cookie) as ws:
        await init(ws, csrf_token, id, data_phx_session, data_phx_static, TOKEN)
        # Send a deal event
        hallucinations = []
        results = []
        consecutive_wins = 0
        for run in range(1000):
            deal_reply = await deal(ws)
            # Parse the reply to extract the cards available to choose from.
            available_cards = parse_available_cards(deal_reply)
            #print("Available cards:", available_cards)

            # Define the full deck
            full_deck = {s + r for s in ['s', 'h', 'c', 'd']
                         for r in ["a", "2", "3", "4", "5", "6", "7", "8", "9", "x", "j", "q", "k"]}

            # Find the difference between the full deck and the available cards
            unavailable_cards = full_deck - available_cards
            print(f"Unavailable cards ({len(unavailable_cards)}):", unavailable_cards)
            hallucinations.append(unavailable_cards)

            if available_cards:
                chosen_card = random.choice(list(unavailable_cards))
                print("Guessing card:", chosen_card)
                result = await guess(ws, chosen_card)
                is_correct = "you guessed wrong!" not in result
                results.append(is_correct)
                if is_correct:
                    consecutive_wins += 1
                else:
                    consecutive_wins = 0
 
                print("Guess result:", "Correct!" if is_correct else "Incorrect.")
                print(f"Current consecutive wins: {consecutive_wins}")

                if consecutive_wins >= 5:
                    print("ABBIAMO VINTO!!! PRINTING FLAG...")
                    print(result)
                    with open("abbiamovinto", "w") as f:
                        f.write("\n\nabbiamo vinto:\n")
                        f.write(result)
                    exit(0)
            else:
                print("No available cards found to guess.")
                exit(1)

        correct_guesses = sum(results)
        #print("Final results:", results)
        print(f"\n\n\n\nNumber of correct guesses: {correct_guesses} / {len(results)}")

        hallucination_count = {}
        for hallucination in hallucinations:
            for card in hallucination:
                if card not in hallucination_count:
                    hallucination_count[card] = 0
                hallucination_count[card] += 1
        
        sorted_hallucination_count = dict(sorted(hallucination_count.items(), key=lambda item: item[1], reverse=True))
        #print("Hallucination count:")
        #for card, count in sorted_hallucination_count.items():
        #    print(f"{card}: {count}")


if __name__ == "__main__":
    for _ in range(10):
        asyncio.run(do())
    
