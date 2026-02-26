from django.urls import path
from django.conf.urls.static import static
from django.conf import settings

from . import views

urlpatterns = [
    path('', views.index, name='index'),

    # Auth
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('join/', views.join, name='join'),

    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),

    # Pages
    path('about-us/', views.about_us, name='about_us'),
    path('training-programs/', views.training_programs, name='training_programs'),
    path('trainer/<int:trainer_id>/', views.trainer_detail, name='trainer_detail'),
    path('program/<int:id>/', views.program_detail, name='program_detail'),

    # Memberships
    path('memberships/', views.memberships_list, name='memberships_list'),
    path('memberships/create/<int:program_id>/', views.create_membership, name='create_membership'),

    # Payments
    path('payment/<int:program_id>/', views.process_payment, name='process_payment'),
    path('payments/', views.payments, name='payments'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),

    # Community
    path('community/', views.community, name='community'),
    path('new_post/', views.new_post, name='new_post'),
    path('edit/<int:post_id>/', views.edit_post, name='edit_post'),
    path('like_add/<int:post_id>/', views.like_add, name='like_add'),
    path('like_remove/<int:post_id>/', views.like_remove, name='like_remove'),
    path('user/<str:username>/', views.user_posts, name='user_posts'),
    path('delete_post/<int:post_id>/', views.delete_post, name='delete_post'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)