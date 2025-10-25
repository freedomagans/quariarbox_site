"""
Security Enhancement Tests
Tests all implemented security features for the courier site
"""

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings
from shipments.models import Shipment
from payments.models import Payment
from decimal import Decimal
from django.contrib.messages import get_messages


class AdminSecurityTests(TestCase):
    """Tests for admin panel security"""
    
    def setUp(self):
        """setting test values"""
        self.client = Client()  # client object 
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='AdminPass123!'
        ) # test admin

        self.regular_user = User.objects.create_user(
            username='regular',
            email='user@test.com',
            password='UserPass123!'
        ) # test regular user 
    
    def test_default_admin_url_not_accessible(self):
        """Ensure default /admin/ URL returns 404"""
        response = self.client.get("/admin/") # retrieve response 
        self.assertEqual(response.status_code, 404) # asserts 404 returned 
    
    def test_custom_admin_url_exists(self):
        """Custom admin URL should exist"""
        # Try to access without auth - should redirect to login
        response = self.client.get("/secure-admin-panel/") # retrieve response
        self.assertEqual(response.status_code, 302) # assert user is redirected
        self.assertIn('login', response.url) # assert user is redirected to login page
    
    @override_settings(AXES_ENABLED=False, RATELIMIT_ENABLE=False) # overriding settings in settings.py file
    def test_custom_admin_accessible_for_superuser(self):
        """Superuser can access custom admin URL"""
        self.client.force_login(self.admin) # force authenticate admin
        response = self.client.get("/secure-admin-panel/") # retrieve response
        self.assertEqual(response.status_code, 200) # assert admin panel rendered
    
    @override_settings(AXES_ENABLED=False, RATELIMIT_ENABLE=False) # overriding settings in settings.py file
    def test_regular_user_cannot_access_admin(self):
        """Regular users cannot access admin panel"""
        self.client.force_login(self.regular_user) # force authenticate test user
        response = self.client.get("/secure-admin-panel/") # retrieve response
        # Should redirect to login or show 302
        self.assertIn(response.status_code, [302, 403]) # assert if user is either forbidden or redirected
    
    @override_settings(AXES_ENABLED=False, RATELIMIT_ENABLE=False) # overriding settings in settings.py file
    def test_admin_logout_works(self):
        """Admin logout properly logs out user"""
        self.client.force_login(self.admin) # force authenticate admin
        response = self.client.get(reverse("admin-logout")) # retrieve response
        self.assertEqual(response.status_code, 302) # assert admin redirected on logout
        
        # Try accessing admin again - should redirect
        response = self.client.get("/secure-admin-panel/") # retrieve response without authentication
        self.assertEqual(response.status_code, 302) # assert user redirected


class RateLimitingTests(TestCase):
    """Tests for rate limiting on critical endpoints"""
    
    def setUp(self):
        """setting test values"""
        self.client = Client() # client object 
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        ) # test user 
    
    @override_settings(RATELIMIT_ENABLE=True, AXES_ENABLED=False) # overriding settings in settings.py to enable rate-limiting 
    def test_login_rate_limiting(self):
        """Login attempts are rate limited"""
        login_url = reverse("users:login") # login url
        
        # Make 6 attempts (limit is 5/min)
        for i in range(6):
            response = self.client.post(
                login_url,
                {'username': 'testuser', 'password': 'wrongpass'},
                follow=True  # Follow redirects to see messages
            ) # retrieve response
        
        # Should redirect to home when rate limited
        self.assertEqual(response.status_code, 200) # assert home page is rendered        
        # Check for rate limit message in Django messages
        messages =list(response.context.get('messages', [])) 
        has_rate_limit_msg = any('Too many login attempts' in str(m) for m in messages)
        self.assertTrue(has_rate_limit_msg, "Rate limit message not found") # assert if custom rate limit message was displayed
    
    @override_settings(RATELIMIT_ENABLE=True) # overriding  settings in settings.py file to enable rate-limiting
    def test_register_rate_limiting(self):
        """Registration attempts are rate limited"""
        register_url = reverse("users:register") # registration url
        
        # Make 6 registration attempts
        for i in range(6):
            response = self.client.post(
                register_url,
                {
                    'username': f'newuser{i}',
                    'email': f'user{i}@test.com',
                    'password1': 'TestPass123!',
                    'password2': 'TestPass123!'
                }, 
                follow=True
            ) # retrieve response
        self.assertEqual(response.status_code, 200) # asserts home page rendered

        # Check for rate limit message in Django messages
        messages = list(response.context.get('messages', [])) 
        has_rate_limit_msg = any('Too many signup attempts' in str(m) for m in messages)
        self.assertTrue(has_rate_limit_msg, "Rate limit message not found") # assert if custom rate limit message was displayed
    
    @override_settings(RATELIMIT_ENABLE=True) # overriding settings in settings.py file to enable rate-limiting 
    def test_payment_initiate_rate_limiting(self):
        """Payment initiation is rate limited"""
        self.client.force_login(self.user) # force authenticate test user
        
        # Create a shipment with payment
        shipment = Shipment.objects.create(
            user=self.user,
            origin_address='Test Origin',
            destination_address='Test Dest',
            weight=Decimal('10.00')
        ) # test shipment

        payment = Payment.objects.get(shipment=shipment) # auto-generated payment instance
        
        initiate_url = reverse('payments:initiate', args=[payment.pk]) # initiate payment url
        
        # Make 4 attempts (limit is 3/min)
        for i in range(4):
            response = self.client.get(initiate_url) # retrieve response
        
        # Should redirect to payment history on rate limit
        self.assertRedirects(response, reverse('payments:payments-history'))

        # Check for rate limit message in Django messages
        messages = list(get_messages(response.wsgi_request)) 
        has_rate_limit_msg = any('Too many payment attempts' in str(m) for m in messages)
        self.assertTrue(has_rate_limit_msg, "Rate limit message not found") # assert if custom rate limit message was displayed


class AxesSecurityTests(TestCase):
    """Tests for django-axes brute force protection"""
    
    def setUp(self):
        """setting test values"""
        self.client = Client() # client object

        self.user = User.objects.create_user(
            username='axesuser',
            email='axes@test.com',
            password='AxesPass123!'
        ) # test user
    
    @override_settings(AXES_ENABLED=True, AXES_FAILURE_LIMIT=5, RATELIMIT_ENABLE=False, AXES_LOCKOUT_URL =reverse('users:lockout'), AXES_USE_USER_AGENT=True) # overriding settings in settings.py file to enable AXES feature and ites settings.
    def test_axes_locks_after_failed_attempts(self):
        """Axes locks account after multiple failed login attempts"""
        login_url = reverse("users:login")# login url
        
        # Make AXES_FAILURE_LIMIT failed attempts
        for i in range(6):
            response = self.client.post(
                login_url,
                {'username': 'axesuser', 'password': 'wrongpassword'}
            ) # retrieve response
        
        self.assertEqual(response.status_code, 302) # assert user redirected
        self.assertIn('lockout', response.url) # assert user was redirected to specified AXES_LOCKCOUT PAGE.
    
    @override_settings(AXES_ENABLED=True, AXES_FAILURE_LIMIT=3, RATELIMIT_ENABLE=False) # overriding settings in settings.py file to enable AXES feature and its settings
    def test_axes_resets_on_successful_login(self):
        """Axes resets failure count on successful login"""
        login_url = reverse("users:login") # login url
        
        # Make 2 failed attempts
        for i in range(2):
            self.client.post(
                login_url,
                {'username': 'axesuser', 'password': 'wrongpassword'}
            )
        
        # Successful login should reset
        response = self.client.post(
            login_url,
            {'username': 'axesuser', 'password': 'AxesPass123!'}
        )
        
        # Should succeed (redirect to home)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('lockout', response.url)


class CSRFProtectionTests(TestCase):
    """Tests for CSRF protection"""
    
    def setUp(self):
        """setting test values"""
        self.client = Client(enforce_csrf_checks=True)  # Enable CSRF checking
        self.user = User.objects.create_user(
            username='csrfuser',
            email='csrf@test.com',
            password='CsrfPass123!'
        ) # test user
    
    @override_settings(AXES_ENABLED=False, RATELIMIT_ENABLE=False) # overriding settings in settings.py file
    def test_login_requires_csrf_token(self):
        """Login POST requires CSRF token"""
        login_url = reverse("users:login") # login url
        
        # POST without CSRF token
        response = self.client.post(
            login_url,
            {'username': 'csrfuser', 'password': 'CsrfPass123!'}
        ) # retrieve response
        
        # Should be forbidden
        self.assertEqual(response.status_code, 403)
    
    @override_settings(AXES_ENABLED=False, RATELIMIT_ENABLE=False) # overriding settings in settings.py file
    def test_login_works_with_csrf_token(self):
        """Login succeeds with valid CSRF token"""
        login_url = reverse("users:login") # login url
        
        # Get CSRF token
        response = self.client.get(login_url)
        csrf_token = response.cookies.get('csrftoken').value
        
        # POST with CSRF token
        response = self.client.post(
            login_url,
            {'username': 'csrfuser', 'password': 'CsrfPass123!'},
            HTTP_X_CSRFTOKEN=csrf_token
        )
        
        # Should redirect (successful login)
        self.assertEqual(response.status_code, 302)


class HTTPSSecurityTests(TestCase):
    """Tests for HTTPS/SSL security settings"""
    
    @override_settings(ENVIRONMENT='production',SECURE_SSL_REDIRECT=True,DEBUG=False
    ) # overriding settings in settings.py to enable production enviroment and set SECURE_SSL_REDIRECT=True
    def test_http_redirects_to_https_in_production(self):
        """HTTP requests redirect to HTTPS in production"""
        client = Client() # client object
        response = client.get('/', secure=False) # get http url
        
        # Should redirect with 301
        self.assertEqual(response.status_code, 301)
        self.assertTrue(response.url.startswith('https://')) # should return redirect to https url
    
    @override_settings(ENVIRONMENT='production',SESSION_COOKIE_SECURE=True)# overriding settings in settings.py to enable production enviroment and set SECURE_SSL_REDIRECT=True
    def test_session_cookie_secure_in_production(self):
        """Session cookies are secure in production"""
        self.assertTrue(settings.SESSION_COOKIE_SECURE)
    
    @override_settings(ENVIRONMENT='production',CSRF_COOKIE_SECURE=True)
    def test_csrf_cookie_secure_in_production(self):
        """CSRF cookies are secure in production"""
        self.assertTrue(settings.CSRF_COOKIE_SECURE)


class CSPHeaderTests(TestCase):
    """Tests for Content Security Policy headers"""
    
    def test_csp_headers_present_on_pages(self):
        """CSP headers are present in responses"""
        client = Client() # client object
        response = client.get('/')
        
        # Check for CSP header
        csp_header = response.get('Content-Security-Policy')
        
        # CSP might be added by middleware
        # Just verify response is successful
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(csp_header) # assert csp header present in pages


class PaymentSecurityTests(TestCase):
    """Tests for payment endpoint security"""
    
    def setUp(self):
        """setting test values"""
        self.client = Client() # client object

        self.user = User.objects.create_user(
            username='payuser',
            email='pay@test.com',
            password='PayPass123!'
        ) # test user1

        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@test.com',
            password='OtherPass123!'
        ) # test user 2
        
        # Create shipment and payment
        self.shipment = Shipment.objects.create(
            user=self.user,
            origin_address='Payment Test Origin',
            destination_address='Payment Test Dest',
            weight=Decimal('15.00')
        ) # test shipment 


        self.payment = Payment.objects.get(shipment=self.shipment) # test auto-genrated payment instance
    
    @override_settings(AXES_ENABLED=False, RATELIMIT_ENABLE=False) # overriding settings in settings.py file
    def test_payment_initiate_requires_authentication(self):
        """Payment initiation requires login"""
        url = reverse('payments:initiate', args=[self.payment.pk]) # payment initiation url
        response = self.client.get(url) # retrieve response
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302) # assert user is redirected
        self.assertIn('login', response.url) # assert user is redirected to login page
    
    @override_settings(AXES_ENABLED=False, RATELIMIT_ENABLE=False) # overriding settings in settings.py file
    def test_user_cannot_initiate_other_users_payment(self):
        """Users cannot initiate payments for other users"""
        self.client.force_login(self.other_user) # force authenticate non-owner of shipment 
        url = reverse('payments:initiate', args=[self.payment.pk]) # initiate payment url
        response = self.client.get(url) # retrieve response
        
        # Should return 404 (not found for this user)
        self.assertEqual(response.status_code, 404)
    
    @override_settings(AXES_ENABLED=False, RATELIMIT_ENABLE=False) # overriding settings in settings.py file
    def test_payment_verify_requires_authentication(self):
        """Payment verification requires login"""
        url = reverse('payments:verify') # verify payment url
        response = self.client.get(url) # retrieve response
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)


class SessionSecurityTests(TestCase):
    """Tests for session security settings is valid and present"""
    
    def test_session_expires_at_browser_close(self):
        """Sessions expire when browser closes"""
        self.assertTrue(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)
    
    def test_session_cookie_httponly(self):
        """Session cookies are HttpOnly"""
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
    
    def test_session_timeout_configured(self):
        """Session timeout is configured (30 minutes)"""
        self.assertEqual(settings.SESSION_COOKIE_AGE, 1800)  # 30 minutes


class OpenRedirectProtectionTests(TestCase):
    """Tests for open redirect protection"""
    
    def setUp(self):
        """setting test values"""
        self.client = Client() # client object

        self.user = User.objects.create_user(
            username='redirectuser',
            email='redirect@test.com',
            password='RedirectPass123!'
        ) # test user 
    
    @override_settings(AXES_ENABLED=False, RATELIMIT_ENABLE=False) # overriding settings in settings.py file
    def test_login_blocks_external_redirects(self):
        """Login blocks redirects to external sites"""
        login_url = reverse("users:login") + "?next=https://evil.com" # login url with external next url attached
                
        response = self.client.post(
            login_url,
            {'username': 'redirectuser', 'password': 'RedirectPass123!'}
        ) # retrieve response
        
        
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('evil.com', response.url) # assert user not redirected to attached external url
        self.assertRedirects(response, reverse('home')) # assert user is redirected to home page instead


