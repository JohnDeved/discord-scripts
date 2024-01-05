import os, json, requests, datetime, statistics, argparse
from dotenv import load_dotenv
from typing import Optional, Union
from typing_extensions import TypedDict

load_dotenv()

# Create the parser and add the arguments
parser = argparse.ArgumentParser()
parser.add_argument('CHANNEL_ID', type=str, nargs='?', default=os.getenv('CHANNEL_ID', ''))
args = parser.parse_args()

CHANNEL_ID, DISCORD_TOKEN = args.CHANNEL_ID, os.getenv('DISCORD_TOKEN', '')
CACHE_FILE = os.path.join('./cache', f'{CHANNEL_ID}.json')

# print('channel id:', CHANNEL_ID, 'token:', DISCORD_TOKEN)

# type definitions
class Call(TypedDict):
    ended_timestamp: Optional[str]

class Message(TypedDict):
    id: str
    timestamp: str
    call: Call

class DCError(TypedDict):
    message: str
    
all_messages: list[Message] = []
before: Optional[str] = None

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE) as f:
        all_messages = json.load(f)

while True:
    url = f"https://discord.com/api/v9/channels/{CHANNEL_ID}/messages?limit=100"
    if before: url += f"&before={before}"
    res: Union[list[Message], DCError] = requests.get(url, headers={'authorization': DISCORD_TOKEN}).json()
    
    # check if has "message" property, if so it's an error
    if 'message' in res:
        raise Exception(res)

    # filter out messages that are already in the cache
    res = [m for m in res if m['id'] not in [m['id'] for m in all_messages]]
    
    all_messages.extend(res)
    
    print(f'got {len(all_messages)} messages')
    if len(res) < 100: break
    before = res[-1]['id']

with open(CACHE_FILE, 'w') as f:
    json.dump(all_messages, f, indent=2)

# filter for call messages
call_messages = [m for m in all_messages if m.get('call')]

# calculate total, longest and average call time
call_times: list[int] = [
    (datetime.fromisoformat(call_message['call']['ended_timestamp']) - datetime.fromisoformat(call_message['timestamp'])).total_seconds()
    for call_message in call_messages
    if call_message['call']['ended_timestamp'] is not None
]

total_call_time = sum(call_times)
longest_call_time = max(call_times)
average_call_time = statistics.mean(call_times)

print('total calls:', len(call_times))
print('total call time:', f'{total_call_time / 3600:.2f} hours')
print('longest call time:', f'{longest_call_time / 3600:.2f} hours')
print('average call time:', f'{average_call_time / 3600:.2f} hours')