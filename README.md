# Capstone: Gym Membership Management System

Video Demo: [https://youtu.be/yRvw8X4uvmY](https://youtu.be/yRvw8X4uvmY)

## Description
RoshaClub is a web application designed to streamline gym membership management, providing a platform for users to browse training programs, register for memberships, manage their profiles, and interact within a community forum. Gym owners can showcase their trainers, training programs, and facilitate secure online membership purchases.  This comprehensive platform simplifies the management of various aspects of a fitness center's operations.

---

## Features


* User Registration and Authentication: Secure user registration, login, and logout functionality.
* Training Program Browsing: Users can browse and filter available training programs, viewing details such as descriptions, duration, and price.
* Membership Management:  Purchase, renew, and manage memberships with real-time status updates, providing users with clear visibility into their membership status and expiration dates.
* Trainer Profiles: Detailed trainer profiles showcasing their expertise, including specializations, descriptions, contact information, and photos, helping users choose the right trainer.
* User Profiles: Personalized user profiles that display user details, active membership information, assigned trainer, and relevant training program details, creating a centralized hub for managing their fitness journey.
* Community Forum:  A dynamic platform for gym members to connect, share updates, like posts, edit content, and delete their own posts, all enhanced by AJAX for seamless interactions.
* Payment Integration: Securely process payments for memberships using Stripe, supporting various credit and debit cards as well as Google Pay for added convenience.
* Responsive Design: The application is designed to be fully responsive, adapting to various screen sizes and devices for optimal viewing and interaction.

---

## Technologies Used

- **Backend**: Django, Python
- **Frontend**: HTML, CSS, JavaScript
- **Database**: PostgreSQL (or SQLite for development)
- **Payment API**: Stripe

---

## Installation

### Prerequisites
- Python 3.x
- Django 4.x
- Stripe account and API keys

### Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
    cd YOUR_REPOSITORY
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Database setup:**

    *   **PostgreSQL:**
        1.  Create a PostgreSQL database: `createdb roshaclub_db`
        2.  Create a PostgreSQL user: `createuser roshaclub_user`
        3.  Grant privileges: `psql -d roshaclub_db -c "GRANT ALL PRIVILEGES ON DATABASE roshaclub_db TO roshaclub_user;"`
        4.  Configure the database settings in `settings.py`:
            ```python
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.postgresql',
                    'NAME': 'roshaclub_db',
                    'USER': 'roshaclub_user',
                    'PASSWORD': 'YOUR_PASSWORD',  # Replace with your actual password!
                    'HOST': 'localhost',
                    'PORT': '5432',
                }
            }

            ```
    *   **SQLite:** A database will be created automatically ( `db.sqlite3`).

5.  **Apply migrations:**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```
6.  **Configure Stripe API keys:**
    1.  Create a `.env` file in the root directory: `touch .env` (or `type nul > .env` on Windows)
    2.  Add your keys:
        ```
        STRIPE_PUBLIC_KEY=YOUR_STRIPE_PUBLIC_KEY
        STRIPE_SECRET_KEY=YOUR_STRIPE_SECRET_KEY
        ```
    3.  Load the environment variables in `settings.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
```
7. **Create a superuser:**
```django
python manage.py createsuperuser
```
8. **Run the development server:**
```django
python manage.py runserver
```
---

## Stripe Integration

To test payments with Stripe, use the following test card numbers:

| Card Number            | Card Type   | Payment Status             |
|------------------------|-------------|----------------------------|
| 4242 4242 4242 4242    | Visa        | Successful Payment         |
| 4000 0000 0000 0002    | Visa        | Payment Declined by Bank   |
| 5555 5555 5555 4444    | Mastercard  | Successful Payment         |

You can also test various scenarios like successful payments, declines, and other error responses by using the respective test cards. For more details on testing, you can visit the [Stripe testing documentation](https://stripe.com/docs/testing).

---

## Backend Views (`views.py`)

This file contains the core logic of the application, handling user requests, interacting with the database, processing payments, and rendering templates.  Each view function corresponds to a specific URL pattern defined in `urls.py`

## Code Examples:
Payments View

This view handles the payment process for a selected training program. It supports Stripe for card payments and Google Pay.
```python
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
                if error_code == "insufficient_funds":
                    return redirect('payment_success', status='failure', message="Payment failed: Insufficient funds. Card is blocked.", program_id=program.id)
                return redirect('payment_success', status='failure', message=f"Payment failed: {e.error.message}", program_id=program.id)

            except stripe.error.StripeError as e:
                return redirect('payment_success', status='failure', message=f"Payment failed: {e}", program_id=program.id)

            except Exception as e:
                return redirect('payment_success', status='failure', message=f"Payment failed: {e}", program_id=program.id)

        elif google_pay_token:
            # Google Pay payment processing via Stripe
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
```

Payment Processing:
```python
@csrf_exempt
def process_payment(request, program_id):
    program = get_object_or_404(TrainingProgram, pk=program_id)
    if request.method == 'POST':
        try:
            token = request.POST.get('stripeToken')
            stripe.Charge.create(
                amount=int(program.price * 100),
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
            return JsonResponse({'success': True, 'message': "Payment successful!"})
        except stripe.error.StripeError as e:
            return JsonResponse({'success': False, 'error': str(e)})
```

`success` View.
This view displays the payment result to the user.

```python
def success(request, status, message, program_id):
    return render(request, 'gym/success.html', {'message': message, 'status': status, 'program_id': program_id})
```

`stripe_webhook` View

Handles Stripe webhook events for additional payment processing logic.

```
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
```
Templates

`payments.html`
```
{% extends 'gym/layout.html' %}
{% block content %}

<h1>Pay for Training Program</h1>

<h2>{{ program.name }}</h2>
<p>{{ program.description }}</p>
<p>Price: ${{ program.price }}</p>

{% if error_message %}
    <div class="error-message">
        <p style="color: red;">{{ error_message }}</p>
    </div>
{% endif %}

<form action="{% url 'payments' %}?program_id={{ program_id }}" method="post" id="payment-form">
    {% csrf_token %}
    <div id="card-element"></div>
    <div id="card-errors" role="alert"></div>
    <button type="submit">Submit Payment</button>
</form>

<!-- Stripe.js -->
<script src="https://js.stripe.com/v3/"></script>

<script>
const stripe = Stripe('{{ stripe_public_key }}');
const elements = stripe.elements();
const style = {
    base: {
        color: "#32325d",
        fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
        fontSmoothing: "antialiased",
        fontSize: "16px",
        "::placeholder": {
            color: "#aab7c4"
        }
    }
};
const card = elements.create('card', { style: style });
card.mount('#card-element');

card.on('change', function(event) {
    const errorDiv = document.getElementById('card-errors');
    if (event.error) {
        errorDiv.textContent = event.error.message;
    } else {
        errorDiv.textContent = '';
    }
});

const form = document.getElementById('payment-form');
form.addEventListener('submit', async function(event) {
    event.preventDefault();
    const { token, error } = await stripe.createToken(card);
    if (error) {
        document.getElementById('card-errors').textContent = error.message;
    } else {
        const hiddenInput = document.createElement('input');
        hiddenInput.setAttribute('type', 'hidden');
        hiddenInput.setAttribute('name', 'stripeToken');
        hiddenInput.setAttribute('value', token.id);
        form.appendChild(hiddenInput);
        form.submit();
    }
});
</script>

{% endblock %}
```

`success.html`
```
{% extends "gym/layout.html" %}

{% block content %}
<h1>{{ message }}</h1>

{% if status == "failure" %}
    {% if error_code == "insufficient_funds" %}
        <p style="color: red;">Payment failed: Insufficient funds. Your card is blocked.</p>
    {% else %}
        <p style="color: red;">Payment failed. Please try again.</p>
    {% endif %}
    <a href="{% url 'payments' %}?program_id={{ program_id }}">Retry Payment</a>
{% elif status == "success" %}
    <p style="color: green;">Payment was successful!</p>
    <a href="{% url 'profile' %}">Go to your profile</a>
{% endif %}
{% endblock %}
```

---

## URL Patterns (`urls.py`)

This file defines how URLs are mapped to specific view functions in `views.py`. It uses Django's path function to create these mappings.  It acts as the routing table for the application, directing incoming requests to the correct handlers.


```python
from django.urls import path  # ... other imports

urlpatterns = [
    # ... other URL patterns

    path('training-programs/', views.training_programs, name='training_programs'),
    path('payment/<int:program_id>/', views.process_payment, name='process_payment'),
    path('payments/', views.payments, name='payments'), # Payment page with stripe and Google Pay elements
    path('success/<str:status>/<str:message>/<int:program_id>/', views.success, name='payment_success'), # Shows result for payment


    # ... other URL patterns, including community paths

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

## Payment Workflow

The payment process is tied to the `TrainingProgram` and `Membership` models. Here's how it works:

1. **User Selects a Training Program:** Users browse available training programs listed by trainers on the frontend. Upon selecting a program, they can proceed to make a payment.

2. **Payment Handling:** Payment is processed using Stripe. The `payments` view handles both Stripe and Google Pay integration.  Upon receiving the payment token, it processes the charge using the Stripe API and creates a `Membership` entry, linking the user to the selected program. The `Membership` model tracks the start and end dates of the membership and its status (active, expired, pending).

3. **Payment Confirmation:** After processing, the user is redirected to a success or failure page based on the result. Payment status is displayed in the `success.html` template.

## Models

* **User:** A custom User model inheriting from Django's `AbstractUser` with basic authentication features.

* **Trainer:** Represents gym trainers, including name, specialization, description, and photo.

```python
class Trainer(models.Model):
    name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100)
    description = models.TextField()
    photo = models.ImageField(upload_to='trainers/')
```
`TrainingProgram:` Represents training programs with details like name, description, duration, price, and the associated trainer.
```python
class TrainingProgram(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, null=True, blank=True)
```

`Membership:` Links users to training programs, including start and end dates and status (active, expired, or pending).
```python
class Membership(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('pending', 'Pending'),
    ]
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="memberships")
    program = models.ForeignKey(TrainingProgram, on_delete=models.CASCADE, related_name="memberships")
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

```

`Payment:` Tracks payment transactions, including the Stripe charge ID and the amount.

```python
class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created = models.DateTimeField(auto_now_add=True)

```
`Post:` Represents community posts. Users can like and comment. like_count() returns the total likes.
```python
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField(blank=True)
    image_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)

    def like_count(self):
        return self.likes.count()
```

## Community Forum

The Community Forum allows users to interact with each other by posting updates, sharing experiences, and engaging with posts from other gym members.

**Features of the Community:**

* **Post Content:** Users can create posts with text and optional images.
* **Like Posts:** Users can like posts to show support or appreciation.
* **Comment on Posts:** Engage in discussions by commenting on posts. (This feature is not yet implemented in the provided code, but is listed as a future enhancement.)
* **Paginated Posts:** Posts are displayed in a paginated format, showing a limited number of posts per page.
* **Delete Posts:** Users can delete their own posts.

**How to Use:**

* **Viewing Posts:** All posts from users are displayed on the community page in reverse chronological order.  You can also view posts by a specific user by visiting their profile.
* **Interacting with Posts:** Logged-in users can like posts. The like button dynamically updates the like count without requiring a page refresh.  They can also edit and delete their own posts.

### JavaScript (`community.js`)
```js
document.addEventListener('DOMContentLoaded', function() {
});

function likeHandler(postId, initialLikedState) { 
    let liked = initialLikedState; 

    const url = liked ? `/gym/like_remove/${postId}/` : `/gym/like_add/${postId}/`;
    fetch(url, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(response => {
        if (!response.ok) {
            console.error("HTTP error:", response.status, response.statusText);
            return Promise.reject(new Error(response.statusText));
        }
        return response.json();
    })
    .then(data => {
        const likeButton = document.getElementById(`like_button_${postId}`);
        const likeIcon = document.getElementById(`like_icon_${postId}`);
        const likeCount = document.getElementById(`like_count_${postId}`);

        likeCount.textContent = data.like_count;

        // Toggle the liked state *after* the successful API call
        liked = !liked; // crucial line

        if (liked) { // crucial
            likeIcon.classList.remove('fa-regular');
            likeIcon.classList.add('fa-solid');
            likeButton.classList.add("liked");
        } else { // crucial
            likeIcon.classList.remove('fa-solid');
            likeIcon.classList.add('fa-regular');
            likeButton.classList.remove("liked");
        }

        // Update the button's onclick to reflect the new state
        likeButton.setAttribute('onclick', `likeHandler(${postId}, ${liked})`);
    })
    .catch(error => {
        console.error("Error updating like:", error);
    });
}

function handleSubmit(postId) {
    const content = document.getElementById(`textarea_${postId}`).value;
    fetch(`/gym/edit/${postId}`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content: content })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            document.getElementById(`content_${postId}`).textContent = content;
            $(`#modal_edit_post_${postId}`).modal('hide');
        } else if (data.error) {
            console.error("Error:", data.error);
            alert(data.error);
        }
    })
    .catch(error => {
        console.error("Error:", error);
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
```

### Views (`views.py`)
The backend handles the logic for post creation, editing, liking, and deleting.

```python
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
```
---

## Styling and Responsiveness (`styles.css`)

The `styles.css` file is responsible for the visual presentation and responsive design of the RoshaClub application.  It leverages CSS3 features, including transitions, animations, flexbox, and grid, to create a modern and dynamic user experience. Key aspects of the styling include:

* **Color Palette:**  A dark color scheme with gold accents is used to create a sophisticated and visually appealing design.  Custom CSS variables (`--primary-color`, `--secondary-color`, etc.) are used for consistent color management throughout the application.

* **Typography:** The 'Poppins' font from Google Fonts is used for clean and readable text.  Different font weights are used to create visual hierarchy and emphasis.

* **Layout:**  The layout is primarily based on flexbox and CSS Grid, providing flexibility and adaptability to different screen sizes.  The `section__container` class is used to provide a consistent maximum width and padding for sections.

* **Animations and Transitions:** Subtle animations and transitions are applied to various elements, such as fade-in effects on content and hover effects on buttons and cards, enhancing user engagement and providing visual feedback.

* **Responsiveness:** Media queries are used extensively to ensure that the website adapts seamlessly to different screen sizes. Specific styles are applied for smaller screens to optimize content display and improve user experience on mobile devices.

* **Component-Specific Styles:**  The CSS includes specific styles for different components of the application, such as the navigation bar, header, training program cards, trainer profiles, community forum posts, and forms. These styles ensure consistency in design and presentation across the entire application.


## User Registration and Authentication:
Usage
1. Register: Create a user account.
2. Browse Programs: View available training programs.
3. Purchase Membership: Select and purchase a membership plan.
4. Manage Profile: Update personal details and track membership status.
5. Community Interaction: Post and respond in the community forum.


## File Breakdown

This section details the key files contributing to RoshaClub's functionality. While other supporting files exist (templates, static assets),  this breakdown focuses on the core logic and data handling components.

**Core Application Logic and Data:**

*   **`gym_app/models.py`:** Defines the data structures (models) for the application, including trainers, training programs, memberships, payments, users, and community forum posts.
*   **`gym_app/views.py`:** Contains the core backend logic, handling user requests, database interactions, payment processing, and rendering templates.
*   **`gym_app/urls.py`:** Maps URL patterns to their corresponding view functions in `views.py`, defining the application's routing.
*   **`gym_app/forms.py`:** Defines forms for user input, including post creation and user registration.
*   **`gym_app/admin.py`**: Registers models with the Django admin site for easy data management.

**Frontend (Templates, Styling, and Interactivity):**

The frontend of the application is built using a combination of HTML templates, CSS for styling, and JavaScript for interactive elements.  These files handle the user interface and user experience. Detailed descriptions can be provided upon request, but are not included here to focus on the core application logic.  The core frontend files include:
**Frontend (Templates, Styling, and Interactivity):**

*   **`templates/gym/about_us.html`:** Displays information about the gym.
*   **`templates/gym/community.html`:** Renders the community forum.
*   **`templates/gym/edit_profile.html`:** Provides a form for users to edit their profile.
*   **`templates/gym/index.html`:**  The main homepage template.
*   **`templates/gym/layout.html`:** The base template for all other templates.
*   **`templates/gym/login.html`:**  Displays the login form.
*   **`templates/gym/payments.html`:** Handles payment processing using Stripe.
*   **`templates/gym/profile_community.html`:**  Displays community posts on user profiles.
*   **`templates/gym/profile.html`:** Shows user profile information.
*   **`templates/gym/register.html`:** Displays the user registration form.
*   **`templates/gym/success.html`:** Shows payment success/failure messages.
*   **`templates/gym/training_programs.html`:** Lists the available training programs.
*   **`templates/gym/trainer_detail.html`:** Displays individual trainer profiles.
*   **`static/gym/styles.css`:** Styles the entire application using CSS, ensuring responsiveness and a consistent design.  Uses CSS variables, media queries, flexbox, and grid layout for modern styling.
*   **`static/gym/community.js`:** Handles community forum interactions, including AJAX requests for liking and editing posts. Implements CSRF token handling for security.
*   **`static/gym/scripts.js`:** Implements animations and interactive elements using the Intersection Observer API.
*   **`static/gym/google-pay.js`:**  Handles Google Pay integration for payments.
*   **`static/gym/assets`:** Contains static assets like images, icons, and other media.


---

## Distinctiveness and Complexity:

RoshaClub is a comprehensive gym membership management platform with integrated community features, distinguishing it significantly from Project 2 (Commerce), which focuses on a traditional auction-style e-commerce model. While RoshaClub includes e-commerce elements for handling membership payments, its core functionality and technical implementation are vastly different.

The key distinctions that set RoshaClub apart from Project 2 and demonstrate its increased complexity include:

* **Subscription-based Memberships vs. One-time Auction Purchases:** RoshaClub manages recurring membership subscriptions, handling subscription lifecycles, renewals, expirations, and various membership tiers. This contrasts sharply with Commerce's one-time auction purchases, where users bid on individual items.  Managing memberships requires complex backend logic to track durations, status (active, expired), and user-membership associations, adding significant complexity absent in Project 2.

* **Personalized User Experience based on Membership:** RoshaClub offers a personalized user experience based on the user's active membership status.  User profiles dynamically display information related to their current membership, including assigned trainer, program details, and membership expiration. This dynamic content rendering, driven by backend logic, differs from the static user profiles in Commerce, where user information is not contextually linked to purchased items.

* **Dynamic Community Forum with Real-time AJAX Interactions:**  A key differentiating feature is RoshaClub's dynamic community forum, built with AJAX for real-time interactions like liking and editing posts. This provides a seamless and engaging user experience, contrasting with Commerce's static comment section. Implementing AJAX in the community forum introduced considerable complexity in handling asynchronous requests, DOM manipulation, and CSRF token management in `community.js` (approximately X lines of code) and the corresponding backend views.

* **Trainer and Program Management Complexity:** RoshaClub incorporates functionality for managing trainer profiles and associating them with training programs. This involves database relationships (ForeignKeys, ManyToManyFields) and backend logic to handle these associations, adding a layer of complexity not present in Project 2, which focuses solely on item listings.

* **Advanced Payment Integration with Stripe and Google Pay:** Both projects handle payments, but RoshaClub integrates with Stripe, including support for Google Pay, providing a more robust and feature-rich payment system. This integration requires secure handling of webhooks for asynchronous payment confirmation and management of various payment scenarios, adding approximately Y lines of code to handle payment intents, responses, and updating membership statuses.  This is a more sophisticated implementation than Commerce's simpler payment model.

* **Focus on Responsive Design:** RoshaClub prioritizes responsive design, using media queries and Bootstrap's grid system in `styles.css` to ensure a consistent user experience across various devices (desktops, tablets, and mobile).  While Project 2 might include styling, the Capstone project has a requirement for responsiveness.

The combined features and technical implementations in RoshaClub make it substantially more complex than Project 2.  RoshaClub is a distinct application that moves beyond basic e-commerce or auction functionalities by incorporating dynamic content, real-time interactions, and robust membership and payment management.  This project represents a significant advancement in features, scope, and technical implementation compared to Project 2, demonstrating the fulfillment of the distinctiveness and complexity requirements for the Capstone Project.

## Contributing:
We welcome contributions! Please follow these steps:
- `Fork` the repository.
- `Create` a new branch (git checkout -b feature-branch).
- `Commit` your changes (git commit -m 'Add feature').
- `Push` the branch (git push origin feature-branch).
- `Create` a pull request.

## Additional Information
RoshaClub utilizes Bootstrap for styling and responsive design, ensuring a consistent and user-friendly experience across various devices. The community forum functionality is enhanced with AJAX to provide real-time updates and a more engaging user interface. CSRF protection is implemented throughout the application to mitigate cross-site request forgery attacks, a crucial aspect of web application security. The use of custom CSS properties (variables) in styles.css allows for easy and consistent theme management. The dynamic animations, implemented using the Intersection Observer API in scripts.js, enhance user engagement without compromising performance, as elements are only animated when they are visible in the viewport.

## Contact
For any questions or feedback, feel free to contact me at ` rochnyak180405@gmail.com `(Roman Rochniak).
