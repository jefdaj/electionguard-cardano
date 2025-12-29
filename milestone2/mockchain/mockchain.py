#!/usr/bin/env python3

import asyncio
import aioipfs
import os
import sys
import re

from pprint import pprint
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

class MockchainSubscriber(FileSystemEventHandler):
    def __init__(self, loop, mockchain_dir, debounce_seconds=1.0, *args, **kwargs):
        super(MockchainSubscriber, self).__init__(*args, **kwargs)
        self.loop = loop
        self.mockchain_dir = mockchain_dir

        # the subscriber will only read from <channel>/NNNN.json
        self.valid_channels = set(['admin'])

        # for json files that may be partially written or just have multiple fs events
        self.debounce_seconds = debounce_seconds
        self.pending_events = {} # path -> asyncio.Handle

        # TODO also handle when the events are done but the ipfs file hasn't propagated

        # TODO self.newjson_callback or similar

    def is_subscribed_mockchain_event(self, event):
        "Is the event creation/edit of a new json in a subscribed channel dir?"
        if event.is_directory:
            return False
        regex = '^data/(' + '|'.join(self.valid_channels) + ')/[0-9]{3}.json$'
        match = re.match(regex, event.src_path)
        return match

    def on_created(self, event):
        if self.is_subscribed_mockchain_event(event):
            self.on_subscribed_mockchain_event(event)

    def on_modified(self, event):
        if self.is_subscribed_mockchain_event(event):
            self.on_subscribed_mockchain_event(event)

    def on_subscribed_mockchain_event(self, event):
        path = event.src_path
        print(f'on_subscribed_mockchain_event {event}')

        # TODO and how do we handle it now?
        #      probably a delayed/debounced callback?

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
