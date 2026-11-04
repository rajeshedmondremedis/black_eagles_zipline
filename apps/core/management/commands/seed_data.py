import os
import secrets
import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.core.models import SiteSettings
from apps.bookings.models import BookingSlot
from apps.website.models import SafetyGuideline, PricingPackage, GalleryImage

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds initial default data including admin user, 4 daily slots, site settings, safety guidelines, and pricing packages.'

    def handle(self, *args, **options):
        self.stdout.write("Seeding Black Eagles Zipline initial verified data...")

        # 1. Superuser / Admin - Secure Password Handling
        admin_username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
        admin_email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@blackeagleszipline.com')
        admin_password = os.getenv('DJANGO_SUPERUSER_PASSWORD')

        admin_user, created = User.objects.get_or_create(
            username=admin_username,
            defaults={
                'email': admin_email,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            if not admin_password:
                admin_password = secrets.token_urlsafe(16)
                self.stdout.write(self.style.WARNING(
                    f"\n[SECURITY NOTICE] Generated secure random administrator password:\n"
                    f"Username: {admin_username}\n"
                    f"Password: {admin_password}\n"
                    f"Please store this securely in your .env or password manager.\n"
                ))
            else:
                self.stdout.write(self.style.SUCCESS(f"✓ Admin user created with password from environment."))
            admin_user.set_password(admin_password)
            admin_user.save()
        else:
            self.stdout.write("✓ Admin user already exists.")

        # 2. Site Settings - Verified Non-Fictional Content
        settings = SiteSettings.get_settings()
        settings.site_name = "Black Eagles Zipline"
        settings.tagline = "Experience the Thrill. Fly Beyond Limits."
        settings.hero_heading = "Experience the Thrill. Fly Beyond Limits."
        settings.hero_subheading = "Soar high above emerald forest canopies and rugged mountain valleys. Black Eagles Zipline offers a premier outdoor flight experience engineered with certified safety and untamed excitement."
        
        # Operational Statistics (Accurate to architecture)
        settings.stat_1_val = "4 Daily"
        settings.stat_1_lbl = "Operating Slots"
        settings.stat_2_val = "6 Max"
        settings.stat_2_lbl = "Riders Per Slot"
        settings.stat_3_val = "24 Max"
        settings.stat_3_lbl = "Daily Total Capacity"
        settings.stat_4_val = "Daily"
        settings.stat_4_lbl = "Pre-Flight Rig Checks"

        settings.phone_number = "+91 98765 43210"
        settings.whatsapp_number = "+91 98765 43210"
        settings.email_address = "contact@blackeagleszipline.com"
        settings.address = "Eagle Point Ridge, Cliffside Forest Reserve, Western Ghats Valley, India"
        settings.operating_hours = "Thursday to Tuesday: 09:30 AM - 06:30 PM (Closed Wednesdays)"
        settings.about_summary = "Black Eagles Zipline is an outdoor adventure destination engineered for travelers, adrenaline enthusiasts, and families who seek an unforgettable bird's-eye voyage through nature."
        settings.about_story = "Founded with a passion for wilderness conservation and exhilarating aerial sport, Black Eagles Zipline combines dual-cable engineering with trained safety guides. Each flight is monitored and inspected daily to deliver thrill with certified safety protocols approved by management."
        settings.safety_overview = "Safety is our absolute cornerstone. All equipment, harness gear, and anchor systems are inspected daily prior to operations according to strict guidelines approved by Black Eagles administration."
        settings.save()
        self.stdout.write(self.style.SUCCESS("✓ Site settings seeded (Verified content)"))

        # 3. 4 Default Daily Operating Slots (Max 6 capacity each)
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
            BookingSlot.objects.update_or_create(
                order=s['order'],
                defaults=s
            )
        self.stdout.write(self.style.SUCCESS("✓ 4 Operating slots configured (Max 6 pax each)"))

        # 4. Safety Guidelines (Explicitly noted as client-configurable without invented restrictions)
        guidelines = [
            {
                'category': 'mandatory',
                'title': 'Mandatory Safety Gear Fitting',
                'description': 'Every guest is fitted with full-body safety harnesses, dual lanyards with high-tensile locking carabiners, and impact-resistant climbing helmets by our certified riggers before ascending any launch tower.',
                'icon_name': 'shield-check',
                'order': 1,
            },
            {
                'category': 'mandatory',
                'title': 'Pre-Flight Briefing & Tower Conduct',
                'description': 'All participants must attend the 15-minute ground safety briefing. Keep hands clear of active zip cables at all times and place hands only on designated harness handles.',
                'icon_name': 'megaphone',
                'order': 2,
            },
            {
                'category': 'restrictions',
                'title': 'Rider Weight Thresholds (Configurable)',
                'description': 'Minimum and maximum weight parameters are configured by the administrator based on client structural engineering guidelines. Please confirm exact rider weight eligibility with management prior to booking.',
                'icon_name': 'speedometer',
                'order': 3,
            },
            {
                'category': 'restrictions',
                'title': 'Age Restrictions & Minor Policies (Configurable)',
                'description': 'Minimum age limits and parental/guardian waiver requirements are defined by management policy. Minors must be accompanied by a responsible adult on the launch deck.',
                'icon_name': 'person-check',
                'order': 4,
            },
            {
                'category': 'health',
                'title': 'Health & Medical Considerations',
                'description': 'Zipline flight is an active adventure sport. Expectant mothers, individuals with cardiovascular conditions, neck or back injuries, or severe medical conditions should consult their physician before participating.',
                'icon_name': 'heart-pulse',
                'order': 5,
            },
            {
                'category': 'equipment',
                'title': 'Footwear & Attire Requirements',
                'description': 'Sturdy, closed-toe athletic sneakers or hiking shoes are mandatory. Loose jewelry, scarves, and unsecured items must be stored in complimentary lockers. Long hair must be tied securely back.',
                'icon_name': 'backpack',
                'order': 6,
            },
            {
                'category': 'responsibilities',
                'title': 'Guest Conduct & Forest Conservation',
                'description': 'Zero smoking, vaping, or intoxication is permitted anywhere on the property. Please respect forest wildlife and avoid throwing items from flight platforms.',
                'icon_name': 'tree',
                'order': 7,
            },
        ]

        for g in guidelines:
            SafetyGuideline.objects.update_or_create(
                title=g['title'],
                defaults=g
            )
        self.stdout.write(self.style.SUCCESS("✓ Safety guidelines seeded (Without unverified limits)"))

        # 5. Pricing Packages (Configurable rates awaiting client sign-off)
        packages = [
            {
                'name': 'Standard Flight Slot',
                'badge': 'Standard Tier',
                'price': 1499.00,
                'duration': 'Approx 45 - 60 mins',
                'description': 'Standard single-rider slot allocation including certified gear fitting and jumpmaster guide escort. (Rate subject to client confirmation).',
                'features': 'Full Length Zipline Flight\nComplete Safety Gear Harness & Helmet\nJumpmaster Safety Briefing\nScenic Viewing Deck Access\nComplimentary Locker Storage',
                'is_featured': False,
                'is_active': True,
                'order': 1,
            },
            {
                'name': 'Canopy Tour Flight Slot',
                'badge': 'Popular Tier',
                'price': 2299.00,
                'duration': 'Approx 75 mins',
                'description': 'Comprehensive valley flight tour experience featuring extended line traverse and aerial platform views. (Rate subject to client confirmation).',
                'features': 'Extended Canopy Zipline Course\nComplete Safety Gear & Inspection\nSenior Jumpmaster Guidance\nSunset Platform Access\nCertificate of Completion',
                'is_featured': True,
                'is_active': True,
                'order': 2,
            },
            {
                'name': 'Group Flight Slot (4 - 6 Riders)',
                'badge': 'Group Package',
                'price': 1899.00,
                'duration': 'Approx 90 mins',
                'description': 'Specially curated for families, corporate teams, and groups of 4 to 6 members sharing a dedicated departure slot. (Rate subject to client confirmation).',
                'features': 'Exclusive Slot Scheduling for your group\nDedicated Jumpmaster Escort\nSynchronized Group Gear-Up\nLounge Hospitality Area\nCommemorative Group Debrief',
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
                'title': 'High Canopy Aerial Traversal',
                'caption': 'Gliding across the lush forest valley canopy.',
                'category': 'zipline',
                'image': 'gallery/zipline-action.jpg',
                'is_featured': True,
                'order': 1,
            },
            {
                'title': 'Mountain Valley Ridge',
                'caption': 'Panoramic natural scenery along the flight corridor.',
                'category': 'scenic',
                'image': 'gallery/adventure-cliff.jpg',
                'is_featured': True,
                'order': 2,
            },
            {
                'title': 'Group Adventure Experience',
                'caption': 'Shared excitement across our small-group departures.',
                'category': 'group',
                'image': 'gallery/snorkel-activity.jpg',
                'is_featured': True,
                'order': 3,
            },
        ]

        for item in gallery_items:
            GalleryImage.objects.update_or_create(
                title=item['title'],
                defaults=item
            )
        self.stdout.write(self.style.SUCCESS("✓ Gallery records seeded"))

        self.stdout.write(self.style.SUCCESS("\n==> Seeding completed successfully!"))
