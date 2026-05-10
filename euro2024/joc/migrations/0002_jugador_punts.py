from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('joc', '0001_initial'),
    ]

    operations = [
        migrations.AddField(model_name='jugador', name='punts_setzens', field=models.PositiveSmallIntegerField(default=0)),
        migrations.AddField(model_name='jugador', name='punts_vuitens', field=models.PositiveSmallIntegerField(default=0)),
        migrations.AddField(model_name='jugador', name='punts_quarts', field=models.PositiveSmallIntegerField(default=0)),
        migrations.AddField(model_name='jugador', name='punts_semis', field=models.PositiveSmallIntegerField(default=0)),
        migrations.AddField(model_name='jugador', name='punts_tercer', field=models.PositiveSmallIntegerField(default=0)),
        migrations.AddField(model_name='jugador', name='punts_final', field=models.PositiveSmallIntegerField(default=0)),
        migrations.AddField(model_name='jugador', name='punts_quadre_final', field=models.PositiveSmallIntegerField(default=0)),
        migrations.CreateModel(
            name='PronosticEquipFase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fase', models.CharField(choices=[('R32', 'Setzens de final'), ('R16', 'Vuitens de final'), ('QF', 'Quarts de final'), ('SF', 'Semifinals'), ('3rd', 'Tercer i quart lloc'), ('F', 'Final')], max_length=3)),
                ('posicio', models.PositiveSmallIntegerField(default=0)),
                ('equip', models.ForeignKey(on_delete=models.deletion.CASCADE, to='joc.equip')),
                ('jugador', models.ForeignKey(on_delete=models.deletion.CASCADE, to='joc.jugador')),
            ],
            options={'unique_together': {('jugador', 'fase', 'equip')}},
        ),
    ]
