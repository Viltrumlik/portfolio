from django.db import migrations


def install(apps, schema_editor):
    from automations.defaults import ensure_builtin_rules

    ensure_builtin_rules(apps.get_model("automations", "Rule"))


def remove(apps, schema_editor):
    apps.get_model("automations", "Rule").objects.filter(is_builtin=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("automations", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(install, remove),
    ]
