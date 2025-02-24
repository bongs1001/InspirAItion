from django.db import migrations

def create_initial_charge_code(apps, schema_editor):
    ChargeCode = apps.get_model('accounts', 'ChargeCode')
    ChargeCode.objects.create(code='team6', amount=5000)

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0006_reset_all_balances'),
    ]

    operations = [
        migrations.RunPython(create_initial_charge_code),
    ]