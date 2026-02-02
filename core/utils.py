import os
import random
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

def render_to_pdf(template_src, context_dict={}):
    """
    Renders a Django template to a PDF response.
    """
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None

def generate_pdf_response(template_src, context_dict, filename="document.pdf", download=False):
    """
    Generates an HttpResponse containing a PDF.
    """
    pdf_content = render_to_pdf(template_src, context_dict)
    if pdf_content:
        response = HttpResponse(pdf_content, content_type='application/pdf')
        content_disposition = 'attachment' if download else 'inline'
        response['Content-Disposition'] = f'{content_disposition}; filename="{filename}"'
        return response
    return HttpResponse("Error generating PDF", status=500)

def generate_otp(length=6):
    """Generates a numeric OTP of specified length."""
    return "".join([str(random.randint(0, 9)) for _ in range(length)])
