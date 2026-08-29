from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
from blog.models import BlogPost

class BlogModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('admin_user', 'admin@test.com', 'pass123')
        
    def test_reading_time_calculation(self):
        """Verify reading time dynamic calculation based on word count."""
        post = BlogPost.objects.create(
            title="Word Count Test",
            content="word " * 150,  # 150 words -> 1 min
            excerpt="Excerpt",
            featured_image="test.jpg",
            author=self.user
        )
        self.assertEqual(post.reading_time, 1)

        post.content = "word " * 500  # 500 words -> 3 mins (round(500/200))
        post.save()
        self.assertEqual(post.reading_time, 3)

    def test_view_counter_increments(self):
        """Verify post detail page load increments views count in database."""
        post = BlogPost.objects.create(
            title="Views Test",
            content="Content",
            excerpt="Excerpt",
            featured_image="test.jpg",
            status="published",
            author=self.user
        )
        self.assertEqual(post.views_count, 0)
        
        detail_url = reverse('blog:post_detail', args=[post.slug])
        # Load first time
        self.client.get(detail_url)
        post.refresh_from_db()
        self.assertEqual(post.views_count, 1)
        
        # Load second time
        self.client.get(detail_url)
        post.refresh_from_db()
        self.assertEqual(post.views_count, 2)

    def test_draft_protection_guest_vs_staff(self):
        """Verify draft posts return 404 for guests but render for logged-in staff."""
        post = BlogPost.objects.create(
            title="Draft Post",
            content="Content",
            excerpt="Excerpt",
            featured_image="test.jpg",
            status="draft",
            author=self.user
        )
        detail_url = reverse('blog:post_detail', args=[post.slug])
        
        # Guest request -> should 404
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 404)
        
        # Logged in staff -> should succeed (200)
        self.client.force_login(self.user)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)

    def test_scheduled_publishing_visibility(self):
        """Verify future scheduled posts return 404 for guests but load for staff."""
        future_date = timezone.now() + datetime.timedelta(days=2)
        post = BlogPost.objects.create(
            title="Scheduled Post",
            content="Content",
            excerpt="Excerpt",
            featured_image="test.jpg",
            status="published",
            publish_date=future_date,
            author=self.user
        )
        detail_url = reverse('blog:post_detail', args=[post.slug])
        
        # Guest request -> should 404
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 404)
        
        # Logged in staff -> should succeed (200)
        self.client.force_login(self.user)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)

    def test_seo_metadata_rendering(self):
        """Verify detail page renders custom SEO titles, meta descriptions, and Twitter Cards."""
        post = BlogPost.objects.create(
            title="SEO Post",
            content="Content",
            excerpt="Teaser excerpt detail",
            featured_image="test.jpg",
            status="published",
            seo_title="My Custom SEO Title Override",
            meta_description="Custom SEO meta description details",
            meta_keywords="gta, test, seo",
            canonical_url="https://pawanmod.com/canonical-test/",
            og_title="OG Title Override",
            og_description="OG Description Details Override",
            author=self.user
        )
        detail_url = reverse('blog:post_detail', args=[post.slug])
        
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Custom SEO Title Override")
        self.assertContains(response, "Custom SEO meta description details")
        self.assertContains(response, "gta, test, seo")
        self.assertContains(response, 'href="https://pawanmod.com/canonical-test/"')
        self.assertContains(response, 'content="OG Title Override"')
        self.assertContains(response, 'content="OG Description Details Override"')

    def test_homepage_latest_articles_visibility(self):
        """Verify only published and past/current scheduled articles list on homepage."""
        # 1. Published post (past)
        post_pub = BlogPost.objects.create(
            title="Published Post",
            content="Content",
            excerpt="Excerpt",
            featured_image="test.jpg",
            status="published",
            publish_date=timezone.now() - datetime.timedelta(hours=1),
            author=self.user
        )
        # 2. Draft post
        post_draft = BlogPost.objects.create(
            title="Draft Post",
            content="Content",
            excerpt="Excerpt",
            featured_image="test.jpg",
            status="draft",
            author=self.user
        )
        # 3. Scheduled post (future)
        post_sched = BlogPost.objects.create(
            title="Scheduled Post Future",
            content="Content",
            excerpt="Excerpt",
            featured_image="test.jpg",
            status="published",
            publish_date=timezone.now() + datetime.timedelta(days=1),
            author=self.user
        )
        
        response = self.client.get(reverse('marketplace:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published Post")
        self.assertNotContains(response, "Draft Post")
        self.assertNotContains(response, "Scheduled Post Future")
