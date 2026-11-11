from .models import SiteSetting, SocialLink, SEO


def site_settings(request):
    """
    Context processor to make site settings available globally
    """
    try:
        site_settings = SiteSetting.get_singleton()
        social_links = SocialLink.objects.filter(is_active=True)
        
        # Get SEO metadata for current page
        seo_data = {}
        if hasattr(request, 'path'):
            page_key = request.path.strip('/') or 'home'
            try:
                seo = SEO.objects.get(page_key=page_key)
                seo_data = {
                    'meta_title': seo.meta_title,
                    'meta_description': seo.meta_description,
                    'meta_keywords': seo.meta_keywords,
                    'og_image': seo.og_image,
                }
            except SEO.DoesNotExist:
                # Default SEO data
                seo_data = {
                    'meta_title': site_settings.site_name,
                    'meta_description': f"{site_settings.hero_title} - {site_settings.hero_subtitle}",
                    'meta_keywords': 'portfolio, developer, django, python',
                    'og_image': None,
                }
        
        return {
            'site_settings': site_settings,
            'social_links': social_links,
            'seo': seo_data,
        }
    except Exception:
        # Fallback for when database is not ready
        return {
            'site_settings': None,
            'social_links': [],
            'seo': {
                'meta_title': 'Portfolio',
                'meta_description': 'Personal Portfolio Website',
                'meta_keywords': 'portfolio, developer',
                'og_image': None,
            }
        }
