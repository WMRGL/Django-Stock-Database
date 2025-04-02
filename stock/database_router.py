class AccountRouter:
    # We only allow read access for models with the app_label 'stock_web'
    # all other database operations from other apps are performed on the default database

    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'stock_web' and model._meta.model_name == 'staff':
            return 'Shire_Data'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'stock_web' and model._meta.model_name == 'staff':
            return 'Shire_Data'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if (
                obj1._meta.app_label == 'stock_web' and obj1._meta.model_name == 'staff'
                or obj2._meta.app_label == 'stock_web' and obj2._meta.model_name == 'staff'
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'stock_web' and model_name == 'staff':
            return db == 'Shire_Data'
        return None