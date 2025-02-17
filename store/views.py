from django.shortcuts import render,redirect,get_object_or_404

from django.views.generic import View

from store.forms import SignUpForm,LoginForm,OrderForm,ReviewForm

from django.core.mail import send_mail

from store.models import User,Size,BasketItem,OrderItem,Order,MedicineType

from django.db.models import Q

from django.contrib import messages

from django.contrib.auth import authenticate,login,logout

from store.models import Product,ReviewRating

from django.core.paginator import Paginator

from django.views.decorators.csrf import csrf_exempt

from django.utils.decorators import method_decorator

from decouple import config

from django.template.loader import render_to_string

from django.http import HttpResponse

from store.decorators import signin_required

from django.views.decorators.cache import never_cache

from django.core.exceptions import ValidationError

RZP_KEY_ID=config('RZP_KEY_ID')

RZP_KEY_SECRET=config('RZP_KEY_SECRET')

decs=[signin_required,never_cache]


def send_otp_email(user):

    user.generate_otp()

    subject="verify your email"

    message=f"otp for account verification is {user.otp}"

    from_email="ajimon031@gmail.com"

    to_email=[user.email]

    send_mail(subject,message,from_email,to_email )

    
class SignUpView(View):

    template_name="register.html"

    form_class=SignUpForm

    def get(self,request,*args,**kwargs):

        form_instance=self.form_class()

        return render(request,self.template_name,{"form":form_instance})

    def post(self,request,*args,**kwargs):

        form_data=request.POST 

        form_instance=self.form_class(form_data)

        if form_instance.is_valid():

            user_object=form_instance.save(commit=False)

            user_object.is_active=False

            user_object.save()

            send_otp_email(user_object)

            return redirect("verify-email")

        return render(request,self.template_name,{"form":form_instance})

class VerifyEmailView(View):

    template_name="verify_email.html"

    def get(self,request,*args,**kwargs):

        return render(request,self.template_name)

    def post(self,request,*args,**kwargs):

        otp=request.POST.get("otp")

        try:

            user_object=User.objects.get(otp=otp)

            user_object.is_active=True

            user_object.is_verified=True

            user_object.otp=None

            user_object.save()

            return redirect("signin")

        except:

            messages.error(request,"invalid otp")

            return render(request,self.template_name)

class SignInView(View):

    template_name="login.html"

    form_class=LoginForm

    def get(self,request,*args,**kwargs):

        form_instance=self.form_class()

        return render(request,self.template_name,{"form":form_instance})

    def post(self,request,*args,**kwargs):

        form_data=request.POST 

        form_instance=self.form_class(form_data)

        if form_instance.is_valid():

            uname=form_instance.cleaned_data.get("username")

            pwd=form_instance.cleaned_data.get("password")

            user_object=authenticate(request,username=uname,password=pwd)

            if user_object:

                login(request,user_object)

                return redirect("product-list")

        return render(request,self.template_name,{"form":form_instance})

class SignOutView(View):

    def get(self,request,*args,**kwargs):

        logout(request)

        return redirect("signin")

@method_decorator(decs,name="dispatch")
class ProductListView(View):

    template_name="index.html"

    def get(self, request, *args, **kwargs):

        search_text = request.GET.get("filter", "")

        qs = Product.objects.all()
        

        if search_text:
            qs = qs.filter(Q(title__icontains=search_text) |Q(medicinetype_object__MedicineType__icontains=search_text) |Q(manufacture__icontains=search_text)
            )
            messages.success(request, "Product list fetched successfully")

        paginator = Paginator(qs, 9)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        all_medicine_type = MedicineType.objects.values_list("MedicineType", flat=True).distinct()

        all_medicine = Product.objects.values_list("title", flat=True).distinct()
        
        all_manufacturer = Product.objects.values_list("manufacture", flat=True).distinct()

        all_records = list(all_medicine_type) + list(all_medicine) + list(all_manufacturer)

        return render(request, self.template_name, {"page_obj": page_obj, "data": qs, "records": all_records})

@method_decorator(decs,name="dispatch")
class productDetailView(View):

    template_name="product_detail.html"

    def get(self,request,*args,**kwargs):

        id=kwargs.get("pk")

        qs=Product.objects.get(id=id)

        reviews=ReviewRating.objects.filter(product=qs)

        return render(request,self.template_name,{"product":qs,"reviews":reviews})





@method_decorator(decs, name="dispatch")
class AddToCartView(View):

    def post(self, request, *args, **kwargs):

        product_id = kwargs.get('pk')

        quantity = int(request.POST.get('quantity', 1))

        size_id = request.POST.get('size_id')

        product = get_object_or_404(Product, id=product_id)

        basket = request.user.cart  

        try:
            basket_item = BasketItem.objects.get(
                product_object=product,

                size_object_id=size_id,

                basket_object=basket,

                is_order_placed=False
            )
            basket_item.quantity += quantity

            basket_item.clean()

            basket_item.save()

        except BasketItem.DoesNotExist:

            basket_item = BasketItem(
                product_object=product,
                quantity=quantity,
                size_object_id=size_id,
                basket_object=basket
            )
            
            try:
                basket_item.clean()  

                basket_item.save()

            except ValidationError as e:

                messages.error(request, e.message)

                return redirect('product-detail', pk=product_id)

        except ValidationError as e:

            messages.error(request, e.message)

            return redirect('product-detail', pk=product_id)

        current_total = sum(item.item_total for item in basket.cart_item.all())

        new_item_total = product.price * quantity

        new_total = current_total + new_item_total

        if new_total > 5000:

            return redirect('cart-summary')

        return redirect('cart-summary')

@method_decorator(csrf_exempt, name='dispatch')  
class UpdateQuantityView(View):
    def post(self, request, item_id, *args, **kwargs):  # Accept item_id from URL
        try:
            new_quantity = request.POST.get("quantity")  # Get quantity from form data
            if new_quantity:
                basket_item = BasketItem.objects.get(id=item_id)
                basket_item.quantity = int(new_quantity)
                basket_item.save()

        except BasketItem.DoesNotExist:
            pass  

        return redirect('cart-summary')

@method_decorator(decs,name="dispatch")
class CartSummaryView(View):
    template_name = "cart_summary.html"

    def get(self, request, *args, **kwargs):
        qs = BasketItem.objects.filter(basket_object=request.user.cart, is_order_placed=False)
        basket_item_count = qs.count()
        basket_total = sum([bi.item_total for bi in qs])
        return render(request, self.template_name, {"basket_items": qs, "basket_total": basket_total, "basket_item_count": basket_item_count})

    def post(self, request, *args, **kwargs):
        item_id = request.POST.get('item_id')
        new_quantity = int(request.POST.get('quantity', 1))

        basket_item = get_object_or_404(BasketItem, id=item_id, basket_object=request.user.cart, is_order_placed=False)

        if new_quantity > 11:
            messages.error(request, "Quantity cannot exceed 11.")
            return redirect('cart-summary')

        basket_item.quantity = new_quantity

        try:
            basket_item.clean()
            basket_item.save()
            messages.success(request, "Item quantity updated successfully.")
        except ValidationError as e:
            messages.error(request, e.message)

        return redirect('cart-summary')



# class CartSummaryView(View):

#     template_name="cart_summary.html"

#     def get(self,request,*args,**kwargs):

#         qs=BasketItem.objects.filter(basket_object=request.user.cart,is_order_placed=False)

#         basket_item_count=qs.count()

#         basket_total=sum([bi.item_total for bi in qs])

#         return render(request,self.template_name,{"basket_items":qs,"basket_total":basket_total,"basket_item_count":basket_item_count})
    
@method_decorator(decs,name="dispatch")
class ItemDeleteView(View):

    def get(self,request,*args,**kwargs):

        id=kwargs.get("pk")

        BasketItem.objects.get(id=id).delete()

        return redirect("cart-summary")


import razorpay

@method_decorator(decs,name="dispatch")
class PlaceOrderView(View):

    form_class=OrderForm

    template_name="order.html"

    def get(self,request,*args,**kwargs):

        form_instance=self.form_class()

        qs=request.user.cart.cart_item.filter(is_order_placed=False)

        total=sum([bi.item_total for bi in qs])

        return render(request,self.template_name,{"form":form_instance,"items":qs,"total":total})


    def post(self,request,*args,**kwargs):

        form_data=request.POST 

        form_instance=self.form_class(form_data)

        form_instance.instance.customer=request.user

        if form_instance.is_valid():

            order_instance=form_instance.save()

            basket_item=request.user.cart.cart_item.filter(is_order_placed=False)

            payment_method=form_instance.cleaned_data.get("payment_method")

            print(payment_method)

            for bi in basket_item:

                OrderItem.objects.create(
                    order_object=order_instance,
                    product_object=bi.product_object,
                    quantity=bi.quantity,
                    # size_object=bi.size_object,
                    price=bi.product_object.price
                )

                bi.is_order_placed=True

                bi.save()

            if payment_method=="ONLINE":

                client = razorpay.Client(auth=(RZP_KEY_ID,RZP_KEY_SECRET))

                total=sum([bi.item_total for bi in basket_item])*100

                data = { "amount": total, "currency": "INR", "receipt": "order_rcptid_11" }

                payment = client.order.create(data=data)

                print(payment)

                rzp_order_id=payment.get("id")

                order_instance.rzp_order_id=rzp_order_id

                order_instance.save()

                context={
                    "amount":total,
                    "key_id":RZP_KEY_ID,
                    "order_id":rzp_order_id,
                    "currency":"INR"
                }

                return render(request,"payment.html",context)



        return redirect("product-list")

@method_decorator(decs,name="dispatch")
class OrderSummaryView(View):

    template_name="order_summary.html"

    def get(self,request,*args,**kwargs):

        qs=request.user.orders.all().order_by("-created_date")

        return render(request,self.template_name,{"orders":qs})

@method_decorator([csrf_exempt],name="dispatch")
class PaymentVerificationView(View):


    def post(self,request,*args,**kwargs):

        client = razorpay.Client(auth=(RZP_KEY_ID,RZP_KEY_SECRET))

        try:
            client.utility.verify_payment_signature(request.POST)
            print("payment sucess")

            order_id=request.POST.get("razorpay_order_id")

            order_object=Order.objects.get(rzp_order_id=order_id)

            order_object.is_paid=True

            order_object.save()
            
            login(request,order_object.customer)
            
        except:
            print("payment failed")

        


        return redirect("order-summary")





@method_decorator(decs,name="dispatch")
class InvoiceDownloadView(View):

    def get(self, request, order_id, *args, **kwargs):

            order = Order.objects.get(id=order_id, customer=request.user)

            html_invoice = render_to_string('invoice.html', {'order': order, 'order_items':  order.orderitems.all()})

            response = HttpResponse(html_invoice, content_type='text/html')

            response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.html"'

            return response
        


@method_decorator(decs, name="dispatch")
class SubmitReviewView(View):

    form_class = ReviewForm

    template_name = "product_detail.html"

    def get(self, request, *args, **kwargs):

        form_instance = self.form_class()

        return render(request, self.template_name, {"form": form_instance})

    def post(self, request, *args, **kwargs):

        form_data = request.POST

        form_instance = self.form_class(form_data)

        product = get_object_or_404(Product, pk=kwargs.get("pk"))

        has_purchased = OrderItem.objects.filter(
            order_object__customer=request.user,
            product_object=product
        ).exists()

        if not has_purchased:
            messages.error(request, "You can only review products you have purchased.")

            return redirect("product-detail", pk=product.pk)

        has_reviewed = ReviewRating.objects.filter(
            product=product,
            user=request.user
        ).exists()

        if has_reviewed:
            messages.error(request, "You have already reviewed this product.")

            return redirect("product-detail", pk=product.pk)

        if form_instance.is_valid():

            review = form_instance.save(commit=False)

            review.product = product

            review.user = request.user

            review.save()

            messages.success(request, "Review added successfully.")

            return redirect("product-detail", pk=product.pk)

        messages.error(request, "Review not added.")

        return render(request, self.template_name, {"form": form_instance})
