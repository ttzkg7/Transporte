from django.shortcuts import render

def principal_view(request):
    return render(request, 'requisicoes/principal.html')