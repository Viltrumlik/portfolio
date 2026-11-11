from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils import timezone
from datetime import date

from core.models import SiteSetting, SocialLink, SEO
from pages.models import Skill, Experience, AboutSection, Service, ServiceFeature
from portfolio.models import Technology, Project
from blog.models import Category, Tag, Article


class Command(BaseCommand):
    help = 'Populate the database with generic placeholder content for the portfolio template'

    def handle(self, *args, **options):
        self.stdout.write('Populating placeholder data...')

        # ── Site settings ──────────────────────────────────────────────────
        SiteSetting.objects.get_or_create(
            pk=1,
            defaults={
                'site_name': 'Alex Morgan',
                'hero_title': "I'm Alex Morgan",
                'hero_subtitle': 'Full-Stack Developer',
                'hero_greeting': '👋 Hello, I am',
                'hero_description': "I build clean, scalable web applications with a focus on great "
                                    "user experiences and reliable backend systems.",
                'contact_email': 'hello@example.com',
                'phone': '',
                'location': 'Remote · Worldwide',
            }
        )

        # ── Social links ───────────────────────────────────────────────────
        social_links_data = [
            {'platform_name': 'github', 'url': 'https://github.com/yourusername',
             'icon_class': 'fab fa-github', 'order': 1},
            {'platform_name': 'linkedin', 'url': 'https://www.linkedin.com/in/yourusername/',
             'icon_class': 'fab fa-linkedin-in', 'order': 2},
            {'platform_name': 'twitter', 'url': 'https://twitter.com/yourusername',
             'icon_class': 'fab fa-twitter', 'order': 3},
            {'platform_name': 'instagram', 'url': 'https://instagram.com/yourusername',
             'icon_class': 'fab fa-instagram', 'order': 4},
        ]
        for data in social_links_data:
            SocialLink.objects.get_or_create(platform_name=data['platform_name'], defaults=data)

        # ── Skills ─────────────────────────────────────────────────────────
        skills_data = [
            {'name': 'HTML5', 'level': 95, 'group': 'frontend', 'icon_class': 'fab fa-html5'},
            {'name': 'CSS3', 'level': 90, 'group': 'frontend', 'icon_class': 'fab fa-css3-alt'},
            {'name': 'JavaScript', 'level': 85, 'group': 'frontend', 'icon_class': 'fab fa-js'},
            {'name': 'React', 'level': 80, 'group': 'frontend', 'icon_class': 'fab fa-react'},
            {'name': 'Python', 'level': 90, 'group': 'backend', 'icon_class': 'fab fa-python'},
            {'name': 'Django', 'level': 88, 'group': 'backend', 'icon_class': 'fas fa-server'},
            {'name': 'Node.js', 'level': 75, 'group': 'backend', 'icon_class': 'fab fa-node-js'},
            {'name': 'REST APIs', 'level': 85, 'group': 'backend', 'icon_class': 'fas fa-plug'},
            {'name': 'PostgreSQL', 'level': 80, 'group': 'database', 'icon_class': 'fas fa-database'},
            {'name': 'Redis', 'level': 65, 'group': 'database', 'icon_class': 'fas fa-database'},
            {'name': 'Git', 'level': 92, 'group': 'devops', 'icon_class': 'fab fa-git-alt'},
            {'name': 'Docker', 'level': 75, 'group': 'devops', 'icon_class': 'fab fa-docker'},
        ]
        for data in skills_data:
            Skill.objects.get_or_create(name=data['name'], defaults=data)

        # ── Technologies ───────────────────────────────────────────────────
        technologies_data = [
            {'name': 'Django', 'icon_class': 'fas fa-server'},
            {'name': 'Python', 'icon_class': 'fab fa-python'},
            {'name': 'React', 'icon_class': 'fab fa-react'},
            {'name': 'JavaScript', 'icon_class': 'fab fa-js'},
            {'name': 'PostgreSQL', 'icon_class': 'fas fa-database'},
            {'name': 'Docker', 'icon_class': 'fab fa-docker'},
            {'name': 'Tailwind CSS', 'icon_class': 'fas fa-wind'},
            {'name': 'Git', 'icon_class': 'fab fa-git-alt'},
        ]
        for data in technologies_data:
            Technology.objects.get_or_create(name=data['name'], defaults=data)

        # ── Blog categories & tags ─────────────────────────────────────────
        categories_data = [
            {'name': 'Web Development', 'description': 'Articles about building for the web'},
            {'name': 'Python', 'description': 'Python programming tutorials and tips'},
            {'name': 'Career', 'description': 'Lessons from working as a developer'},
        ]
        for data in categories_data:
            Category.objects.get_or_create(name=data['name'], defaults=data)

        for tag_name in ['python', 'django', 'web-development', 'tutorial', 'javascript',
                         'react', 'css', 'productivity']:
            Tag.objects.get_or_create(name=tag_name, defaults={'slug': slugify(tag_name)})

        # ── About section ──────────────────────────────────────────────────
        AboutSection.objects.get_or_create(
            pk=1,
            defaults={
                'title': 'About Me',
                'content': "<p>I'm a full-stack developer who loves turning ideas into polished, "
                           "production-ready products. I care about clean architecture, thoughtful "
                           "UX, and code that's a pleasure to maintain.</p>"
                           "<p>I work primarily with Python, Django, and modern JavaScript "
                           "frameworks, and I'm always exploring new tools to sharpen my craft.</p>",
                'education': 'B.Sc. Computer Science',
                'location': 'Remote · Worldwide',
                'languages': 'English',
                'years_experience': '5+',
                'projects_completed': '40+',
                'happy_clients': '25+',
            }
        )

        # ── Experience ─────────────────────────────────────────────────────
        experiences_data = [
            {
                'company': 'Acme Digital', 'role': 'Senior Full-Stack Developer',
                'description': 'Lead development of customer-facing web applications, mentor junior '
                               'engineers, and drive architecture decisions across the stack.',
                'start_date': date(2022, 1, 1), 'is_current': True, 'order': 1,
            },
            {
                'company': 'Bright Labs', 'role': 'Backend Developer',
                'description': 'Designed and built REST APIs, optimised database performance, and '
                               'shipped features for a high-traffic SaaS platform.',
                'start_date': date(2019, 6, 1), 'end_date': date(2021, 12, 1), 'order': 2,
            },
            {
                'company': 'Freelance', 'role': 'Web Developer',
                'description': 'Delivered websites and small applications for a range of clients, '
                               'handling everything from design to deployment.',
                'start_date': date(2018, 1, 1), 'end_date': date(2019, 5, 1), 'order': 3,
            },
        ]
        for data in experiences_data:
            Experience.objects.get_or_create(
                company=data['company'], role=data['role'], defaults=data)

        # ── Services ───────────────────────────────────────────────────────
        services_data = [
            {'title': 'Web Development', 'icon_class': 'fas fa-code', 'order': 1,
             'description': 'Responsive, fast websites and web apps built with modern frameworks.',
             'features': ['Responsive design', 'SEO-friendly', 'Performance-focused']},
            {'title': 'Backend & APIs', 'icon_class': 'fas fa-server', 'order': 2,
             'description': 'Robust server-side systems and clean, well-documented APIs.',
             'features': ['REST APIs', 'Database design', 'Authentication']},
            {'title': 'Consulting', 'icon_class': 'fas fa-lightbulb', 'order': 3,
             'description': 'Architecture reviews and technical guidance to keep projects on track.',
             'features': ['Code review', 'Architecture', 'Best practices']},
        ]
        for data in services_data:
            features = data.pop('features', [])
            service, created = Service.objects.get_or_create(title=data['title'], defaults=data)
            if created:
                for name in features:
                    ServiceFeature.objects.create(service=service, name=name)

        # ── Sample projects ────────────────────────────────────────────────
        techs = {t.name: t for t in Technology.objects.all()}
        projects_data = [
            {
                'title': 'TaskFlow', 'slug': 'taskflow',
                'short_description': 'A collaborative task management app with real-time updates.',
                'description': 'TaskFlow is a full-featured project management tool with boards, '
                               'drag-and-drop tasks, team collaboration, and real-time updates. '
                               'Built with Django on the backend and React on the frontend.',
                'github_url': 'https://github.com/yourusername/taskflow',
                'live_url': 'https://example.com/taskflow', 'is_featured': True,
                'techs': ['Django', 'React', 'PostgreSQL'],
            },
            {
                'title': 'DevBlog API', 'slug': 'devblog-api',
                'short_description': 'A RESTful blogging API with authentication and rich content.',
                'description': 'A clean, well-tested REST API for a blogging platform, featuring '
                               'JWT authentication, role-based permissions, markdown content, and '
                               'comprehensive OpenAPI documentation.',
                'github_url': 'https://github.com/yourusername/devblog-api',
                'is_featured': True, 'techs': ['Django', 'Python', 'PostgreSQL'],
            },
            {
                'title': 'ShopLite', 'slug': 'shoplite',
                'short_description': 'A lightweight e-commerce storefront with cart and checkout.',
                'description': 'ShopLite is a minimal e-commerce solution with a product catalogue, '
                               'shopping cart, checkout flow, and an admin dashboard for managing '
                               'inventory and orders.',
                'github_url': 'https://github.com/yourusername/shoplite',
                'live_url': 'https://example.com/shoplite', 'is_featured': False,
                'techs': ['Django', 'JavaScript', 'Docker'],
            },
        ]
        for data in projects_data:
            tech_names = data.pop('techs', [])
            project, created = Project.objects.get_or_create(slug=data['slug'], defaults=data)
            if created:
                project.technologies.add(*[techs[n] for n in tech_names if n in techs])

        # ── Sample articles ────────────────────────────────────────────────
        web_dev_cat = Category.objects.get(name='Web Development')
        python_cat = Category.objects.get(name='Python')
        articles_data = [
            {
                'title': 'Building Your First Django App', 'slug': 'building-your-first-django-app',
                'excerpt': 'A friendly, step-by-step introduction to building a web app with Django.',
                'content': '# Building Your First Django App\n\n'
                           'Django makes it easy to build robust web applications quickly. In this '
                           'guide we walk through creating a project from scratch.\n\n'
                           '## Getting Started\n\n```bash\npip install django\n'
                           'django-admin startproject myproject\n```\n\n'
                           '## Creating an App\n\n```bash\npython manage.py startapp blog\n```\n\n'
                           '## Conclusion\n\nYou now have the foundations to keep building. Happy coding!',
                'category': web_dev_cat, 'published': True, 'published_at': timezone.now(),
            },
            {
                'title': 'Writing Clean Python Code', 'slug': 'writing-clean-python-code',
                'excerpt': 'Practical tips for writing Python that is readable and maintainable.',
                'content': '# Writing Clean Python Code\n\n'
                           'Clean code is easier to read, test, and maintain. Here are a few habits '
                           'that go a long way.\n\n'
                           '## Use Descriptive Names\n\n```python\n# Good\n'
                           'def calculate_total_price(items):\n    ...\n```\n\n'
                           '## Keep Functions Small\n\nEach function should do one thing well.\n\n'
                           '## Conclusion\n\nSmall, consistent improvements compound over time.',
                'category': python_cat, 'published': True, 'published_at': timezone.now(),
            },
        ]
        for data in articles_data:
            article, created = Article.objects.get_or_create(slug=data['slug'], defaults=data)
            if created:
                tags = Tag.objects.filter(name__in=['python', 'django'])
                article.tags.add(*tags)

        # ── SEO ────────────────────────────────────────────────────────────
        seo_data = [
            {'page_key': 'home', 'meta_title': 'Alex Morgan — Full-Stack Developer',
             'meta_description': 'Portfolio of Alex Morgan, a full-stack developer building clean, '
                                 'scalable web applications.',
             'meta_keywords': 'portfolio, developer, full-stack, django, python, react'},
            {'page_key': 'pages/about', 'meta_title': 'About — Alex Morgan',
             'meta_description': "Learn more about Alex Morgan's background, skills, and experience.",
             'meta_keywords': 'about, developer, experience, skills'},
        ]
        for data in seo_data:
            SEO.objects.get_or_create(page_key=data['page_key'], defaults=data)

        self.stdout.write(self.style.SUCCESS('Placeholder data populated successfully!'))
