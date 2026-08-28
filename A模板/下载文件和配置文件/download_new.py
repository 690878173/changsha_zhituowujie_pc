import configparser
import hashlib
import os
import queue
import random
import threading
import time
import warnings
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
FILE_LOCK = threading.Lock()

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


class IMG_download_ljp:
    def __init__(self, config_file="config.ini"):
        self.config_file = os.path.abspath(config_file)
        self.base_dir = os.path.dirname(self.config_file) or os.getcwd()
        self.config = self.load_config(self.config_file)

        self.proxies_list = self.load_proxies()
        self.failed_count = 0
        self.failed_log = self.resolve_path(self.config["PATHS"].get("failed_log", "failed_images.txt"))
        self.proxy_warning_printed = False

        if os.path.exists(self.failed_log):
            open(self.failed_log, "w", encoding="utf-8").close()

        # ── 运行参数 ──
        cfg_p = self.config["PROXY"]
        cfg_r = self.config["REQUEST"]

        self.max_attempts = cfg_p.getint("max_attempts", 8)
        configured_workers = cfg_p.getint("max_workers", 4)
        worker_cap = cfg_r.getint("max_workers_cap", 20)
        self.max_workers = min(configured_workers, worker_cap)

        default_convert = max(1, min(2, os.cpu_count() or 1))
        self.max_convert_workers = cfg_r.getint("max_convert_workers", default_convert)
        self.convert_limiter = threading.BoundedSemaphore(self.max_convert_workers)

        self.request_timeout = cfg_r.getfloat("timeout", 60.0)
        self.retry_base_delay = cfg_r.getfloat("retry_base_delay", 2.0)
        self.retry_max_delay = cfg_r.getfloat("retry_max_delay", 15.0)
        self.request_delay_min = cfg_r.getfloat("request_delay_min", 0.5)
        self.request_delay_max = cfg_r.getfloat("request_delay_max", 2.0)

        self.webp_quality = cfg_r.getint("webp_quality", 85)
        self.webp_lossless = cfg_r.getboolean("webp_lossless", False)
        self.webp_method = cfg_r.getint("webp_method", 3)
        self.reencode_webp = cfg_r.getboolean("reencode_webp", False)

        self.max_image_bytes = cfg_r.getint("max_image_mb", 50) * 1024 * 1024
        self.log_each_success = cfg_r.getboolean("log_each_success", False)
        self.log_each_skip = cfg_r.getboolean("log_each_skip", False)
        self.jd_len = cfg_r.getint("progress_every", 50)

        self.use_random_ua = cfg_r.getboolean("use_random_ua", True)
        self.use_random_impersonate = cfg_r.getboolean("use_random_impersonate", True)

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

        self.img_split = cfg_r.get("csv_images_split", ",")

    def load_config(self, config_file):
        """加载配置文件"""
        config = configparser.ConfigParser()
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"配置文件 {config_file} 不存在")

        config.read(config_file, encoding='utf-8')

        if "PATHS" not in config:
            raise KeyError("配置文件没有 [PATHS]")
        if "PROXY" not in config:
            config["PROXY"] = {}
        if "REQUEST" not in config:
            config["REQUEST"] = {}
        return config

    def load_proxies(self):
        """加载代理列表"""
        proxy_file = self.config['PROXY'].get('proxy_file', 'proxies.txt')
        if not os.path.exists(proxy_file):
            print(f"警告: 代理文件 {proxy_file} 不存在，将不使用代理")
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

        print(f"加载了 {len(proxies)} 个代理")
        return proxies

    def resolve_path(self, path):
        if not path:
            return path
        if os.path.isabs(path):
            return path
        return os.path.join(self.base_dir, path)

    def get_random_proxy(self):
        if not self.proxies_list:
            if not self.proxy_warning_printed:
                safe_print("没有可用代理，将直接连接下载")
                self.proxy_warning_printed = True
            return None
        return random.choice(self.proxies_list)

    def atomic_write_bytes(self, content, file_path):
        temp = f"{file_path}.tmp.{threading.get_ident()}"
        with open(temp, "wb") as f:
            f.write(content)
        os.replace(temp, file_path)

    def save_as_webp(self, image_bytes, file_path):
        if (image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP") and not self.reencode_webp:
            self.atomic_write_bytes(image_bytes, file_path)
            return
        temp = f"{file_path}.tmp.{threading.get_ident()}"
        with self.convert_limiter:
            try:
                with Image.open(BytesIO(image_bytes)) as img:
                    img.seek(0)
                    converted = (
                        img.convert("RGBA")
                        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
                        else img.convert("RGB")
                    )
                    try:
                        converted.save(
                            temp, format="WEBP", quality=self.webp_quality,
                            lossless=self.webp_lossless, method=self.webp_method,
                        )
                    finally:
                        converted.close()
                os.replace(temp, file_path)
            except (UnidentifiedImageError, OSError) as exc:
                if os.path.exists(temp):
                    os.remove(temp)
                raise ValueError(f"图片解码/WebP 转换失败: {exc}") from exc

    def is_valid_image_response(self, response, content):
        if response.status_code != 200:
            return False
        ct = (response.headers.get("content-type") or "").lower()
        if ct.startswith("image/"):
            return True
        if content[:2] == b"\xff\xd8" or content[:8] == b"\x89PNG\r\n\x1a\n":
            return True
        if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
            return True
        return False

    def validate_size_headers(self, response):
        cl = response.headers.get("content-length")
        if not cl:
            return
        try:
            size = int(cl)
        except ValueError:
            return
        if size > self.max_image_bytes:
            raise ValueError(f"图片过大 (Content-Length): {size} bytes > {self.max_image_bytes // 1024 // 1024} MB")

    def retry_sleep(self, attempt):
        delay = min(self.retry_max_delay, self.retry_base_delay * (2 ** (attempt - 1)))
        delay += random.uniform(0.5, 1.5)
        time.sleep(delay)

    def random_request_delay(self):
        if self.request_delay_min > 0:
            time.sleep(random.uniform(self.request_delay_min, self.request_delay_max))

    def record_failed_url(self, image_url):
        with FILE_LOCK:
            self.failed_count += 1
            with open(self.failed_log, "a", encoding="utf-8") as f:
                f.write(image_url + "\n")

    def get_image_urls(self):
        script_dir = os.path.dirname(os.path.abspath(__file__)).split('/')[-1].replace('_ljp','')
        default_filename_ls = [f"{script_dir}_quchong.csv",f"{script_dir}_variable.csv"]

        input_csv = self.config['PATHS'].get('input_csv',None)
        if not input_csv:
            for path in default_filename_ls:
                input_csv = path
                if not input_csv or not os.path.exists(input_csv):
                    continue
                else:
                    break
        if not input_csv or not os.path.exists(input_csv):
            raise FileNotFoundError(f"输入文件 {input_csv} 不存在")

        else:
            safe_print(f'使用默认文件:{input_csv}')

        csv_encoding = self.config["REQUEST"].get("csv_encoding", "utf-8-sig")
        df = pd.read_csv(
            input_csv,
            encoding=csv_encoding,
            usecols=lambda column: column == "Images",
        )

        if "Images" not in df.columns:
            raise KeyError("文件没有图片列")

        meta_images = df['Images'].unique().tolist()

        img_split = self.img_split
        images = []
        seen = set()
        for value in meta_images:
            if not isinstance(value, str):
                value = str(value)

            if value.lower() == "nan":
                continue

            if self.img_split not in value and ',http' in value:
                img_split = ','

            for url in value.split(img_split):
                url = url.strip()
                if url and url not in seen:
                    seen.add(url)
                    images.append(url)

        images = list(set(filter(None, images)))
        print(f"从CSV中提取到 {len(images)} 个唯一图片URL")
        return images

    def download_image(self, image_url):
        filename = generate_image_filename(image_url)
        output_dir = self.resolve_path(self.config["PATHS"].get("output_images", "./images"))
        file_path = os.path.join(output_dir, filename)

        if os.path.exists(file_path):
            if self.log_each_skip:
                safe_print(f"跳过已存在: {filename}")
            return None

        parsed_uri = urlparse(image_url)
        referer = f"{parsed_uri.scheme}://{parsed_uri.netloc}/"
        origin = referer.rstrip("/")

        session = None

        for attempt in range(1, self.max_attempts + 1):
            response = None
            try:
                if attempt == 1 or session is None:
                    imp = (
                        random.choice(IMPERS_TYPES)
                        if self.use_random_impersonate else IMPERS_TYPES[0]
                    )
                    if session:
                        try:
                            session.close()
                        except Exception:
                            pass
                    session = requests.Session(
                        timeout=self.request_timeout, impersonate=imp,
                    )

                self.random_request_delay()
                proxy = self.get_random_proxy()

                headers = self.image_headers_base.copy()
                headers["referer"] = referer
                headers["origin"] = origin
                headers["user-agent"] = (
                    random.choice(USER_AGENTS)
                    if self.use_random_ua else USER_AGENTS[0]
                )
                if len(image_url) >= 1000:
                    url = image_url[:1000]
                    safe_print(f'[WAR] url 过长:{url[:200]}')
                else:
                    url = image_url

                response = session.get(
                    url, proxies=proxy, headers=headers,
                    impersonate=imp, timeout=self.request_timeout,
                )

                if response.status_code == 403:
                    raise ConnectionError("错误 403")
                if response.status_code != 200:
                    raise ConnectionError(f"非200状态码:{response.status_code}")

                self.validate_size_headers(response)
                content = response.content

                if len(content) > self.max_image_bytes:
                    raise ValueError(f"图片过大: {len(content)} bytes")

                if self.is_valid_image_response(response, content):
                    os.makedirs(output_dir, exist_ok=True)
                    self.save_as_webp(content, file_path)
                    if self.log_each_success:
                        safe_print(f"已下载:{filename}:{image_url}")
                    return None

                raise ValueError("无效图片内容")

            except Exception as exc:
                sc = getattr(response, "status_code", "N/A") if response else "N/A"
                safe_print(f"第 {attempt} 次失败: HTTP {sc} - {exc}, url={image_url[:60]}...")
                if session:
                    try:
                        session.close()
                    except Exception:
                        pass
                session = None
            finally:
                if response is not None:
                    close_fn = getattr(response, "close", None)
                    if callable(close_fn):
                        try:
                            close_fn()
                        except Exception:
                            pass

            if attempt < self.max_attempts:
                self.retry_sleep(attempt)

        if session:
            try:
                session.close()
            except Exception:
                pass
        self.record_failed_url(image_url)
        return image_url

    def run(self):
        try:
            images = self.get_image_urls()
            if not images:
                print("没有找到可下载的图片URL")
                return

            total = len(images)
            safe_print(f"开始下载: 共 {total} 个, workers={self.max_workers}")

            started = time.monotonic()
            q = queue.Queue(maxsize=self.max_workers * 2)
            c_lock = threading.Lock()
            cnt = [0]  # 列表包装，闭包内可变

            def worker():
                while True:
                    url = q.get()
                    if url is None:
                        q.task_done()
                        break
                    try:
                        self.download_image(url)
                    except Exception as exc:
                        safe_print(f"Worker 异常: {exc}")
                    finally:
                        q.task_done()
                        with c_lock:
                            cnt[0] += 1
                            n = cnt[0]
                        if n % self.jd_len == 0 or n == total:
                            safe_print(
                                f'\n\n'
                                f"进度: {n}/{total}, "
                                f"失败={self.failed_count}, "
                                f"耗时={max(0.1, time.monotonic() - started):.1f}s"
                                f'\n\n'
                            )

            # 启动消费者线程
            workers = []
            for _ in range(self.max_workers):
                t = threading.Thread(target=worker, daemon=True)
                t.start()
                workers.append(t)

            # 生产者：逐条投喂，队列满时自动阻塞 → 天然背压
            for url in images:
                q.put(url)

            q.join()  # 等待全部 task_done

            for _ in workers:
                q.put(None)
            for t in workers:
                t.join()

            safe_print(f"\n下载完成! 总共失败: {self.failed_count}")

        except KeyboardInterrupt:
            safe_print(f"\n[用户终止] 已记录失败数: {self.failed_count}")
        except Exception as exc:
            safe_print(f"下载出错: {exc}")




def main():
    don = IMG_download_ljp()
    don.run()


if __name__ == "__main__":
    main()