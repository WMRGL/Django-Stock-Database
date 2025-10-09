from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group
from stock_web.models import STAFF


class Command(BaseCommand):
    help = (
        "Syncs user first name, last name, and email from the STAFF database table "
        'and ensures they are in the "User" group.'
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting user synchronization..."))

        try:
            user_group = Group.objects.get(name="User")
        except Group.DoesNotExist:
            raise CommandError(
                'The "User" group does not exist. Please create it in the admin panel.'
            )

        users = User.objects.all()
        updated_count = 0
        skipped_count = 0

        for user in users:
            try:
                staff_record = STAFF.objects.get(STAFF_CODE=user.username)

                if staff_record.NAME and staff_record.EMAIL:
                    fullname = staff_record.NAME.split()
                    if len(fullname) > 1:
                        user.first_name = fullname[0]
                        user.last_name = fullname[-1]
                    elif fullname:
                        user.first_name = fullname[0]
                        user.last_name = ""  # Ensure last_name is cleared if not present

                    user.email = staff_record.EMAIL
                    user.groups.add(user_group)
                    user.save()
                    updated_count += 1
                    self.stdout.write(f"Updated user: {user.username}")

            except STAFF.DoesNotExist:
                self.stdout.write(f"No STAFF record found for user: {user.username}. Skipping.")
                skipped_count += 1
                continue

        self.stdout.write(self.style.SUCCESS(f"\nSynchronization complete."))
        self.stdout.write(self.style.SUCCESS(f"Successfully updated {updated_count} users."))
        self.stdout.write(self.style.WARNING(f"Skipped {skipped_count} users (not found in STAFF table)."))