import base

from app01 import models


def run():
    exits = models.PricePolicy.objects.filter(category=1, title='个人免费版').exists()
    if not exits:
        models.PricePolicy.objects.create(
            category=1,
            title='个人免费版',
            price=0,
            project_num=3,
            project_member=2,
            project_space=20,
            project_size=5,
        )
    models.User.objects.filter(id=7).delete()


if __name__ == '__main__':
    run()
