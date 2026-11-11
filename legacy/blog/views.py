from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils.feedgenerator import Rss201rev2Feed
import markdown
from .models import Article, Category, Tag


class ArticleListView(ListView):
    model = Article
    template_name = 'blog/article_list.html'
    context_object_name = 'articles'
    paginate_by = 6
    
    def get_queryset(self):
        return Article.objects.filter(published=True).select_related('category').prefetch_related('tags').order_by('-published_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['tags'] = Tag.objects.all()
        context['featured_articles'] = Article.objects.filter(
            published=True
        ).order_by('-published_at')[:3]
        return context


class ArticleDetailView(DetailView):
    model = Article
    template_name = 'blog/article_detail.html'
    context_object_name = 'article'
    
    def get_queryset(self):
        return Article.objects.filter(
            published=True
        ).select_related('category').prefetch_related('tags')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = context['article']  # Already fetched by DetailView
        
        # Convert markdown content to HTML
        context['content_html'] = markdown.markdown(
            article.content,
            extensions=['codehilite', 'fenced_code', 'tables', 'toc']
        )
        
        # Get related articles (same category)
        context['related_articles'] = Article.objects.filter(
            category=article.category,
            published=True
        ).exclude(id=article.id)[:3]
        
        # Get all categories and tags for sidebar
        context['categories'] = Category.objects.all()
        context['tags'] = Tag.objects.all()
        
        return context


class CategoryArticleListView(ListView):
    model = Article
    template_name = 'blog/article_list.html'
    context_object_name = 'articles'
    paginate_by = 6
    
    def get_queryset(self):
        category_slug = self.kwargs['slug']
        category = get_object_or_404(Category, slug=category_slug)
        return Article.objects.filter(
            category=category,
            published=True
        ).select_related('category').prefetch_related('tags')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs['slug']
        context['category'] = get_object_or_404(Category, slug=category_slug)
        context['categories'] = Category.objects.all()
        context['tags'] = Tag.objects.all()
        return context


class TagArticleListView(ListView):
    model = Article
    template_name = 'blog/article_list.html'
    context_object_name = 'articles'
    paginate_by = 6
    
    def get_queryset(self):
        tag_slug = self.kwargs['slug']
        tag = get_object_or_404(Tag, slug=tag_slug)
        return Article.objects.filter(
            tags=tag,
            published=True
        ).select_related('category').prefetch_related('tags')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tag_slug = self.kwargs['slug']
        context['tag'] = get_object_or_404(Tag, slug=tag_slug)
        context['categories'] = Category.objects.all()
        context['tags'] = Tag.objects.all()
        return context


class BlogFeed(Feed):
    title = "Portfolio Blog Feed"
    link = "/blog/"
    description = "Latest articles from my portfolio blog"
    feed_type = Rss201rev2Feed
    
    def items(self):
        return Article.objects.filter(published=True).order_by('-published_at')[:10]
    
    def item_title(self, item):
        return item.title
    
    def item_description(self, item):
        return item.excerpt
    
    def item_link(self, item):
        return item.get_absolute_url()
    
    def item_pubdate(self, item):
        return item.published_at
