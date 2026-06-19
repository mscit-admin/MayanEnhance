from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ExternalShare',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Token')),
                ('target_type', models.CharField(choices=[('document', 'Document'), ('cabinet', 'Cabinet')], db_index=True, max_length=32, verbose_name='Target type')),
                ('target_id', models.PositiveIntegerField(db_index=True, verbose_name='Target ID')),
                ('permission', models.CharField(choices=[('view', 'View only'), ('download', 'View and download')], default='view', max_length=16, verbose_name='Permission')),
                ('password_hash', models.CharField(blank=True, max_length=128, verbose_name='Password hash')),
                ('expires_at', models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='Expires at')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('label', models.CharField(blank=True, max_length=255, verbose_name='Label')),
                ('datetime_created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('creator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='external_shares', to=settings.AUTH_USER_MODEL, verbose_name='Creator')),
            ],
            options={
                'ordering': ('-datetime_created',),
                'verbose_name': 'External share',
                'verbose_name_plural': 'External shares',
            },
        ),
    ]
