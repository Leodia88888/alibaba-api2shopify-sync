import schedule
import time
import logging
from sync import sync_all_products
from db import initialize_db
from config import SYNC_INTERVAL_MINUTES

def main():
    # 初始化数据库（创建映射表）
    initialize_db()

    logging.info("开始初次同步任务")
    sync_all_products()

    # 设置定时任务，建议将 SYNC_INTERVAL_MINUTES 调低（如 1 或 5 分钟），便于更频繁同步
    schedule.every(SYNC_INTERVAL_MINUTES).minutes.do(sync_all_products)
    logging.info("定时任务已设置，每 %s 分钟同步一次", SYNC_INTERVAL_MINUTES)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
