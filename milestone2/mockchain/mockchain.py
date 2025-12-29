#!/usr/bin/env python3

import asyncio
import aioipfs
import os
import sys
import re
import json

from pprint import pprint
from os.path import basename, dirname, join
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

class MockchainSubscriber(FileSystemEventHandler):
    def __init__(self, loop, mockchain_dir, debounce_seconds=1.0, *args, **kwargs):
        super(MockchainSubscriber, self).__init__(*args, **kwargs)

        self.mockchain_dir = mockchain_dir

        # map of valid channels -> index of latest json parsed from that channel
        self.channel_state = {'admin': 0}

        # for json files that may be partially written or just have multiple fs events
        # self.debounce_seconds = debounce_seconds
        # self.pending_events = {} # path -> asyncio.Handle
        # TODO also handle when the events are done but the ipfs file hasn't propagated
        # TODO self.newjson_callback or similar
        # self.loop = loop # TODO what's this for?

    def on_created(self, event):
        return self.on_fs_event(event)

    def on_modified(self, event):
        return self.on_fs_event(event)

    def on_fs_event(self, event):
        info = self.mockchain_event_info(event)
        if info is not None:
            try:
                return self.on_mockchain_event(**info)
            except Exception as e:
                print(e)

    def subscribed_json_regex(self):
        return (
            '^' +
            self.mockchain_dir +
            '/([^/]*)'
            '/([0-9]{3,3}).json$'
        )

    def subscribed_json_path(self, channel: str, index: int) -> str:
        return join(self.mockchain_dir, channel, f'{index:03d}.json')

    def next_json_index(self, channel_name):
        "What should be the index of the next event?"
        return self.channel_state[channel_name] + 1

    def mockchain_event_info(self, event):
        try:
            match = re.match(self.subscribed_json_regex(), event.src_path)
            return {
                'channel': match.group(1),
                'index': int(match.group(2))
            }
        except Exception as e:
            # print(f'{event} -> {e}')
            return None

    def on_mockchain_event(self, channel: str, index: int):
        if not channel in self.channel_state.keys():
            raise Exception(f'invalid mockchain_channel {channel}')
        if index < self.next_json_index(channel):
            msg = f'invalid mockchain_index for {channel}: {index}'
            raise Exception(msg)
        if index > self.next_json_index(channel):
            # TODO in this case, try to parse the earlier presumably missed message first?
            msg = f'invalid mockchain_index for {channel}: {index}'
            raise Exception(msg)
        obj = self.parse_mockchain_json(channel, index)
        self.channel_state[channel] += 1
        pprint(obj)
        if obj['action'] == 'create_mockchain_channel':
            self.create_mockchain_channel(obj)
        # TODO actually handle message here

    def parse_mockchain_json(self, channel: str, index: int) -> dict:
        parsed = {'mockchain_channel': channel, 'mockchain_index': index}
        path = self.subscribed_json_path(channel, index)
        with open(path, 'r') as f:
            parsed.update(json.load(f))
        return parsed

    def create_mockchain_channel(self, obj: dict):
        print(f'create_mockchain_channel {obj}')
        channel = obj['new_channel_name']
        channel_dir = join(self.mockchain_dir, channel)
        os.makedirs(channel_dir, exist_ok=True)
        if channel in self.channel_state.keys():
            raise Exception(f'channel already exists: {channel}')
        self.channel_state[channel] = 0


if __name__ == '__main__':
    mockchain_dir = sys.argv[1]
    os.makedirs(mockchain_dir, exist_ok=True)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    observer = Observer() # TODO what does this do?
    subscriber = MockchainSubscriber(loop, mockchain_dir)
    observer.schedule(subscriber, path=mockchain_dir, recursive=True)
    try:
        observer.start()
        loop.run_forever()
    except:
        observer.stop()
        observer.join()
        loop.close()
