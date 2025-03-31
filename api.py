import time
import hashlib
import hmac
import requests
from urllib.parse import quote
import logging
from config import ALIBABA_APP_KEY, ALIBABA_APP_SECRET, ALIBABA_ACCESS_TOKEN, ALIBABA_API_URL, SHOPIFY_API_URL, SHOPIFY_ACCESS_TOKEN, DEFAULT_LANGUAGE

def get_timestamp():
    return str(int(time.time() * 1000))

def generate_signature(params, app_secret):
    sorted_items = sorted(params.items())
    concat_str = "".join(f"{k}{v}" for k, v in sorted_items)
    return hmac.new(app_secret.encode("utf-8"), concat_str.encode("utf-8"), hashlib.sha256).hexdigest().upper()

def get_alibaba_product_ids(current_page=1, page_size=30):
    params = {
        "app_key": ALIBABA_APP_KEY,
        "access_token": ALIBABA_ACCESS_TOKEN,
        "timestamp": get_timestamp(),
        "sign_method": "sha256",
        "format": "json",
        "method": "alibaba.icbu.product.list",
        "current_page": current_page,  # 修改为 current_page
        "page_size": page_size,        # 注意：最大值为30
        "status": "published",
        "language": DEFAULT_LANGUAGE
    }
    params["sign"] = generate_signature(params, ALIBABA_APP_SECRET)
    encoded = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
    url = f"{ALIBABA_API_URL}?{encoded}"
    try:
        response = requests.get(url)
        data = response.json()
        items = data["alibaba_icbu_product_list_response"]["products"]["alibaba_product_brief_response"]
        product_ids = [item["id"] for item in items]
        logging.info("获取到 %s 个阿里商品ID", len(product_ids))
        return product_ids
    except Exception as e:
        logging.error("获取阿里商品列表失败: %s", e)
        return []


def get_alibaba_product(product_id, language=DEFAULT_LANGUAGE):
    params = {
        "app_key": ALIBABA_APP_KEY,
        "access_token": ALIBABA_ACCESS_TOKEN,
        "method": "alibaba.icbu.product.get",
        "timestamp": get_timestamp(),
        "sign_method": "sha256",
        "format": "json",
        "language": language,
        "product_id": product_id
    }
    params["sign"] = generate_signature(params, ALIBABA_APP_SECRET)
    encoded = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
    url = f"{ALIBABA_API_URL}?{encoded}"
    try:
        response = requests.get(url)
        return response.json()
    except Exception as e:
        logging.error("获取阿里商品详情失败 (ID: %s): %s", product_id, e)
        return {}

def create_shopify_product(payload):
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(SHOPIFY_API_URL, json=payload, headers=headers)
        if response.status_code == 201:
            logging.info("成功创建 Shopify 商品")
            return response.json()["product"]
        else:
            logging.error("创建 Shopify 商品失败: %s", response.text)
            return None
    except Exception as e:
        logging.error("创建 Shopify 商品异常: %s", e)
        return None

def update_shopify_product(shopify_id, payload):
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    update_url = f"{SHOPIFY_API_URL.replace('.json','')}/{shopify_id}.json"
    try:
        response = requests.put(update_url, json=payload, headers=headers)
        if response.status_code == 200:
            logging.info("成功更新 Shopify 商品 (ID: %s)", shopify_id)
            return response.json()["product"]
        else:
            logging.error("更新 Shopify 商品失败: %s", response.text)
            return None
    except Exception as e:
        logging.error("更新 Shopify 商品异常: %s", e)
        return None

def get_shopify_product(shopify_id):
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    url = f"{SHOPIFY_API_URL.replace('.json','')}/{shopify_id}.json"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()["product"]
        else:
            logging.warning("获取 Shopify 商品失败 (ID: %s): %s", shopify_id, response.status_code)
            return None
    except Exception as e:
        logging.error("获取 Shopify 商品异常: %s", e)
        return None