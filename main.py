import asyncio

from config import TOKEN, OkoBot


async def main():
    bot = OkoBot()
    async with bot:
        await bot.start(token=TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
