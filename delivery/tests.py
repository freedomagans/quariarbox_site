from django.test import TestCase
from django.urls import reverse
from .models import DeliveryAssignment, Courier, CourierApplication
from shipments.models import Shipment
from django.contrib.auth.models import User

class DeliveryAssignmentTests(TestCase):
    """
    tests delivery assignment logic in the delivery app
    """

    def setUp(self):
        """setting test values"""

        """users"""
        self.admin = User.objects.create_superuser(username='admin', password='testpass111') # admin
        self.admin.profile.role = 'admin'
        self.admin.profile.save()

        # courier
        self.user2 = User.objects.create_user(username='courier', password='testpass222')
        self.user2.profile.role = 'courier'
        self.user2.profile.save()
        self.courier = Courier.objects.create(user=self.user2, phone='08168247299', vehicle='testvehicle') # courier object for courier


        self.customer = User.objects.create_user(username='customer', password='testpass333') # customer

        """customer's shipment"""
        self.shipment = Shipment.objects.create(user=self.customer, origin_address='lagos', destination_address='benin', weight=100)
    
    def test_admin_can_assign_delivery(self):
        """
        tests if admins can assign deliveries to couriers
        """
        self.client.login(username='admin', password='testpass111') # authenticates superuser(admin)
        url = reverse("admin:delivery_deliveryassignment_add") # the add delivery page in the admin panel
        response = self.client.post(url, {'shipment': self.shipment.pk,'courier':self.courier.pk, 'status': 'ASSIGNED'}) # retrieving response on posting data to the create new delivery assignment page on the admin panel
        self.assertEqual(response.status_code, 302) # asserts if admin is redirected successfully
        self.assertTrue(DeliveryAssignment.objects.filter(shipment=self.shipment, courier= self.courier).exists()) # asserts if shipment was assigned

    def test_other_users_cannot_assign_deliveries(self):
        """
        tests if other users cannot assign deliveries to couriers
        """
        self.client.login(username='courier', password='testpass222') # authenticates user 
        url = reverse("admin:delivery_deliveryassignment_add") # assign delivery page in admin panel
        response = self.client.post(url, {'shipment': self.shipment.pk, 'courier':self.courier.pk, 'status': 'ASSIGNED'}) # retrieves response on postin data to assign delivery page
        self.assertRedirects(response, "/admin/login/?next=/admin/delivery/deliveryassignment/add/") # asserts if non-admin is redirected to login as admin
        self.assertFalse(DeliveryAssignment.objects.filter(shipment=self.shipment).exists()) # asserts if the delivery assignment wasn't created

    def test_prevent_duplicate_assignment(self):
        """
        tests if duplicate delivery assignment is prevented.
        """
        DeliveryAssignment.objects.create(shipment=self.shipment, courier=self.courier) # assigns a shipment to a courier
        self.client.login(username='admin', password='testpass111') # authenticates user
        url = reverse("admin:delivery_deliveryassignment_add") # assign delivery page
        response = self.client.post(url, {'shipment': self.shipment.pk, 'courier':self.courier.pk, 'status': 'ASSIGNED'}) # retrieving response from assign delivery page on posting new delivery assignment data
        self.assertEqual(DeliveryAssignment.objects.count(), 1) # asserts if only one delivery shipment record was created and no duplicates.

class CourierApplicationTests(TestCase):
    """
    tests for courier application logic
    """
    def setUp(self):
        """setting test values"""
        self.user = User.objects.create_user(username='testuser', password='testpass123') # test user
        self.admin = User.objects.create_superuser(username='admin', password='testpass321', email='admin@test.com')
  

    def test_user_can_submit_courier_application(self):
        """
        tests if an authenticated user can 
        submit a courier application
        """
        self.client.login(username='testuser', password='testpass123') # authenticates user 
        url = reverse("delivery:create") # courier application page
        response = self.client.post(url, {'user':self.user, 'phone':'08168247299', 'address':'benin', 'vehicle': 'van', 'is_approved': False}) # retrieving response from courier application page 
        self.assertRedirects(response,reverse('delivery:success')) # asserts if user is redirected to success page
        self.assertEqual(CourierApplication.objects.count(), 1) # asserts if the application was persisted in the database
    
    def test_duplicate_application_not_allowed(self):
        """
        tests if users already applied are redirected to home page 
        without creating new applications for user
        """
        CourierApplication.objects.create(user=self.user, phone='08064952530', address='benin', vehicle='van') # create courierapplication instance

        self.client.login(username='testuser', password='testpass123') # authenticates user
        url = reverse('delivery:create')  # application page
        response = self.client.post(url, {'user':self.user, 'phone':'08168247299', 'address':'benin', 'vehicle': 'van', 'is_approved': False}) # retrieving response from courier application page
        self.assertRedirects(response, reverse('home')) # asserts if user is redirected to home page 
        self.assertEqual(CourierApplication.objects.count(), 1) # asserts if courier application was not duplicated.

    def test_admin_can_view_application(self):
        """
        tests if admin can view courier applications 
        in the admin panel
        """
        CourierApplication.objects.create(user=self.user, phone='08064952530', address='benin', vehicle='van') # create courierapplication instance

        self.client.login(username='admin', password='testpass321') # authenticates user
        url = reverse("admin:delivery_courierapplication_changelist") # list of applications page in adminn panel
        response = self.client.get(url) # retrieve response
        self.assertEqual(response.status_code, 200) # asserts if page loaded successfully
        self.assertContains(response, 'testuser') # asserts if the page contains the application info.

    def test_admin_can_approve_application(self):
        """
        tests if admin can approve submitted
        courier applications
        """
        application = CourierApplication.objects.create(
            user= self.user,
            phone= '08106101396',
            address= 'benin',
            vehicle= 'van',
            is_approved = False
        ) # creates courier Application instance
        
        self.client.login(username='admin', password='testpass321') # authenticates user
        url = reverse("admin:delivery_courierapplication_change", args=[application.pk]) # courier application edit page on admin panel
        response = self.client.post(url, {
            'user': self.user.pk,
            'phone': '08106101396',
            'address': 'benin',
            'vehicle': 'van',
            'is_approved': 'on',
        }, follow=True)    # retrieve response from posting data with is_approved turned on on application form.

        self.assertEqual(response.status_code, 200) # asserts if page rendered successfully
        self.assertTrue(Courier.objects.filter(user=self.user).exists()) # asserts if the courier object for the user was created as application was approved.

    def test_admin_can_unapprove_application_and_delete_courier(self):
        """
        tests if admins can unapprove application -> Courier object is deleted.
        """
        application = CourierApplication.objects.create(
            user= self.user,
            phone= '08106101396',
            address= 'benin',
            vehicle= 'van',
            is_approved = False
        ) # creates courier Application instance
        application.is_approved = True
        application.save() # approves application
        self.assertTrue(Courier.objects.filter(user=self.user).exists()) # asserts if courier object created

        self.client.login(username='admin', password='testpass321') # authenticates user
        url = reverse("admin:delivery_courierapplication_change", args=[application.pk]) # courierapplication page

        response = self.client.post(url,  {
            'user': self.user.pk,
            'phone': '08106101396',
            'address': 'benin',
            'vehicle': 'van',
        }, follow=True)    # retrieve response from posting data with is_approved not passed therefore turning it off on application form.)
        self.assertEqual(response.status_code, 200) # asserts if page rendered
        self.assertFalse(Courier.objects.filter(user=self.user).exists()) # asserts if courier object is deleted as application was unapproved

class DeliveryViewTests(TestCase):
    """
    tests Delivery views logic
    """
    def setUp(self):
        """setting tests values """

        # admin user 
        self.admin = User.objects.create_superuser(username='admin', password='testpass111')
        self.admin.profile.role = 'admin'
        self.admin.profile.save()

        # courier user1
        self.courier_user1 = User.objects.create_user(username='courier1', password='testpass222')
        self.courier1 = Courier.objects.create(user=self.courier_user1, phone='08168247299', vehicle='testvehicle') # courier object for courier
        
        # courier user2
        self.courier_user2 = User.objects.create_user(username='courier2', password='testpass222')
        self.courier2 = Courier.objects.create(user=self.courier_user2, phone='08168247299', vehicle='testvehicle') # courier object for courier

        # customer 
        self.customer = User.objects.create_user(username='customer', password='testpass333')

        # shipment for customer 
        self.shipment = Shipment.objects.create(user=self.customer, origin_address='origin', destination_address='destination', weight=100)

        # delivery assignment not yet accepted
        self.assignment = DeliveryAssignment.objects.create(shipment=self.shipment, courier=self.courier1, status='ASSIGNED')


        
    def test_courier_list_shows_only_assigned(self):
        """
        tests if Courier sees only deliveries assigned to them.
        """
        
        #courier1 login 
        self.client.login(username='courier1', password='testpass222') # authenticates courier1
        url = reverse("delivery:list") # assigned deliveries page
        response = self.client.get(url) # retrieve response
        self.assertEqual(response.status_code, 200) # asserts if page loaded successfully
        self.assertIsNotNone(response.context['assigned_deliveries'], "ListView context queryset not found; check context_object_name") # asserts if the correct context was passed to the template 
        self.assertTrue(any(obj.pk == self.assignment.pk for obj in response.context['assigned_deliveries']), msg="Assignment not found in courier's list") # asserts if the courier sees his/her assigned delivery/shipment

        #courier2 login
        self.client.login(username='courier2', password='testpass222') # authenticates courier2
        response2 = self.client.get(url) # retrieves response
        self.assertIsNotNone(response2.context['assigned_deliveries']) # asserts if correct context object was passed to template
        self.assertFalse(any(obj.pk == self.assignment.pk for obj in response2.context['assigned_deliveries']), msg="Other courier incorrectly sees someone else's assignment") # asserts if other courier correctly cannot see another's assigned delivery/shipment

    def test_courier_cannot_view_unassigned_shipment_detail(self):
        """
        tests if couriers can view details on only 
        shipments assigned to them.
        """

        detail_url = reverse("shipments:detail", args=[self.shipment.pk]) # detail page

        #courier1 accessing detail page 
        self.client.login(username='courier1', password='testpass222')
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shipments/detail.html')

        # courier2 accessing detail page
        self.client.login(username='courier2', password='testpass222')
        response2 = self.client.get(detail_url)
        self.assertEqual(response2.status_code, 404)

    def test_courier_can_accept_delivery(self):
        """
        tests if a courier can accept an assigned delivery.
        """
        self.client.login(username='courier1', password='testpass222')
        url = reverse("delivery:accept", args=[self.shipment.pk])
        response = self.client.post(url, follow=True)
        self.assignment.refresh_from_db()
        self.shipment.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.assignment.status, "ACCEPTED")
        self.assertEqual(self.shipment.status, 'IN_TRANSIT')

    def test_courier_cannot_accept_others_assignment(self):
        """
        tests if couriers cannot accept 
        someone else's assigned delivery
        """
        self.client.login(username='courier2', password='testpass222')
        url = reverse("delivery:accept", args=[self.shipment.pk])
        response = self.client.post(url, follow=True)
        self.assignment.refresh_from_db()
        self.shipment.refresh_from_db()
        self.assertNotEqual(self.assignment.status, 'ACCEPTED')
        self.assertNotEqual(self.shipment.status, 'IN_TRANSIT')
        self.assertEqual(response.status_code, 404)

    def test_courier_cannot_mark_delivered_without_accepting(self):
        """
        tests that a courier mark a delivery 
        as delivered only when he/she has accepted it first.
        """
        self.client.login(username='courier1', password='testpass222')
        url = reverse('delivery:delivered', args=[self.shipment.pk])
        response = self.client.post(url, follow=True)
        self.assignment.refresh_from_db()
        self.shipment.refresh_from_db()

        self.assertNotEqual(self.assignment.status, 'DELIVERED')
        self.assertNotEqual(self.shipment.status, 'DELIVERED')
        self.assertRedirects(response, reverse('delivery:list'))

    def test_courier_can_mark_as_delivered(self):
        """
        tests if a courier can mark an 
        accepted delivery as delivered.
        """
        self.assignment.status = 'ACCEPTED'
        self.assignment.save()

        self.client.login(username='courier1', password='testpass222')
        url = reverse('delivery:delivered', args=[self.shipment.pk])
        response = self.client.post(url, follow=True)
        self.assignment.refresh_from_db()
        self.shipment.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.assignment.status, "DELIVERED")
        self.assertEqual(self.shipment.status, 'DELIVERED')

    def test_other_courier_cannot_mark_as_delivered(self):
        """
        tests if other courier cannot another
         courier's  delivery as delivered.
        """
        self.assignment.status = 'ACCEPTED'
        self.assignment.save()

        self.client.login(username='courier2', password='testpass222')
        url = reverse('delivery:delivered', args=[self.shipment.pk])
        response = self.client.post(url, follow=True)
        self.assignment.refresh_from_db()
        self.shipment.refresh_from_db()
        self.assertEqual(response.status_code, 404)
        self.assertNotEqual(self.assignment.status, "DELIVERED")
        self.assertNotEqual(self.shipment.status, 'DELIVERED')
    

    def test_customer_cannot_access_delivered_view(self):
        """
        tests that a customer cannot directly 
        hit the delivered endpoint for their own shipment.
        """
        self.assignment.status = 'ACCEPTED'
        self.assignment.save()
        self.client.login(username='customer', password='tespass333')
        url = reverse('delivery:delivered', args=[self.shipment.pk])
        response = self.client.post(url, follow=True)
        self.assignment.refresh_from_db()
        self.shipment.refresh_from_db()
        #.assertEqual(response.status_code, 404)
        self.assertNotEqual(self.assignment.status, "DELIVERED")
        self.assertNotEqual(self.shipment.status, 'DELIVERED')