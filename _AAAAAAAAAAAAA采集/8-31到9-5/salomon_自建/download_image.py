import pandas as pd
import os
from curl_cffi import requests
import configparser
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import warnings
from PIL import Image
import tempfile
from urllib.parse import unquote
import threading  # 新增：用于线程安全的计数器

warnings.filterwarnings("ignore")


class ImageDownloader:
    def __init__(self, config_file='config.ini'):
        self.config = self.load_config(config_file)
        self.proxies_list = self.load_proxies()
        self.failed_images = []
        self.proxy_warning_printed = False
        # 新增：进度跟踪
        self.completed_count = 0
        self.total_count = 0
        self.count_lock = threading.Lock()

    def load_config(self, config_file):
        """加载配置文件"""
        config = configparser.ConfigParser()
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"配置文件 {config_file} 不存在")

        config.read(config_file, encoding='utf-8')
        return config

    def load_proxies(self):
        """加载代理列表"""
        proxy_file = self.config['PROXY'].get('proxy_file', 'proxies.txt')
        if not os.path.exists(proxy_file):
            print(f"警告: 代理文件 {proxy_file} 不存在，将不使用代理")
            return []

        proxies = []
        with open(proxy_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 4:
                        ip, port, username, password = parts[:4]
                        proxy_url = f"http://{username}:{password}@{ip}:{port}"
                        proxies.append({
                            'http': proxy_url,
                            'https': proxy_url
                        })

        print(f"加载了 {len(proxies)} 个代理")
        return proxies

    def get_random_proxy(self):
        """获取随机代理"""
        if not self.proxies_list:
            if not self.proxy_warning_printed:
                print("没有可用代理，将直接连接下载")
                self.proxy_warning_printed = True
            return None
        return random.choice(self.proxies_list)

    def extract_image_urls(self):
        """从CSV文件中提取图片URL"""
        input_csv = self.config['PATHS'].get('input_csv')
        if not os.path.exists(input_csv):
            raise FileNotFoundError(f"输入文件 {input_csv} 不存在")

        df = pd.read_csv(input_csv)
        meta_images = df['Images'].unique().tolist()

        images = []
        for meta_image in meta_images:
            if isinstance(meta_image, str):
                urls = meta_image.split(',')
                images.extend(urls)

        images = list(set(filter(None, images)))
        print(f"从CSV中提取到 {len(images)} 个唯一图片URL")
        return images

    def sanitize_filename(self, image_url):
        """根据URL生成唯一的基准文件名（不含后缀）"""
        decoded_url = unquote(image_url)
        clean_name = decoded_url.split('/')[-1]

        for char in [".", "?", "&", "#", "$", "=", ",", ":", " ", "%"]:
            clean_name = clean_name.replace(char, "_")

        return clean_name.strip('_')

    def update_progress(self, success=True):
        """更新进度显示"""
        with self.count_lock:
            self.completed_count += 1
            progress = self.completed_count / self.total_count * 100
            status = "✓" if success else "✗"
            # 使用 \r 实现同一行刷新
            print(f'\r进度: [{self.completed_count}/{self.total_count}] {progress:.1f}% {status}', end='', flush=True)
            # 如果全部完成，换行
            if self.completed_count >= self.total_count:
                print()

    def download_image(self, image_url):
        """下载单个图片并根据分辨率阶梯式转换为 WebP 格式（内存优化版）"""
        base_filename = self.sanitize_filename(image_url)
        filename = f"{base_filename}.webp"

        output_dir = self.config['PATHS'].get('output_images', './images')
        file_path = os.path.join(output_dir, filename)

        # 检查文件是否已存在
        if os.path.exists(file_path):
            print(f'{filename} 已存在，跳过下载')
            self.update_progress(success=True)
            return None

        max_attempts = self.config['PROXY'].getint('max_attempts', 10)

        for attempt in range(max_attempts):
            temp_file_path = None
            try:
                current_proxy = self.get_random_proxy()

                response = requests.get(
                    image_url,
                    proxies=current_proxy,
                    impersonate='safari',
                    timeout=60,
                    verify=False,
                    stream=True
                )

                if response.status_code == 200:
                    os.makedirs(output_dir, exist_ok=True)

                    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                        temp_file_path = temp_file.name
                        for chunk in response.iter_content(chunk_size=65536):
                            if chunk:
                                temp_file.write(chunk)

                    try:
                        with Image.open(temp_file_path) as img:
                            width, height = img.size
                            total_pixels = width * height

                            if total_pixels >= 3600000:
                                current_quality = 20
                            elif total_pixels >= 900000:
                                current_quality = 50
                            else:
                                current_quality = 80

                            img.save(file_path, "WEBP", quality=current_quality)

                        # 下载成功，更新进度
                        self.update_progress(success=True)
                        return None

                    except Exception as img_err:
                        # 图片格式错误，也算失败
                        self.update_progress(success=False)
                        return image_url

                else:
                    # HTTP错误，继续重试
                    pass

            except Exception as e:
                # 网络错误，继续重试
                pass

            finally:
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                    except:
                        pass

            if attempt < max_attempts - 1:
                time.sleep(1)

        # 所有重试失败
        self.update_progress(success=False)
        return image_url

    def run_download(self):
        """执行下载任务"""
        try:
            images = self.extract_image_urls()

            if not images:
                print("没有找到可下载的图片URL")
                return

            # 设置总数
            self.total_count = len(images)
            self.completed_count = 0
            
            print(f"开始下载，共 {self.total_count} 个图片...")
            print("进度: [0/{}] 0.0%".format(self.total_count), end='', flush=True)

            max_workers = self.config['PROXY'].getint('max_workers', 20)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_image = {
                    executor.submit(self.download_image, image): image
                    for image in images
                }

                for future in as_completed(future_to_image):
                    img_url = future_to_image[future]
                    failed_img = future.result()
                    if failed_img:
                        self.failed_images.append(failed_img)

            # 确保进度显示完成
            print()  # 换行
            self.handle_failed_downloads()

        except Exception as e:
            print(f"\n下载过程中发生错误: {e}")

    def handle_failed_downloads(self):
        """处理下载失败的图片"""
        failed_log = self.config['PATHS'].get('failed_log', 'failed_images.txt')

        if self.failed_images:
            print(f'\n下载失败 {len(self.failed_images)} 个图片')
            # 只打印前5个失败URL作为示例
            if len(self.failed_images) <= 5:
                for img in self.failed_images:
                    print(f'  - {img}')
            else:
                for img in self.failed_images[:5]:
                    print(f'  - {img}')
                print(f'  ... 还有 {len(self.failed_images) - 5} 个失败')

            with open(failed_log, 'w', encoding='utf-8') as f:
                for img in self.failed_images:
                    f.write(img + '\n')
            print(f'失败记录已保存到: {failed_log}')
        else:
            print('✓ 所有图片下载成功!')


def main():
    """主函数"""
    try:
        downloader = ImageDownloader('config.ini')
        downloader.run_download()
    except Exception as e:
        print(f"程序执行失败: {e}")


if __name__ == "__main__":
    main()