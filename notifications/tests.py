from django.test import RequestFactory, TestCase
from django.contrib.auth.models import User
from .models import Notification
from django.urls import reverse
from delivery.models import Courier, DeliveryAssignment, CourierApplication
from shipments.models import Shipment
from notifications.context_processor import notifications_count

class NotificationModelTests(TestCase):
    """
    tests for the Notification Model behaviour
    """

    def setUp(self):
        """setting test values"""
        self.user = User.objects.create_user(username='testsuser', password='testpass123') # tst user 
        self.notification = Notification.objects.create(recipient=self.user, message='Your Shipment has been delivered', link=None) # test nofification

    def test_notification_creation(self):
        """
        tests if Notification instance was created.
        """
        self.assertEqual(Notification.objects.count(), 1) # asserts if Notification instance created
        self.assertEqual(self.notification.recipient, self.user) # asserts if Notification instance created with correct recipient

    def test_mark_as_read(self):
        """
        tests mark as read method sets 
        is_read attribute to True
        """
        self.notification.mark_as_read()
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)


class NotificationSignalsTest(TestCase):
    """
    Tests for the notification signals 
    to ensure automatic notification creation 
    works correctly
    """

    def setUp(self):
        """setting test values"""
        #admin 
        self.admin = User.objects.create_superuser(username='admin', password='testpass111')

        #customer
        self.customer = User.objects.create_user(username='customer', password='testpass222')
        
        #courier user and courier object
        self.courier_user = User.objects.create_user(username='courier', password='testpass333')
        self.courier = Courier.objects.create(user=self.courier_user, phone='08064952530', vehicle='van')

        # shipment 
        self.shipment = Shipment.objects.create(
            user=self.customer,
            origin_address = 'lagos',
            destination_address= 'abuja',
            weight= 100
        )

    def test_shipment_created_notification(self):
        """
        tests if user and admin are notified 
        when a shipment is created
        """
        notif_user = Notification.objects.filter(recipient=self.customer) # user notification
        notif_admin = Notification.objects.filter(recipient=self.admin) # admin notification
        self.assertTrue(notif_user.exists()) # asserts if user notification was created
        self.assertTrue(notif_admin.exists()) # asserts if admin notification was created
    
    def test_delivery_assignment_creates_notification(self):
        """
        tests if courier is notified when delivery is assigned
        """
        DeliveryAssignment.objects.create(shipment=self.shipment, courier=self.courier, status='ASSIGNED') # test delivery assignment 
        notif_courier = Notification.objects.filter(recipient=self.courier_user) # Notification for user 
        self.assertTrue(notif_courier.exists()) # asserts if notification for user exists 

    def test_courier_accepts_shipment_creates_notification(self):
        """
        tests if user and admin is notified when courier 
        accepts delivery assignment 
        """
        assignment = DeliveryAssignment.objects.create(shipment=self.shipment, courier=self.courier) # test delivery assignment
        assignment.status = 'ACCEPTED'
        assignment.save() # sets assignemnt status to accpeted
        notif_user = Notification.objects.filter(recipient=self.customer, message__icontains="In Transit") # notificatio for user
        notif_admin = Notification.objects.filter(recipient=self.admin, message__icontains='delivery was accepted') # notification for admin 
        self.assertTrue(notif_user.exists()) # asserts if user notified 
        self.assertTrue(notif_admin.exists()) # asserts if admin notified

    def test_shipment_delivered_creates_notification(self):
        """
        tests if user and admins are notified 
        when shipments are marked delivered
        """
        self.shipment.status = 'DELIVERED'
        self.shipment.save() # sets shipment status to delivered 
        notif_user = Notification.objects.filter(recipient=self.customer, message__icontains='Delivered') # user's notificaiton 
        notif_admin = Notification.objects.filter(recipient=self.admin, message__icontains='Delivered') # admins notification
        self.assertTrue(notif_user.exists()) # asserts if user notified
        self.assertTrue(notif_admin.exists()) # asserts if admin notified 

    def test_courier_application_approved_creates_notification(self):
        """
        tests if user is notified on approved courier application
        """
        application = CourierApplication.objects.create(
            user=self.courier_user,
            phone='08168247299',
            address='Benin',
            vehicle='van',
            is_approved=False
        ) # test courier application 
        application.is_approved = True
        application.save() # approves application 

        notif_user = Notification.objects.filter(recipient=self.courier_user, message__icontains='approved') # user notificaiton 
        notif_admin = Notification.objects.filter(recipient=self.admin, message__icontains='application received') # admin notification 
        
        self.assertTrue(notif_user.exists()) # asserts if user notified
        self.assertTrue(notif_admin.exists()) # asserts if admin notified

    def test_shipment_deleted_creates_notification(self):
        """
        tests if user and admin are notified 
        if shipment is deleted
        """
        self.shipment.delete() # deletes shipment 
        notif_user = Notification.objects.filter(recipient=self.customer, message__icontains='deleted successfully') # user notification 
        notif_admin = Notification.objects.filter(recipient=self.admin, message__icontains='was deleted') # admin notification 

        self.assertTrue(notif_user.exists()) # asserts if user notified 
        self.assertTrue(notif_admin.exists()) # asserts if admin notified 


class NotificationViewsTests(TestCase):
    """
    Tests views logic for the notifications app
    """

    def setUp(self):
        """setting test values"""
        self.user = User.objects.create_user(username='testuser', password='testpass123') # user1
        self.user2 = User.objects.create_user(username='testuser2', password='testpass123') # test user 2

        self.notification_1 = Notification.objects.create(
            recipient=self.user,
            message='New Shipment update',
            link= reverse("shipments:list")
        ) # user 1 notification1

        self.notification_2 = Notification.objects.create(
            recipient=self.user,
            message='Delivery completed',
            is_read=True
        ) # user 1 notification2

        self.notification_3 = Notification.objects.create(
            recipient=self.user2,
            message='You have a new message'
        ) # user 2 notification
    
    def test_notication_list_view_shows_only_user_notifications(self):
        """
        tests that only authenticated user's notifications 
        are displayed.
        """
        self.client.login(username='testuser', password='testpass123') # authenticates user
        url = reverse("notifications:list") # notification list page
        response = self.client.get(url) # retrieve response from page

        self.assertEqual(response.status_code, 200) # asserts if page was rendered successfully
        self.assertTemplateUsed(response, 'notifications/list.html') # asserts if correct template rendered
        self.assertIn(self.notification_1, response.context['notifications']) # asserts user1 notification is in reponse context 
        self.assertNotIn(self.notification_3, response.context['notifications']) # asserts if user2 notification is not in response context

        unread_count = response.context['unread_count']
        self.assertEqual(unread_count, 1) # asserts if unread_count 1 in response context

    def test_mark_as_read(self):
        """
        tests if user can mark a notification as read
        """
        self.client.login(username='testuser', password='testpass123') # authenticates user
        url = reverse("notifications:mark_as_read", args=[self.notification_1.pk]) 
        response = self.client.get(url) # marks notification as read
        self.notification_1.refresh_from_db() # refreshes db
        self.assertTrue(self.notification_1.is_read) # asserts if notification was mark as read
        self.assertRedirects(response, reverse('shipments:list')) # asserts if user is redirected to correct link

    def test_mark_as_read_only_by_recipient(self):
        """
        tests if only user can mark notification as read
        """
        self.client.login(username='testuser2', password='testpass123') # authenticates user
        url = reverse('notifications:mark_as_read', args=[self.notification_1.pk]) # url for marking as read
        response = self.client.get(url) # retrieves response
        self.assertEqual(response.status_code, 404) # asserts if non user can't mark as read


    def test_mark_all_as_read(self):
        """
        tests if user can mark all notifications as read
        """
        self.notification_2.is_read = False
        self.notification_2.save() # sets notification2 to is_read = false

        self.client.login(username='testuser', password='testpass123')   # authenticates user
        url = reverse('notifications:mark_all_read') # url to mark_all_as_read
        response = self.client.get(url) # retrieves response
        #refreshes db
        self.notification_1.refresh_from_db() 
        self.notification_2.refresh_from_db()

        self.assertRedirects(response, reverse('notifications:list')) # asserts if user redirected
        self.assertTrue(self.notification_1.is_read) # asserts if notification marked as read
        self.assertTrue(self.notification_2.is_read) # asserts if notification marked as read

    def test_delete_notifications(self):
        """
        tests if user can delete notification 
        """
        self.client.login(username='testuser', password='testpass123')
        url = reverse("notifications:delete", args=[self.notification_1.pk])
        response = self.client.get(url)
        self.assertFalse(Notification.objects.filter(pk=self.notification_1.pk).exists())
        self.assertRedirects(response, reverse('notifications:list'))

    def test_delete_all_notificatiosn(self):
        """
        tests is user can delete all notifications
        """
        self.client.login(username='testuser', password='testpass123') # authenticate user
        url = reverse('notifications:delete_all') # url for delete all
        response = self.client.get(url) # retrieves response
        self.assertFalse(Notification.objects.filter(pk=self.notification_1.pk).exists()) # asserts if notification no longer exists
        self.assertFalse(Notification.objects.filter(pk=self.notification_2.pk).exists()) # asserts if notfications no longer exists
        self.assertRedirects(response, reverse('notifications:list')) # asserts if user redirected

    def test_only_user_can_delelete_notifications(self):
        """
        tests if only user can delete notifications
        """
        self.client.login(username='testuser2', password='testpass123') # authenticates user
        url = reverse('notifications:delete', args=[self.notification_1.pk]) # url for delete notification
        response = self.client.get(url) # retrieves response
        self.assertEqual(response.status_code, 404) # asserts if 404 returned for non-recipient of notification 

    def test_if_unauthenticated_user_redirected_to_login(self):
        """tests if unauthenticated users are redirected to login"""
        url = reverse('notifications:list')
        response = self.client.get(url)
        self.assertRedirects(response, '/users/login/?next=/notifications/')


class ContextProcessorTests(TestCase):
    """tests for context_processor.py in notifications app"""
    def setUp(self):
        """setting test values"""
        self.factory = RequestFactory() # used to mimic user request
        self.user = User.objects.create_user(username='testuser', password='testpass123') # test user
        for i in range(8):
            """creating notifications for test user"""
            Notification.objects.create(recipient=self.user, message=f'Notification {i}', is_read=(i % 2 == 0)) # half will be unread and the other half read.

    def test_returns_empty_for_anonymous_user(self):
        """
        tests if unauthenticated users get empty context
        """
        request = self.factory.get('/') # mimics request
        request.user = type('AnonymousUser', (), {'is_authenticated': False})() # mimics an anonymous user
        context = notifications_count(request) # context 
        self.assertEqual(context, {}) # asserts if empty dict was returned for anonymous user

    def test_returns_unread_count_and_recent_notifications(self):
        """
        tests if context contains correct unread count and recent notifications
        """
        request = self.factory.get('/') # mimics user request
        request.user = self.user # sets user to self.user

        context = notifications_count(request) # context
        self.assertIn('unread_notification_count', context) # asserts if context has key 'unread_notification_count'
        unread_count = Notification.objects.filter(recipient=self.user, is_read=False).count() # unread count for user 
        self.assertEqual(context['unread_notification_count'], unread_count) # asserts if the unread count for context is correct 
        self.assertLessEqual(len(context['recent_notifications']), 6) # asserts if the num of recent notifications do not exceed 6
        for notif in context['recent_notifications']:
            """asserts if all notifications are received by appropriate user"""
            self.assertEqual(notif.recipient, self.user)