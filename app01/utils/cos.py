# -*- coding=utf-8
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
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

    # 1. 设置用户属性, 包括 secret_id, secret_key, region等。Appid 已在 CosConfig 中移除，请在参数 Bucket 中带上 Appid。Bucket 由 BucketName-Appid 组成
    secret_id = os.environ[
        'COS_SECRET_ID']  # 用户的 SecretId，建议使用子账号密钥，授权遵循最小权限指引，降低使用风险。子账号密钥获取可参见 https://cloud.tencent.com/document/product/598/37140
    secret_key = os.environ[
        'COS_SECRET_KEY']  # 用户的 SecretKey，建议使用子账号密钥，授权遵循最小权限指引，降低使用风险。子账号密钥获取可参见 https://cloud.tencent.com/document/product/598/37140
    region = 'ap-nanjing'  # 替换为用户的 region，已创建桶归属的 region 可以在控制台查看，https://console.cloud.tencent.com/cos5/bucket
    # COS 支持的所有 region 列表参见 https://cloud.tencent.com/document/product/436/6224

    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, )
    client = CosS3Client(config)

    response = client.create_bucket(
        Bucket=bucket,
        ACL="public-read",
    )
