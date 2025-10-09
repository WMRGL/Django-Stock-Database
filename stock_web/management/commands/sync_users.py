from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group
from stock_web.models import STAFF
from django.apps import apps
from django.db import models, transaction
from collections import defaultdict

class Command(BaseCommand):
    help = (
        "Syncs user first name, last name, and email from the STAFF database table "
        'and ensures they are in the "User" group.'
        " Also sets staff/superadmin status and group for specific users."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--merge-users",
            action="store_true",
            help="Merge user accounts with case-insensitive duplicate usernames before syncing.",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting user synchronization..."))

        superadmin_usernames = {"ihon", "rnmn", "jhln", "jsdr", "orln"}

        try:
            # Pre-fetch groups to avoid repeated lookups
            user_group = Group.objects.get(name="User")
            superadmin_group = Group.objects.get(name="Superadmin")
        except Group.DoesNotExist as e:
            raise CommandError(
                f'The "{e.args[0].split()[-1]}" group does not exist. Please create it in the admin panel.'
            )

        if options["merge_users"]:
            self.merge_duplicate_users(superadmin_usernames)

        # Re-fetch users in case some were merged and deleted
        users = User.objects.all()
        updated_count = 0
        skipped_count = 0
        processed_count = 0

        for user in users:
            processed_count += 1
            user_changed = False
            # --- Handle Superadmin logic ---
            if user.username in superadmin_usernames:
                user.is_staff = True
                user.is_superuser = True
                user.groups.set([superadmin_group])
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Processed {user.username} as a Superadmin."
                    )
                )
                user_changed = True
            # --- Handle regular user logic ---
            else:
                user.is_staff = False
                user.is_superuser = False
                user.groups.set([user_group])
                user_changed = True

            # --- Sync details from STAFF table for all users ---
            try:
                staff_record = STAFF.objects.get(STAFF_CODE=user.username)

                if staff_record.NAME and staff_record.EMAIL:
                    fullname = staff_record.NAME.split()
                    name_changed = False
                    email_changed = False

                    if len(fullname) > 1:
                        if user.first_name != fullname[0] or user.last_name != fullname[-1]:
                            user.first_name = fullname[0]
                            user.last_name = fullname[-1]
                            name_changed = True
                            user_changed = True
                    elif fullname:
                        if user.first_name != fullname[0] or user.last_name != "":
                            user.first_name = fullname[0]
                            user.last_name = ""  # Ensure last_name is cleared if not present
                            name_changed = True
                            user_changed = True

                    if user.email != staff_record.EMAIL:
                        user.email = staff_record.EMAIL
                        email_changed = True
                        user_changed = True

                    if user_changed:
                        user.save()
                        updated_count += 1
                        if name_changed or email_changed:
                            self.stdout.write(f"Synced details for user: {user.username}")

            except STAFF.DoesNotExist:
                self.stdout.write(f"No STAFF record found for user: {user.username}. Skipping.")
                skipped_count += 1
                continue

        self.stdout.write(self.style.SUCCESS(f"\nSynchronization complete."))
        self.stdout.write(self.style.SUCCESS(f"Processed {processed_count} users."))
        self.stdout.write(self.style.WARNING(f"Skipped {skipped_count} users (not found in STAFF table)."))

    def merge_duplicate_users(self, superadmin_usernames):
        self.stdout.write(self.style.NOTICE("\n--- Starting User Merge Process ---"))
        
        user_map = defaultdict(list)
        for user in User.objects.all().order_by('pk'):
            user_map[user.username.lower()].append(user)

        for username_lower, user_group in user_map.items():
            if len(user_group) <= 1:
                continue

            self.stdout.write(self.style.WARNING(f"Found duplicate group for '{username_lower}': {[u.username for u in user_group]}"))

            # Determine the primary user to keep
            primary_user = None
            # Prioritize a superadmin username if present
            for u in user_group:
                if u.username in superadmin_usernames:
                    primary_user = u
                    break
            # Otherwise, pick the one with the lowest pk (first created)
            if not primary_user:
                primary_user = user_group[0]

            duplicate_users = [u for u in user_group if u.pk != primary_user.pk]
            self.stdout.write(f"  - Primary user set to: '{primary_user.username}' (ID: {primary_user.pk})")
            self.stdout.write(f"  - Duplicates to be merged: {[u.username for u in duplicate_users]}")

            # Find all models with ForeignKey, OneToOneField, or ManyToManyField to User
            for model in apps.get_models():
                for field in model._meta.get_fields():
                    # Handle ForeignKey and OneToOneField
                    if isinstance(field, (models.ForeignKey, models.OneToOneField)) and field.related_model == User:
                        for dup_user in duplicate_users:
                            with transaction.atomic():
                                related_objects = model.objects.filter(**{field.name: dup_user})
                                if related_objects.exists():
                                    updated_count = related_objects.update(**{field.name: primary_user})
                                    self.stdout.write(f"    - Re-assigned {updated_count} '{model._meta.verbose_name}' records from '{dup_user.username}' to '{primary_user.username}'")

                    # Handle ManyToManyField
                    if isinstance(field, models.ManyToManyField) and field.related_model == User:
                        for dup_user in duplicate_users:
                            with transaction.atomic():
                                related_manager = getattr(dup_user, field.name)
                                related_objects = related_manager.all()
                                if related_objects.exists():
                                    primary_related_manager = getattr(primary_user, field.name)
                                    primary_related_manager.add(*related_objects)
                                    related_manager.clear()
                                    self.stdout.write(f"    - Merged {len(related_objects)} '{field.name}' relations from '{dup_user.username}' to '{primary_user.username}'")

            # Delete the duplicate users
            for dup_user in duplicate_users:
                dup_user.delete()
                self.stdout.write(self.style.SUCCESS(f"  - Successfully deleted duplicate user: '{dup_user.username}'"))
        self.stdout.write(self.style.NOTICE("--- User Merge Process Complete ---\n"))