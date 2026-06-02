from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('joc', '0004_jugador_lliga'),
    ]

    operations = [
        migrations.AddField(
            model_name='partit',
            name='notes',
            field=models.TextField(blank=True, default=''),
        ),
    ]
