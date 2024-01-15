from django.core.mail import send_mail
from django.conf import settings
from celery_tasks.celery import app
from meiduo_mall.libs.yuntongxun.sms import CCP


@app.task(bind=True)
def send_verify_email(self,verify_url,email):

    #1, 发送短信
    result = -1
    try:
        result = send_mail(subject='美多商城,验证链接',message=verify_url, recipient_list=[email],
                           from_email=settings.EMAIL_FROM)
        # result = send_mail(subject='美多商城,验证链接', recipient_list=[email],
        #                    from_email=settings.EMAIL_FROM,html_message=verify_url)
    except Exception as e:
        result = -1

    #2,判断是否发送成功
    print("result = %s"%result)
    if result == -1:
        #重试, exc: 发送短信失败报的异常,  countdown: 间隔几秒重试, max_retries:重试的次数
        self.retry(exc=Exception("发送邮件失败"),countdown=5,max_retries=3)

