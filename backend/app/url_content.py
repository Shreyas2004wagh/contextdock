from __future__ import annotations

import asyncio
import ipaddress
import socket
from html.parser import HTMLParser
from urllib.parse import urljoin

import httpx

MAX_URL_BYTES = 1024 * 1024


class ReadableHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ignored = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self.ignored += 1
        if tag in {"p", "br", "div", "li", "h1", "h2", "h3", "section"} and not self.ignored:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"}:
            self.ignored = max(0, self.ignored - 1)
        if tag in {"p", "div", "li", "h1", "h2", "h3", "section"} and not self.ignored:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.ignored:
            self.parts.append(data)


async def resolve_public_url(value: str) -> tuple[httpx.URL, str]:
    try:
        url = httpx.URL(value)
        if url.scheme not in {"http", "https"} or not url.host or url.userinfo or url.port not in {None, 80, 443}:
            raise ValueError
        addresses = await asyncio.get_running_loop().getaddrinfo(url.host, url.port or (443 if url.scheme == "https" else 80), type=socket.SOCK_STREAM)
        ips = {entry[4][0] for entry in addresses}
        if not ips or any(not ipaddress.ip_address(ip).is_global for ip in ips):
            raise ValueError
    except (ValueError, httpx.InvalidURL, socket.gaierror) as exc:
        raise ValueError("Use a public HTTP or HTTPS URL without credentials or custom ports.") from exc
    return url, sorted(ips)[0]


async def fetch_url_text(value: str) -> str:
    original = value
    async with httpx.AsyncClient(timeout=15, follow_redirects=False, trust_env=False) as client:
        for _ in range(4):
            url, address = await resolve_public_url(value)
            # Pin the validated IP for this connection; retain the original TLS name.
            request = client.build_request(
                "GET", url.copy_with(host=address),
                headers={"Host": url.netloc.decode(), "Accept-Encoding": "identity", "User-Agent": "WheresMyContext/1.0"},
                extensions={"sni_hostname": url.host},
            )
            response = await client.send(request, stream=True)
            try:
                if response.is_redirect:
                    location = response.headers.get("location")
                    if not location:
                        raise ValueError("The URL returned an invalid redirect.")
                    value = urljoin(str(url), location)
                    continue
                if not response.is_success:
                    raise ValueError("The page could not be fetched. Check that it is publicly accessible.")
                media_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
                if media_type not in {"text/html", "text/plain", "text/markdown"}:
                    raise ValueError("URL ingestion supports HTML and plain text pages. Upload documents as files.")
                if response.headers.get("content-encoding", "identity") != "identity":
                    raise ValueError("This page requires compressed transfer. Upload its text as a file instead.")
                data = bytearray()
                async for chunk in response.aiter_raw(chunk_size=64 * 1024):
                    data.extend(chunk)
                    if len(data) > MAX_URL_BYTES:
                        raise ValueError("The page exceeds the 1 MB URL ingestion limit.")
                text = data.decode("utf-8", errors="replace")
                if media_type == "text/html":
                    parser = ReadableHTML()
                    parser.feed(text)
                    text = "".join(parser.parts)
                text = "\n".join(" ".join(line.split()) for line in text.splitlines() if line.strip())
                if not text:
                    raise ValueError("No readable page text was found. JavaScript-only pages are not supported.")
                if len(text) > 200_000:
                    raise ValueError("The page contains too much text. Upload a shorter extract instead.")
                return f"Source URL: {original}\nFinal URL: {url}\n\n{text}"
            finally:
                await response.aclose()
    raise ValueError("The page redirects too many times.")
