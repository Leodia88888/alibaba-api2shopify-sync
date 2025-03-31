import logging
from bs4 import BeautifulSoup
from tqdm import tqdm
from cloudinary_uploader import upload_url_to_cloudinary

def replace_images_in_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    img_tags = soup.find_all("img")
    for img in tqdm(img_tags, desc="替换图片"):
        src = img.get("src", "")
        if src.startswith("//"):
            src = "https:" + src
        try:
            new_url = upload_url_to_cloudinary(src)
            if new_url:
                img["src"] = new_url
        except Exception as e:
            logging.error("图片上传失败: %s", e)
    return str(soup)

def convert_price_ranges_to_variants(product):
    try:
        discounts = product["product_sku"]["skus"]["sku_definition"][0]["bulk_discount_prices"]["bulk_discount_price"]
    except (KeyError, IndexError, TypeError):
        logging.error("没有找到 bulk_discount_price 阶梯价格")
        # 如果没有阶梯价格，可以考虑返回一个默认变体数据
        default_price = product.get("price")
        if default_price:
            return [{"option1": "1 pcs", "price": str(default_price)}]
        return []
    variants = []
    for item in discounts:
        qty = item.get("start_quantity")
        price = item.get("price")
        if qty and price:
            variant = {"option1": f"{qty}+ pcs", "price": str(price)}
            inventory = item.get("inventory")
            if inventory is not None:
                variant["inventory_quantity"] = inventory
            variants.append(variant)
    return variants


def build_html(product):
    # 构建产品详情 HTML，包括视频、描述及详情图片
    parts = []
    video_url = product.get("video_info", {}).get("video_url")
    if video_url:
        try:
            uploaded_video = upload_url_to_cloudinary(video_url)
            if uploaded_video:
                parts.append(f'<video controls><source src="{uploaded_video}" type="video/mp4"></video>')
        except Exception as e:
            logging.error("视频上传失败: %s", e)
    description = product.get("description", "")
    if description:
        parts.append(f"<div>{description}</div>")
    images = product.get("description_images", {}).get("image_urls", [])
    if images:
        for url in images:
            try:
                uploaded_image = upload_url_to_cloudinary(url)
                if uploaded_image:
                    parts.append(f'<img src="{uploaded_image}" />')
            except Exception as e:
                logging.error("详情图片上传失败: %s", e)
    html = "\n".join(parts)
    return replace_images_in_html(html)

def compare_product_data(shopify_product, alibaba_product):
    differences = {}
    # 比较标题
    shopify_title = shopify_product.get("title", "")
    alibaba_title = alibaba_product.get("subject", "")
    if shopify_title != alibaba_title:
        differences["title"] = {"shopify": shopify_title, "alibaba": alibaba_title}
    # 比较描述
    shopify_body = shopify_product.get("body_html", "")
    alibaba_description = alibaba_product.get("description", "")
    if alibaba_description not in shopify_body:
        differences["description"] = {"shopify": shopify_body, "alibaba": alibaba_description}
    # 比较主图数量（此处示例仅简单对比数量）
    shopify_images = shopify_product.get("images", [])
    alibaba_images = alibaba_product.get("main_image", {}).get("images", {}).get("string", [])
    if len(shopify_images) != len(alibaba_images):
        differences["images"] = {"shopify": len(shopify_images), "alibaba": len(alibaba_images)}
    return differences