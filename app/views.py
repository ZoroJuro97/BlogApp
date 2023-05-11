from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from app.forms import CommentForm, NewUserForm, SubscribeForm
from django.http import HttpResponseRedirect
from app.models import Comments, Post, Profile, Tag, WebsiteMeta
from django.contrib.auth.models import User
from django.db.models import Count
from django.contrib.auth import login

# Create your views here.

def index(request):
    posts = Post.objects.all()
    top_posts = Post.objects.all().order_by('-view_count')[0:3]
    recent_posts = Post.objects.all().order_by('-last_updated')[0:3]
    featured = Post.objects.filter(is_featured=True)
    subscribe_form = SubscribeForm()
    successful = None
    website_info = None

    if WebsiteMeta.objects.all().exists():
        website_info = WebsiteMeta.objects.all()[0]
    
    if featured:
        featured = featured[0]

    if request.POST:
        subscribe_form = SubscribeForm(request.POST)
        if subscribe_form.is_valid:
            subscribe_form.save()
            request.session['subscribed'] = True
            successful = 'Successful'
            subscribe_form = SubscribeForm()    #reset form

    context = {'posts':posts, 'top_posts':top_posts, 'recent_posts':recent_posts, 'website_info':website_info,
    'subscribe_form':subscribe_form, 'successful':successful, 'featured':featured}
    return render(request, "app/index.html", context)

def tag_page(request, slug):
    tag = Tag.objects.get(slug=slug)
    top_posts = Post.objects.filter(tag__in=[tag.id]).order_by('-view_count')[0:2]
    recent_posts = Post.objects.filter(tag__in=[tag.id]).order_by('-last_updated')[0:2]
    tags = Tag.objects.all()
    
    context={'tag':tag, 'top_posts':top_posts, 'recent_posts':recent_posts, 'tags':tags}
    return render(request, "app/tag.html", context)

def author_page(request,slug):
    author = Profile.objects.get(slug=slug)
    top_posts = Post.objects.filter(author__in=[author.id]).order_by('-view_count')[0:2]
    recent_posts = Post.objects.filter(author__in=[author.id]).order_by('-last_updated')[0:2]
    top_authors = User.objects.annotate(number=Count('post')).order_by('number')
    
    context = {'author':author, 'top_posts':top_posts, 'recent_posts':recent_posts, 'top_authors':top_authors}
    return render(request, "app/author.html", context)

def post_page(request, slug):
    post = Post.objects.get(slug = slug)
    comments = Comments.objects.filter(post=post, parent=None)
    form = CommentForm()

    #Bookmark Logic
    bookmarked = False
    if post.bookmarks.filter(id = request.user.id).exists():
        bookmarked = True
    is_bookmarked = bookmarked

    #Liked Logic
    liked = False
    if post.likes.filter(id = request.user.id).exists():
        liked = True
    number_of_likes = post.number_of_likes()
    post_is_liked = liked
    
    if request.POST:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid:
            if request.POST.get('parent'):
                #saving comments as replies
                parent = request.POST.get('parent')
                parent_obj = Comments.objects.get(id = parent)
                if parent_obj:
                    reply_comment = comment_form.save(commit=False)
                    reply_comment.post = post
                    reply_comment.parent = parent_obj
                    reply_comment.save()
                    return HttpResponseRedirect(reverse('post_page', kwargs={'slug':slug}))
            else:
                #saving comments
                comment = comment_form.save(commit=False)
                postid = request.POST.get('post_id')
                post = Post.objects.get(id = postid)
                comment.post=post
                comment.save()
                return HttpResponseRedirect(reverse('post_page', kwargs={'slug':slug}))
    
    if post.view_count is None:
        post.view_count = 1
    else:
        post.view_count = post.view_count + 1
    post.save()
        
    #Side-Bar
    recent_posts = Post.objects.exclude(id=post.id).order_by('-last_updated')[0:3]
    top_authors = User.objects.annotate(number=Count('post')).order_by('-number')
    tags = Tag.objects.all()
    related_posts = Post.objects.exclude(id=post.id).filter(author=post.author)[0:3]

    context = {"post":post, "form":form, "comments":comments, 'is_bookmarked':is_bookmarked, 
               "post_is_liked":post_is_liked, "number_of_likes":number_of_likes, 'recent_posts':recent_posts,
               'top_authors':top_authors, 'tags':tags, 'related_posts':related_posts}
    return render(request, "app/post.html", context)

def search_posts(request):
    search_query=''
    if request.GET.get('q'):
        search_query = request.GET.get('q')
    posts = Post.objects.filter(title__icontains=search_query)
    context={'posts':posts, 'search_query':search_query}
    return render(request, "app/search.html", context)

def about_page(request):
    web_info = None

    if WebsiteMeta.objects.all().exists():
        web_info = WebsiteMeta.objects.all()[0]
    context={'web_info':web_info}
    return render(request, "app/about.html", context)

def register_user(request):
    form = NewUserForm()

    if request.method == 'POST':
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/")

    context={'form':form}
    return render(request, "registration/registration.html", context)

def bookmark_post(request, slug):
    post = get_object_or_404(Post, id=request.POST.get('post_id'))
    if post.bookmarks.filter(id=request.user.id).exists():
        post.bookmarks.remove(request.user)
    else:
        post.bookmarks.add(request.user)
    return HttpResponseRedirect(reverse('post_page', args=[str(slug)]))

def like_post(request, slug):
    post = get_object_or_404(Post, id=request.POST.get('post_id'))
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
    return HttpResponseRedirect(reverse('post_page', args=[str(slug)]))

def all_bookmarked_posts(request):
    all_bookmarked_posts = Post.objects.filter(bookmarks=request.user)
    context={'all_bookmarked_posts':all_bookmarked_posts}
    return render(request, "app/all_bookmarked_posts.html", context)

def all_posts(request):
    all_posts = Post.objects.all()
    context={'all_posts':all_posts}
    return render(request, "app/all_posts.html", context)

def all_liked_posts(request):
    all_liked_posts = Post.objects.filter(likes=request.user)
    context={'all_liked_posts':all_liked_posts}
    return render(request, "app/all_liked_posts.html", context)