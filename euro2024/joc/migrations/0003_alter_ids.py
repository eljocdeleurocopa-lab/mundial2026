from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('joc', '0002_jugador_punts'),
    ]

    operations = [
        migrations.AlterField(model_name='equip', name='id', field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        migrations.AlterField(model_name='estadi', name='id', field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        migrations.AlterField(model_name='grup', name='id', field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        migrations.AlterField(model_name='jugador', name='id', field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        migrations.AlterField(model_name='partit', name='id', field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        migrations.AlterField(model_name='pronosticequipfase', name='id', field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        migrations.AlterField(model_name='pronosticequipgrup', name='id', field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        migrations.AlterField(model_name='pronosticpartit', name='id', field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        migrations.AlterUniqueTogether(name='pronosticpartit', unique_together={('jugador', 'partit')}),
    ]
