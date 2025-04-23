from django.contrib.postgres.operations import BtreeGistExtension
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        BtreeGistExtension(),
    ] 