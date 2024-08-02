import logging
import argparse
import asyncio
import aiohttp
from aiohttp import ClientSession
from aiohttp.client_exceptions import (
    ClientError,
    ClientResponseError,
    ServerTimeoutError,
    ClientConnectorError,
)
from tqdm import tqdm
import random
import yaml
from urllib.parse import urlparse
import os
import json
import sys
from typing import List, Dict, Optional
from logging.handlers import RotatingFileHandler
from colorama import init, Fore, Style

init(autoreset=True)

VERSION = "1.0.0"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
]


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }
    EMOJIS = {
        "DEBUG": "🐛",
        "INFO": "✅",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "❗",
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, Fore.WHITE)
        emoji = self.EMOJIS.get(record.levelname, "ℹ️")
        formatted_message = super().format(record)
        return f"{color}{emoji} {formatted_message}{Style.RESET_ALL}"


def setup_logging(log_file: str, log_level: int) -> None:
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10**6, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(
        ColoredFormatter("%(asctime)s - %(levelname)s - %(message)s")
    )

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[file_handler, stream_handler],
    )


def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


async def fetch(
    url: str, session: ClientSession, retries: int, resume: bool
) -> Optional[bytes]:
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    if resume:
        headers["Range"] = "bytes=0-"

    for attempt in range(retries):
        try:
            logging.debug(f"Attempting to fetch URL: {url} (Attempt {attempt + 1})")
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    content = await response.read()
                    logging.info(f"Successfully fetched URL: {url}")
                    return content
                elif response.status in (301, 302, 303):
                    url = response.headers.get("Location")
                    if url:
                        logging.info(f"Redirected to: {url}")
                        continue
                else:
                    logging.error(
                        f"Failed to fetch URL {url} with status code {response.status} - {response.reason}"
                    )
                    break
        except (
            ClientConnectorError,
            ServerTimeoutError,
            ClientResponseError,
            ClientError,
            asyncio.TimeoutError,
        ) as e:
            logging.warning(f"Network error for {url} on attempt {attempt + 1}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error for {url} on attempt {attempt + 1}: {e}")
    return None


def get_filename_from_url(url: str) -> str:
    path = urlparse(url).path
    return os.path.basename(path) or "downloaded_file"


def save_to_directory(data: Dict[str, bytes], output_dir: str) -> None:
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            logging.info(f"Created directory: {output_dir}")
            print(f"{Fore.YELLOW}📁 Created directory: {output_dir}")
        except Exception as e:
            logging.error(f"Failed to create directory {output_dir}: {e}")
            print(f"{Fore.RED}❌ Failed to create directory: {output_dir}")
            return

    for url, content in data.items():
        filename = get_filename_from_url(url)
        file_path = os.path.join(output_dir, filename)
        try:
            with open(file_path, "wb") as file:
                file.write(content)
            logging.info(f"Saved content to {file_path}")
            print(f"{Fore.GREEN}✅ Downloaded content saved to {file_path}")
        except Exception as e:
            logging.error(f"Failed to save content to {file_path}: {e}")
            print(f"{Fore.RED}❌ Failed to save content to {file_path}")


async def download_urls(
    urls: List[str], output_dir: str, retries: int, max_connections: int, resume: bool
) -> None:
    connector = aiohttp.TCPConnector(limit=max_connections)
    async with ClientSession(connector=connector) as session:
        valid_urls = [url for url in urls if is_valid_url(url)]
        invalid_urls = [url for url in urls if not is_valid_url(url)]

        for url in invalid_urls:
            logging.warning(f"Invalid URL skipped: {url}")
            print(f"{Fore.RED}🚫 Invalid URL skipped: {url}")

        tasks = [fetch(url, session, retries, resume) for url in valid_urls]
        results = []

        with tqdm(
            total=len(valid_urls), desc="🔽 Downloading", unit="url", ncols=100
        ) as pbar:
            for url, task in zip(valid_urls, tasks):
                content = await task
                if content is not None:
                    results.append((url, content))
                    pbar.update(1)
                else:
                    logging.error(f"Failed to fetch content from {url}")
                    print(f"{Fore.RED}❌ Failed to fetch content from {url}")

        downloaded_content = dict(results)
        save_to_directory(downloaded_content, output_dir)


def load_config(config_file: str) -> Dict[str, str]:
    try:
        with open(config_file, "r") as file:
            return yaml.safe_load(file) or {}
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_file}")
        return {}
    except yaml.YAMLError as e:
        logging.error(f"Error parsing configuration file: {e}")
        return {}


def validate_args(args: argparse.Namespace) -> bool:
    if args.retries < 1:
        logging.error("Retries must be at least 1")
        return False
    if args.max_connections < 1:
        logging.error("Max connections must be at least 1")
        return False
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download content from a list of URLs."
    )
    parser.add_argument("-f", "--file", type=str, help="Input JSON file with URLs")
    parser.add_argument(
        "-d",
        "--dest",
        type=str,
        default=".",
        help="Output directory for downloaded content",
    )
    parser.add_argument("-l", "--log", type=str, help="Log file")
    parser.add_argument(
        "-r",
        "--retries",
        type=int,
        default=3,
        help="Number of retries for failed downloads",
    )
    parser.add_argument(
        "-m",
        "--max-connections",
        type=int,
        default=10,
        help="Maximum number of concurrent connections",
    )
    parser.add_argument("-c", "--config", type=str, help="Configuration file")
    parser.add_argument(
        "-u", "--url", type=str, nargs="+", help="Inline URLs to download"
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume download from where it left off",
    )
    args = parser.parse_args()

    if not validate_args(args):
        sys.exit(1)
    return args


def main() -> None:
    args = parse_args()

    # Determine the log file path based on the operating system
    if args.log:
        log_file = args.log
    else:
        if os.name == "nt":  # Windows
            log_file = os.path.join(os.path.expanduser("~"), ".kalpak", "kalpak.log")
        else:  # UNIX-like systems
            log_file = "/var/log/kalpak.log"

    # Ensure the directory exists for Windows
    if os.name == "nt" and not os.path.exists(os.path.dirname(log_file)):
        try:
            os.makedirs(os.path.dirname(log_file))
            logging.info(f"Created directory: {os.path.dirname(log_file)}")
        except Exception as e:
            logging.error(
                f"Failed to create directory {os.path.dirname(log_file)}: {e}"
            )
            sys.exit(1)

    setup_logging(log_file, logging.INFO)

    if args.file:
        try:
            with open(args.file, "r") as file:
                urls = json.load(file).get("urls", [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Error reading URLs from file: {e}")
            sys.exit(1)
    elif args.url:
        urls = args.url
    else:
        logging.error("No URLs provided")
        sys.exit(1)

    config = load_config(args.config) if args.config else {}
    output_dir = args.dest
    retries = args.retries
    max_connections = args.max_connections
    resume = args.resume

    asyncio.run(download_urls(urls, output_dir, retries, max_connections, resume))


if __name__ == "__main__":
    main()
