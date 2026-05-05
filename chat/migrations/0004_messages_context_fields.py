from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("onboarding", "0005_alter_quiz_answers_correct_and_more"),
        ("chat", "0003_alter_messages_sent_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="messages",
            name="user_path",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="chat_messages",
                to="onboarding.user_paths",
            ),
        ),
        migrations.AddField(
            model_name="messages",
            name="user_task",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="chat_messages",
                to="onboarding.user_tasks",
            ),
        ),
    ]
