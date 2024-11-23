import asyncio
import aiohttp

async def fetch_content(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

async def crawl_chapters_async(story_title, start_chapter, end_chapter):
    tasks = []
    for chapter_number in range(start_chapter, end_chapter + 1):
        chapter_url = f"{CRAWL_URL}/{story_title}/chuong-{chapter_number}"
        tasks.append(fetch_content(chapter_url))

    results = await asyncio.gather(*tasks)
    for result in results:
        # Xử lý lưu dữ liệu như trên
        pass
