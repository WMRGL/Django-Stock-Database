from stock_web.models import Inventory, Internal, potentials
from django.db import transaction

start_idx = potentials.index(tuple("GKR0"))
end_idx = potentials.index(tuple("GKSR"))

batch_numbers_to_delete = ["".join(potentials[i]) for i in range(start_idx, end_idx + 1)]

with transaction.atomic():
    internals_to_delete = Internal.objects.filter(batch_number__in=batch_numbers_to_delete)
    items_to_delete = Inventory.objects.filter(internal__in=internals_to_delete)

    if items_to_delete.exists():
        reagent = items_to_delete.first().reagent

        if reagent.track_vol:
            vol_to_remove = sum(item.current_vol for item in items_to_delete)
            reagent.count_no -= vol_to_remove
        else:
            reagent.count_no -= items_to_delete.count()

        reagent.save()

        items_to_delete.delete()
        internals_to_delete.delete()

        print(f"Successfully deleted {len(batch_numbers_to_delete)} records.")