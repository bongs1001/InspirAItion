from django.db import migrations

def set_initial_ownership(apps, schema_editor):
    Post = apps.get_model('app', 'Post')
    for post in Post.objects.all():
        post.current_owner = post.user
        post.original_creator = post.user
        post.ownership_history = [{
            'owner': post.user.id,
            'date': post.date_posted.isoformat(),
            'type': 'creation'
        }]
        post.save()

def reverse_ownership(apps, schema_editor):
    Post = apps.get_model('app', 'Post')
    for post in Post.objects.all():
        post.current_owner = None
        post.original_creator = None
        post.ownership_history = []
        post.save()

class Migration(migrations.Migration):
    dependencies = [
        ('app', '0004_post_current_owner_post_original_creator_and_more'),
    ]

    operations = [
        migrations.RunPython(set_initial_ownership, reverse_ownership)
    ]