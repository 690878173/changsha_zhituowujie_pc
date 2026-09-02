import configparser
import hashlib
import os
import random
import threading
import time
import warnings
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from io import BytesIO
from urllib.parse import urlparse

import pandas as pd
from curl_cffi import requests

try:
    from PIL import Image, UnidentifiedImageError
except ImportError as exc:
    raise RuntimeError("Missing Pillow. Install it with: pip install pillow") from exc


warnings.filterwarnings("ignore")

PRINT_LOCK = threading.Lock()
FILE_LOCK = threading.Lock()  # 新增：用于多线程并发追加写入失败日志时的线程锁

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/141.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/142.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.7 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
]

IMPERS_TYPES = [
    "chrome",
    "safari",
    "safari_ios",
    "chrome110",
    "chrome116",
    "chrome119",
    "chrome120",
    "chrome124",
    "safari15_5",
    "safari17_0",
]


def safe_print(message):
    with PRINT_LOCK:
        print(message, flush=True)


def generate_image_filename(image_url):
    url_hash = hashlib.md5(image_url.encode("utf-8")).hexdigest()
    return f"{url_hash}.webp"


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


class ImageDownloader:
    def __init__(self, config_file="config.ini"):
        self.config_file = os.path.abspath(config_file)
        self.base_dir = os.path.dirname(self.config_file) or os.getcwd()
        self.config = self.load_config(self.config_file)

        self.proxies_list = self.load_proxies()
        self.failed_count = 0  # 统计总失败数
        self.failed_log = self.resolve_path(self.config["PATHS"].get("failed_log", "failed_images.txt"))
        self.proxy_warning_printed = False
        self.local = threading.local()

        self.img_split = self.config["REQUEST"].get("csv_images_split", ",")

        # 初始化时清空上一次的失败日志，准备重新记录
        if os.path.exists(self.failed_log):
            open(self.failed_log, "w", encoding="utf-8").close()

        self.max_attempts = self.get_int("PROXY", "max_attempts", 8, 1, 30)
        configured_workers = self.get_int("PROXY", "max_workers", 4, 1, 32)
        worker_cap = self.get_int("REQUEST", "max_workers_cap", 20, 1, 32)
        self.max_workers = min(configured_workers, worker_cap)

        default_convert_workers = max(1, min(2, os.cpu_count() or 1))
        self.max_convert_workers = self.get_int(
            "REQUEST",
            "max_convert_workers",
            default_convert_workers,
            1,
            self.max_workers,
        )
        self.convert_limiter = threading.BoundedSemaphore(self.max_convert_workers)

        self.request_timeout = self.get_float("REQUEST", "timeout", 60.0, 5.0, 300.0)
        self.retry_base_delay = self.get_float("REQUEST", "retry_base_delay", 2.0, 0.0, 60.0)
        self.retry_max_delay = self.get_float("REQUEST", "retry_max_delay", 15.0, 0.0, 300.0)
        self.request_delay_min = self.get_float("REQUEST", "request_delay_min", 0.5, 0.0, 30.0)
        self.request_delay_max = self.get_float("REQUEST", "request_delay_max", 2.0, 0.0, 60.0)

        self.webp_quality = self.get_int("REQUEST", "webp_quality", 85, 1, 100)
        self.webp_lossless = self.get_bool("REQUEST", "webp_lossless", False)
        self.webp_method = self.get_int("REQUEST", "webp_method", 3, 0, 6)
        self.reencode_webp = self.get_bool("REQUEST", "reencode_webp", False)

        self.max_image_bytes = self.get_int("REQUEST", "max_image_mb", 50, 1, 1024) * 1024 * 1024
        self.log_each_success = self.get_bool("REQUEST", "log_each_success", False)
        self.log_each_skip = self.get_bool("REQUEST", "log_each_skip", False)
        self.progress_every = self.get_int("REQUEST", "progress_every", 50, 1, 1_000_000)

        self.use_random_ua = self.get_bool("REQUEST", "use_random_ua", True)
        self.use_random_impersonate = self.get_bool("REQUEST", "use_random_impersonate", True)

        self.image_headers_base = {
            "accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "sec-fetch-dest": "image",
            "sec-fetch-mode": "no-cors",
            "sec-fetch-site": "cross-site",
            "sec-ch-ua": '"Google Chrome";v="139", "Chromium";v="139", "Not?A_Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "upgrade-insecure-requests": "1",
        }

    def load_config(self, config_file):
        config = configparser.ConfigParser()
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Config file does not exist: {config_file}")

        config.read(config_file, encoding="utf-8-sig")
        if "PATHS" not in config:
            raise KeyError("Config file is missing [PATHS]")
        if "PROXY" not in config:
            config["PROXY"] = {}
        if "REQUEST" not in config:
            config["REQUEST"] = {}
        return config

    def get_int(self, section, key, fallback, minimum, maximum):
        try:
            value = self.config[section].getint(key, fallback=fallback)
        except ValueError:
            value = fallback
        return clamp(value, minimum, maximum)

    def get_float(self, section, key, fallback, minimum, maximum):
        try:
            value = self.config[section].getfloat(key, fallback=fallback)
        except ValueError:
            value = fallback
        return clamp(value, minimum, maximum)

    def get_bool(self, section, key, fallback):
        try:
            return self.config[section].getboolean(key, fallback=fallback)
        except ValueError:
            return fallback

    def resolve_path(self, path):
        if not path:
            return path
        if os.path.isabs(path):
            return path
        return os.path.join(self.base_dir, path)

    def load_proxies(self):
        proxy_file = self.resolve_path(self.config["PROXY"].get("proxy_file", "proxies.txt"))
        if not proxy_file or not os.path.exists(proxy_file):
            safe_print(f"Proxy file not found, running without proxy: {proxy_file}")
            return []

        proxies = []
        with open(proxy_file, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line or ":" not in line:
                    continue

                parts = line.split(":")
                if len(parts) < 4:
                    continue

                ip, port, username, password = parts[:4]
                proxy_url = f"http://{username}:{password}@{ip}:{port}"
                proxies.append({"http": proxy_url, "https": proxy_url})

        safe_print(f"Loaded proxies: {len(proxies)}")
        return proxies

    def get_random_proxy(self):
        if not self.proxies_list:
            if not self.proxy_warning_printed:
                safe_print("No proxy available, downloading directly.")
                self.proxy_warning_printed = True
            return None
        return random.choice(self.proxies_list)

    def get_random_user_agent(self):
        if self.use_random_ua:
            return random.choice(USER_AGENTS)
        return USER_AGENTS[0]

    def get_random_impersonate(self):
        if self.use_random_impersonate:
            return random.choice(IMPERS_TYPES)
        return IMPERS_TYPES[0]

    def create_new_session(self, impersonate_type):
        return requests.Session(
            timeout=self.request_timeout,
            impersonate=impersonate_type,
        )

    def close_session(self, session):
        if session is not None:
            try:
                session.close()
            except Exception:
                pass

    def record_failed_url(self, image_url):
        """实时追加写入失败链接到文件，并加线程锁保证多线程安全"""
        with FILE_LOCK:
            self.failed_count += 1
            with open(self.failed_log, "a", encoding="utf-8") as file:
                file.write(image_url + "\n")

    def extract_image_urls(self):
        input_csv = self.resolve_path(self.config["PATHS"].get("input_csv"))
        if not input_csv or not os.path.exists(input_csv):
            raise FileNotFoundError(f"Input CSV does not exist: {input_csv}")

        csv_encoding = self.config["REQUEST"].get("csv_encoding", "utf-8-sig")
        df = pd.read_csv(
            input_csv,
            encoding=csv_encoding,
            usecols=lambda column: column == "Images",
        )
        if "Images" not in df.columns:
            raise KeyError("Input CSV is missing the Images column")

        seen = set()
        images = []
        img_split = self.img_split
        for value in df["Images"].dropna():
            if not isinstance(value, str):
                value = str(value)
            if img_split not in value:
                _img_split = ','
            else:
                _img_split = img_split
            new_image_urls = []
            for url in value.split(_img_split):
                url = url.strip()
                if pd.isna(url) or str(url).strip() == "":
                    url = ''
                if url and url not in seen:
                    seen.add(url)
                    new_image_urls.append(url)
                # if value and value not in seen:
                #     seen.add(value)
                #     images.append(value)


        safe_print(f"Extracted unique image URLs: {len(images)}")
        return images

    def sanitize_filename(self, image_url):
        return generate_image_filename(image_url)

    def atomic_write_bytes(self, content, file_path):
        temp_file_path = f"{file_path}.tmp.{threading.get_ident()}"
        with open(temp_file_path, "wb") as file:
            file.write(content)
        os.replace(temp_file_path, file_path)

    @staticmethod
    def is_webp_bytes(content):
        return content[:4] == b"RIFF" and content[8:12] == b"WEBP"

    def save_as_webp(self, image_bytes, file_path):
        if self.is_webp_bytes(image_bytes) and not self.reencode_webp:
            self.atomic_write_bytes(image_bytes, file_path)
            return

        temp_file_path = f"{file_path}.tmp.{threading.get_ident()}"

        with self.convert_limiter:
            try:
                with Image.open(BytesIO(image_bytes)) as image:
                    image.seek(0)
                    if image.mode in ("RGBA", "LA") or (
                        image.mode == "P" and "transparency" in image.info
                    ):
                        converted = image.convert("RGBA")
                    else:
                        converted = image.convert("RGB")

                    try:
                        converted.save(
                            temp_file_path,
                            format="WEBP",
                            quality=self.webp_quality,
                            lossless=self.webp_lossless,
                            method=self.webp_method,
                        )
                    finally:
                        converted.close()

                os.replace(temp_file_path, file_path)
            except (UnidentifiedImageError, OSError) as exc:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                raise ValueError(f"Image decode/WebP conversion failed: {exc}") from exc

    def is_valid_image_response(self, response, content):
        if response.status_code != 200:
            return False

        content_type = (response.headers.get("content-type") or "").lower()
        if content_type.startswith("image/"):
            return True

        if content[:2] == b"\xff\xd8":
            return True
        if content[:8] == b"\x89PNG\r\n\x1a\n":
            return True
        if self.is_webp_bytes(content):
            return True

        return False

    def validate_size_headers(self, response):
        content_length = response.headers.get("content-length")
        if not content_length:
            return
        try:
            size = int(content_length)
        except ValueError:
            return
        if size > self.max_image_bytes:
            max_mb = self.max_image_bytes // 1024 // 1024
            raise ValueError(f"Image too large by Content-Length: {size} bytes > {max_mb} MB")

    def retry_sleep(self, attempt):
        delay = min(self.retry_max_delay, self.retry_base_delay * (2 ** (attempt - 1)))
        delay += random.uniform(0.5, 1.5)
        time.sleep(delay)

    def random_request_delay(self):
        if self.request_delay_min > 0:
            delay = random.uniform(self.request_delay_min, self.request_delay_max)
            time.sleep(delay)

    def download_image(self, image_url):
        filename = self.sanitize_filename(image_url)
        filename = filename.split('?')[0]
        output_dir = self.resolve_path(self.config["PATHS"].get("output_images", "./images"))
        file_path = os.path.join(output_dir, filename)

        if os.path.exists(file_path):
            if self.log_each_skip:
                safe_print(f"Skip existing: {filename}")
            return None

        parsed_uri = urlparse(image_url)
        dynamic_referer = f"{parsed_uri.scheme}://{parsed_uri.netloc}/"
        dynamic_origin = dynamic_referer.rstrip('/')

        current_session = None
        current_impersonate = None

        for attempt in range(1, self.max_attempts + 1):
            response = None
            try:
                if attempt == 1 or current_session is None or (response and response.status_code == 403):
                    current_impersonate = self.get_random_impersonate()
                    self.close_session(current_session)
                    current_session = self.create_new_session(current_impersonate)
                    safe_print(f"Attempt {attempt}: Using impersonate={current_impersonate}, url={image_url[:60]}...")

                self.random_request_delay()

                proxy = self.get_random_proxy()
                user_agent = self.get_random_user_agent()

                request_headers = self.image_headers_base.copy()
                request_headers["referer"] = dynamic_referer
                request_headers["origin"] = dynamic_origin
                request_headers["user-agent"] = user_agent
                if len(image_url) >= 1000:
                    safe_print(f'[WA] URI Too Large,url before 50 size:{image_url[:100]}...')
                    image_url = image_url.split(self.img_split)[0]

                response = current_session.get(
                    image_url,
                    proxies=proxy,
                    headers=request_headers,
                    impersonate=current_impersonate,
                    timeout=self.request_timeout,
                )

                if response.status_code == 403:
                    safe_print(f"403 Forbidden - will switch fingerprint, attempt={attempt}, url={image_url[:60]}...")
                    raise ConnectionError("HTTP 403 Forbidden")

                if response.status_code != 200:
                    raise ConnectionError(f"HTTP {response.status_code}")

                self.validate_size_headers(response)
                content = response.content

                if len(content) > self.max_image_bytes:
                    max_mb = self.max_image_bytes // 1024 // 1024
                    raise ValueError(f"Image too large: {len(content)} bytes > {max_mb} MB")

                if self.is_valid_image_response(response, content):
                    os.makedirs(output_dir, exist_ok=True)
                    self.save_as_webp(content, file_path)

                    if self.log_each_success:
                        safe_print(f"Downloaded: {filename}")
                    return None

                raise ValueError("Invalid image content")

            except Exception as exc:
                status_code = getattr(response, "status_code", "N/A") if response else "N/A"
                safe_print(f"Attempt {attempt} failed: HTTP_CODE {status_code} - {exc}, url={image_url[:60]}...")

                self.close_session(current_session)
                current_session = None

            finally:
                if response is not None:
                    close = getattr(response, "close", None)
                    if callable(close):
                        try:
                            close()
                        except Exception:
                            pass

            if attempt < self.max_attempts:
                self.retry_sleep(attempt)

        self.close_session(current_session)
        # 重试结束仍失败，直接实时写入 txt 文件
        self.record_failed_url(image_url)
        return image_url

    def run_download(self):
        try:
            images = self.extract_image_urls()
            if not images:
                safe_print("No image URL found.")
                return

            safe_print(
                "Runtime limits: "
                f"download_workers={self.max_workers}, "
                f"convert_workers={self.max_convert_workers}, "
                f"webp_method={self.webp_method}, "
                f"quality={self.webp_quality}, "
                f"impersonate_types={len(IMPERS_TYPES)}"
            )

            started = time.monotonic()
            total = len(images)
            completed = 0
            next_index = 0
            pending = {}
            max_pending = max(1, self.max_workers * 2)

            def submit_until_full(executor):
                nonlocal next_index
                while next_index < total and len(pending) < max_pending:
                    image = images[next_index]
                    pending[executor.submit(self.download_image, image)] = image
                    next_index += 1

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                submit_until_full(executor)
                while pending:
                    done, _ = wait(pending, return_when=FIRST_COMPLETED)
                    for future in done:
                        image = pending.pop(future)
                        try:
                            future.result()
                        except Exception as exc:
                            safe_print(f"Unhandled worker error: {exc}, url={image}")

                        completed += 1
                        if completed % self.progress_every == 0 or completed == total:
                            elapsed = max(0.1, time.monotonic() - started)
                            safe_print(
                                f"Progress: {completed}/{total}, "
                                f"failed_recorded={self.failed_count}, "
                                f"elapsed={elapsed:.1f}s"
                            )

                    submit_until_full(executor)

            safe_print(f"\nDownload completed! Total failed URLs logged: {self.failed_count}")

        except KeyboardInterrupt:
            safe_print(f"\n[Terminated by user] Program stopped manually. Recorded failed URLs so far: {self.failed_count}")
        except Exception as exc:
            safe_print(f"Download process failed: {exc}")


def main():
    try:
        downloader = ImageDownloader("config.ini")
        downloader.run_download()
    except KeyboardInterrupt:
        safe_print("\nProgram terminated by user.")
    except Exception as exc:
        safe_print(f"Program failed: {exc}")


if __name__ == "__main__":
    main()