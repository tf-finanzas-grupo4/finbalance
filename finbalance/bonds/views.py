from django.shortcuts import render

def bond_list(request):
  
    return render(request, 'bonds/list.html')
