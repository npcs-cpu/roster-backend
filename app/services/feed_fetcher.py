import hashlib

import httpx



def normalize_feed_url(feed_url: str) -> str:
    value = feed_url.strip()
    if value.startswith("webcal://"):
        return "https://" + value[len("webcal://"):]
    if value.startswith("webcals://"):
        return "https://" + value[len("webcals://"):]
    return value


async def fetch_feed(feed_url: str) -> tuple[str, str]:
    normalized = normalize_feed_url(feed_url)
    timeout = httpx.Timeout(20.0, connect=10.0)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        response = await client.get(normalized)
        response.raise_for_status()
        text = response.text

    source_hash = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()
    return text, source_hash
