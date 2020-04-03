import os

import celery
import pymysql
from celery.schedules import crontab

from zufang import settings

pymysql.install_as_MySQLdb()

# 加载Django项目配置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zufang.settings')

app = celery.Celery(
	'zufang',
	# broker='redis//:8753.@120.27.241.198:6379/1',
	broker='amqp://loren:8753.@120.27.241.198:5672/zufangwang_vhost',
	backend='redis://:8753.@120.27.241.198:6379/2'
)

# 直接通过代码修改Celery相关配置
# http://docs.celeryproject.org/en/latest/userguide/configuration.html
app.conf.update(
	# 接受的内容
	accept_content=['json', 'pickle'],
	# 任务序列化方式
	task_serializer='pickle',
	# 任务执行结果序列化方式
	result_serializer='json',
	# 时区设置
	timezone=settings.TIME_ZONE,
	# 启用协调世界时
	enable_utc=True,
	# 配置定时任务
	# celery -A zufang beat -l debug 消息的生产者
	# celery -A zufang worker -l debug 消息的消费者
	beat_schedule={
		'task1': {
			'task': 'common.tasks.remove_expired_records',
			'schedule': crontab('0', '2', '*', '*', '*'),
			'args': ()
		},
	},
)

# 从配置文件中读取Celery相关配置
# app.config_from_object('django.conf:settings')
app.autodiscover_tasks(('common',))

