from .models import *
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

class AnswerInline(admin.TabularInline):
    model = Answer
    def has_add_permission(self,request):
        return False
class CommitAdmin(admin.ModelAdmin):
    inlines = [AnswerInline]

class CommitInline(admin.StackedInline):
    model = Commit
    def has_add_permission(self,request):
        return False

class QuestionAdmin(admin.ModelAdmin):
    ordering = ('-questionnaire', 'order')

class AxisEntryAdmin(admin.ModelAdmin):
    ordering = ('axis_number','order','pk')

UserAdmin.inlines = [CommitInline]

# Register your models here.
admin.site.register(Questionnaire)
admin.site.register(Question, QuestionAdmin)
admin.site.register(ScaleQuestion)
admin.site.register(Choice)
admin.site.register(AxisEntry,AxisEntryAdmin)
admin.site.register(Commit,CommitAdmin)
admin.site.register(Answer)
admin.site.unregister(User)
admin.site.register(User,UserAdmin)
admin.site.register(UserSuggest)
admin.site.register(Dependency)
admin.site.register(SiteSettings)
