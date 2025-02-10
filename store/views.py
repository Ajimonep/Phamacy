from django.shortcuts import render,redirect,get_object_or_404

from django.views.generic import View

from store.forms import SignUpForm,LoginForm,OrderForm,ReviewForm

from django.core.mail import send_mail

from store.models import User,Size,BasketItem,OrderItem,Order

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

    def get(self,request,*args,**kwargs):

        qs=Product.objects.all()

        paginator=Paginator(qs,9)

        page_number=request.GET.get("page")

        page_obj=paginator.get_page(page_number)

        print(qs)

        return render(request,self.template_name,{"page_obj":page_obj,"data":qs})

@method_decorator(decs,name="dispatch")
class productDetailView(View):

    template_name="product_detail.html"

    def get(self,request,*args,**kwargs):

        id=kwargs.get("pk")

        qs=Product.objects.get(id=id)

        reviews=ReviewRating.objects.filter(product=qs)

        return render(request,self.template_name,{"product":qs,"reviews":reviews})

@method_decorator(decs,name="dispatch")
class AddToCartView(View):

    def post(self,request,*args,**kwargs):

        id=kwargs.get("pk")

        quantity=request.POST.get("quantity")

        product_object=Product.objects.get(id=id)

        size=request.POST.get("size")

        size_object=Size.objects.get(name=size)


        # unit=product_object.unit

        basket_object=request.user.cart

        BasketItem.objects.create(
            product_object=product_object,
            quantity=quantity,
            size_object=size_object,

            
            basket_object=basket_object
        )

        print("item has been added to cart")

        return redirect("cart-summary")

@method_decorator(decs,name="dispatch")
class CartSummaryView(View):

    template_name="cart_summary.html"

    def get(self,request,*args,**kwargs):

        qs=BasketItem.objects.filter(basket_object=request.user.cart,is_order_placed=False)

        basket_item_count=qs.count()

        basket_total=sum([bi.item_total for bi in qs])

        return render(request,self.template_name,{"basket_items":qs,"basket_total":basket_total,"basket_item_count":basket_item_count})
    
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

        

        print(request.POST)

        return redirect("order-summary")





@method_decorator(decs,name="dispatch")
class InvoiceDownloadView(View):

    def get(self, request, order_id, *args, **kwargs):

            order = Order.objects.get(id=order_id, customer=request.user)

            html_invoice = render_to_string('invoice.html', {'order': order, 'order_items':  order.orderitems.all()})

            response = HttpResponse(html_invoice, content_type='text/html')

            response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.html"'

            return response
        

@method_decorator(decs,name="dispatch")
class SubmitReviewView(View):

    form_class=ReviewForm

    template_name="product_detail.html"

    def get(self,request,*args,**kwargs):

        form_instance=self.form_class

       
        return render(request,self.template_name,{"form":form_instance})

    def post(self,request,*args,**kwargs):

        form_data=request.POST

        form_instance=self.form_class(form_data)

        if form_instance.is_valid():

            data=form_instance.cleaned_data

            product = get_object_or_404(Product, pk=kwargs.get("pk"))

            review = form_instance.save(commit=False)

            review.product = product

            review.user = request.user

            review.save()

            return redirect("product-detail",pk=product.pk)

            messages.success(request,"review added sucessfully")


        messages.error(request,"review not added ")

        return render(request,self.template_name,{"form":form_instance})

