from django.shortcuts import render

def bond_list(request):
    return render(request, 'bonds/list.html')

def bond_create(request):
    return render(request, 'bonds/create.html')

def bond_detail(request, bond_id):
    return render(request, 'bonds/detail.html', {'bond_id': bond_id})
