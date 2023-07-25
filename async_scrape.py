"""
DEMO asynchronous web scraper of talkpython.fm
Scrape a range of episode numbers
"""

import aiohttp
import aiodns
import bs4
from colorama import Fore


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_title_range(loop))
    print("Done")


async def get_html(episode_number: int) -> str:
    print(Fore.YELLOW + f"Getting HTML for episode {episode_number}", flush=True)
    
    url = f'https://talkpython.fm/{episode_number}'

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as reply:
            reply.raise_for_status()
            html = await reply.text()
            return html


def get_title(html: str, episode_number: int) -> str:
    print(Fore.CYAN + f"Getting TITLE for episode {episode_number}", flush=True)
    soup = bs4.BeautifulSoup(html, 'html.parser')
    header = soup.select_one('h1')
    if not header:
        return 'MISSING'
    
    return header.text.strip()


async def get_title_range(loop: AbstractEventLoop):
    tasks = []
    # using a small range to avoid DDoS   
    for n in range(190, 200):
        tasks.append((loop.create_task(get_html(n)), n))

    for task in tasks:
        html = await task
        title = await get_title(html, n)
        print(Fore.WHITE + f'Title found: {title}', flush=True)
        

if __name__ == '__main__':
    main()
