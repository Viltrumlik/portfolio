from django.urls import path
from .views import ArticleListView, ArticleDetailView, CategoryArticleListView, TagArticleListView, BlogFeed

app_name = 'blog'

urlpatterns = [
    path('', ArticleListView.as_view(), name='article_list'),
    path('feed/', BlogFeed(), name='feed'),
    path('category/<slug:slug>/', CategoryArticleListView.as_view(), name='category_articles'),
    path('tag/<slug:slug>/', TagArticleListView.as_view(), name='tag_articles'),
    path('<slug:slug>/', ArticleDetailView.as_view(), name='article_detail'),
]
