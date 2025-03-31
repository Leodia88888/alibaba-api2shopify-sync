import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from api import (
    get_alibaba_product_ids,
    get_alibaba_product,
    create_shopify_product,
    update_shopify_product,
    get_shopify_product
)
from data_processor import build_html, compare_product_data, convert_price_ranges_to_variants
from db import get_shopify_id, save_mapping
from cloudinary_uploader import upload_url_to_cloudinary

def get_shopify_product_by_alibaba_id(alibaba_id):
    """
    根据阿里商品ID，从数据库中获取对应的 Shopify 商品ID，
    并调用 API 获取 Shopify 商品数据。
    """
    shopify_id = get_shopify_id(alibaba_id)
    if shopify_id:
        return get_shopify_product(shopify_id)
    return None

def sync_single_product(product_id):
    # 调用阿里接口获取商品详情
    alibaba_data = get_alibaba_product(product_id)
    product = alibaba_data.get("alibaba_icbu_product_get_response", {}).get("product", {})
    if not product:
        logging.error("未获取到有效的阿里商品数据 (ID: %s)", product_id)
        return

    title = product.get("subject", "Alibaba Product")
    # 构建详情页 HTML（包含视频、描述、详情图）
    html_body = build_html(product)
    # 生成变体数据（阶梯价格等）
    variants = convert_price_ranges_to_variants(product)
    if not variants:
        logging.error("商品 %s 没有有效的变体数据", product_id)
        return

    # ---------------------------
    # 处理主图上传
    # ---------------------------
    main_images = product.get("main_image", {}).get("images", {}).get("string", [])[:6]
    logging.info("正在上传主图，共 %s 张...", len(main_images))
    uploaded_images = []
    for url in main_images:
        try:
            cloud_url = upload_url_to_cloudinary(url)
            if cloud_url:
                uploaded_images.append({"src": cloud_url})
        except Exception as e:
            logging.error("主图上传失败: %s", e)

    # 构造 Shopify 同步所需的 payload，状态设为 active 表示在线商品
    payload = {
        "product": {
            "title": title,
            "body_html": html_body,
            "vendor": "Alibaba Imported",
            "product_type": "Synced Product",
            "tags": f"AlibabaID:{product_id}",
            "status": "active",  # 在线状态
            "options": [{"name": "MOQ"}],
            "images": uploaded_images,
            "variants": variants
        }
    }

    # 判断数据库中是否已有映射记录，存在则更新，否则创建新商品
    alibaba_pid = product.get("product_id") or str(product.get("id"))
    existing_product = get_shopify_product_by_alibaba_id(alibaba_pid)
    if existing_product:
        diffs = compare_product_data(existing_product, product)
        if diffs:
            logging.info("检测到数据差异，更新商品 (Shopify ID: %s)", existing_product.get("id"))
            updated = update_shopify_product(existing_product.get("id"), {"product": payload["product"]})
            if updated:
                logging.info("商品更新成功")
        else:
            logging.info("商品数据一致，无需更新 (Shopify ID: %s)", existing_product.get("id"))
    else:
        new_product = create_shopify_product(payload)
        if new_product:
            save_mapping(alibaba_pid, new_product.get("id"))
            logging.info("成功创建商品到 Shopify (ID: %s)", new_product.get("id"))

def sync_all_products():
    all_ids = set()
    page_size = 30  # 根据接口说明，最大为30
    from config import MAX_ALIBABA_PAGES  # 确保在 config.py 中有这个配置项
    for page_no in range(1, MAX_ALIBABA_PAGES + 1):
        # 修改此处，使用 current_page 参数名称
        product_ids = get_alibaba_product_ids(current_page=page_no, page_size=page_size)
        if not product_ids:
            logging.info("第 %s 页无数据，结束遍历", page_no)
            break
        logging.info("第 %s 页获取到 %s 个商品ID", page_no, len(product_ids))
        all_ids.update(product_ids)
        if len(product_ids) < page_size:
            logging.info("第 %s 页返回数量少于 %s，认为是最后一页", page_no, page_size)
            break

    all_ids = list(all_ids)
    logging.info("总共获取到 %s 个商品ID，开始同步...", len(all_ids))
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_pid = {executor.submit(sync_single_product, pid): pid for pid in all_ids}
        for future in as_completed(future_to_pid):
            pid = future_to_pid[future]
            try:
                future.result()
            except Exception as e:
                logging.error("同步商品 %s 时出现异常: %s", pid, e)
