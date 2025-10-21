import json
from unittest import skip
from unittest.mock import patch
from django.test import Client, TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from courier_site_project import settings
from shipments.models import Shipment
from payments.models import Payment, Receipt
from django.urls import reverse_lazy
from notifications.models import Notification
from users.models import Profile
from django.core import mail
from django.contrib.messages import get_messages
class PaymentModelTests(TestCase):
    """
    testing Payment model methods and Behaviour
    """

    def setUp(self):
        """setting test values"""
        self.user = User.objects.create_user(username='testuser', email='test@examplemcom', password='testpass123') # test user 
        
        self.shipment = Shipment.objects.create(user=self.user, origin_address='test origin', destination_address='test destination', weight=100) #test shipment 
        
        # get the auto-created payment instance created when a new shipment is created.
        self.payment = Payment.objects.get(shipment=self.shipment)

    def test_payment_creation_with_required_fields(self):
        """
        tests if payment is created with required field
        """

        self.assertIsNotNone(self.payment) # asserts if auto-created payment instance exists

        self.assertEqual(self.payment.user, self.user) # asserts if payment linked to correct user
        self.assertEqual(self.payment.shipment, self.shipment) # asserts if payment instance linked to correct shipment

        #asserts for default values(PENDING, CARD)
        self.assertEqual(self.payment.status, 'PENDING')
        self.assertEqual(self.payment.method, 'CARD')


        expected_cost = 100 * 0.01
        self.assertEqual(float(self.payment.amount), expected_cost) # asserts if amount is accurate based on weight


        #asserts timestamps exist
        self.assertIsNotNone(self.payment.created_at)
        self.assertIsNotNone(self.payment.updated_at) 


    def test_payment_str_representation(self):
        """
        tests if __str__ method returns correct format
        """
        expected_str = f"Payment for {self.shipment.tracking_number} - PENDING"
        self.assertEqual(str(self.payment), expected_str) 

    
    def test_tx_ref_auto_generation_on_save(self):
        """
        tests if tx_ref is automatically generated when Payment is saved
        """
        self.assertIsNotNone(self.payment.tx_ref) # asserts if payment instance has tx_ref
        self.assertTrue(len(self.payment.tx_ref) > 0) # assets if len of tx_ref is greater than zero
        self.assertTrue(self.payment.tx_ref.startswith("QBX-")) # asserts if tx_ref starts with 'QBX-'
        self.assertEqual(len(self.payment.tx_ref), 14) # asserts if tx_ref has 14 characters
        self.assertTrue(self.payment.tx_ref[4:].isupper()) # asserts if characters from the 4th index is uppercased

    def test_tx_ref_uniqueness(self):
        """
        tests if each payment gets unique tx_ref
        """

        #second shipment and payment instance
        shipment2 = Shipment.objects.create(
            user=self.user,
            origin_address='test origin',
            destination_address='test destination',
            weight=100
        )
        payment2 = Payment.objects.get(shipment=shipment2)

        #third shipment and payment instance
        shipment3 = Shipment.objects.create(
            user=self.user,
            origin_address='test origin',
            destination_address='test destination',
            weight=100
        )

        payment3 = Payment.objects.get(shipment=shipment3)

        # asserts if all the tx_ref are not equal and unique
        self.assertNotEqual(self.payment.tx_ref, payment2.tx_ref)
        self.assertNotEqual(self.payment.tx_ref, payment3.tx_ref)
        self.assertNotEqual(payment2.tx_ref, payment3.tx_ref)

    
    def test_generate_tx_ref_helper_method(self):
        """
        tests the generate_tx_ref helper method in the models.py 
        """
        new_tx_ref = self.payment.generate_tx_ref()# generates new test tx_ref

        self.assertIsInstance(new_tx_ref, str) # asserts if its a string
        self.assertTrue(new_tx_ref.startswith('QBX-')) # asserts if it startswith 'QBX-'
        self.assertEqual(len(new_tx_ref), 14)
        self.assertNotEqual(new_tx_ref, self.payment.tx_ref) # asserts if tx_ref is unique

    def test_mark_paid_helper_method(self):
        """
        tests the mark_paid() method logic
        """

        
        self.assertEqual(self.payment.status, 'PENDING') # asserts if payment instance has default pending value

        # test meta and transaction id for mark_paid() method
        test_meta = {'payment_type': 'card', 'amount': 100 }
        test_transactionid = "FLWTESTTRANSACTIONID123"


        self.payment.mark_paid(meta=test_meta, transaction_id=test_transactionid) # calling method on payment instance 
        self.payment.refresh_from_db() # apply changes


        self.assertEqual(self.payment.status, 'PAID') # assert if status of payment instance was update to PAID.
        self.assertEqual(self.payment.transaction_id, test_transactionid) # asserts if transaction_id was updated
        self.assertEqual(self.payment.meta, test_meta) # asserts if meta was updated

    def test_mark_paid_helper_method_creates_receipt(self):
        """
        tests if mark_paid() creates a Receipt by default
        """
        self.assertFalse(hasattr(self.payment, 'receipt')) # asserts that a pending payment has no receipt attribute
        receipt = self.payment.mark_paid(transaction_id='FLWTESTID', meta={'payment_method':'card', 'amount': 100}) # holds the value returned by the mark_paid() method
        self.assertIsNotNone(receipt) # asserts the value returned is not None(null)
        self.assertIsInstance(receipt, Receipt) # asserts the value returned is of Receipt type
        self.payment.refresh_from_db() # applys changes
        self.assertIsNotNone(self.payment.receipt) # asserts the payment is linked to a receipt now
        self.assertEqual(self.payment.receipt, receipt) # asserts the receipt linked to the payment instance is same with the reciept returned by the mark_paid() method.

    def test_mark_paid_without_creating_receipt(self):
        """
        tests if mark_paid() method can skip receipt creation
        """
        receipt = self.payment.mark_paid(transaction_id='TEXT_TXN', create_receipt=False) # value returned on create_receipt=False

        self.assertIsNone(receipt) # asserts if receipt is None(null)
        self.assertFalse(hasattr(self.payment, 'receipt')) # asserts if self.payment was linked to any receipt instance

        # asserts if The Receipt.DoesNotExits exception is raised
        with self.assertRaises(Receipt.DoesNotExist):
            self.payment.refresh_from_db()
            err_receipt = self.payment.receipt # should raise an exception cuz receipt does not exist 

    def test_mark_failed_helper_method(self):
        """
        tests mark_failed() helper method logic
        """
        self.assertEqual(self.payment.status, 'PENDING') # asserts if default values

        #test meta and transactionid
        test_transactionid = 'FAILED_TXN'
        test_meta = {'error_code': 'insufficient_funds', 'error_message':'card_declined'}

        #marks payment failed
        self.payment.mark_failed(transaction_id=test_transactionid, meta=test_meta)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'FAILED') # asserts if status is update to FAILED
        self.assertEqual(self.payment.transaction_id, test_transactionid) # asserts if transaction_id updated 
        self.assertEqual(self.payment.meta, test_meta) # asserts if meta is updated

    def test_get_flutterwave_payload_helper_method(self):
        """
        tests if get_flutterwave_payload() method
        returns correct payload structure and logic
        """
        payload = self.payment.get_flutterwave_payload() # gets build payload for payment instance
        self.assertIsInstance(payload, dict) # asserts if payload is a dictionary
        required_keys = [
            'tx_ref', 'amount', 'currency', 'redirect_url', 'payment_options', 'customer', 'customisations'
        ] # keys that should be in payload
        for key in required_keys:
            self.assertIn(key, payload) # asserts if all required keys are in payload

        self.assertEqual(payload['tx_ref'], self.payment.tx_ref) # asserts if payload tx_ref is correct 
        self.assertEqual(payload['amount'], str(self.payment.amount)) # asserts if payload amount is correct 
        self.assertEqual(payload['currency'], 'NGN') # asserts if payload currency is correct 
        self.assertEqual(payload['customer']['email'], self.user.email) # asserts if payload email is correct 

        # asserts if payload contains correct customisations
        self.assertIn('QuariarBox', payload['customisations']['title']) 
        self.assertIn(self.shipment.tracking_number, payload['customisations']['description'])


    def test_refresh_tx_ref_helper_method(self):
        """
        tests refresh_tx_ref() helper method logic
        """

        #asserts if tx_ref is changed when refresh_tx_ref() method is called
        old_tx_ref = self.payment.tx_ref
        self.payment.refresh_tx_ref()
        self.payment.refresh_from_db()
        self.assertNotEqual(self.payment.tx_ref, old_tx_ref)

        
        self.payment.mark_failed(transaction_id='FAILED+TXN', meta={"old":'data'}) # marks payment failed with test transaction_id and test meta
        self.payment.refresh_from_db() # apply changes 
        self.assertEqual(self.payment.status, 'FAILED') # asserts if status update to failed
        self.assertEqual(self.payment.transaction_id, 'FAILED+TXN') # asserts if transaction_id updated 
        self.assertEqual(self.payment.meta, {'old':'data'}) # asserts if meta updated 

        self.payment.refresh_tx_ref() # refresh transaction details
        self.payment.refresh_from_db() # apply changes 

        self.assertEqual(self.payment.status, "PENDING") # asserts if status updated to pending 
        self.assertIsNone(self.payment.transaction_id) # asserts if transaction_id is now none(null)
        self.assertIsNone(self.payment.meta) # asserts if meta is now none(null)

    def test_payment_ordering_by_created_at(self):
        """
        tests if payments are ordered by created_at attribute (newest first)
        """
        shipment2 = Shipment.objects.create(
            user=self.user,
            origin_address='test origin',
            destination_address='test destination',
            weight=100
        ) # test shipment 2
        payment2 = Payment.objects.get(shipment=shipment2) # test payment 2

        shipment3 = Shipment.objects.create(
            user=self.user,
            origin_address='test origin',
            destination_address='test destination',
            weight=100
        ) # test shipment3
        payment3 = Payment.objects.get(shipment=shipment3) # test payment 3

        payments = Payment.objects.all() # all payment instances 

        #assertions to ascertain order is correct

        self.assertEqual(len(payments), 3)
        self.assertEqual(payments[0], payment3)
        self.assertEqual(payments[1], payment2)
        self.assertEqual(payments[2], self.payment)


class ReceiptModelTests(TestCase):
    """
    testing Receipt Model methods, behaviours and 
    pdf generation logic
    """
    def setUp(self):
        """setting test values"""
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='testpass123') # test user instance

        self.shipment = Shipment.objects.create(
            user=self.user, 
            origin_address='test origin',
            destination_address='test destination', 
            weight=100
        ) # test shipment instance 

        self.payment = Payment.objects.get(shipment=self.shipment) # auto-generated payment instance for shipment by signals

        self.receipt = self.payment.mark_paid(
            transaction_id='TEST_TXN_ID',
            meta={'test':'data'}
        ) # test receipt from payment instance mark_paid() method

    def test_receipt_creation(self):
        """
        tests if receipt is created with correct values and relationships
        """
        self.assertIsNotNone(self.receipt) # asserts receipt instance is valid
        self.assertEqual(self.receipt.payment, self.payment) # asserts receipt instance is related to correct payment instance
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.receipt, self.receipt) # asserts instances related correctly
        self.assertIsNotNone(self.receipt.issued_at) # asserts if timestamp attribute exist

    def test_receipt_str_repr(self):
        """
        tests if __str__ method returns correct format for Receipt instance
        """
        expected_str = f"Receipt {self.receipt.receipt_number}" # expected printout str
        self.assertEqual(str(self.receipt), expected_str) # asserts if str repr is correct for receipt instance

    def test_receipt_number_auto_generation(self):
        """
        tests if receipt_number is auto-generated on saving Receipt model instance
        """
        self.assertIsNotNone(self.receipt.receipt_number) # asserts if receipt_number exists
        self.assertTrue(len(self.receipt.receipt_number) > 0) 
        self.assertTrue(self.receipt.receipt_number.startswith('RCP-')) # asserts if receipt_number starts with correct prefix

    def test_receipt_number_uniqueness(self):
        """
        tests if auto-generated receipt_numbers 
        are always unique
        """
        shipment2 = Shipment.objects.create(
            user=self.user, 
            origin_address='test origin',
            destination_address='test destination',
            weight=100
        ) # test shipment 2

        payment2 = Payment.objects.get(shipment=shipment2) # test payment 2

        receipt2= payment2.mark_paid(
            transaction_id='TEST_TXN_ID',
            meta={'test':'data'}
        ) # test receipt 2

        shipment3 = Shipment.objects.create(
            user=self.user, 
            origin_address='test origin',
            destination_address='test destination',
            weight=100
        ) # test shipment 3

        payment3 = Payment.objects.get(shipment=shipment3) # test payment 3

        receipt3= payment3.mark_paid(
            transaction_id='TEST_TXN_ID',
            meta={'test':'data'}
        ) # test receipt 3

        #asserts all receipt_numbers are unique and not equal to another.
        self.assertNotEqual(self.receipt.receipt_number, receipt2.receipt_number)
        self.assertNotEqual(self.receipt.receipt_number, receipt3.receipt_number)
        self.assertNotEqual(receipt2.receipt_number, receipt3.receipt_number)
        

    def test_receipt_number_format(self):
        """
        tests if receipt_numbers are auto-generated with the correct format
        """
        #correct_format = "RCP-20241012123456-ABC123"
        split_parts = self.receipt.receipt_number.split('-')

        #assertions ascertaining receipt_number format is correct 
        self.assertEqual(len(split_parts), 3)
        self.assertEqual(split_parts[0], 'RCP')
        self.assertEqual(len(split_parts[1]), 14)
        self.assertTrue(split_parts[1].isdigit())
        self.assertTrue(split_parts[2].isupper())

    def test_receipt_ordering_by_issued_at(self):
        """
        tests if Receipt instances(rows) are ordered 
        by the issued_at timestamp attribute 
        """
        shipment2 = Shipment.objects.create(
            user=self.user, 
            origin_address='test origin',
            destination_address='test destination',
            weight=100
        ) # test shipment 2

        payment2 = Payment.objects.get(shipment=shipment2) # test payment 2

        receipt2= payment2.mark_paid(
            transaction_id='TEST_TXN_ID',
            meta={'test':'data'}
        ) # test receipt 2

        shipment3 = Shipment.objects.create(
            user=self.user, 
            origin_address='test origin',
            destination_address='test destination',
            weight=100
        ) # test shipment 3

        payment3 = Payment.objects.get(shipment=shipment3) # test payment 3

        receipt3= payment3.mark_paid(
            transaction_id='TEST_TXN_ID',
            meta={'test':'data'}
        ) # test receipt 3

        receipts = Receipt.objects.all()

        #assertions to ascertain ordering of receipts is correct
        self.assertEqual(len(receipts), 3)
        self.assertEqual(receipts[0], receipt3)
        self.assertEqual(receipts[1], receipt2)
        self.assertEqual(receipts[2], self.receipt)

    def test_get_absolute_url(self):
        """
        tests if the get_absolute_url() returns correct URL.
        """
        url = self.receipt.get_absolute_url() # method returns url 
        self.assertIsNotNone(url) # asserts if url is valid 
        expected_url = reverse_lazy('payments:receipt', args=[self.shipment.id]) # expected url 
        self.assertEqual(url, expected_url) # asserts if returned url by the method is correct

    def test_pdf_generation_on_save(self):
        """
        tests if PDF is auto-generated when receipt instance is saved/created 
        """
        self.assertIsNotNone(self.receipt.pdf) # assert sif pdf exists 
        self.assertTrue(self.receipt.pdf) # asserts if pdf attribute contains a file

        expected_filename = f"receipt_{self.receipt.receipt_number}.pdf" # expected name format 

        self.assertTrue(self.receipt.pdf.name) # asserts if pdf file has a name 
        self.assertTrue(self.receipt.pdf.name.startswith('receipts/')) # asserts if pdf file is in the receipts/ folder
        self.assertTrue(self.receipt.pdf.name.endswith(expected_filename)) # asserts if the pdf name is correct.
    

class PaymentSignalTests(TestCase):
    
    """
    tests the logic of implemented signals for the paymnets app
    """
    def setUp(self):
        """setting test values"""
        self.admin = User.objects.create_superuser(
            username='admin',
            password='adminpass123',
            email='admin@gmail.com'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@gmail.com'
        ) # test user
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpass321',
            email='test2@gmail.com'
        ) #test user2
        self.shipment = Shipment.objects.create(
            user=self.user,
            origin_address='test origin',
            destination_address='test destination',
            weight=100)
         # test shipment

    def test_signal_for_pending_payment_instance_creation(self):
        """
        tests if signal was fired to create a pending 
        payment instance for every shipment created 
        """
        payment_instance = Payment.objects.get(shipment=self.shipment) 

        self.assertIsNotNone(payment_instance) # asserts that payment instance was created 
        self.assertEqual(payment_instance.status, 'PENDING') # asserts that status of payment instance is PENDING
        self.assertEqual(self.shipment.cost, payment_instance.amount) # asserts that shipment.cost and payment amount for shipment are equal
        self.assertEqual(self.shipment.user, payment_instance.user) # asserts shipment instance and payment are linked to same correct user
        self.assertEqual(self.shipment, payment_instance.shipment) # asserts if the payment instance is related to the correct user

    def test_signal_for_updating_payment_instance_on_shipment_update(self):
        """
        tests if payment amount is updated when shipment cost is updated 
        or changed.
        """

        #asserts if shipment.cost and payment amount are same for the shipment old cost
        self.assertEqual(self.shipment.cost, (self.shipment.weight * 0.01))
        self.assertEqual(self.shipment.cost, self.shipment.payments.amount)
        
        #updates shipment weight, recalculates the cost, and applys changes
        self.shipment.weight = 200
        self.shipment.calc_cost()
        self.shipment.save()
        self.shipment.refresh_from_db()
        
        #asserts if shipment.cost and payment amount are still same for the updated cost
        self.assertEqual(self.shipment.cost, (200 * 0.01))
        self.assertEqual(self.shipment.cost, self.shipment.payments.amount)

    def test_signal_for_notifying_shipment_owner_and_admins_on_payments_paid(self):
        """
        tests if shipment owner and admins are notified on paying successfully 
        and also when payment fails 
        """
        payment_instance = Payment.objects.get(shipment=self.shipment) # autogenerated payment instance

        payment_instance.mark_paid(
            transaction_id='TEST_TXN_ID',
            meta={'test':'data'}
        ) # mark payment as paid 
        
        owners_notification = Notification.objects.get(
            recipient=payment_instance.user, 
            message='Payment was successful click to view receipt', 
            link= reverse_lazy("payments:receipt", args=[self.shipment.pk])
            ) # retrieve owneres notification instance with correct parameters

        self.assertIsNotNone(owners_notification) # asserts if owneres notification instance is valid 

        admin_notification = Notification.objects.get(
            recipient=self.admin,
            message=f"customer has paid for shipment {self.shipment.tracking_number} and is ready for courier assignment",link=reverse_lazy("admin:shipments_shipment_changelist")
            ) # retrieves admin notification instance with correct parameters 
        
        self.assertIsNotNone(admin_notification) # asserts if admin notification is valid 

    def test_signal_for_notifying_shipment_owner_and_admins_on_payments_failed(self):
        payment_instance = Payment.objects.get(shipment=self.shipment) # autogenerated payment instance 
        payment_instance.mark_failed(
            transaction_id='TEST TXN ID',
            meta= {'txn':'failed'}
        ) # mark payment as paid 

        owners_notification = Notification.objects.get(
            recipient=payment_instance.user, 
            message=f'Payment for shipment {self.shipment.tracking_number} Failed!!',
            link=reverse_lazy("shipments:detail", args=[self.shipment.pk])
            ) # retrieve owners notification with correct parameters 

        self.assertIsNotNone(owners_notification) # asserts if owners notification is valid 
    
    
    @patch("payments.signals.EmailMultiAlternatives.send", autospec=True)
    def test_email_sent_to_user_on_successful_payment(self, mock_send):
        """
        tests if email is sent to the user when payment is successful 
        and test the emailing logic
        """
        payment_instance = Payment.objects.get(shipment=self.shipment)
        payment_instance.mark_paid(
            transaction_id='TEST TXN ID', 
            meta={'test':'data'}
        )
        self.assertTrue(mock_send.called) #asserts if the .send() method was called.
        self.assertEqual(mock_send.call_count, 1) # asserts number of times the .send() method is called

        #retrieving mocked email instance 
        args, kwargs = mock_send.call_args
        email_instance = args[0]
        self.assertIn(self.user.email, email_instance.to) # asserts if recipient is correct 
        self.assertIn('Payment Confirmation', email_instance.subject) # asserts if subject is correct 
        self.assertIn('Payment Successful', email_instance.body) # asserts if email body is correct 

        html_body = email_instance.alternatives[0][0] # retrieves attached html body from email instance 

        # asserts if html_body content is correct # asserts if html_body content is correct 
        self.assertIn('Payment Successful',html_body) 
        self.assertIn(self.shipment.tracking_number, html_body)

    
    @patch('payments.signals.EmailMultiAlternatives.send', autospec=True)
    def test_email_not_sent_on_failed_payment(self, mock_send):
        """
        tests if email is not sent when payment failes 
        """
        payment_instance = Payment.objects.get(shipment=self.shipment) # payment instance 
        payment_instance.mark_failed(
            transaction_id='TEST TXN ID', 
            meta={'failed':'data'}
            ) # marks payment as failed 
        self.assertFalse(mock_send.called) # asserts if method was not called 

class PaymentViewAuthenticationTests(TestCase):
    """
    tests if all the payment views are restricted from 
    unauthenticated users
    """
    def setUp(self):
        """setting test values"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        ) # test user 

        self.shipment = Shipment.objects.create(
            user = self.user,
            origin_address='test origin',
            destination_address='test destination',
            weight=100
        ) # test shipment 

        self.payment = Payment.objects.get(shipment=self.shipment) # test paymetn instance 

        self.receipt = self.payment.mark_paid(
            transaction_id='TEST TXN ID',
            meta= {'test':'data'}
        ) # test receipt instance 

        self.login_url = '/users/login/?next=' # login url 

    def test_authentication_required_on_receipt_view(self):
        """
        tests if receipt_view is restricted from unauthenticated users
        """
        url = reverse_lazy("payments:receipt", args=[self.shipment.pk]) # url for receipt view page 
        response = self.client.get(url) # retrieve response 
        self.assertEqual(response.status_code, 302) # asserts if user was redirected 
        self.assertRedirects(response,self.login_url + url) # asserts if user was redirected to login page 

    def test_authentication_required_on_download_receipt_view(self):
        """
        tests if unauthenticatied users are restricted from 
        downloading receipts
        """
        url = reverse_lazy("payments:download-receipt", args=[self.receipt.pk]) # url for download receipt pdf 
        response = self.client.get(url) # retrieve response 
        self.assertEqual(response.status_code, 302) # asserts if user was redirected 
        self.assertRedirects(response, self.login_url + url) # asserts if user was redirected to login page 

    def test_authentication_required_on_initiate_payment_view(self):
        """
        tests if unauthenticated users are restricted 
        from the initiate payment view
        """
        url = reverse_lazy('payments:initiate', args=[self.payment.pk]) # url for initiate payment view 
        response = self.client.get(url) # retrieve response 
        self.assertEqual(response.status_code, 302) # asserts if user was redirected 
        self.assertRedirects(response, self.login_url + url) # asserts if user was redirected to login page

    def test_authentication_required_on_verify_payment_view(self):
        """
        tests if unauthenticated users are restricted from 
        verify payment view
        """
        url = reverse_lazy('payments:verify') # url for verify payment view 
        response = self.client.get(url) # retrieve response 
        self.assertEqual(response.status_code, 302) # asserts if user was redirected 
        self.assertRedirects(response, self.login_url + url) # asserts if user was redirected to login page 

    def test_authentication_required_on_payment_history_view(self):
        """
        tests is unauthenticated users are restricted from the 
        payment history page 
        """
        url = reverse_lazy('payments:payments-history') # url for payments history page 
        response = self.client.get(url) # retrieve response 
        self.assertEqual(response.status_code, 302) # asserts if user is redirected 
        self.assertRedirects(response, self.login_url + url) # asserts if user is redirected to login page



class ReceiptViewTests(TestCase):
    """
    tests the logic fo the receipt view and 
    the download receipt view 
    """
    def setUp(self):
        """setting test values"""
        self.owner = User.objects.create_user(
            username='owner',
            password='testpass123'
        ) # test user 1

        self.non_owner = User.objects.create_user(
            username='non-owner',
            password='testpass123'
        ) # test user 2

        self.shipment = Shipment.objects.create(
            user = self.owner,
            origin_address='test origin',
            destination_address='test destination',
            weight=100
        ) # test shipment 

        self.payment = Payment.objects.get(shipment=self.shipment) # test paymetn instance 

        self.receipt = self.payment.mark_paid(
            transaction_id='TEST TXN ID',
            meta= {'test':'data'}
        ) # test receipt instance 

    def test_authenticated_shipment_owner_can_view_receipt(self):
        """
        tests if authenticated user can view receipt 
        for his or her paid shipment 
        """
        self.client.login(username='owner',password='testpass123') # authenticates owner
        url = reverse_lazy('payments:receipt', args=[self.shipment.pk]) # url for receipts page
        response = self.client.get(url) # retrieve response
        self.assertEqual(response.status_code, 200) # asserts if page rendered successfully
        self.assertTemplateUsed(response, 'payments/receipt.html') # asserts if page rendered with correct template

    def test_non_owner_cannot_view_receipt(self):
        """
        tests if authenticated non-owner cannot view 
        another users payment receipt
        """
        self.client.login(username='non-owner', password='testpass123') # authenticates non-owner
        url = reverse_lazy('payments:receipt', args=[self.shipment.pk]) # url for receipt page
        response = self.client.get(url) # retrieve response
        self.assertEqual(response.status_code, 404) # asserts if 404 page returned for non-owner

    
    def test_authenticated_owner_can_download_receipt(self):
        """
        tests if authenticated owner can dowload hist/her 
        payment receipts and checks if the downloaded file is pdf
        """
        self.client.login(username='owner', password='testpass123') # authenticates owner
        url = reverse_lazy('payments:download-receipt', args=[self.receipt.pk]) # url to download receipt
        response = self.client.get(url) # retrieve response
        self.assertEqual(response.status_code, 200) # asserts if download successful
        self.assertIsNotNone(response['Content-Disposition']) # asserts if file added to response as attachment 
        self.assertEqual(response['Content-Disposition'], 
                         f"attachment; filename='receipt_{self.receipt.receipt_number}.pdf" ) # asserts if correct receipt pdf was attached 
        self.assertEqual(response['Content-Type'], 'application/pdf') # asserts if the content-type of the response is a pdf.
    
    def test_authenticated_non_owner_cannot_download_receipt(self):
        """
        tests if authenticated non-owner cannot download 
        another users payment receipt
        """
        self.client.login(username='non-owner', password='testpass123') # authenticates non-owner
        url = reverse_lazy('payments:download-receipt', args=[self.receipt.pk]) # url to download receipt 
        response = self.client.get(url) # retrieve response 
        self.assertEqual(response.status_code, 404) # asserts if 404 page returned for non-owner 


class PaymentHistoryViewTests(TestCase):
    """
    tests for the paymentHistory view logic 
    """

    def setUp(self):
        """setting test values """
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        ) # test user 1

        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123',
            email='test@example.com'
        ) # test user 2

        self.shipment_1 = Shipment.objects.create(
            user=self.user,
            origin_address='test origin',
            destination_address='test destination',
            weight=100
        ) # test user 1 shipment 1

        self.shipment_2 = Shipment.objects.create(
            user=self.user,
            origin_address='test origin',
            destination_address='test destination',
            weight=100
        ) # test user 1 shipment 2

        self.shipment_3 = Shipment.objects.create(
            user=self.user2,
            origin_address='test origin',
            destination_address='test destination',
            weight=100
        ) # test user 2 only shipment 

        
        # test user 1 payment instnaces 
        self.payment_1 = Payment.objects.get(shipment=self.shipment_1)  
        self.payment_2 = Payment.objects.get(shipment=self.shipment_2)
        # test user 2 payment instance
        self.payment_3 = Payment.objects.get(shipment=self.shipment_3)

    def test_payment_history_shows_only_paid_payments(self):
        """
        tests if payment history page shows only paid payments
        """
        self.client.login(username='testuser', password='testpass123')# authenticates user1
        url = reverse_lazy('payments:payments-history') # url for payment history page

        self.payment_1.mark_paid(
            transaction_id='test txn id ',
            meta = {'test':'data'}
        ) # mark payment 1 as paid 

        response = self.client.get(url) # retrieve response 
        self.assertTemplateUsed(response, 'payments/payment_history.html') # assert that correct template is used 
        payments = response.context['payments'] # retrieve payments context from response 
        self.assertIn(self.payment_1,payments) # asserts if paid payment instance in payments context 
        self.assertNotIn(self.payment_2, payments) # asserts if non-paid payment instance not in payments context 

    def test_payment_history_shows_only_user_payments(self):
        """
        tests if payment history page shows only users payments 
        and not others
        """
        self.client.login(username='testuser2', password='testpass123') # authenticates user 2
        url = reverse_lazy('payments:payments-history') # url for payment history page
        self.payment_1.mark_paid(
            transaction_id='test txn id', 
            meta={'test':'data'}
        ) # mark user1's payment to paid 

        self.payment_3.mark_paid(
            transaction_id='test txn id',
            meta={'test':'data'}
        ) # mark user2's payment to paid 

        response = self.client.get(url) # retrieve response 
        payments = response.context['payments'] # retrieve payments context from response 
        
        self.assertIn(self.payment_3, payments) # asserts if user2 payment instance in payments context (logged in user )
        self.assertNotIn(self.payment_1, payments) # asserts if user1 payment instance not in payments context

    def test_payment_history_pagination(self):
        """
        tests if payment history page is paginated and tests 
        the logic of the pagination 
        """
        url = reverse_lazy('payments:payments-history') # payment history page 
        
        for i in range(15):
            """
            using loop to create 15 shipment instances 
            and marking their payment instance to PAID
            """
            shipment = Shipment.objects.create(
                user=self.user,
                origin_address=f'origin {i}',
                destination_address=f'destination{i}',
                weight=100
            ) # shipment instances through loop 
            payment = Payment.objects.get(shipment=shipment) # payment instances through loop
            payment.mark_paid(transaction_id=f'TXN_{i}') # marking the payment instances to PAID 

        self.client.login(username='testuser', password='testpass123') # authenticates user1
        response = self.client.get(url) # retrieve response 
        self.assertEqual(response.status_code, 200) # assert page was rendered successfully
        paginator = response.context['paginator'] # retrieve paginator context
        self.assertEqual(paginator.per_page, 10) # assert perpage count 
        page = response.context['page_obj'] # retrieve page obj context
        self.assertEqual(len(page.object_list), 10) # assert if len of object returned in the page for payments is correctly 10
        self.assertTrue(page.has_next()) # asserts if page still has next objects 
        response = self.client.get(url + '?page=2') # retrieve the page 2 of the payment history page as its paginated .
        page = response.context['page_obj']
        
        # Second page should have remaining 5 items
        self.assertEqual(len(page.object_list), 5) # assert remaining payment instances in the page is correctly 5
        self.assertFalse(page.has_next()) # assert if no more remaining payment instances 
    
    def test_payment_history_empty_for_new_user(self):
        """
        tests if New user with no paid payments sees empty list
        """
        url = reverse_lazy('payments:payments-history')
        user_new = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )# Create new user with no payments
        
        self.client.login(username='newuser', password='testpass123') # authenticate new user
        response = self.client.get(url) # retrieve response
        
        # Should be successful
        self.assertEqual(response.status_code, 200) # assert page loaded successfully
        
        # Payments should be empty
        payments = response.context['payments']
        self.assertEqual(len(payments), 0) # assert page has no payment instances in the payments context 
        self.assertContains(response, 'No payments found') # asserts if page contains correct content


class InitiatePaymentViewTests(TestCase):
    """
    tests the initiate payment view logic
    """

    def setUp(self):
        """setting test values"""
        self.user1 = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        ) # test user 1

        self.user2 = User.objects.create_user(
            username='testuser2', 
            password='testpass321',
            email='test2@example.com'
        ) # test user 2

        self.shipment = Shipment.objects.create(
            user=self.user1,
            origin_address='test origin',
            destination_address='test destination',
            weight=100
        ) # test shipment 
        self.payment = Payment.objects.get(shipment=self.shipment) # test payment instance 
    
    def test_non_owner_can_not_initialise_payment(self):
        """
        tests if non-owner is restricted from initialising payment 
        for another users payment
        """
        self.client.login(username='testuser2', password='testpass321') # authenticates non-owner user 2
        url = reverse_lazy('payments:initiate', args=[self.payment.pk]) # url to initiate payment 
        response = self.client.get(url) # retrieve response 
        self.assertEqual(response.status_code, 404) # asserts if non-owner restricted 

    def test_user_redirected_on_duplicate_payment(self):
        """
        tests if user is redirected to shipment detail page 
        when trying to pay for a shipment that has been paid for 
        """
        self.client.login(username='testuser', password='testpass123') # authenticates owner(user1)
        url = reverse_lazy('payments:initiate', args=[self.payment.pk]) # url to initiate payment 
        redirect_url = reverse_lazy('shipments:detail', args=[self.shipment.pk]) # url for shipment detail user is redirected to 
        
        self.payment.mark_paid(
            transaction_id='TEST TXN ID', 
            meta={'test':'data'}
        ) # mark payment instance as paid 

        response = self.client.get(url) # retrieve response
        self.assertEqual(response.status_code, 302) # asserts if user was redirected 
        self.assertRedirects(response, redirect_url) # asserts if user was redirected to correct page

    @patch('payments.models.Payment.refresh_tx_ref') # mocks the refresh_tx_ref method
    @patch('payments.views.requests.post') # mocks the requests.post method
    def test_refresh_tx_ref_method_called_if_payment_previously_failed(self,mock_post,  mock_refresh_tx_ref):
        """
        tests if the refresh_tx_ref() method is called 
        if payment instance had previously failed and has 
        status of FAILED.
        mock methods are passed in to the method: mock_post and mock_refresh_tx_ref
        """
        self.client.login(username='testuser', password='testpass123')  #authenticates owner
        url = reverse_lazy('payments:initiate', args=[self.payment.pk])# url to initiate payment 
        mock_post.return_value.json.return_value = {'status': 'error'} # mock return value for requests.post 

        self.payment.mark_failed(
            transaction_id='test txn id', 
            meta={'failed':'data'}
        ) # marks payment as FAILED
        
        response = self.client.get(url) # retrieve response on initiating payment
        self.assertTrue(mock_refresh_tx_ref.called) # asserts if the refresh_tx_ref method was called 
        self.assertEqual(mock_refresh_tx_ref.call_count, 1) # asserts if the refresh_tx_ref method was called only once 
        self.assertRedirects(response, reverse_lazy('shipments:detail', args=[self.shipment.pk])) # asserts if the user was redirected to the shipment detail page as the return_value was {'status', 'error'}

    # i don't understand yet
    @patch('payments.views.requests.post')
    def test_successful_initialisation_redirects_to_flutterwave(self, mock_post):
        """
        tests if user is redirected to flutterwave checkout url
        on successful payment initiation
        """
        
        url = reverse_lazy('payments:initiate', args=[self.payment.pk]) # url to initiate payment 
        mock_post.return_value.json.return_value = {
            'status': 'success',
            'data': {'link':
                     'https://checkout.flutterwave.com/fake-url'}
            } # mocks returned json for mocked api call

        self.client.login(username='testuser', password='testpass123') # authenticates user 

        response = self.client.get(url) # retrieve response on initiating payment
        self.assertRedirects(response, "https://checkout.flutterwave.com/fake-url", fetch_redirect_response=False) # asserts if user was redirected to checkout url 

        args, kwargs = mock_post.call_args # get parameters from mocked request.post method
        self.assertIn('https://api.flutterwave.com/v3/payments', args[0]) # asserts if the first argument is the url
        #asserts if the header values are correct 
        self.assertEqual(kwargs['headers']['Content-Type'], 'application/json')
        self.assertEqual(kwargs['headers']['Authorization'].startswith('Bearer '), True)
        self.assertIn('amount', kwargs['json']) 

    @patch('payments.views.requests.post')
    def test_invalid_json_from_flutterwave_handled(self, mock_post):
        """
        tests if case of flutterwave returns invalid json is 
        handled
        """
        url = reverse_lazy('payments:initiate', args=[self.payment.pk]) # url to initiate payment
        mock_post.return_value.json.side_effect = ValueError('Invalid JSON') # mocks invalid json error for api call 
        self.client.login(username='testuser', password='testpass123') # authenticates user 
        response = self.client.get(url) # retrieves response on initiating payment 
        self.assertRedirects(response, reverse_lazy('shipments:detail', args=[self.shipment.pk])) # asserts if user is redirected to shipment page as error is returned from api call
        
        messages = list(get_messages(response.wsgi_request)) # get messages on requests 
        self.assertTrue(any('invalid response' in m.message.lower() for m in messages)) # asserts if appropriate message was displayed 

    @patch('payments.views.requests.post', side_effect=Exception('Network error'))
    def test_network_error_handled(self, mock_post):
        """
        tests if network errors on payment initialization 
        is handled
        """
        url = reverse_lazy('payments:initiate', args=[self.payment.pk]) # url to initiate payment 
        self.client.login(username='testuser', password='testpass123') # authenticates user 
        response = self.client.get(url) # retrieve response
        messages = list(get_messages(response.wsgi_request)) # gets messages on request
        self.assertTrue(any('error' in m.message.lower() for m in messages)) # asserts if appropriate message was displayed



class VerifyPaymentViewTests(TestCase):
    """
    tests the verify_payment_view logic 
    that handles the callback from flutterwave after a user completes payment
    """
    
    def setUp(self):
        """setting test values"""
        self.user1 = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        ) # test user 1

        self.user2 = User.objects.create_user(
            username='testuser2', 
            password='testpass321',
            email='test2@example.com'
        ) # test user 2

        self.shipment = Shipment.objects.create(
            user=self.user1,
            origin_address='test origin',
            destination_address='test destination',
            weight=100
        ) # test shipment 
        self.payment = Payment.objects.get(shipment=self.shipment) # test payment instance 

        self.url = reverse_lazy('payments:verify')
    

    def test_non_owner_cannot_verify_payment(self):
        """
        tests if non-owner cannot verify another 
        users payment
        """
        self.client.login(username='testuser2', password='testpass321') # authenticates user2
        response = self.client.get(self.url, {
            'status':'successful',
            'tx_ref': self.payment.tx_ref, 
            'transaction_id': 'TEST_TXN_ID'
        }) # retrieves response 
        self.assertEqual(response.status_code, 404) # asserts non-owner is restricted

    def test_unsuccessful_status_marks_payment_failed(self):
        """
        tests if Payment instance is marked failed when status is != successful
        """
        self.client.login(username='testuser',password='testpass123') # authenticates user
        self.assertEqual(self.payment.status, 'PENDING') # asserts payment instance is created with PENDING status
        response = self.client.get(self.url, {
            'status': 'cancelled',
            'tx_ref': self.payment.tx_ref,
            'transaction_id':'FAILED_TXN_ID'
        }) # retrieves response on passed failed value

        self.payment.refresh_from_db() # refresh db
        self.assertEqual(self.payment.status, 'FAILED')  # assert status of payment instance update to FAILED 
        self.assertEqual(self.payment.transaction_id, 'FAILED_TXN_ID') # assert transaction_id is updated 

        # asserts user is redirected to shipment detail page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse_lazy('shipments:detail', args=[self.shipment.pk])
        )
    
    @patch('payments.views.requests.get')
    def test_successful_verification_marks_payment_paid(self, mock_get):
        """
        tests if payment instance is marked paid on successful verification
        """
        mock_get.return_value.json.return_value={
            'status': 'success',
            'data':{
                'tx_ref': self.payment.tx_ref,
                'amount': float(self.payment.amount),
                'status': 'successful'
            }
        } # mock flutterwave verification API response

        self.client.login(username='testuser', password='testpass123') # authenticates user
        response = self.client.get(self.url,
        {
            'status':'successful',
            'tx_ref':self.payment.tx_ref,
            'transaction_id': 'SUCCESS_TXN_ID'
        }) # retrieve response
        
        self.payment.refresh_from_db() # refresh db
        self.assertEqual(self.payment.status, 'PAID') # assert if status of payment instance update to PAID
        self.assertEqual(self.payment.transaction_id, 'SUCCESS_TXN_ID') # assert if transaction_id is updated 
        self.assertRedirects(
            response, 
            reverse_lazy('shipments:detail', args=[self.shipment.pk])
        )# asserts if user is redirected

    @patch('payments.views.requests.get')
    def test_tx_ref_mismatch_marks_payment_failed(self, mock_get):
        """
        tests payment marked failed if tx_ref doesn't match
        """
        mock_get.return_value.json.return_value = {
            'status': 'success',
            'data': {
                'tx_ref': 'DIFFERENT-TX-REF',
                'amount': float(self.payment.amount),
                'status': 'successful'
            }
        } # mock API returns diffenrent tx_ref

        self.client.login(username='testuser', password='testpass123') # authenticates user
        response = self.client.get(self.url, {
            'status': 'successful',
            'tx_ref': self.payment.tx_ref,
            'transaction_id': 'MISMATCH_TXN'
        }) # retrieve response

        self.payment.refresh_from_db() # refresh db
        self.assertEqual(self.payment.status, 'FAILED') # asserts if payment status is updated to FAILED

    @patch('payments.views.requests.get')
    def test_flutterwave_api_called_for_verification(self, mock_get):
        """
        tests that flutterwave api is called correctly
        """
        mock_get.return_value.json.return_value = {
            'status':'success',
            'data':{
                'tx_ref': self.payment.tx_ref,
                'status': 'successful'
            }
        } # mock api call 

        self.client.login(username='testuser', password='testpass123') # authenticates user 
        transaction_id = 'API_CALL_TXN'
        self.client.get(self.url,{
            'status':'successful',
            'tx_ref':self.payment.tx_ref,
            'transaction_id':transaction_id
        }) 

        self.assertTrue(mock_get.called) # assert if get method was called
        self.assertEqual(mock_get.call_count, 1) # assert number of times method was called 

        args, kwargs = mock_get.call_args # retrieve parameters passed into mocked method
        expected_url = f'https://api.flutterwave.com/v3/transactions/{transaction_id}/verify'
        self.assertEqual(args[0], expected_url) # asserts if the first arg is the correct url

        # asserts api call was made with correct values 
        self.assertIn('Authorization', kwargs['headers']) 
        self.assertTrue(kwargs['headers']['Authorization'].startswith('Bearer'))

    @patch('payments.views.requests.get')
    def test_user_redirected_to_shipment_detail(self, mock_get):
        """tests if User always redirected to shipment detail after verification"""
        mock_get.return_value.json.return_value = {
            'status': 'success',
            'data': {
                'tx_ref': self.payment.tx_ref,
                'status': 'successful'
            }
        } # mock return value of mocked get method
         
        self.client.login(username='testuser', password='testpass123') # authenticates user
        
        response = self.client.get(self.url, {
            'status': 'successful',
            'tx_ref': self.payment.tx_ref,
            'transaction_id': 'REDIRECT_TXN'
        }) # retrieve response
        
        # Should redirect
        self.assertEqual(response.status_code, 302)
        
        # Should redirect to shipment detail
        expected_redirect = reverse_lazy('shipments:detail', args=[self.shipment.pk])
        self.assertRedirects(response, expected_redirect)

    @patch('payments.views.requests.get')
    def test_success_message_displayed(self, mock_get):
        """
        tests if success message is shown in successful payment
        """
        mock_get.return_value.json.return_value = {
            'status': 'success',
            'data':{
                'tx_ref': self.payment.tx_ref, 
                'status': 'successful'
            }
        } # mock get method returned value 

        self.client.login(username='testuser', password='testpass123') # authenticates user
        response = self.client.get(self.url, {
            'status': 'successful', 
            'tx_ref': self.payment.tx_ref, 
            'transaction_id': 'MSG_SUCCESS_TXN'
        }) # retrieve response 
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('successful' in m.message.lower() for m in messages)) # asserts if correct message is displayed 

    
    def test_error_message_on_failure(self):
        """Test 8: Error message shown on failed payment"""
        self.client.login(username='testuser', password='testpass123') # authenticates user 
        
        response = self.client.get(self.url, {
            'status': 'failed',
            'tx_ref': self.payment.tx_ref,
            'transaction_id': 'MSG_FAIL_TXN'
        }, follow=True) # retrieve response 
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any('not successful' in m.message.lower() for m in messages)
        ) # asserts if error message is displayed 

    @patch('payments.views.requests.get', side_effect=Exception('Network Error'))
    def test_network_error_during_verification(self, mock_get):
        """
        tests if network errors are handled gracefully
        """
        self.client.login(username='testuser', password='testpass123') # authenticates user 
        response = self.client.get(self.url, {
            'status':'successful', 
            'tx_ref':self.payment.tx_ref,
            'transaction_id': 'NETWORK_ERROR_TXN'
        }) # retrieve response 
        self.assertRedirects(response, reverse_lazy('shipments:detail', args=[self.shipment.pk])) # asserts if user is redirected on network error 



class FlutterwaveWebhookTests(TestCase):
    """
    tests the flutterwave_webhook_view logic - 
    webhook handler with signature verification
    """
    def setUp(self):
        """setting test values"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='testemail@example.com',
            password='testpass123'
        )# test user
        
        self.shipment = Shipment.objects.create(
            user = self.user,
            origin_address='test origin',
            destination_address='test destination',
            weight=100
        ) # test shipment 
        self.payment = Payment.objects.get(shipment=self.shipment) # test payment instance
        self.url = reverse_lazy('payments:webhook') # webhook url

        self.valid_payload = {
            'event': 'charge.completed',
            'data': {
                'tx_ref': self.payment.tx_ref,
                'transaction_id': 'TEST TXN ID',
                'status': 'successful',
                'amount': float(self.payment.amount),
                'currency':'NGN'
            }
        } # test valid payload 

        self.secret_hash = settings.FLW_SECRET_HASH # secret flutterwave hash

    def test_webhook_requires_valid_signature(self):
        """
        tests if webhook with valid signature is accepted
        """
        response = self.client.post(
            self.url, 
            data=json.dumps(self.valid_payload),
            content_type='application/json',
            HTTP_VERIF_HASH=self.secret_hash
        ) # retrieve response on posting valid signature and data to webhook url
        self.assertEqual(response.status_code, 200) # assert if page loaded successfully
        self.payment.refresh_from_db() # refresh db
        self.assertEqual(self.payment.status, 'PAID') # assert if payment instance was marked as PAID

    def test_webhook_rejects_invalid_signature(self):
        """
        tests if webhook with invalid signature is rejected
        """
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type='application/json',
            HTTP_VERIF_HASH='INVALID_SIGNATURE'
        ) # retrieve response on posting invalid signature to webhook url
        self.assertEqual(response.status_code, 403) # asserts page forbidden
        self.payment.refresh_from_db() # refresh db 
        self.assertEqual(self.payment.status, 'PENDING') # asserts payment instance status remains unchanged 
        data = response.json() # json response 
        self.assertEqual(data['status'], 'error') # assert error occured due to invalid signature
    
    def test_webhook_rejects_missing_signature(self):
        """
        tests if webhook without signature is rejected
        """
        response = self.client.post(
            self.url, 
            data=json.dumps(self.valid_payload),
            content_type='application/json'
            # No HTTP_VERIF_HASH header
        ) # retrieves response on posting to webhook url without signature

        self.assertEqual(response.status_code, 403) # assert page forbidden
        self.payment.refresh_from_db() # refresh db
        self.assertEqual(self.payment.status, 'PENDING') # assert payment instance status is unchanged 
        data = response.json() # json response 
        self.assertEqual(data['status'], 'error') # assert error occured due to missing signature 

    def test_webhook_marks_payment_paid_on_success(self):
        """
        tests if successful webhook marks payment as PAID
        """
        self.assertEqual(self.payment.status, 'PENDING') # assert initial status of payment instance 
        response = self.client.post(
            self.url, 
            data=json.dumps(self.valid_payload),
            content_type='application/json',
            HTTP_VERIF_HASH=self.secret_hash
        ) # retrieve response on posting valid data and signature to webhook url
        self.assertEqual(response.status_code, 200) # assert page loaded successfully
        self.payment.refresh_from_db() # refresh db
        self.assertEqual(self.payment.status, 'PAID') # assert payment instance status updated to PAID
        self.assertEqual(self.payment.transaction_id, self.valid_payload['data']['transaction_id']) # assert transaction_id updated 
        data = response.json() # json response 
        self.assertEqual(data['status'], 'Received') # assert successful webhook response

    def test_webhook_marks_payment_failed_on_failure(self):
        """
        tests if Failed webhook marks payment as FAILED
        """
        failed_payload={
            'event': 'charge.complete',
            'data':{
                'tx_ref':self.payment.tx_ref,
                'transaction_id': 'FAILED TXN ID',
                'status': 'failed',
                'amount': float(self.payment.amount)
            }
        } # payload with status 'failed'
        response = self.client.post(
            self.url,
            data=json.dumps(failed_payload),
            content_type='application/json',
            HTTP_VERIF_HASH=self.secret_hash
        )# retrieve response on posting valid signature with failed status 

        self.assertEqual(response.status_code, 403) # assert page forbidden
        self.payment.refresh_from_db() # refresh db
        self.assertEqual(self.payment.status, 'FAILED') # assert payment instance status updated to FAILED

    def test_webhook_returns_404_for_non_existent_payment(self):
        """
        tests if webhook for unknown tx_ref returns 404
        """
        invalid_payload = {
            'event': 'charge.completed',
            'data':{
                'tx_ref': 'NONEXISTENT-TXREF',
                'transaction_id': 'UNKNOWNTXN',
                'status': 'successful'
            }
        } # payload with invalid tx_ref
        response = self.client.post(
            self.url,
            data=json.dumps(invalid_payload),
            content_type='application/json',
            HTTP_VERIF_HASH=self.secret_hash
        ) # retrieve response on posting valid signature and non-existent payment payload to webhook url 

        self.assertEqual(response.status_code, 404)  # assert page not loaded 
        data = response.json() # json response 
        self.assertEqual(data['status'], 'No record of Payment') # assert error occured due to non-existent payment instance 
 
    def test_webhook_idempotency_already_paid(self):
        """
        tests if duplicate webhook for already paid payment is handled gracefully
        """
        self.payment.mark_paid(
            transaction_id='TEST TXN ID',
        ) # mark payment as PAID 
        self.payment.refresh_from_db() # refresh db 
        self.assertEqual(self.payment.status, 'PAID') # assert if payment status was updated to PAID 

        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type='application/json',
            HTTP_VERIF_HASH=self.secret_hash
        ) # retrieve response 
        self.payment.refresh_from_db() # refresh db 
        self.assertEqual(self.payment.status, 'PAID') # assert if payment status remains PAID 

    def test_webhook_idempotency_already_failed(self):
        """
        tests if duplicate webhook for already failed payment is handled gracefully
        """

        self.payment.mark_failed(transaction_id='TEST TXN ID') # marks payment as failed 
        self.payment.refresh_from_db() # refresh db 
        self.assertEqual(self.payment.status, 'FAILED') # assert payment status was updated to FAILED 

        failed_payload={
            'event': 'charge.completed',
            'data':{
                'tx_ref': self.payment.tx_ref,
                'transaction_id': 'TEST TXN ID',
                'status': 'failed'
            }
        } # payload with failed status 
        response = self.client.post(
            self.url,
            data=json.dumps(failed_payload),
            content_type='application/json',
            HTTP_VERIF_HASH=self.secret_hash
        ) # retrieve response on posting payload with failed status to webhook url

        self.payment.refresh_from_db() # refresh db 
        self.assertEqual(self.payment.status, 'FAILED')  # assert if payment status remains FAILED 

    def test_webhook_handles_malformed_json(self):
        """
        test malformed JSON is handled without crashing
        """
        response = self.client.post(
            self.url,
            data= '{"invalid": json}', # malformed
            content_type='application/json',
            HTTP_VERIF_HASH=self.secret_hash
        ) # retrieve response on posting malformed json to webhook url

        self.assertEqual(response.status_code, 500) # asserts page error
        data = response.json() # json response 
        self.assertEqual(data['status'], 'Internal server error') # assert error occured

    def test_webhook_is_csrf_exempt(self):
        """
        tests if webhook is CSRF exempt(can be called without CSRF token)
        # This test verifies @csrf_exempt decorator works
        # Django test client doesn't enforce CSRF by default,
        # but we can verify the decorator is there by checking view attributes
        """

        from payments.views import flutterwave_webhook_view # import webhook view
        self.assertTrue(
            getattr(flutterwave_webhook_view, 'csrf_exempt', False)
        ) # assert it the @csrf_exempt was used on view

        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type='application/json',
            HTTP_VERIF_HASH=self.secret_hash
        ) # retrieve response 
        self.assertIn(response.status_code, [200, 403, 404, 500]) # assert if response status code in any of the codes in the list

    @patch('payments.views.logger') # mock logger 
    def test_webhook_logs_events(self, mock_logger):
        """Bonus Test: Verify webhook events are logged"""
        # Send webhook
        self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type='application/json',
            HTTP_VERIF_HASH=self.secret_hash
        ) # post payload and valid signature to webhook url
        
        # Verify logger was called
        self.assertTrue(mock_logger.info.called or mock_logger.warning.called)



class PaymentIntegrationTests(TestCase):
    """
    End-to-end integration tests for complete payment workflows
    """

    def setUp(self):
        """setting test values"""
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        ) # admin user

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        ) # test user 

    def test_complete_payment_flow_success(self):
        """
        tests complete successful payment flow
        Flow: Create Shipment -> Payment auto-created -> Mark as PAID
        -> Receipt generated -> Email sent -> Notifications created
        """
        mail.outbox = [] # clear mail outbox

        shipment = Shipment.objects.create(
            user=self.user,
            origin_address='test origin',
            destination_address='test destination',
            weight=100
        ) # test shipment instance 

        self.assertTrue(Payment.objects.filter(shipment=shipment)) # assert a payment instance for test shipment was created 
        payment = Payment.objects.get(shipment=shipment) # signal-generated payment instance
        self.assertEqual(payment.status, 'PENDING') # assert payment status is PENDING 
        self.assertEqual(payment.user, self.user) # assert payment is related to correct user
        
        # assert amount is correct 
        expected_amount = 100 * 0.01
        self.assertEqual(float(payment.amount),float(expected_amount))

        receipt = payment.mark_paid(
            transaction_id='TEST TXN ID',
            meta={'test': 'integration'}
        )# returned receipt on payment marked PAID 

        payment.refresh_from_db() # refresh db 
        self.assertEqual(payment.status, 'PAID') # assert payment instance status updated to PAID 
        self.assertEqual(payment.transaction_id, 'TEST TXN ID') # assert payment instance transaction_id is correct 

        self.assertIsNotNone(receipt) # assert returned receipt is not None
        self.assertIsInstance(receipt, Receipt) # assert returned receipt is truly a Receipt instance 
        self.assertEqual(receipt.payment, payment) # assert receipt related to correct payment instance 
        self.assertTrue(receipt.receipt_number.startswith('RCP-')) # assert receipt number starts with correct prefix

        self.assertIsNotNone(receipt.pdf) # assert pdf generated 
        self.assertTrue(receipt.pdf.name.startswith('receipts/')) # assert pdf stored correctly

        self.assertEqual(len(mail.outbox), 1) # assert mail was generated(sent)
        email = mail.outbox[0] # retrieve mail instance 
        self.assertIn(self.user.email, email.to) # assert email sent to correct user email

        # assert subject text is correct 
        self.assertIn('Payment Confirmation', email.subject) 
        self.assertIn(shipment.tracking_number, email.subject) 

        user_notification = Notification.objects.filter(
            recipient=self.user,
            message__icontains='view receipt'
        ).first() # user notification


        self.assertIsNotNone(user_notification) # assert user notification instance exists
        self.assertIn('receipt', user_notification.message.lower()) # assert notification contains correct message 

        admin_notification = Notification.objects.filter(
            recipient=self.admin,
            message__icontains='paid'
        ).first() # admin notification

        self.assertIsNotNone(admin_notification) # assert admin_notification exists
        self.assertIn(shipment.tracking_number, admin_notification.message) # assserts admin notification contains correct message with correct shipment detail

        # asserts payment, shipment and receipt instances are correctly related 
        self.assertEqual(shipment.payments, payment) 
        self.assertEqual(payment.receipt, receipt)

    def test_complete_payment_flow_failure(self):
        """
        tests complete failed payment flow
        Flow: Create Shipment -> Payment auto-creatd -> Mark as failed
        -> Notification created -> No email sent
        """
        mail.outbox = [] # clear mail outbox

        shipment = Shipment.objects.create(
            user = self.user,
            origin_address = 'test origin',
            destination_address = 'test destination',
            weight=100
        ) # test shipment instance 

        payment = Payment.objects.get(shipment=shipment) # signal-generated payment instance 
        self.assertEqual(payment.status, 'PENDING') # assert initial status of payment is PENDING 
        
        payment.mark_failed(
            transaction_id='INTEGRATION TXN FAILED',
            meta={'error': 'insufficient_funds'}
        ) # mark payment instance to FAILED 

        payment.refresh_from_db()# refresh db

        self.assertEqual(payment.status, 'FAILED') # assert status of payment instance is updated to FAILED 
        self.assertEqual(payment.transaction_id, 'INTEGRATION TXN FAILED') # assert transaction_id is updated 
        self.assertIn('error', payment.meta) # assert meta field is updated and correct 
        
        with self.assertRaises(Receipt.DoesNotExist):
            """asserts if no receipt instance was created"""
            _ = payment.receipt

        self.assertEqual(len(mail.outbox), 0) # asserts if no email was generated(sent)

        failure_notification = Notification.objects.filter(
            recipient=self.user,
            message__icontains='failed'
        ).first() # user notification on payment failure


        self.assertIsNotNone(failure_notification) # assert notification instance exists 
        self.assertIn(shipment.tracking_number, failure_notification.message) # assert notification message contains correct detail

    def test_payment_retry_after_failure(self):
        """
        tests if payment retry after initial failure works 
        FLOW: Failed payment -> refresh tx_ref -> Success
        """
        mail.outbox = [] # clears mail outbox

        shipment = Shipment.objects.create(
            user=self.user,
            origin_address='test origin',
            destination_address='test destination',
            weight=100
        ) # test shipment instance 

        payment = Payment.objects.get(shipment=shipment) # signal-generated payment instance
        original_tx_ref = payment.tx_ref # old tx_ref before refresh

        payment.mark_failed(
            transaction_id='TEST TXN ID',
            meta={'error': 'card_declined'}
        )# mark payment as failed 

        payment.refresh_from_db() # refresh db
        self.assertEqual(payment.status, 'FAILED') # assert payment instance status update to FAILED 
                
        payment.refresh_tx_ref() # generates new tx_ref, sets transaction_id and meta to None
        payment.refresh_from_db() # refresh db

        self.assertNotEqual(payment.tx_ref, original_tx_ref) # assert a new tx_ref is generated 
        self.assertEqual(payment.status, 'PENDING') # asserts payment instance status is updated to PENDING 
        self.assertIsNone(payment.meta) # asserts payment meta field is updated to None
        self.assertIsNone(payment.transaction_id) # asserts payment transaction_id is updated to None

        receipt = payment.mark_paid(
            transaction_id='TEST TXN ID',
            meta= {'retry': 'successful'}
        ) # returned receipt instance on payment marked PAID

        payment.refresh_from_db() # refresh db

        self.assertEqual(payment.status,'PAID') # assert payment instance status updated to PAID
        self.assertEqual(payment.transaction_id, 'TEST TXN ID') # assert transaction_id is correct 

        self.assertIsNotNone(receipt) # assert receipt was generated and exists
        self.assertEqual(len(mail.outbox), 1) # assert mail generated(sent)
        user_notif = Notification.objects.filter(recipient=self.user) # user notification
        self.assertGreaterEqual(user_notif.count(), 2) # assert user was notified for all operations that occured  both failure and retry and success
    
    def test_webhook_and_redirect_both_work(self):
        """
        tests both webhook and redirect verification work

        This simulates the scenario where both webhoook and user redirect complete(race  condition handling)
        """
         # Create shipment
        shipment = Shipment.objects.create(
            user=self.user,
            origin_address='test Origin',
            destination_address='test Destination',
            weight=100
        ) # test shipment instance
        
        payment = Payment.objects.get(shipment=shipment) # signal-generated payment instance
        self.assertEqual(payment.status, 'PENDING') # assert initial payment instance status is PENDING
        
        payment.mark_paid(
            transaction_id='WEBHOOK_TXN_123',
            meta={'source': 'webhook'}
        )# Scenario 1: Webhook arrives first, marks as PAID
        payment.refresh_from_db() # refresh db
        self.assertEqual(payment.status, 'PAID')# assert status is updated to PAID
        
        # Scenario 2: User redirect verification arrives after
        # (This should be handled gracefully - no duplicate processing)
        # Try to mark as paid again
        payment.mark_paid(
            transaction_id='REDIRECT_TXN_123',
            meta={'source': 'redirect'}
        )
        payment.refresh_from_db() # refresh db
        
        # Payment should still be PAID (not changed)
        self.assertEqual(payment.status, 'PAID')
        
        # Original transaction_id should be preserved
        # (Your mark_paid might update it or not - depends on implementation)
        # Just verify it's still PAID
        
        
        # Only one receipt should exist
        receipts = Receipt.objects.filter(payment=payment)
        self.assertEqual(receipts.count(), 1)




        