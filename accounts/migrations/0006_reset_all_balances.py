from django.db import migrations

def reset_all_balances(apps, schema_editor):
    Profile = apps.get_model('accounts', 'Profile')
    Profile.objects.all().update(balance=0)

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0005_chargecode'),
    ]

    operations = [
        migrations.RunPython(reset_all_balances),
    ]