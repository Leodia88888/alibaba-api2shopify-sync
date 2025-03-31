import os
import time
import hashlib
import tempfile
import logging
import config  # 引入全局配置，包括自定义 session
from requests.exceptions import RequestException

print("✅ Cloudinary 配置检测：")
print("CLOUD_NAME:", os.getenv("CLOUDINARY_CLOUD_NAME"))
print("API_KEY:", os.getenv("CLOUDINARY_API_KEY"))
print("API_SECRET:", os.getenv("CLOUDINARY_API_SECRET"))

def upload_url_to_cloudinary(url, folder="alibaba-sync"):
    try:
        # 使用全局 session 下载临时文件
        response = config.session.get(url, stream=True)
        if response.status_code != 200:
            raise Exception(f"下载失败: {url}")
        # 获取文件后缀（如果没有则默认 .jpg）
        suffix = os.path.splitext(url.split("?")[0])[1] or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            for chunk in response.iter_content(chunk_size=8192):
                tmp.write(chunk)
            tmp_path = tmp.name

        # 构造 Cloudinary 上传 API URL
        upload_url = f"https://api.cloudinary.com/v1_1/{config.CLOUDINARY_CLOUD_NAME}/image/upload"

        # 计算 timestamp
        timestamp = str(int(time.time()))
        # 构造需要签名的参数字典（不包括 file 和 api_key、signature）
        params_to_sign = {
            "folder": folder,
            "overwrite": "true",
            "timestamp": timestamp,
            "unique_filename": "false",
            "use_filename": "true"
        }
        # 按 key 升序排序并拼接成字符串，格式：key1=value1&key2=value2&...
        sorted_keys = sorted(params_to_sign.keys())
        string_to_sign = "&".join(f"{k}={params_to_sign[k]}" for k in sorted_keys)
        # 拼接 API_SECRET 后计算 SHA1 哈希
        string_to_sign += config.CLOUDINARY_API_SECRET
        signature = hashlib.sha1(string_to_sign.encode('utf-8')).hexdigest()

        data = {
            "api_key": config.CLOUDINARY_API_KEY,
            "timestamp": timestamp,
            "signature": signature,
            "folder": folder,
            "use_filename": "true",
            "unique_filename": "false",
            "overwrite": "true",
            "resource_type": "auto"
        }

        # 构造文件参数，上传时以 multipart/form-data 形式提交
        with open(tmp_path, "rb") as f:
            files = {"file": f}
            # 使用全局 session 发起 POST 请求上传文件
            upload_response = config.session.post(upload_url, data=data, files=files)

        # 删除临时文件
        try:
            os.remove(tmp_path)
        except Exception as e:
            logging.warning("删除临时文件失败: %s", e)

        if upload_response.status_code == 200:
            result = upload_response.json()
            return result.get("secure_url")
        else:
            logging.error("Cloudinary 上传失败, 状态码: %s, 响应: %s", upload_response.status_code, upload_response.text)
            return None
    except Exception as e:
        logging.error("❌ 上传失败: %s - %s", url, str(e))
        return None
