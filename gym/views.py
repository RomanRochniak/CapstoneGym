from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import TrainingProgram, Membership, Trainer, Post, Payment
from django.utils import timezone
from datetime import date, timedelta
from django.contrib import messages
from django.contrib.auth.models import User 
from django.http import JsonResponse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
import stripe
from django.conf import settings
import os
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json


stripe.api_key = settings.STRIPE_SECRET_KEY


# Create your views here.

@csrf_exempt
def process_payment(request, program_id):
    program = get_object_or_404(TrainingProgram, pk=program_id)

    if request.method == 'POST':
        try:
            payment_token = request.POST.get('google_pay_token')
            if not payment_token:
                raise ValueError("Payment token is missing.")

            Membership.objects.create(
                user=request.user,
                program=program,
                start_date=date.today(),
                end_date=date.today().replace(year=date.today().year + 1),
                status='active'
            )
            return JsonResponse({'success': True, 'message': "Payment successful!"})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return render(request, '/gym/payments.html', {'program': program})


@login_required
def memberships_list(request):
    memberships = Membership.objects.filter(user=request.user)
    return render(request, 'memberships/list.html', {'memberships': memberships})

@login_required
def create_membership(request, program_id):
    program = get_object_or_404(TrainingProgram, id=program_id)
    Membership.objects.create(
        user=request.user, 
        program=program, 
        start_date=date.today(), 
        end_date=date.today() + timedelta(days=30), 
        status='active'
    )
    return redirect('memberships_list')


def index(request):
    programs = TrainingProgram.objects.all()
    return render(request, 'gym/index.html', {'programs': programs})

def about_us(request):
    trainers = Trainer.objects.all()
    context = {'trainers': trainers} 
    return render(request, 'gym/about_us.html', context)


@login_required
def training_programs(request):
    programs = TrainingProgram.objects.all()
    trainers = Trainer.objects.all()  

    user_memberships = Membership.objects.filter(user=request.user)

    context = {
        'programs': programs,
        'trainers': trainers,
        'user_memberships': user_memberships
    }
    return render(request, 'gym/training_programs.html', context)

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        
        if password != confirmation:
            return render(request, "gym/register.html", {
                "message": "Passwords must match."
            })
        
        try:
            User = get_user_model()
            user = User._default_manager.create_user(username=username, email=email, password=password)
            user.save()
        except IntegrityError:
            return render(request, "gym/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "gym/register.html")

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "gym/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "gym/login.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

@login_required
def profile(request):
    membership = None
    trainer = None

    try:
        membership = Membership.objects.get(user=request.user, status='active')
        print("Membership found:", membership)
        if membership and membership.program:
            print("Program found:", membership.program)
            trainer = membership.program.trainer
            print("Trainer found:", trainer)
        else:
            print("No program or trainer found.")
    except Membership.DoesNotExist:
        print("No active membership found.")

    context = {
        'user': request.user,
        'membership': membership,
        'trainer': trainer,
    }
    return render(request, 'gym/profile.html', context)


User = get_user_model()

@login_required
def edit_profile_view(request):
    user = request.user 
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)

        user.save() 
        
        messages.success(request, "Профіль оновлено успішно!")
        return redirect('profile') 

    return render(request, 'gym/edit_profile.html', {'user': user})

def program_detail(request, id):
    program = get_object_or_404(TrainingProgram, id=id)
    return render(request, 'gym/program_detail.html', {'program': program})

@login_required
def trainer_detail(request, trainer_id):
    trainer = get_object_or_404(Trainer, id=trainer_id)
    
    programs = TrainingProgram.objects.filter(trainer=trainer)
    
    if trainer.photo:
        photo_path = os.path.join(settings.MEDIA_ROOT, str(trainer.photo))
        print("Path to the trainer's photo:", photo_path)
    else:
        print("There is no photo of the trainer.")
    
    return render(request, 'gym/trainer_detail.html', {'trainer': trainer, 'programs': programs})

@login_required
def payments(request):
    program_id = request.GET.get('program_id')
    if not program_id:
        messages.error(request, "No training program selected for payment.")
        return redirect('training_programs') 

    program = get_object_or_404(TrainingProgram, pk=program_id)

    if request.method == 'POST':
        token = request.POST.get('stripeToken')
        google_pay_token = request.POST.get('google_pay_token')

        if token:
            # Stripe payment processing (Credit/Debit card)
            try:
                charge = stripe.Charge.create(
                    amount=int(program.price * 100),  # Convert to cents
                    currency='usd',
                    description=f'Payment for program {program.name}',
                    source=token,
                )

                Membership.objects.create(
                    user=request.user,
                    program=program,
                    start_date=date.today(),
                    end_date=date.today() + timedelta(days=30),
                    status='active'
                )
                return redirect('payment_success', status='success', message='Payment successful!', program_id=program.id)

            except stripe.error.CardError as e:
                error_code = e.error.code  # Get the error code

                # If the error is due to insufficient funds or card blocking
                if error_code == "insufficient_funds":
                    return redirect('payment_success', status='failure', message="Payment failed: Insufficient funds. Card is blocked.", program_id=program.id)

                # Other card errors
                return redirect('payment_success', status='failure', message=f"Payment failed: {e.error.message}", program_id=program.id)

            except stripe.error.StripeError as e:
                return redirect('payment_success', status='failure', message=f"Payment failed: {e}", program_id=program.id)

            except Exception as e:
                return redirect('payment_success', status='failure', message=f"Payment failed: {e}", program_id=program.id)

        elif google_pay_token:
            # Обробка Google Pay через Stripe
            try:
                payment_intent = stripe.PaymentIntent.create(
                    amount=int(program.price * 100),  # Convert to cents
                    currency='usd',
                    payment_method=google_pay_token,
                    confirmation_method='manual',
                    confirm=True,
                )

                Membership.objects.create(
                    user=request.user,
                    program=program,
                    start_date=date.today(),
                    end_date=date.today() + timedelta(days=30),
                    status='active'
                )

                return redirect('payment_success', status='success', message='Payment successful!', program_id=program.id)

            except stripe.error.CardError as e:
                return redirect('payment_success', status='failure', message=f"Payment failed: {e.error.message}", program_id=program.id)

            except stripe.error.StripeError as e:
                return redirect('payment_success', status='failure', message=f"Payment failed: {e}", program_id=program.id)

            except Exception as e:
                return redirect('payment_success', status='failure', message=f"Payment failed: {e}", program_id=program.id)

        else:
            return redirect('payment_success', status='failure', message="No payment token provided.", program_id=program.id)

    return render(request, 'gym/payments.html', {'stripe_public_key': settings.STRIPE_PUBLIC_KEY, 'program_id': program_id, 'program': program})



def success(request, status, message, program_id):
    return render(request, 'gym/success.html', {'message': message, 'status': status, 'program_id': program_id})


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = 'twoj_sekret_webhooka'

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event['type'] == 'charge.succeeded':
        charge = event['data']['object']

    return HttpResponse(status=200)

# logic for community
def community(request):
    all_posts = Post.objects.order_by('-created_at')
    paginator = Paginator(all_posts, 10)
    page_number = request.GET.get('page')
    page_posts = paginator.get_page(page_number)

    if request.user.is_authenticated:
        liked_post_ids = list(request.user.liked_posts.values_list('id', flat=True))

        # Filter liked_post_ids to only include posts that are on the current page
        liked_posts_on_current_page = request.user.liked_posts.filter(id__in=[post.id for post in page_posts]) 
        liked_post_ids_on_current_page = [post.id for post in liked_posts_on_current_page]

    else:
        liked_post_ids = []
        liked_post_ids_on_current_page = []

    return render(request, "gym/community.html", {
        "page_posts": page_posts,
        "liked_post_ids": liked_post_ids_on_current_page, 
        "user": request.user  
    })


@login_required
def new_post(request):
    if request.method == "POST":
        content = request.POST.get("content")
        image_url = request.POST.get("image_url")
        post = Post(user=request.user, content=content, image_url=image_url)
        post.save()
        return redirect('community')  # Redirect to community view
    return redirect('community') # Redirect to avoid empty submission error


@login_required
@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id) 
    if request.method == "POST":
        if post.user == request.user:
            try:
                data = json.loads(request.body.decode('utf-8')) 
                post.content = data.get("content")
                post.image_url = data.get("image_url")
                post.save()
                return JsonResponse({"message": "Post edited successfully"})
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON data"}, status=400)
        else:
            return JsonResponse({"error": "Unauthorized"}, status=403) 
    else: 
        return JsonResponse({"error": "Only POST requests are allowed for edit."}, status=405)



@login_required
def like_add(request, post_id): # like_add
    if request.method == 'POST':
        post = get_object_or_404(Post, pk=post_id)
        post.likes.add(request.user)
        return JsonResponse({'liked': True, 'like_count': post.like_count()})  
    return JsonResponse({'error': 'Invalid request method.'}, status=405) 


@login_required
def like_remove(request, post_id): # like_remove
    if request.method == 'POST':
        post = get_object_or_404(Post, pk=post_id)
        post.likes.remove(request.user)
        return JsonResponse({'liked': False, 'like_count': post.like_count()}) 
    return JsonResponse({'error': 'Invalid request method.'}, status=405)

def user_posts(request, username):  
    user = get_object_or_404(User, username=username) 
    posts = Post.objects.filter(user=user).order_by('-created_at') 

    if request.user.is_authenticated:
        liked_post_ids = list(request.user.liked_posts.values_list('id', flat=True))
    else:
        liked_post_ids = []

    context = {
        'profile_user': user,  
        'posts': posts, 
        'liked_post_ids': liked_post_ids, 
    }
    return render(request, 'gym/profile_community.html', context)



from django.http import HttpResponseForbidden

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if post.user != request.user:
        return HttpResponseForbidden("You cannot delete this post.")
    
    post.delete()
    messages.success(request, "The post was successfully deleted.")
    return redirect('community')