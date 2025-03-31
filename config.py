import os
import logging
from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 阿里巴巴 API 配置
ALIBABA_APP_KEY = os.getenv("ALIBABA_APP_KEY")
ALIBABA_APP_SECRET = os.getenv("ALIBABA_APP_SECRET")
ALIBABA_ACCESS_TOKEN = os.getenv("ALIBABA_ACCESS_TOKEN")
ALIBABA_API_URL = "https://open-api.alibaba.com/sync"

# Shopify API 配置
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_API_URL = f"https://{SHOPIFY_STORE_URL}/admin/api/2023-10/products.json"

# Cloudinary 配置（假设你已配置上传图片的相关信息）
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

# 其他配置
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "ENGLISH")
SYNC_INTERVAL_MINUTES = int(os.getenv("SYNC_INTERVAL_MINUTES", "30"))
EMAIL_ALERT = os.getenv("EMAIL_ALERT", "your_email@example.com")  # 报警通知邮箱

# 创建全局 Session 对象，并设置连接池大小
session = requests.Session()
adapter = HTTPAdapter(pool_connections=10, pool_maxsize=10)
session.mount('https://', adapter)
session.mount('http://', adapter)

MAX_ALIBABA_PAGES = int(os.getenv("MAX_ALIBABA_PAGES", "100"))
