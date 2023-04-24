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
    cors_config = {
        'CORSRule': [
            {
                'AllowedOrigin': '*',
                'AllowedMethod': ['GET', 'PUT', 'HEAD', 'POST', 'DELETE'],
                'AllowedHeader': '*',
                'ExposeHeader': '*',
                'MaxAgeSeconds': 500
            }
        ]
    }
    client.put_bucket_cors(
        Bucket=bucket,
        CORSConfiguration=cors_config
    )


def upload_file(bucket, region, file_object, key):
    """ 上传图片 """
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY, )
    client = CosS3Client(config)
    client.upload_file_from_buffer(
        Bucket=bucket,
        Body=file_object,
        Key=key,
    )

    return "https://{}.cos.{}.myqcloud.com/{}".format(bucket, region, key)


def delete_file(bucket, region, key):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY, )
    client = CosS3Client(config)
    client.delete_object(
        Bucket=bucket,
        Key=key,
    )


def check_file(bucket, region, key):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY, )
    client = CosS3Client(config)
    data = client.head_object(
        Bucket=bucket,
        Key=key,
    )
    return data


def delete_file_list(bucket, region, key_list):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY, )
    client = CosS3Client(config)
    objects = {
        "Quiet": "true",
        "Object": key_list
    }
    client.delete_objects(
        Bucket=bucket,
        Delete=objects,
    )


def credential(bucket, region):
    from sts.sts import Sts
    config = {
        'duration_seconds': 1800,
        'secret_id': settings.TENCENT_COS_ID,
        'secret_key': settings.TENCENT_COS_KEY,
        'bucket': bucket,
        'region': region,
        'allow_prefix': '*',
        'allow_actions': [
            # 'name/cos:PostObject',
            '*',
        ],
    }
    sts = Sts(config)
    result_dict = sts.get_credential()
    return result_dict


def delete_bucket(bucket, region):
    """ 删除桶
    1. 删除文件
    2. 删除碎片
    3. 删除空桶
    """
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY, )
    client = CosS3Client(config)

    # 1
    while True:
        # 获取桶中文件(最大100个)
        part_objects = client.list_objects(bucket)
        contents = part_objects.get('Contents')
        if not contents:
            # 获取不到时
            break
        # 批量删除
        objects = {
            "Quiet": "true",
            "Object": [{'Key': item["Key"]} for item in contents]
        }
        client.delete_object(bucket, objects)

        if part_objects['IsTruncated'] == 'false':
            break

    # 2
    while True:
        part_uploads = client.list_multipart_uploads(bucket)
        uploads = part_uploads.get('Upload')
        if not uploads:
            break
        for item in uploads:
            client.abort_multipart_upload(bucket, item['Key'], item['UploadId'])
        if part_objects['IsTruncated'] == 'false':
            break

    # 3
    client.delete_bucket(bucket)
