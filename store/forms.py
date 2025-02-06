from django import forms

from store.models import User,Order

from django.contrib.auth.forms import UserCreationForm

class SignUpForm(UserCreationForm):


    password1=forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control mb-3'}))

    password2=forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control mb-3'}))


    class Meta:

        model=User

        fields=["username","email","password1","password2","phone"]

        widgets={

            "username":forms.TextInput(attrs={'class':'form-control mb-3'}),
            "email":forms.EmailInput(attrs={'class':'form-control mb-3'}),
            "phone":forms.TextInput(attrs={'class':'form-control mb-3'})
        }

class LoginForm(forms.Form):

    username=forms.CharField(widget=forms.TextInput(attrs={'class':'form-control mb-3'}))

    password=forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control mb-3'}))

class OrderForm(forms.ModelForm):

    class Meta:

        model=Order

        fields=["address","phone","payment_method"]
