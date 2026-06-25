from django import forms
from .models import Order

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['full_name', 'email', 'phone', 'address', 'city', 'zip_code', 'payment_method']
        
    full_name = forms.CharField(label="Full Name", widget=forms.TextInput(attrs={'class': 'block w-full pl-11 pr-4 py-4 text-base rounded-2xl border-none bg-gray-50 focus:bg-white focus:ring-2 focus:ring-green-500/20 transition-all font-semibold text-gray-900 placeholder:text-gray-300', 'placeholder': 'Enter your full name'}))
    email = forms.EmailField(label="Email Address", widget=forms.EmailInput(attrs={'class': 'block w-full pl-11 pr-4 py-4 text-base rounded-2xl border-none bg-gray-50 focus:bg-white focus:ring-2 focus:ring-green-500/20 transition-all font-semibold text-gray-900 placeholder:text-gray-300', 'placeholder': 'example@email.com'}))
    phone = forms.CharField(
        label="Phone Number", 
        widget=forms.TextInput(attrs={'class': 'block w-full pl-11 pr-4 py-4 text-base rounded-2xl border-none bg-gray-50 focus:bg-white focus:ring-2 focus:ring-green-500/20 transition-all font-semibold text-gray-900 placeholder:text-gray-300', 'placeholder': '01600818139'})
    )
    zip_code = forms.CharField(
        label="Zip/Postal Code", 
        widget=forms.TextInput(attrs={'class': 'block w-full px-5 py-4 text-base rounded-2xl border-none bg-gray-50 focus:bg-white focus:ring-2 focus:ring-green-500/20 transition-all font-semibold text-gray-900 placeholder:text-gray-300', 'placeholder': '1000'})
    )

    address = forms.CharField(label="Street Address", widget=forms.Textarea(attrs={'rows': 3, 'class': 'block w-full pl-11 pr-4 py-4 text-base rounded-2xl border-none bg-gray-50 focus:bg-white focus:ring-2 focus:ring-green-500/20 transition-all font-semibold text-gray-900 placeholder:text-gray-300', 'placeholder': 'House/Road, Area...'}))
    city = forms.CharField(label="City", widget=forms.TextInput(attrs={'class': 'block w-full px-5 py-4 text-base rounded-2xl border-none bg-gray-50 focus:bg-white focus:ring-2 focus:ring-green-500/20 transition-all font-semibold text-gray-900 placeholder:text-gray-300', 'placeholder': 'Dhaka'}))
    payment_method = forms.ChoiceField(label="Payment Method", choices=Order.PAYMENT_METHOD_CHOICES, widget=forms.Select(attrs={'class': 'block w-full px-5 py-4 text-base rounded-2xl border-none bg-gray-50 focus:bg-white focus:ring-2 focus:ring-green-500/20 transition-all font-bold text-gray-900 cursor-pointer'}))

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
