from django.db import models
from django.utils import timezone
from django.conf import settings

# Create your models here.
class UserSuggest(models.Model):
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='suggestions')
    elder = models.ForeignKey(settings.AUTH_USER_MODEL,related_name='admissions')
    suggest = models.TextField(blank=True)
    decision = models.NullBooleanField(null=True,blank=True)

class Questionnaire(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    def __str__(self):
        return self.name

class Question(models.Model):
    question_text = models.TextField()
    optional = models.BooleanField(default=False)
    is_choice = models.BooleanField(default=False)
    questionnaire = models.ForeignKey(Questionnaire)
    order = models.IntegerField(default=0)
    answer_type = models.CharField(max_length=20,default='text')
    dropdown_unit = models.CharField(default='', max_length=10,blank=True, null=True)
    def __str__(self):
        return  '%d. %s (%s)' % (self.order, self.question_text, self.questionnaire)
    
    class Meta:
        ordering = ['order','id']
    
    def is_of_type(self, type_name):
        return self.answer_type == type_name

    def is_choices(self):
        return self.is_of_type('choices')
    
    def is_dropdown(self):
        return self.is_of_type('dropdown')

    def is_text(self):
        return self.is_of_type('text')

    def is_scale(self):
        return self.is_of_type('scale')

    def is_table(self):
        return self.is_of_type('table')
    
    def has_unit(self):
        return self.is_dropdown() and self.dropdown_unit != ''

class ScaleQuestion(Question):
    min_val = models.IntegerField(default=-4)
    max_val = models.IntegerField(default=4)
    min_description = models.CharField(max_length=20,default='-4')
    max_description = models.CharField(max_length=20,default='4')

    def range(self):
        return range(self.min_val, self.max_val+1)

class AxisEntry(models.Model):
    question = models.ForeignKey(Question)
    text_content = models.TextField()
    order = models.IntegerField(default = 0)
    axis_number = models.PositiveSmallIntegerField(default = 1)
    def __str__(self):
        var = ['x','y','z'][self.axis_number-1]
        return '%s = "%s"' % (var, self.text_content)
    class Meta:
        ordering = ['order','id']

class Choice(models.Model):
    question = models.ForeignKey(Question)
    text_content = models.TextField()
    def __str__(self):
        return '%s: %s' % (str(self.question), self.text_content)
    
    def toString(self):
        if self.question.is_dropdown():
            return '%s %s' % (self.text_content, self.question.dropdown_unit)
        return self.text_content

class Dependency(models.Model):
    question = models.ForeignKey(Question)
    depends_on = models.ForeignKey(Choice)
    def __str__(self):
        return '%s 依赖于：%s 的选项 %s' % (self.question,
            self.depends_on.question,
            self.depends_on.text_content)

class Commit(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='commits')
    questionnaire = models.ForeignKey(Questionnaire)
    commit_time = models.DateTimeField(default=timezone.now)
    is_under_review = models.BooleanField(default=True)
    def __str__(self):
        return '{}: {}'.format(self.questionnaire.name, self.user.username)
    class Meta:
        permissions = (
            ("manage_commit", "Can view and do other management to commits."),
        )
        ordering = ['commit_time']

class Answer(models.Model):
    question = models.ForeignKey(Question)
    commit = models.ForeignKey(Commit)
    is_answered = models.BooleanField(default=True)
    choice_answer = models.ForeignKey(Choice,blank=True,null=True,on_delete=models.CASCADE)
    text_answer = models.TextField(blank=True,null=True)
    scale_answer = models.IntegerField(blank=True, null=True)
    class Meta:
        ordering = ['commit','question','id']
    
    def _content_text(self):
        if not self.is_answered:
            return 'Unanswered'
        elif self.question.is_scale() and self.scale_answer != None:
            sq = self.question.scalequestion
            return '%d (%s %d 到 %d %s)' % (
                self.scale_answer,
                sq.min_description,
                sq.min_val,
                sq.max_val,
                sq.max_description
            )
        elif self.question.is_table() and self.table_answer() != None:
            return str(self.table_answer())
        elif (self.question.is_choices() or self.question.is_choice) and self.choice_answer != None:
            return self.choice_answer.toString()
        elif self.text_answer!=None:
            return self.text_answer
        else:
            return 'Unknown answer'
    
    def table_answer(self):
        if self.question.is_table():
            aea = AxisEntryAnswer.objects.filter(answer=self)
            d = {}
            for row in aea:
                d[row.y_axis_answer.text_content] = row.x_axis_answer.text_content
            return d
        else:
            return None

    def __str__(self):
        return '%s (%s)' % (self._content_text(), self.question.question_text)


class AxisEntryAnswer(models.Model):
    answer = models.ForeignKey(Answer)
    x_axis_answer = models.ForeignKey(AxisEntry, blank=True, null=True, related_name='x_axis_answer')
    y_axis_answer = models.ForeignKey(AxisEntry, blank=True, null=True, related_name='y_axis_answer')

class SiteSettings(models.Model):
    key = models.CharField(max_length=100)
    value = models.TextField()
    def __str__(self):
        return "%s: %s" % (self.key, self.value)

class SiteSettingManager:
    def __getitem__(self, key):
        try:
            return SiteSettings.objects.get(key=key).value
        except:
            return None
    
    def __setitem__(self, key, value):
        try:
            o = SiteSettings.objects.get(key=key)
            o.value = value
            o.save()
            return o
        except:
            return None