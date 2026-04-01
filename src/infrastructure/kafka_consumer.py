import json

from aiokafka import AIOKafkaConsumer


class KafkaConsumer:
    def __init__(self, bootstrap_servers: str, topic: str, group_id: str):
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._group_id = group_id
        self._consumer: AIOKafkaConsumer | None = None

    async def start(self):
        self._consumer = AIOKafkaConsumer(
            self._topic,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            key_deserializer=lambda k: k.decode("utf-8") if k else None,
            enable_auto_commit=False,
        )
        await self._consumer.start()

    def __aiter__(self):
        return self

    async def __anext__(self):
        return await self._consumer.getone()

    async def commit(self):
        await self._consumer.commit()

    async def stop(self):
        if self._consumer:
            await self._consumer.stop()
