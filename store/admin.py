from django.contrib import admin

from store.models import MedicineType,Size,Product,Unit_type

# Register your models here.

admin.site.register(MedicineType)
admin.site.register(Unit_type)
admin.site.register(Size)
admin.site.register(Product)
