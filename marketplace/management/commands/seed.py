from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from marketplace.models import Category, Product, Review
from blog.models import BlogPost
from orders.models import Coupon
import os
import datetime

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing products, categories, blog posts, and coupons before seeding.',
        )

    def handle(self, *args, **options):
        if options.get('clear'):
            self.stdout.write('Clearing existing database entries...')
            Category.objects.all().delete()
            Product.objects.all().delete()
            BlogPost.objects.all().delete()
            Coupon.objects.all().delete()

        # 1. Create Default Superuser
        username = os.getenv('ADMIN_USERNAME', 'admin')
        email = os.getenv('ADMIN_EMAIL', 'admin@pawanmod.com')
        password = os.getenv('ADMIN_PASSWORD', 'admin123')

        if not User.objects.filter(is_superuser=True).exists():
            self.stdout.write(f'Creating administrative superuser ({username})...')
            User.objects.create_superuser(username, email, password)
        else:
            self.stdout.write('Superuser already exists. Skipping creation.')
        
        # 2. Create Categories
        if Category.objects.exists():
            self.stdout.write('Database already seeded with categories. Skipping.')
            return

        self.stdout.write('Seeding categories...')
        categories_data = [
            {'name': 'Vehicles', 'icon': 'fa-car', 'description': 'Hypercars, sports coupes, roleplay emergency cruisers.'},
            {'name': 'Maps & Safehouses', 'icon': 'fa-map', 'description': 'Custom island addons, safehouse structures, roleplay settings.'},
            {'name': 'Scripts & HUDs', 'icon': 'fa-code', 'description': 'Realism overlays, custom job scripts, interactive systems.'},
            {'name': 'Graphics & Presets', 'icon': 'fa-image', 'description': 'Raytracing reshades, dynamic weather, custom neon skies.'},
            {'name': 'Character Skins', 'icon': 'fa-shirt', 'description': 'Cyber clothing bundles, character overlays, custom textures.'},
            {'name': 'Weapons Pack', 'icon': 'fa-gun', 'description': 'High-definition rifle skins, customized sound profiles.'},
        ]
        
        categories = {}
        for cat in categories_data:
            c = Category.objects.create(
                name=cat['name'],
                icon=cat['icon'],
                description=cat['description']
            )
            categories[cat['name']] = c

        # 3. Create Products
        self.stdout.write('Seeding mods products...')
        products_data = [
            {
                'name': 'GTA 5 Mods Color Full Pencil man Addon ped',
                'category': categories['Character Skins'],
                'short_description': 'High fidelity color full pencil man addon ped character model for GTA V custom maps.',
                'description': 'A fully rigged, high-definition character model featuring realistic texture sets, optimized physics assets, and seamless implementation for singleplayer or FiveM roleplay servers.',
                'requirements': 'ScriptHookV (v1.0+)\nOpenIV (v4.0+)',
                'installation_guide': '1. Extract download ZIP files.\n2. Open OpenIV program and turn on Edit Mode.\n3. Navigate to update/x64/dlcpacks/ and drag files.\n4. Save and boot GTA 5.',
                'price': 799.00,
                'downloads_count': 320,
                'is_featured': True,
                'is_trending': True
            },
            {
                'name': 'Cyberpunk Quadra V-Tech',
                'category': categories['Vehicles'],
                'short_description': 'High fidelity cyberpunk cruiser featuring neon flame exhausts and digital dashboard HUD overlays.',
                'description': 'The legendary vehicle imported directly into GTA V. Comes with complete custom sound banks, responsive handling configs, underglow integrations, and visual livery selections.',
                'requirements': 'ScriptHookV (v1.0+)\nOpenIV (v4.0+)\nCustom Car Spawner Menu',
                'installation_guide': '1. Extract download ZIP files.\n2. Open OpenIV program and turn on Edit Mode.\n3. Navigate to update/x64/dlcpacks/ and drag "quadra" folder.\n4. Open update.rpf/common/data/dlclist.xml and add line: <Item>dlcpacks:\\quadra\\</Item>.\n5. Save and boot GTA 5.',
                'price': 999.00,
                'old_price': 1499.00,
                'downloads_count': 120,
                'is_featured': True,
                'is_trending': True
            },
            {
                'name': 'Realistic Weather & Volumetric Sky',
                'category': categories['Graphics & Presets'],
                'short_description': 'Unlocks photorealistic skybox profiles, raytracing atmospheric shaders, and road surface reflections.',
                'description': 'Overhauls Los Santos weather patterns. Enjoy custom dynamic dust storms, realistic volumetric fog, raytracing-grade puddle reflections, and neon night lighting alignments.',
                'requirements': 'Reshade (v5.0+)\nDirectX 11 Graphics Settings',
                'installation_guide': '1. Download and run Reshade installer.\n2. Copy the "reshade-shaders" folder into your main GTA 5 folder.\n3. Drag custom "PawanModPreset.ini" into game folder.\n4. Boot game and toggle dashboard using HOME button.',
                'price': 0.00,
                'downloads_count': 3450,
                'is_featured': False,
                'is_trending': True
            },
            {
                'name': 'Neo-Tokyo High-Rise Safehouse',
                'category': categories['Maps & Safehouses'],
                'short_description': 'Cyberpunk high-altitude penthouse safehouse atop Maze Bank Tower. Custom neon assets included.',
                'description': 'A fully interactive safehouse mapped top tower. Features functional custom arcade cabinets, private car lift elevators, customized wardrobes, neon layouts, and sound systems.',
                'requirements': 'Map Builder Community Mod\nMenyoo Trainer (latest)',
                'installation_guide': '1. Place the "neotokyo.xml" file inside GTA5/menyooStuff/Spooner/\n2. In-game, open Menyoo Menu (F8) -> Object Spooner -> Manage Files -> Load "neotokyo.xml"',
                'price': 1499.00,
                'old_price': 1999.00,
                'downloads_count': 890,
                'is_featured': True,
                'is_trending': False
            },
            {
                'name': 'Realism Jobs & Inventory HUD',
                'category': categories['Scripts & HUDs'],
                'short_description': 'Interactive drag-and-drop inventory system with pre-configured city jobs backend.',
                'description': 'Overhauls roleplay server mechanics. Brings dynamic health bars, item weight calculations, trade modules, and multi-tier jobs board (Mechanics, EMS, Delivery, Bounty hunting).',
                'requirements': 'ScriptHookVDotNet (v3.0+)\nNativeUI Framework',
                'installation_guide': '1. Copy "PawanHUD.dll" and config files.\n2. Paste them into GTA5/scripts/ directory.\n3. Modify PawanHUD.ini config settings for keys.',
                'price': 2499.00,
                'old_price': 3499.00,
                'downloads_count': 640,
                'is_featured': True,
                'is_trending': True
            }
        ]

        for p in products_data:
            Product.objects.create(
                name=p['name'],
                category=p['category'],
                short_description=p['short_description'],
                description=p['description'],
                requirements=p['requirements'],
                installation_guide=p['installation_guide'],
                price=p['price'],
                old_price=p.get('old_price'),
                downloads_count=p['downloads_count'],
                is_featured=p['is_featured'],
                is_trending=p['is_trending'],
                main_image='products/mock.jpg' # fallback placeholder reference
            )

        # 4. Create Blog Articles
        self.stdout.write('Seeding blog articles...')
        BlogPost.objects.create(
            title='Best GTA Mods in 2026: Realism, Shaders and Custom Cars',
            content='Grand Theft Auto V continues to thrive thanks to the incredible modding community. In 2026, graphical fidelity has reached new heights with raytracing reshades and high-fidelity vehicle model packs. In this article, we look at the essential mods you need to configure to build a truly next-generation gameplay experience, ranging from realistic physics overhauls to dynamic weather controllers. Our top recommendation includes custom scripting utilities that keep FPS stable even with complex texture assets active.',
            excerpt='Explore the top Grand Theft Auto 5 visual presets, hypercars models, and scripting additions to try out in 2026.',
            category='news',
            featured_image='blog/mock_blog.jpg'
        )
        
        BlogPost.objects.create(
            title='How to Install ScriptHookV and Custom Maps Without Crashes',
            content='Installing mods can sometimes be a frustrating process, leading to game crashes on loading screens. The key to stable modding is keeping ScriptHookV up-to-date and using OpenIV mods folder setups correctly. Always ensure you do not edit base directories directly. In this walkthrough, we explain how to build a clean mods folder, configure ASI loader plugins, and troubleshoot typical spooner script crashes when loading high-density mapped interior items.',
            excerpt='A detailed walkthrough explaining clean installation procedures for GTA V scripts and spooner map files.',
            category='guides',
            featured_image='blog/mock_blog2.jpg'
        )

        # 5. Create Coupons
        self.stdout.write('Seeding discount coupons...')
        Coupon.objects.create(
            code='GTA50',
            discount_type='percentage',
            discount_value=50.00,
            active=True,
            expiration_date=timezone.now().date() + datetime.timedelta(days=90)
        )
        
        Coupon.objects.create(
            code='WELCOME100',
            discount_type='fixed',
            discount_value=100.00,
            active=True,
            expiration_date=timezone.now().date() + datetime.timedelta(days=90)
        )

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
