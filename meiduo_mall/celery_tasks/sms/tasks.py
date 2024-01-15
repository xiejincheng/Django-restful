from celery_tasks.celery import app
from meiduo_mall.libs.yuntongxun.sms import CCP


@app.task(bind=True)
def send_message(self,mobile,sms_code):
    #测试耗时
    # import time
    # time.sleep(10)

    #1, 发送短信
    try:
        result = CCP().send_template_sms(mobile, [sms_code, 5], 1)
    except Exception as e:
        result = -1

    #2,判断是否发送成功
    if result == -1:
        #重试, exc: 发送短信失败报的异常,  countdown: 间隔几秒重试, max_retries:重试的次数
        self.retry(exc=Exception("发送短信失败"),countdown=5,max_retries=3)

