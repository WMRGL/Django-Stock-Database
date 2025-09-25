from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from stock_web.models import STAFF


# Copied from ShireXWorkflowMonitoring with login view added
class ShireBackend(BaseBackend):

    def authenticate(self, request, username=None, password=None):
        is_user_password_valid = False
        # Make sure the username and password are both provided
        if username is None or password is None:
            return None
        try:
            user_valid_obj = STAFF.objects.filter(STAFF_CODE=username, EMPLOYMENT_END_DATE__isnull=True)
            # user_valid_obj = get_object_or_404(STAFF, STAFF_CODE=username, EMPLOYMENT_END_DATE__isnull=True)
            # if user_valid_obj.PASSWORD == password:
            #     is_user_password_valid = True
            if user_valid_obj is None:
                return None
            for item in user_valid_obj:
                # Do the password check separate, because the SQL server comparison
                # is not case-sensitive.  Whereas the code below is!
                if item.PASSWORD == password:
                    is_user_password_valid = True

        except Exception:
            return None

        # The following logic is predicated on each user being replicated in
        # the standard Django structure (the User model class)
        if is_user_password_valid:
            try:
                # Try to find the user record in the auth_user table
                user = User.objects.get(username__iexact=username)
            except User.DoesNotExist:
                # If not found create a new user. There's no need to set a password
                user = User(username=username)
                user.save()
            return user

        # Otherwise
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None