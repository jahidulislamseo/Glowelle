from django import forms
from .models import Order

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['full_name', 'email', 'phone', 'address', 'city', 'zip_code', 'payment_method']
        
    full_name = forms.CharField(label="Full Name", widget=forms.TextInput(attrs={'class': 'block w-full pl-10 pr-4 py-3 text-base rounded-lg border-2 border-gray-300 shadow-sm focus:border-green-500 focus:ring-2 focus:ring-green-200 transition-all', 'placeholder': 'আপনার পুরো নাম লিখুন'}))
    email = forms.EmailField(label="Email Address", widget=forms.EmailInput(attrs={'class': 'block w-full pl-10 pr-4 py-3 text-base rounded-lg border-2 border-gray-300 shadow-sm focus:border-green-500 focus:ring-2 focus:ring-green-200 transition-all', 'placeholder': 'example@email.com'}))
    phone = forms.CharField(
        label="Phone Number", 
        widget=forms.TextInput(attrs={'class': 'block w-full pl-10 pr-4 py-3 text-base rounded-lg border-2 border-gray-300 shadow-sm focus:border-green-500 focus:ring-2 focus:ring-green-200 transition-all', 'placeholder': '01XXXXXXXXX'})
    )
    zip_code = forms.CharField(
        label="Zip/Postal Code", 
        widget=forms.TextInput(attrs={'class': 'block w-full px-4 py-3 text-base rounded-lg border-2 border-gray-300 shadow-sm focus:border-green-500 focus:ring-2 focus:ring-green-200 transition-all', 'placeholder': '1000'})
    )

    address = forms.CharField(label="Street Address", widget=forms.Textarea(attrs={'rows': 3, 'class': 'block w-full pl-10 pr-4 py-3 text-base rounded-lg border-2 border-gray-300 shadow-sm focus:border-green-500 focus:ring-2 focus:ring-green-200 transition-all', 'placeholder': 'বাসা/রোড নম্বর, এলাকা'}))
    city = forms.CharField(label="City", widget=forms.TextInput(attrs={'class': 'block w-full px-4 py-3 text-base rounded-lg border-2 border-gray-300 shadow-sm focus:border-green-500 focus:ring-2 focus:ring-green-200 transition-all', 'placeholder': 'ঢাকা'}))
    payment_method = forms.ChoiceField(label="Payment Method", choices=Order.PAYMENT_METHOD_CHOICES, widget=forms.Select(attrs={'class': 'block w-full px-4 py-3 text-base rounded-lg border-2 border-gray-300 shadow-sm focus:border-green-500 focus:ring-2 focus:ring-green-200 transition-all bg-white'}))

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        import re
        # Basic BD phone number validation (starts with +880 or 01, and followed by 8 or more digits)
        if not re.match(r'^(\+8801|01)[3-9]\d{8}$', phone):
            raise forms.ValidationError("Please enter a valid Bangladesh phone number (e.g., 017XXXXXXXX or +88017XXXXXXXX)")
        return phone
        
    def clean_zip_code(self):
        zip_code = self.cleaned_data.get('zip_code')
        if not zip_code.isdigit():
             raise forms.ValidationError("Zip code must contain only numbers.")
        return zip_code
