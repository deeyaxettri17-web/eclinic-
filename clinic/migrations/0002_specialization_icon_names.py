import re

from django.db import migrations

# Specialization.icon used to hold an emoji; it now holds a Bootstrap Icons name.
# Convert the emojis the old demo data used, and clear anything else that is
# not a valid icon name so the template falls back to its default icon.
EMOJI_TO_ICON = {
    '\U0001FA7A': 'thermometer-half',  # stethoscope
    '\u2764\ufe0f': 'heart-pulse',     # red heart
    '\u2764': 'heart-pulse',           # red heart, without variation selector
    '\U0001F9F4': 'droplet-half',      # lotion bottle
    '\U0001F9F8': 'balloon',           # teddy bear
    '\U0001F9B4': 'person-walking',    # bone
    '\U0001F9E0': 'chat-heart',        # brain
}
ICON_NAME = re.compile(r'^[a-z0-9-]*$')


def emojis_to_icon_names(apps, schema_editor):
    Specialization = apps.get_model('clinic', 'Specialization')
    for spec in Specialization.objects.all():
        if ICON_NAME.match(spec.icon):
            continue
        spec.icon = EMOJI_TO_ICON.get(spec.icon.strip(), '')
        spec.save(update_fields=['icon'])


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(emojis_to_icon_names, migrations.RunPython.noop),
    ]
