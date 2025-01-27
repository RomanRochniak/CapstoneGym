from django.contrib import admin
from .models import User, TrainingProgram, Membership, Trainer, Payment, Post

# Register your models here.


admin.site.register(User)
admin.site.register(TrainingProgram)
admin.site.register(Membership)
admin.site.register(Trainer)
admin.site.register(Payment)
admin.site.register(Post)