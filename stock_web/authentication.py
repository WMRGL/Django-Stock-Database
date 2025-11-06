from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from stock_web.models import STAFF


# Copied from ShireXWorkflowMonitoring with login view added
class ShireBackend(BaseBackend):

    def authenticate(self, request, username=None, password=None):
        is_user_password_valid = False
        # Make sure the username and password are both provided
        if username is None or password is None:
            return None
        try:
            user_valid_obj = STAFF.objects.filter(STAFF_CODE=username, EMPLOYMENT_END_DATE__isnull=True).first()
            # user_valid_obj = get_object_or_404(STAFF, STAFF_CODE__iexact=username, EMPLOYMENT_END_DATE__isnull=True)
            if user_valid_obj.PASSWORD == password:
                is_user_password_valid = True
            # if user_valid_obj is None:
            #     return None
            # for item in user_valid_obj:
            #     # Do the password check separate, because the SQL server comparison
            #     # is not case-sensitive.  Whereas the code below is!
            #     if item.PASSWORD == password:
            #         is_user_password_valid = True

        except Exception:
            return None

        # The following logic is predicated on each user being replicated in
        # the standard Django structure (the User model class)
        if is_user_password_valid:
            try:
                # Try to find the user record in the auth_user table
                user = User.objects.get(username__iexact=username)
            except User.DoesNotExist:
                # If not found create a new user.
                fullname = user_valid_obj.NAME.split()

                # Prepare user attributes in a dictionary
                user_kwargs = {
                    'username': username,
                    'first_name': '',
                    'last_name': '',
                    # 'user_valid_obj.EMAIL or ""' ensures that if the email
                    # is None or an empty string, it defaults to ""
                    # which satisfies the NOT NULL database constraint.
                    'email': user_valid_obj.EMAIL or ''
                }

                if len(fullname) >= 1:
                    user_kwargs['first_name'] = fullname[0]
                if len(fullname) >= 2:
                    user_kwargs['last_name'] = fullname[-1]

                # Create the user from the keyword arguments
                user = User(**user_kwargs)
                user.save()
            return user

        # Otherwise
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None