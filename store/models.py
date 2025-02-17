from django.db import models
from django.contrib.auth.models import AbstractUser
from random import randint
from django.db.models.signals import post_save
from django.core.exceptions import ValidationError
class User(AbstractUser):

    is_verified=models.BooleanField(default=False)

    otp=models.CharField(max_length=50,null=True,blank=True)

    phone=models.CharField(max_length=12,null=True)

    def generate_otp(self):

        self.otp=str(randint(1000,9999))+str(self.id)

        self.save()

class BaseModel(models.Model):

    created_date=models.DateTimeField(auto_now_add=True)

    updated_date=models.DateTimeField(auto_now=True)

    is_active=models.BooleanField(default=True)


class MedicineType(BaseModel):

    MedicineType=models.CharField(max_length=100)

    def __str__(self):
        return self.MedicineType



class Size(BaseModel):

    name=models.CharField(max_length=200)

    def __str__(self):
        return self.name

    
class Product(BaseModel):

    title=models.CharField(max_length=200)

    description=models.TextField()

    price=models.PositiveIntegerField()

    picture=models.ImageField(upload_to="product_pictures",null=True,blank=True)

    medicinetype_object=models.ForeignKey(MedicineType,on_delete=models.CASCADE)

    size_objects=models.ManyToManyField(Size,related_name="sizes")
    
    manufacture=models.CharField(max_length=100)

    def __str__(self):

        return self.title
    

    
class Basket(BaseModel):

    owner=models.OneToOneField(User,on_delete=models.CASCADE,related_name="cart")



class BasketItem(BaseModel):

    product_object=models.ForeignKey(Product,on_delete=models.CASCADE)

    quantity=models.PositiveIntegerField(default=1)

    size_object=models.ForeignKey(Size,on_delete=models.CASCADE,null=True)

    is_order_placed=models.BooleanField(default=False)

    basket_object=models.ForeignKey(Basket,on_delete=models.CASCADE,related_name="cart_item")

    @property
    def item_total(self):

        return self.product_object.price*self.quantity

    def clean(self):
        if self.quantity > 11:
            raise ValidationError('Quantity cannot exceed 11.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Order(BaseModel):

    ORDER_STATUS=(
        ('PENDING','Pending'),
        ('PROCESSING','Processing'),
        ('SHIPPED','Shipped'),
        ('DELIVERED','Delivered')
    )

    customer=models.ForeignKey(User,on_delete=models.CASCADE,related_name="orders")

    Products=models.ForeignKey(Product,on_delete=models.CASCADE,null=True)

    address=models.TextField()

    phone=models.CharField(max_length=20)

    PAYMENT_OPTIONS=(
        ("COD","COD"),
        ("ONLINE","ONLINE")
    )

    payment_method=models.CharField(max_length=15,choices=PAYMENT_OPTIONS,default="COD")

    rzp_order_id=models.CharField(max_length=100,null=True,blank=True)

    is_paid=models.BooleanField(default=False)

    status=models.CharField(max_length=20,choices=ORDER_STATUS,default='PENDING')

    @property
    def order_total(self):

        total=sum([oi.item_total for oi in self.orderitems.all()])

        return total



class OrderItem(BaseModel):

    order_object=models.ForeignKey(
                                   Order,on_delete=models.CASCADE,
                                   related_name="orderitems"
                                   )
    
    product_object=models.ForeignKey(Product,on_delete=models.CASCADE)

    quantity=models.PositiveIntegerField(default=1)

    size_object=models.ForeignKey(Size,on_delete=models.CASCADE,null=True)

    price=models.FloatField()

    @property
    def item_total(self):

        return self.price*self.quantity


def create_basket(sender,instance,created,**kwargs):

    if created:

        Basket.objects.create(owner=instance)

post_save.connect(create_basket,User)


class ReviewRating(models.Model):

    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    subject = models.CharField(max_length=100, blank=True)

    review = models.TextField(max_length=500, blank=True)

    rating = models.FloatField()

    status = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject


