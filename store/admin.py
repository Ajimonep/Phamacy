from django.contrib import admin

from store.models import MedicineType,Size,Product,ReviewRating

# Register your models here.

admin.site.register(MedicineType)
admin.site.register(Size)
admin.site.register(Product)
admin.site.register(ReviewRating)
