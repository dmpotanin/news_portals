
from django.shortcuts import get_object_or_404


from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Post, Category
from .filters import PostFilter
from .forms import PostForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.views import View
from django.core.mail import EmailMultiAlternatives  # импортируем класс для создание объекта письма с html
from datetime import datetime

from django.template.loader import render_to_string  # импортируем функцию, которая срендерит наш html в текст
from .models import Appointment

from django.dispatch import receiver
from django.core.mail import send_mail
from django.http import HttpResponse
from django.views import View
from .tasks import hello, printer

class IndexView(View):
    def get(self, request):
        hello.delay()
        return HttpResponse('Hello!')

def send_welcome_email(sender, user, request, **kwargs):
    subject = 'ようこそ'
    message = f' {user.username}様,\n登録してくれた感謝致します。'
    from_email = 'aleksandrbulda@mail.ru'  # Замените на ваш адрес электронной почты
    recipient_list = [user.email]

    send_mail(subject, message, from_email, recipient_list, fail_silently=False)

class AppointmentView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'appointment/make_appointment.html', {})

    def post(self, request, *args, **kwargs):
        appointment = Appointment(
            date=datetime.strptime(request.POST['date'], '%Y-%m-%d'),
            client_name=request.POST['client_name'],
            message=request.POST['message'],
        )
        appointment.save()

        # получаем наш html
        html_content = render_to_string(
            'appointment/appointment_created.html',
            {
                'appointment': appointment,
            }
        )

        # в конструкторе уже знакомые нам параметры, да? Называются правда немного по-другому, но суть та же.
        msg = EmailMultiAlternatives(
            subject=f'{appointment.client_name} {appointment.date.strftime("%Y-%M-%d")}',
            body=appointment.message,  # это то же, что и message
            from_email='aleksandrbulda@mail.ru',
            to=['alexbulda97@gmail.com'],  # это то же, что и recipients_list
        )
        msg.attach_alternative(html_content, "text/html")  # добавляем html
        msg.send()  # отсылаем

        return redirect('appointment_created')

class PostList(ListView):
    model = Post
    ordering = '-title',
    template_name = 'PostCategory.html'
    context_object_name ='PostCategory'
    paginate_by = 3  # вот так мы можем указать количество записей на странице

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = PostFilter(self.request.GET, queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['time_now'] = datetime.utcnow()
        context['next_sale'] = None
        context['filterset'] = self.filterset
        return context

class PostDetail(DetailView):
    model = Post
    template_name = 'PostCategoryOneByOne.html'
    context_object_name = 'PostCategoryOneByOne'



#def create_news(request):
#    form = PostForm()

#    if request.method == 'POST':
 #       form = PostForm(request.POST)
#        if form.is_valid():
#            form.save()
#            return HttpResponseRedirect('/news/')

 #   return render(request, 'post_create.html', {'form': form})

# Добавляем новое представление для создания товаров.
class PostCreate(PermissionRequiredMixin,LoginRequiredMixin, CreateView):
    form_class = PostForm
    model = Post
    template_name = 'post_create.html'
    permission_required = ('news.add_post',)

class PostUpdate(PermissionRequiredMixin,LoginRequiredMixin,UpdateView):
    form_class = PostForm
    model = Post
    template_name = 'post_create.html'
    permission_required = ('news.change_post',)

class PostDelete(DeleteView):
    model = Post
    template_name = 'post_delete.html'
    success_url = reverse_lazy('news')


@method_decorator(login_required(login_url = '/login/'), name='dispatch')
class ProtectedView(TemplateView):
    template_name = 'prodected_page.html'

class ProtectedView(LoginRequiredMixin, TemplateView):
    template_name = 'prodected_page.html'


class CategoryListView(PostList):
    model = Post
    template_name = 'category_list.html'
    context_object_name = 'category_news_list'

    def get_queryset(self):
        self.category = get_object_or_404(Category, id=self.kwargs['pk'])
        queryset = Post.objects.filter(category=self.category).order_by('-created_at')
        return queryset

    def get_context_data(self,**kwargs):
        context = super.get_context_data(**kwargs)
        context['is_nor_subscriber'] = self.request.user not in self.category.subscribers.all()
        context['category'] = self.category
        return context

@login_required
def subscribe(request, pk):
    user = request.user
    category = Category.objects.get(id=pk)
    category.subscribers.add(user)
    message = '登録済み'
    return render(request, 'subscribe.html', {'category': category, 'message':message})