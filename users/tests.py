"""
Defining tests for users app logic using django's TestCase class
"""

from django.test import TestCase  # django's test class
from django.urls import reverse
from django.contrib.auth.models import User


class UserRegistrationTests(TestCase):
    """
    Tests for all registration logic in users app
    """

    def test_registration_page_loads(self):
        """
        tests if GET request to registration page returns 200(loads successfully)
        and uses correct template.
        """
        url = reverse("users:register")  # url for registration page
        response = self.client.get(url)  # using the client object to test url response
        self.assertEqual(response.status_code, 200)  # checks status code on success code(200)
        self.assertTemplateUsed(response, "users/register.html")  # checks if correct template is used

    def test_valid_registration_creates_user(self):
        """
        tests if valid data returned by the POST method on registration page
        creates a new user instance and redirects to login page
        """
        url = reverse("users:register")  # url for register page
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'strongPass123',
            'confirm_password': 'strongPass123',
        }  # data to post to url to test logic
        response = self.client.post(url, data)  # using the client object to test url response on post
        self.assertEqual(response.status_code, 302)  # checks status code on redirect code(302)

        user_exists = User.objects.filter(username='testuser').exists()  # check if user was created
        self.assertTrue(user_exists)  # asserts if user exists

    def test_registration_with_mismatched_passwords_fails(self):
        """
        tests if registration fails when password field
        and confirm password field don't match
        """
        url = reverse("users:register")  # url for registration page
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'StrongPass123',
            'confirm_password': 'WrongPass2',
        }  # test data with wrong password to post to url
        response = self.client.post(url, data)  # using the client object to test url on post data

        """ checks if page re-render with error messages"""
        self.assertEqual(response.status_code, 200)  # using the client object to test status code on success code(200)
        self.assertContains(response, "Passwords do not match")  # checks if response contains error message
        self.assertFalse(User.objects.filter(
            username='testuser').exists())  # checks if user was not registered as passwords mismatched

    def test_registration_with_existing_username_fails(self):
        """
        tests if registration fails if username is already
        in the database
        """

        User.objects.create_user(username='used-name', password='testpass')  # creates a user
        url = reverse("users:register")  # url for registration page
        data = {
            'username': 'used-name',
            'email': 'test@example.com',
            'password': 'StrongPass123',
            'confirm_password': 'StrongPass123',
        }  # test data to post to url with already used username
        response = self.client.post(url, data)

        """checks if page re-rendered with error message"""
        self.assertEqual(response.status_code, 200)  # using the client object to test status code on success code(200)
        self.assertContains(response, 'A user with that username already exists.')  # checks if error message is on page
        self.assertEqual(User.objects.filter(username='used-name').count(), 1)  # checks if number of users with that
        # used name is still only one


class UserLoginTests(TestCase):
    """
    tests for all login logic in users app
    """

    def setUp(self):
        """
        sets up values to use in tests
        """
        self.login_url = reverse("users:login")  # login page
        self.home_url = reverse("home")  # home page
        self.password = "StrongPassword123"  # test password
        self.user = User.objects.create_user(username="testuser", email="test@example.com",
                                             password=self.password)  # test user instance

    def test_login_page_renders(self):
        """tests if login page template is rendered"""
        response = self.client.get(self.login_url)  # using the client object to test status code on success code(200)
        self.assertEqual(response.status_code, 200)  # asserts if page was loaded successfully
        self.assertContains(response, "Login")  # checks template content

    def test_login_with_valid_credentials(self):
        """
        tests login logic with valid entries
        using testuser instance created above
        """
        data = {
            'username': 'testuser',
            'password': 'StrongPassword123',
        }  # test data to post to url
        response = self.client.post(self.login_url, data)  # retrieves response on sending post info to url
        self.assertRedirects(response, self.home_url)  # asserts if user is redirected to home page

    def test_login_with_invalid_credentials(self):
        """
        tests login logic with invalid entries
        """
        data = {
            'username': 'invaliduser',
            'password': 'wrongpassword',
        }  # test data to post to url
        response = self.client.post(self.login_url, data)  # using client object to post test data to login page
        self.assertEqual(response.status_code, 200)  # testing if login page re-rendered
        self.assertContains(response, "Invalid username or password")  # checking if page contains error

    def test_authenticated_user_redirected_if_access_login(self):
        """
        tests if authenticated users are redirected to home page
        on trying to access login page.
        """
        self.client.login(username='testuser', password=self.password)  # using client object to authenticate test user
        response = self.client.get(self.login_url)  # retrieves url response of login page after authentication
        self.assertRedirects(response, self.home_url)  # asserts if user redirected to home page


class UsersLogoutTests(TestCase):
    """
    tests logout logic of the users app
    """
   
    def setUp(self):
            """
            sets up values to use in tests
            """
            self.password = "StrongPassword123" # test password 
            self.user = User.objects.create_user(username='testuser', password=self.password, email='test@example.com') # test user instance
            self.login_Url = reverse('users:login')
            self.home_url = reverse('home') # home url
            self.logout_url = reverse('users:logout') # logout url
            self.restricted_url = reverse('users:profile') # profile page url(accessible only if authenticated)

    def test_logout_redirects_to_home_page(self):
        """
        tests if user is redirected to home page on logout 
        """
        self.client.login(username='testuser', password='StrongPassword123') # authenticates test user
        response = self.client.get(self.logout_url) # using client object to test logout view
        self.assertRedirects(response, self.home_url) # asserts if user redirected to home page
    
    def test_logout_clears_session(self):
        """
        tests if logout view clears session for logged out user
        """
        self.client.login(username='testuser', password='StrongPassword123') # authenticates test user
        self.client.get(self.logout_url) # calls the logout view
        response = self.client.get(self.restricted_url) # using the client object to test access to restricted url
        self.assertRedirects(response, f"{self.login_Url}?next={self.restricted_url}") # asserts if user is redirected to login page


class UsersProfileUpdateTests(TestCase):
    """
    tests for profile update logic in the users app.
    """
    def setUp(self):
        """sets test values """
        self.password = "StrongPassword123"
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password=self.password)
        self.login_url = reverse('users:login')
        self.profile_page_url = reverse('users:profile')
        self.invalid_data = {
            'username': '',
            'email': 'wrongemailformat',
            'phone': '09049314548'
        }
        self.valid_data = {
            'username': 'freemantest',
            'email': 'test@example.com',
            'phone': '09049314547'
        }

    def test_user_redirected_to_login_page_if_unauthenticated(self):
        """
        tests if user is redirected to login page if not authenticated 
        as the profile page is restricted.
        """
        response = self.client.get(self.profile_page_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.profile_page_url}")

    def test_profile_page_rendered(self):
        """
        tests if authenticated users can access the restricted profile page
        """
        self.client.login(username=self.user.username, password=self.password) # authenticates test user
        response = self.client.get(self.profile_page_url) # using client object to retrieve profile page
        self.assertEqual(response.status_code, 200)  # asserts if profile page loaded successfully 
        self.assertTemplateUsed(response, 'users/profile.html') # asserts if profile page template was rendered
    
    def test_profile_update_with_valid_data(self):
        """
        tests if profile is updated successfully with valid data 
        """
        self.client.login(username=self.user.username, password=self.password) # authenticates test user
        response = self.client.post(self.profile_page_url, self.valid_data) # using client object to retrieve response on posting profile page with valid data
        self.user.refresh_from_db() # refresh with updated data
        self.assertEqual(self.user.username, 'freemantest') # asserts if username was updated
        self.assertEqual(self.user.email, 'test@example.com') # asserts if email was updated
        self.assertEqual(self.user.profile.phone, '09049314547') # asserts if phone field was updated

    def test_profile_update_with_invalid_data(self):
        """
        tests if profile page is re-rendered with error messages
        on submitting invalid data on profile update form
        """
        self.client.login(username=self.user.username, password=self.password) # authenticates test user
        response = self.client.post(self.profile_page_url, self.invalid_data) # using client object to retrieve response on passing invalid data to profile page form
        self.user.refresh_from_db() # refreshes db entries for user if updated
        self.assertEqual(response.status_code, 200) # tests if page was re-rendered 
        self.assertContains(response, 'This field is required.') # asserts for form error as invalid data was filled in form
        self.assertNotEqual(self.user.username, '') # asserts if the username field was not set to blank as in the invalid data passed
        self.assertNotEqual(self.user.email, 'wrongemailformat') # asserts if the email field was not updated as in the invalid data passed
        self.assertNotEqual(self.user.profile.phone, '09049314548') # asserts if the phone field was not updated as in the invalid data passed