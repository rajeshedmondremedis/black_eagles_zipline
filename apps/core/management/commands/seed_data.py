import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.core.models import SiteSettings
from apps.bookings.models import BookingSlot, Holiday
from apps.website.models import SafetyGuideline, PricingPackage, GalleryImage

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds initial default data including admin user, 4 daily slots, site settings, safety guidelines, and pricing packages.'

    def handle(self, *args, **options):
        self.stdout.write("Seeding Black Eagles Zipline initial data...")

        # 1. Superuser / Admin
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@blackeagleszipline.com',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("✓ Admin user created (Username: admin, Password: admin123)"))
        else:
            self.stdout.write("✓ Admin user already exists")

        # 2. Site Settings
        settings = SiteSettings.get_settings()
        settings.site_name = "Black Eagles Zipline"
        settings.tagline = "Experience the Thrill. Fly Beyond Limits."
        settings.hero_heading = "Experience the Thrill. Fly Beyond Limits."
        settings.hero_subheading = "Soar high above emerald canopies and rugged canyons. Black Eagles Zipline brings you world-class adventure tourism engineered with certified safety and untamed excitement."
        settings.phone_number = "+91 98765 43210"
        settings.whatsapp_number = "+91 98765 43210"
        settings.email_address = "contact@blackeagleszipline.com"
        settings.address = "Black Eagles Adventure Park, Eagle Ridge Canyon, Western Ghats Valley, Kerala - 673577"
        settings.save()
        self.stdout.write(self.style.SUCCESS("✓ Site settings seeded"))

        # 3. 4 Default Daily Slots (6 pax max each)
        # Temporary configuration values as requested by prompt
        slots_data = [
            {
                'name': 'Slot 1 – Morning Flight',
                'start_time': datetime.time(9, 30),
                'end_time': datetime.time(11, 30),
                'max_capacity': 6,
                'is_active': True,
                'order': 1,
            },
            {
                'name': 'Slot 2 – Midday Rush',
                'start_time': datetime.time(11, 45),
                'end_time': datetime.time(13, 45),
                'max_capacity': 6,
                'is_active': True,
                'order': 2,
            },
            {
                'name': 'Slot 3 – Afternoon Canopy Trek',
                'start_time': datetime.time(14, 15),
                'end_time': datetime.time(16, 15),
                'max_capacity': 6,
                'is_active': True,
                'order': 3,
            },
            {
                'name': 'Slot 4 – Golden Hour Sunset Flight',
                'start_time': datetime.time(16, 30),
                'end_time': datetime.time(18, 30),
                'max_capacity': 6,
                'is_active': True,
                'order': 4,
            },
        ]

        for s in slots_data:
            obj, created = BookingSlot.objects.update_or_create(
                order=s['order'],
                defaults=s
            )
        self.stdout.write(self.style.SUCCESS("✓ 4 Default operating slots configured (Max 6 pax each)"))

        # 4. Safety Guidelines
        guidelines = [
            {
                'category': 'mandatory',
                'title': 'Mandatory Safety Gear Fitting',
                'description': 'Every guest is fitted with Petzl CE/UIAA certified full-body harness, dual lanyards with high-tensile locking carabiners, and impact-resistant climbing helmets by our certified riggers before ascending any tower.',
                'icon_name': 'shield-check',
                'order': 1,
            },
            {
                'category': 'mandatory',
                'title': 'Pre-Flight Briefing & Tower Rules',
                'description': 'All participants must attend the 15-minute ground safety briefing. Keep hands clear of active zip cables at all times and place hands only on designated harness handles.',
                'icon_name': 'megaphone',
                'order': 2,
            },
            {
                'category': 'restrictions',
                'title': 'Rider Weight Thresholds (Configurable)',
                'description': 'For optimal velocity braking and aerial physics balance: Minimum weight requirement is 35 kg (77 lbs) and Maximum weight threshold is 115 kg (253 lbs). Subject to confirmation by client administrator.',
                'icon_name': 'speedometer',
                'order': 3,
            },
            {
                'category': 'restrictions',
                'title': 'Age Restrictions (Configurable)',
                'description': 'Minimum age for riders is 8 years. Participants between ages 8 and 16 must have a parent or guardian signed waiver and must be accompanied on the launch deck.',
                'icon_name': 'person-check',
                'order': 4,
            },
            {
                'category': 'health',
                'title': 'Health & Medical Eligibility',
                'description': 'Ziplining is not permitted for expectant mothers, individuals with severe cardiovascular conditions, recent spinal or neck surgeries, or extreme vertigo without physician clearance.',
                'icon_name': 'heart-pulse',
                'order': 5,
            },
            {
                'category': 'equipment',
                'title': 'Appropriate Footwear & Attire',
                'description': 'Sturdy, closed-toe athletic sneakers or hiking boots are mandatory. Loose jewelry, scarves, and unsecured sunglasses must be stored in complimentary lockers. Long hair must be tied securely back.',
                'icon_name': 'backpack',
                'order': 6,
            },
            {
                'category': 'responsibilities',
                'title': 'Rider Conduct & Environmental Care',
                'description': 'No smoking, vaping, or intoxication is permitted anywhere on the property. Please respect forest wildlife and avoid throwing items from flight platforms.',
                'icon_name': 'tree',
                'order': 7,
            },
        ]

        for g in guidelines:
            SafetyGuideline.objects.update_or_create(
                title=g['title'],
                defaults=g
            )
        self.stdout.write(self.style.SUCCESS("✓ Safety guidelines seeded"))

        # 5. Pricing Packages
        packages = [
            {
                'name': 'Eagle Explorer (Standard Flight)',
                'badge': 'Starter Favorite',
                'price': 1499.00,
                'duration': 'Approx 45 mins',
                'description': 'Perfect for first-time adventurers seeking high-velocity aerial thrills over pristine valley gorges.',
                'features': 'Full Length Dual-Cable Zipline Flight\nProfessional CE/UIAA Safety Gear\nCertified Jumpmaster Briefing\nScenic Viewing Deck Access\nComplimentary Drinking Water & Locker',
                'is_featured': False,
                'is_active': True,
                'order': 1,
            },
            {
                'name': 'Black Eagles Pro Canopy Tour',
                'badge': 'Most Popular',
                'price': 2299.00,
                'duration': 'Approx 75 mins',
                'description': 'The ultimate comprehensive canyon flight experience featuring multiple cable traverses and canyon crossing.',
                'features': 'Dual Canyon Zipline Flight (1.2 km total)\nSkybridge Aerial Suspension Crossing\nComplimentary HD Action Photo Pass\nSenior Jumpmaster Guidance\nExclusive Sunset Platform Access\nCertificate of Completion',
                'is_featured': True,
                'is_active': True,
                'order': 2,
            },
            {
                'name': 'Sky Team Expedition (Group Package)',
                'badge': 'Best Group Value',
                'price': 1899.00,
                'duration': 'Approx 90 mins',
                'description': 'Specially curated for families, corporate teams, and friend groups of 4 to 6 members.',
                'features': 'Dedicated Slot Allocation for your group\nPrivate Guide & Accelerated Gear-Up\nHigh-Res Group Action Video Clips\nRefreshment Lounge Hospitality\nSafety Certified Team Debrief',
                'is_featured': False,
                'is_active': True,
                'order': 3,
            },
        ]

        for p in packages:
            PricingPackage.objects.update_or_create(
                name=p['name'],
                defaults=p
            )
        self.stdout.write(self.style.SUCCESS("✓ Pricing packages seeded"))

        # 6. Gallery Items
        gallery_items = [
            {
                'title': 'High Velocity Forest Flight',
                'caption': 'Gliding at 60 km/h across the emerald mountain canopy.',
                'category': 'zipline',
                'image': 'gallery/zipline-action.jpg',
                'is_featured': True,
                'order': 1,
            },
            {
                'title': 'Valley Horizon View',
                'caption': 'Unmatched panoramic vistas of the Western Ghats mountain ridges.',
                'category': 'scenic',
                'image': 'gallery/adventure-cliff.jpg',
                'is_featured': True,
                'order': 2,
            },
            {
                'title': 'Family Adventure Expedition',
                'caption': 'Shared joy and bonding across our canopy circuit.',
                'category': 'group',
                'image': 'gallery/snorkel-activity.jpg',
                'is_featured': True,
                'order': 3,
            },
            {
                'title': 'Eagle Watch Observation Deck',
                'caption': 'Launch platform towering 300 meters above the canyon floor.',
                'category': 'zipline',
                'image': 'gallery/dashboard-preview.jpg',
                'is_featured': False,
                'order': 4,
            },
        ]

        for item in gallery_items:
            GalleryImage.objects.update_or_create(
                title=item['title'],
                defaults=item
            )
        self.stdout.write(self.style.SUCCESS("✓ Gallery records seeded"))

        self.stdout.write(self.style.SUCCESS("\n==> Seeding completed successfully!"))
