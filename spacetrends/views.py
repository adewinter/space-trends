from django.views.generic.base import TemplateView
from django.shortcuts import render
from django.http import HttpResponse

from .models import Launch

class IndexPageView(TemplateView):
    template_name = 'index.html'    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['launches'] = Launch.objects.all()[:5]
        return context

# def index(request):
#     return HttpResponse("Hello world!")

# Create your views here.
