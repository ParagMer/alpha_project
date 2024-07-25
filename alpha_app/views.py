from django.shortcuts import render
from django.http import JsonResponse
from .models import User, Color, Product
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from django.contrib.auth import logout
from django.db import transaction
from django.contrib import messages
# Create your views here.

def register_user(request):
    if request.method == "GET":
        return render(request, 'register.html')
    
    elif request.method == "POST":
        try:
            error = {}
        
            email = request.POST.get('email')
            username = request.POST.get('username')
            password = request.POST.get('password')

            if not email:
                error['email'] = "These Field is Required"
            elif "@" not in email:
                error['email'] = "Email is invalid"

            if not username:
                error['username'] = "These Field is Required"

            if not password:
                error['password'] = "These Field is Required"

            if bool(error):
                return JsonResponse({'error': True, "statusCode": 422, "error": error}, status=422)


            try:
                user = User.objects.get(email=email)
                return JsonResponse({'error': True, "statusCode": 422, "message": "Email is already exist"}, status=422)
            except User.DoesNotExist:
                user = User.objects.create(email=email, username=username)
                user.set_password(password)
                user.save()
                return JsonResponse({'error': False, "statusCode": 201, "message": "Register Completed"}, status=201)

        except KeyError as e:
            return JsonResponse({"error": True, "statusCode": 500, "message": "Something Went Wrong"}, status=500)
        except Exception as e:
            return JsonResponse({"error": True, "statusCode": 500, "message": "Something Went Wrong"}, status=500)
        
def login_users(request):
    if request.method == "GET":
        return render(request, 'login.html')
    
    elif request.method == "POST":
        try:
            error = {}
        
            email = request.POST.get('email')
            password = request.POST.get('password')

            if not email:
                error['email'] = "These Field is Required"
            elif "@" not in email:
                error['email'] = "Email is invalid"


            if not password:
                error['password'] = "These Field is Required"

            if bool(error):
                return JsonResponse({'error': True, "statusCode": 422, "error": error}, status=422)
            
            try:
                user = authenticate(request, username=email, password=password)
                if user is not None:
                    login(request, user)
                    return JsonResponse({"error": False, "statusCode": 200, "message": "Successfully logged in"})
                else:
                    return JsonResponse({"error": True, "statusCode": 401, "message": "Invalid email or password"}, status=401)
            except User.DoesNotExist:
                return JsonResponse({"error": True, "statusCode": 500, "message": "Email is not registered"}, status=500)
        except Exception as e:
            return JsonResponse({"error": True, "statusCode": 500, "message": "Something Went Wrong"}, status=500)

@method_decorator(login_required, name='dispatch')
class ProductListView(View):
    def get(self, request):
        
        colors = Color.objects.select_related('product').values('price', 'image','product__title', 'product__id')
        # Set up pagination
        paginator = Paginator(colors, 5)  # 5 products per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'dashboard.html', {'page_obj': page_obj})
    
@method_decorator(login_required, name='dispatch')
class ProductAddView(View):
    def get(self, request):
        return render(request, 'add_product.html')

    def post(self, request):
        title = request.POST.get('title')
        description = request.POST.get('description')
        prices = request.POST.getlist('prices')
        colors = request.POST.getlist('colors')
        images = request.FILES.getlist('images')

        if len(prices) == len(colors) == len(images):
            try:
                with transaction.atomic():
                    product = Product.objects.create(
                        title=title, 
                        description=description, 
                        user=request.user
                    )

                    for price, color, image in zip(prices, colors, images):
                        Color.objects.create(
                            product=product, 
                            price=price, 
                            name=color, 
                            image=image
                        )

                messages.success(request, 'Product added successfully.')
                return redirect('dashboard')

            except Exception as e:
                messages.error(request, f'An error occurred: {e}')
                return redirect('dashboard')
        else:
            messages.error(request, 'The number of prices, colors, and images must be the same.')
            return redirect('add_product')
        
@method_decorator(login_required, name='dispatch')
class ProductEdit(View):
    def get(self, request, product_id):
        colors = Color.objects.select_related('product').filter(product__id=product_id).values('name', 'price', 'image','product__title', 'product__description', 'product__id')
        return render(request, 'product_detail.html', {'product': list(colors)[0]})
    

@method_decorator(login_required, name='dispatch')
class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')
    
