from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0007_create_initial_charge_code'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ChargeCode',
        ),
        migrations.CreateModel(
            name='ChargeCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ChargeCodeUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('used_at', models.DateTimeField(auto_now_add=True)),
                ('charge_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.chargecode')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('charge_code', 'user')},
            },
        ),
        migrations.RunPython(
            code=lambda apps, schema_editor: apps.get_model('accounts', 'ChargeCode').objects.create(code='team6', amount=5000)
        ),
    ]