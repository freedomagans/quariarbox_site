from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Shipment
class ShipmentCreationTests(TestCase):
    """
    tests shipment creation logic
    """
    def setUp(self):
        self.password = "StrongPassword123"
        self.user = User.objects.create_user(username="testuser", password=self.password)
        self.login_url = reverse("users:login")
        self.create_shipment_url = reverse("shipments:create")

    def test_authenticated_user_(self):
        """
        tests if authenticated users can create shipments
        """
        self.client.login(username='testuser', password=self.password) # authenticates test user
        response = self.client.get(self.create_shipment_url) # using client object to retrieve response for shipment creation page
        self.assertEqual(response.status_code, 200)  # tests if page loaded successfully
        self.assertTemplateUsed(response, 'shipments/create.html') # tests if correct template was rendered
        response = self.client.post(self.create_shipment_url, {
            "origin_address": "location1",
            "destination_address": "location2",
            "weight": 300
        }) # using client object to post valid data to creation page
        self.assertEqual(Shipment.objects.count(), 1) # asserts if a shipment instance was created
        shipment = Shipment.objects.first() # retrieves the newly created shipment 
        self.assertEqual(self.user, shipment.user) # tests if user is really testuser instance
        self.assertRedirects(response, reverse("shipments:list")) # tests if user is redirected to list page
    
    def test_unathenticated_user(self):
        """
        tests if anonymous user is redirected to login page 
        """
        response = self.client.get(self.create_shipment_url) # using client object to retrieve response 
        self.assertRedirects(response,f"{self.login_url}?next={self.create_shipment_url}") # tests if redirected to login page

    def test_invalid_data_for_creationform(self):
        """
        tests for error message on page if invalid 
        data was filled or entries left blank
        """
        self.client.login(username='testuser', password=self.password) # authenticates test user
        response = self.client.post(self.create_shipment_url, {"origin_address":"",
         "destination_address":"",
         "weight":""
        }) # using client object to retrieve response 
        self.assertContains(response, 'This field is required.')

class ShipmentListTests(TestCase):
    """
    tests shipment list page logics
    """
    def setUp(self):
        """setting test values"""
        self.password = "StrongPassword123"
        self.user1 = User.objects.create_user(username="testuser", password=self.password) # test user 1
        self.user2 = User.objects.create_user(username='testuser22',password=self.password) # test user 2 
        self.user1_shipment = Shipment.objects.create(user=self.user1, origin_address="lagos", destination_address="benin", weight=100) # test shipment for user1
        self.user2_shipment = Shipment.objects.create(user=self.user2, origin_address="lagos", destination_address="benin", weight=100) # test shipment for user2
        self.login_url = reverse("users:login")
        self.shipment_list_url = reverse("shipments:list")
        self.shipment_create_url = reverse("shipments:create")

    def test_authenticated_user_shipmentlist(self):
        """
        tests if authenticated users accesses list of only 
        their shipments and not other users.
        """
        self.client.login(username=self.user1.username, password=self.password) # authenticates user1
        response = self.client.get(self.shipment_list_url) # using client object to retrieve shipment list page 
        user_shipments = response.context['shipments'] # retriving referenced context data
        self.assertEqual(response.status_code, 200) # tests if page was rendered successfully
        self.assertTemplateUsed(response, 'shipments/list.html') # tests if correct template rendered
        self.assertEqual(len(user_shipments), 1) # asserts if shipments in list is one(as its only one for user1)
        self.assertEqual(user_shipments[0].user, self.user1) # asserts if user1 loogged in and accessed only user1's shipments
    
    def test_unauthenticated_user_redirected(self):
        """
        tests if anonymous user is redirected 
        on trying to view shipment list page
        """
        response = self.client.get(self.shipment_list_url) # using client object to retrieve response
        self.assertRedirects(response, f"{self.login_url}?next={self.shipment_list_url}")  # asserts if user is redirected to login page

class ShipmentDetailTests(TestCase):
    """
    tests shipment detail page logic for user
    """

    def setUp(self):
        """setting test values for detail page"""
        self.user1 = User.objects.create_user(username='user1', password='testpass123') # test user 1
        self.user2 = User.objects.create_user(username='user2', password='testpass321') # test user 2
        self.shipment = Shipment.objects.create(user=self.user1, origin_address='origin', destination_address='destination', status='PENDING', weight=100) # testuser1's shipment 

    def test_user_can_view_shipment(self):
        """
        tests if authenticated user that owns 
        the shipment can view their shipment detail page
        """
        self.client.login(username='user1', password='testpass123') # authenticates user
        url = reverse('shipments:detail', args=[self.shipment.pk]) # url for shipment detail page
        response = self.client.get(url) # using the client object to retrieve response from the shipment detail page
        self.assertEqual(response.status_code, 200) # asserts if page was loaded successfully
        self.assertContains(response, self.shipment.origin_address) # asserts if  page contains the origin address detail for the shipment 
    
    def test_other_user_cannot_view_shipment(self):
        """
        tests if another authenticated user is restricted from viewing 
        detail of shipment he/she doesn't own.
        """
        self.client.login(username='user2', password='testpass321') # authenticates user
        url = reverse("shipments:detail", args=[self.shipment.pk]) # shipment detail page
        response = self.client.get(url) # using client object to get response from shipment detail page
        self.assertEqual(response.status_code, 404) # asserts if page was not found as it should be

    def test_redirect_if_not_logged_in(self):
        """
        tests if non-logged in user is redirected to login page 
        when user tries to access the shipment detail page
        """
        url = reverse("shipments:detail", args=[self.shipment.pk]) # shipment detail page
        response = self.client.get(url) # using client object to get the response from the shipment detail page
        self.assertRedirects(response, reverse("users:login") + f"?next=/shipments/{self.shipment.pk}") # asserts if user was redirected to the login page 


class ShipmentUpdateTests(TestCase):
    """
    tests shipment update logic 
    """

    def setUp(self):
        """
        setting test values
        """
        self.user1 = User.objects.create_user(username='testuser1', password='testpass123') # user 1
        self.user2 = User.objects.create_user(username='testuser2', password='testpass321') # user 2
        self.shipment = Shipment.objects.create(user=self.user1, origin_address='origin', destination_address='destination', weight=100) # test shipment for user 1
        self.login_url = reverse("users:login") # login url 
        self.valid_data = {
            'origin_address': 'test_origin_location',
            'destination_address': 'test_destination',
            'weight': 75,
        } # valid data to post to update page
        self.invalid_data = {
            'origin_address': '',
            'destination_address': '',
            'weight': 0,
        } # invalid data to post to update page
        

    def test_owner_can_update_shipment(self):
        """
        tests if authenticated user (owner of shipment)
        can update shipment 
        """
        self.client.login(username='testuser1', password='testpass123') # authenticates user
        response = self.client.post(reverse("shipments:update", args=[self.shipment.pk]), self.valid_data) # using client object to post valid data to shipment update page
        self.assertRedirects(response, reverse("shipments:list")) # asserts if user is redirected to shipments list page on passing valid data
        self.shipment.refresh_from_db() # reloads db to apply passed in values to update page

        """# tests if shipment details were updated."""
        self.assertEqual(self.shipment.origin_address, 'test_origin_location' ) 
        self.assertEqual(self.shipment.destination_address, 'test_destination')
        self.assertEqual(self.shipment.weight, 75)

    def test_other_users_cannot_update_shipment(self):
        """
        tests if other authenticated user (not owners) 
        cannot update shipment
        """
        self.client.login(username='testuser2', password='testpass321') # authenticates user
        response = self.client.post(reverse("shipments:update", args=[self.shipment.pk]), self.valid_data) # retrieves response from shipments update page
        self.assertEqual(response.status_code, 404) # asserts if user couldn't access the update page of the shipment as it's not theirs 
        self.assertNotEqual(self.shipment.origin_address,'test_origin_location') # tests if shipment was not updated

    def test_unauthenticated_users_are_redirected(self):
        """
        tests if unauthenticated users are redirected to login page
        """
        response = self.client.get(reverse('shipments:update', args=[self.shipment.pk])) # retrieves response from update page
        self.assertRedirects(response,f"/users/login/?next=/shipments/{self.shipment.pk}/update/") # asserts if user was redirected to login page

    def test_error_for_invalid_data_on_update(self):
        """
        tests if page is re-rendered with errors if invalid data is 
        passed to the page .
        """
        self.client.login(username='testuser1', password='testpass123') # authenticates test user
        response = self.client.post(reverse("shipments:update", args=[self.shipment.pk]), self.invalid_data) # retrieving response from update page on passing invalid data to page
        self.assertEqual(response.status_code, 200) # asserts if page was rendered
        self.assertContains(response, 'This field is required.') # asserts if error message is in rendered page


class ShipmentDeleteTests(TestCase):
    """
    tests shipment delete logic
    """
    def setUp(self):
        """setting test values"""
        self.user1 = User.objects.create_user(username='testuser1', password='testpass123') # user 1
        self.user2 = User.objects.create_user(username='testuser2', password='testpass321') # user 2
        self.shipment001 = Shipment.objects.create(user=self.user1,origin_address='001', destination_address='destination001', weight=100) # shipment 1
        self.shipment002 = Shipment.objects.create(user=self.user1,origin_address='origin002', destination_address='destination002', weight=100) # shipment 2
        self.url = reverse('shipments:delete') # delete url
        self.login_url = reverse('users:login') # login url

    def test_owner_can_delete_shipment(self):
        """
        tests if  authenticated user that owns a shipment 
        can bulk-delete his/her shipment
        """
        self.client.login(username='testuser1', password='testpass123') # authenticates user
        self.assertTrue(Shipment.objects.filter(user=self.user1).exists()) # asserts if shipments exists before deletion
        response = self.client.post(self.url, {"shipments":[self.shipment001.pk, self.shipment002.pk]}) # using client object to pass in dict of shipments list value to the delete url for bulk delete
        self.assertRedirects(response, reverse("shipments:list")) # asserts if on successful deletion user was redirected to shipment list page
        self.assertFalse(Shipment.objects.filter(user=self.user1).exists()) # asserts if deleted shipments for user still persists in the database

    def test_other_users_cannot_delete_shipment(self):
        """
        tests if other authenticated users are not allowed to delete 
        shipments that are not theirs
        """
        self.client.login(username='testuser2', password='testpass321') # authenticates user
        response = self.client.post(self.url, {'shipments':[self.shipment001.pk, self.shipment002.pk]}) # using client object to pass in dict of shipments list value to the delete url for bulk delete
        self.assertEqual(response.status_code, 404) # asserts if not found page was shown for non-owner
        self.assertTrue(Shipment.objects.filter(user=self.user1).exists()) # asserts if shipments were not deleted.

    def test_unauthenticated_users_are_redirected(self):
        """
        tests unauthenticated users are redirected to 
        the login page 
        """
        response = self.client.post(self.url, {'shipments': [self.shipment001.pk, self.shipment002.pk]})
        self.assertRedirects(response, "/users/login/?next=/shipments/delete/")