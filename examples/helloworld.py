#!/usr/bin/env python3
import asyncio
from mortis import Mortis
import logging
import os

logging.basicConfig(
    level=logging.DEBUG if os.environ.get("DEBUG") else logging.INFO,
    format="%(name)s - %(levelname)s - %(message)s"
)

with open("lines.txt", "r") as f:
    lines = f.readlines()
    lines = [line.strip() for line in lines]
with open("key", "r") as f:
    key = f.read().strip()

mortis = Mortis(lines, key)

async def main():
    print(await mortis.respond("User: 你又睡不着吗"))

if __name__ == "__main__":
    asyncio.run(main())
