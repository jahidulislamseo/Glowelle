
import os
import django
from django.conf import settings
from django.template import Engine
from django.template.loader import get_template

# Setup minimal Django settings
if not settings.configured:
    settings.configure(
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [os.path.join(os.getcwd(), 'templates')],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        }],
        INSTALLED_APPS=[
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'orders',
            'users',
            'products',
            'core',
            'marketing',
        ]
    )
    django.setup()

def verify_template():
    template_name = 'admin/orders/order/change_form.html'
    output_file = "verification_result.txt"
    
    with open(output_file, "w") as out:
        out.write(f"Verifying template: {template_name}...\n")
        try:
            with open( os.path.join('templates', 'admin', 'orders', 'order', 'change_form.html'), 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse it manually to check for syntax errors
            engine = Engine.get_default()
            template = engine.from_string(content)
            out.write("SUCCESS: Template syntax is valid.\n")
            
        except Exception as e:
            out.write(f"ERROR: TemplateSyntaxError found!\n{e}\n")

if __name__ == '__main__':
    verify_template()

