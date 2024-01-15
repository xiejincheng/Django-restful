from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

#1, 加载项目环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_mall.settings.dev")

#2, 创建celery对象
app = Celery('meiduo_mall')

#3, 加载配置
app.config_from_object('celery_tasks.config', namespace='CELERY')

#4, 自动注册任务
app.autodiscover_tasks(['celery_tasks.test','celery_tasks.sms','celery_tasks.mail'])

#5, 手动添加任务
# @app.task(bind=True)
# def debug_task(self):
#     print("debug_task....")

# 启动celery:  celery -A celery_tasks.celery worker -l info
# 发送任务: 任务名称.delay(参数)