from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('joc', '0003_alter_ids'),
    ]

    operations = [
        migrations.AddField(
            model_name='jugador',
            name='lliga',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
    ]
