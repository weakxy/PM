# -*- coding=utf-8
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from django.conf import settings
import sys
import os
import logging


def create_bucket(bucket, region="ap-nanjing"):
    """
    创建桶
    :param bucket: 桶的名称
    :param region: 桶的地域
    :return:
    """
    # 正常情况日志级别使用 INFO，需要定位时可以修改为 DEBUG，此时 SDK 会打印和服务端的通信信息
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY, )
    client = CosS3Client(config)
    client.create_bucket(
        Bucket=bucket,
        ACL="public-read",
    )


def upload_file(bucket, region, file_object, key):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY, )
    client = CosS3Client(config)
    client.upload_file_from_buffer(
        Bucket=bucket,
        Body=file_object,
        Key=key,
    )

    return "https://{}.cos.{}.myqcloud.com/{}".format(bucket, region, key)
