#!/usr/bin/env python

import collections
import threading
import typing
import unittest


T = typing.TypeVar('T')

class Channel(typing.Generic[T]):
    def __init__(self) -> None:
        self._condvar: threading.Condition = threading.Condition()
        self._closed: bool = False
        self._pending_reads: int = 0
        self.q: collections.deque = collections.deque()

    def recv(self) -> typing.Optional[T]:
        "Blocking read. Returns None if channel is closed"
        with self._condvar:
            if self._closed and len(self.q) == 0:
                return None
            self._pending_reads += 1
            while len(self.q) == 0:
                self._condvar.wait()
            item = self.q.popleft()
            self._pending_reads -= 1
            return item

    def send(self, item: T) -> None:
        with self._condvar:
            if self._closed:
                raise RuntimeError("send called on closed channel")
            self.q.append(item)
            self._condvar.notify()

    def close(self) -> None:
        "Close channel and signal consumers"
        with self._condvar:
            self._closed = True
            for _ in range(self._pending_reads):
                self.q.append(None)
            self._condvar.notify_all()


class ChannelTest(unittest.TestCase):

    def test_RecvNoneWhenClosed(self):
        channel = Channel()
        channel.close()
        self.assertIsNone(channel.recv())
        self.assertIsNone(channel.recv())

    def test_SendRaisesErrorWhenClosed(self):
        channel = Channel()
        channel.close()
        self.assertRaises(RuntimeError, channel.send, 0)

    def test_SendDoesntBlock(self):
        channel = Channel()
        channel.send("boom")
        channel.send("blah")
        channel.close()
        self.assertEqual(channel.recv(), "boom")
        self.assertEqual(channel.recv(), "blah")
        self.assertIsNone(channel.recv())

    def test_CloseUnblocksConsumers(self):
        channel = Channel()
        def checkChannelContent():
            self.assertIsNone(channel.recv())
        # spawn 5 readers and make sure they terminate when channel is closed
        readers = [threading.Thread(target=checkChannelContent) for _ in range(5)]
        for thread in readers:
            thread.start()
        channel.close()
        for thread in readers:
            thread.join()

    def test_ClosedChannelReadsPendingContent(self):
        channel = Channel()
        channel.send(1234)
        channel.send(4321)
        channel.close()
        def checkChannelContent():
            self.assertEqual(channel.recv(), 1234)
            self.assertEqual(channel.recv(), 4321)
            self.assertIsNone(channel.recv())
            self.assertIsNone(channel.recv())
        # spawn reader on the side
        reader = threading.Thread(name="reader", target=checkChannelContent)
        reader.start()
        reader.join()

    def test_SendRecv(self):
        channel = Channel()
        # 0. Send some stuff
        senders = [threading.Thread(target=channel.send, args=(x,)) for x in range(10)]
        for thread in senders:
            thread.start()
        # 1. Join some senders
        for thread in senders[:5]:
            thread.join()
        senders = senders[5:]
        # 2. Recieve 3 out of 10 items produced
        values = []
        for _ in range(3):
            value = channel.recv()
            self.assertIsNotNone(value)
            values.append(value)
        # 3. close channel
        channel.close()
        # 4. Recieve 7 remaining items out of 10 items produced
        for _ in range(7):
            value = channel.recv()
            self.assertIsNotNone(value)
            values.append(value)
        # 5. After we've consumed all values, should get None
        self.assertIsNone(channel.recv())
        # 6. Join the remaining senders
        for thread in senders[:5]:
            thread.join()
        # 7. Check values match  what we put into channel
        self.assertListEqual(sorted(values), list(range(10)))


if __name__ == "__main__":
    unittest.main()
