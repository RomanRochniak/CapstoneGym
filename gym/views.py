import json
import os
from datetime import date, timedelta

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

from .models import Membership, Payment, Post, Trainer, TrainingProgram

stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
@login_required
def process_payment(request, program_id):
    """
    Old Google Pay flow.
    Keep it protected so a user cannot create a second active membership.
    """
    program = get_object_or_404(TrainingProgram, pk=program_id)
    today = date.today()

    # Auto-expire old memberships first
    Membership.objects.filter(
        user=request.user,
        status="active",
        end_date__lt=today
    ).update(status="expired")

    # Block purchase if user already has an active membership
    active_membership = Membership.objects.filter(
        user=request.user,
        status="active",
        end_date__gte=today
    ).select_related("program").first()

    if active_membership:
        if request.method == "POST":
            return JsonResponse({
                "success": False,
                "error": f"You already have an active membership ({active_membership.program.name}). You can purchase a new one after it expires or contact the manager."
            }, status=400)

        messages.warning(
            request,
            f"You already have an active membership ({active_membership.program.name}). "
            "You can purchase a new one after it expires or contact the manager."
        )
        return redirect("training_programs")

    if request.method == "POST":
        try:
            payment_token = request.POST.get("google_pay_token")
            if not payment_token:
                raise ValueError("Payment token is missing.")

            Membership.objects.create(
                user=request.user,
                program=program,
                start_date=today,
                end_date=today + timedelta(days=30),
                status="active",
            )

            return JsonResponse({"success": True, "message": "Payment successful!"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return render(
        request,
        "gym/payments.html",
        {
            "program": program,
            "program_id": program.id,
            "stripe_public_key": settings.STRIPE_PUBLIC_KEY,
        },
    )


@login_required
def memberships_list(request):
    memberships = Membership.objects.filter(user=request.user).order_by("-end_date")
    return render(request, "memberships/list.html", {"memberships": memberships})


@login_required
def create_membership(request, program_id):
    program = get_object_or_404(TrainingProgram, id=program_id)

    # Close previous active memberships (avoid multiple actives)
    Membership.objects.filter(user=request.user, status="active").update(status="expired")

    Membership.objects.create(
        user=request.user,
        program=program,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        status="active",
    )
    return redirect("memberships_list")


def index(request):
    programs = TrainingProgram.objects.all()
    return render(request, "gym/index.html", {"programs": programs})


def about_us(request):
    trainers = Trainer.objects.all()
    return render(request, "gym/about_us.html", {"trainers": trainers})


@login_required
def training_programs(request):
    programs = TrainingProgram.objects.all()
    trainers = Trainer.objects.all()

    # Auto-expire on page visit
    today = date.today()
    Membership.objects.filter(
        user=request.user,
        status="active",
        end_date__lt=today
    ).update(status="expired")

    user_memberships = Membership.objects.filter(user=request.user).order_by("-end_date")

    active_membership = Membership.objects.filter(
        user=request.user,
        status="active",
        end_date__gte=today
    ).select_related("program").first()

    context = {
        "programs": programs,
        "trainers": trainers,
        "user_memberships": user_memberships,
        "active_membership": active_membership,
    }
    return render(request, "gym/training_programs.html", context)


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]

        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()

        if password != confirmation:
            return render(request, "gym/register.html", {"message": "Passwords must match."})

        try:
            User = get_user_model()
            user = User._default_manager.create_user(username=username, email=email, password=password)
            user.first_name = first_name
            user.last_name = last_name
            user.save()
        except IntegrityError:
            return render(request, "gym/register.html", {"message": "Username already taken."})

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

        return render(request, "gym/login.html", {"message": "Invalid username and/or password."})

    return render(request, "gym/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


@login_required
def profile(request):
    """
    Auto-expire memberships and show the current active one (by date range).
    """
    today = date.today()

    # 1) expire old actives
    Membership.objects.filter(user=request.user, status="active", end_date__lt=today).update(status="expired")

    # 2) pick current active membership by date
    membership = (
        Membership.objects.filter(user=request.user, start_date__lte=today, end_date__gte=today)
        .select_related("program__trainer")
        .order_by("-end_date")
        .first()
    )

    # Optional: keep status consistent if dates say active
    if membership and membership.status != "active":
        membership.status = "active"
        membership.save(update_fields=["status"])

    trainer = membership.program.trainer if membership and membership.program else None

    return render(
        request,
        "gym/profile.html",
        {
            "user": request.user,
            "membership": membership,
            "trainer": trainer,
        },
    )


@login_required
def edit_profile_view(request):
    user = request.user

    if request.method == "POST":
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.email = request.POST.get("email", user.email)
        user.save()

        messages.success(request, "Profile updated successfully!")
        return redirect("profile")

    return render(request, "gym/edit_profile.html", {"user": user})


def program_detail(request, id):
    program = get_object_or_404(TrainingProgram, id=id)
    return render(request, "gym/program_detail.html", {"program": program})


@login_required
def trainer_detail(request, trainer_id):
    trainer = get_object_or_404(Trainer, id=trainer_id)
    programs = TrainingProgram.objects.filter(trainer=trainer)
    return render(request, "gym/trainer_detail.html", {"trainer": trainer, "programs": programs})

@login_required
def payments(request):
    program_id = request.GET.get("program_id")
    if not program_id:
        messages.error(request, "No training program selected.")
        return redirect("training_programs")

    program = get_object_or_404(TrainingProgram, pk=program_id)
    today = date.today()

    # Auto-expire old active memberships first
    Membership.objects.filter(
        user=request.user,
        status="active",
        end_date__lt=today
    ).update(status="expired")

    # Check if user already has an active membership
    active_membership = Membership.objects.filter(
        user=request.user,
        status="active",
        end_date__gte=today
    ).select_related("program").first()

    if active_membership:
        messages.warning(
            request,
            f"You already have an active membership ({active_membership.program.name}). "
            "You can purchase a new one after it expires or contact the manager."
        )
        return redirect("training_programs")

    if request.method == "POST":
        token = request.POST.get("stripeToken")
        google_pay_token = request.POST.get("google_pay_token")

        try:
            if token:
                # Stripe Card payment
                stripe.Charge.create(
                    amount=int(program.price * 100),
                    currency="usd",
                    description=f"Payment for program {program.name}",
                    source=token,
                )

            elif google_pay_token:
                # Google Pay via Stripe PaymentIntent
                stripe.PaymentIntent.create(
                    amount=int(program.price * 100),
                    currency="usd",
                    payment_method=google_pay_token,
                    confirmation_method="manual",
                    confirm=True,
                )
            else:
                messages.error(request, "No payment token provided.")
                return HttpResponseRedirect(f"{reverse('payments')}?program_id={program.id}")

            Membership.objects.create(
                user=request.user,
                program=program,
                start_date=today,
                end_date=today + timedelta(days=30),
                status="active",
            )

            messages.success(request, f"Congrats! You bought: {program.name} 💪")
            return redirect("profile")

        except stripe.error.CardError as e:
            msg = getattr(e, "user_message", None) or str(e)
            messages.error(request, f"Payment failed: {msg}")
            return HttpResponseRedirect(f"{reverse('payments')}?program_id={program.id}")

        except stripe.error.StripeError:
            messages.error(request, "Payment failed. Stripe error. Please try again.")
            return HttpResponseRedirect(f"{reverse('payments')}?program_id={program.id}")

        except Exception as e:
            messages.error(request, f"Payment failed. {e}")
            return HttpResponseRedirect(f"{reverse('payments')}?program_id={program.id}")

    return render(
        request,
        "gym/payments.html",
        {
            "stripe_public_key": settings.STRIPE_PUBLIC_KEY,
            "program_id": program.id,
            "program": program,
        },
    )

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = "twoj_sekret_webhooka"  # TODO: move to env

    try:
        stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    return HttpResponse(status=200)


def community(request):
    all_posts = Post.objects.order_by("-created_at")
    paginator = Paginator(all_posts, 10)

    page_number = request.GET.get("page")
    page_posts = paginator.get_page(page_number)

    if request.user.is_authenticated:
        liked_post_ids = list(request.user.liked_posts.values_list("id", flat=True))
        liked_posts_on_current_page = request.user.liked_posts.filter(id__in=[post.id for post in page_posts])
        liked_post_ids_on_current_page = [post.id for post in liked_posts_on_current_page]
    else:
        liked_post_ids_on_current_page = []

    return render(
        request,
        "gym/community.html",
        {"page_posts": page_posts, "liked_post_ids": liked_post_ids_on_current_page, "user": request.user},
    )


@login_required
def new_post(request):
    if request.method == "POST":
        content = request.POST.get("content")
        image_url = request.POST.get("image_url")
        Post.objects.create(user=request.user, content=content, image_url=image_url)
    return redirect("community")


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests are allowed for edit."}, status=405)

    if post.user != request.user:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)

    post.content = data.get("content", post.content)
    post.image_url = data.get("image_url", post.image_url)
    post.save()

    return JsonResponse({"message": "Post edited successfully"})


@login_required
def like_add(request, post_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method."}, status=405)

    post = get_object_or_404(Post, pk=post_id)
    post.likes.add(request.user)
    return JsonResponse({"liked": True, "like_count": post.like_count()})


@login_required
def like_remove(request, post_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method."}, status=405)

    post = get_object_or_404(Post, pk=post_id)
    post.likes.remove(request.user)
    return JsonResponse({"liked": False, "like_count": post.like_count()})


def user_posts(request, username):
    User = get_user_model()
    user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(user=user).order_by("-created_at")

    if request.user.is_authenticated:
        liked_post_ids = list(request.user.liked_posts.values_list("id", flat=True))
    else:
        liked_post_ids = []

    return render(
        request,
        "gym/profile_community.html",
        {"profile_user": user, "posts": posts, "liked_post_ids": liked_post_ids},
    )


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.user != request.user:
        return HttpResponseForbidden("You cannot delete this post.")

    post.delete()
    messages.success(request, "The post was successfully deleted.")
    return redirect("community")

def join(request):
    # Logged in -> go straight to training programs + toast message
    if request.user.is_authenticated:
        messages.success(request, "Congrats! You’re in the club 💪")
        return redirect("training_programs")

    # Not logged in -> send to login with next
    login_url = reverse("login")
    next_url = reverse("training_programs")
    return redirect(f"{login_url}?next={next_url}")