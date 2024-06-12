from datetime import datetime
from enum import unique
from pyexpat import model
from turtle import mode
from django.db import models
from Term.models import Terms

from Users.models import MyUser

# Create your models here.


# class StkPayments

class Invoices(models.Model):
    date = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=200)
    amount = models.PositiveIntegerField()
    balance = models.PositiveIntegerField(default=0)
    description = models.TextField(max_length=1000)
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.user)
    

    

class InvoicePayments(models.Model):
    date = models.DateTimeField(auto_now=True)
    processed_at = models.CharField(max_length=100, null=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    mode = models.CharField(max_length=100)
    amount = models.PositiveIntegerField()
    balance = models.PositiveIntegerField()
    invoice = models.ForeignKey(Invoices, on_delete=models.CASCADE)
    user_account = models.CharField(max_length=100)
    

    def __str__(self):
        return str(self.invoice.user)


# class InvoicePayments(models.Model):
#     date = models.DateTimeField(auto_now=True)
#     invoice = models.ForeignKey(Invoices, on_delete=models.CASCADE)
#     transaction = models.ForeignKey(RawInvoicePayments, null=True, on_delete=models.CASCADE)

#     def __str__(self):
#         return str(self.invoice.received_from) + ' ' + str(self.transaction.amount)

# class RawSalaryPayments(models.Model):
    # date = models.DateTimeField(auto_now=True)
    # transaction_id = models.CharField(max_length=100, unique=True)
    # amount = models.PositiveIntegerField()
    # user_account = models.CharField(max_length=100)
    # institution = models.CharField(max_length=100)

    # def __str__(self):
    #     return str(self.user_account)
    
class ProcessedSalaries(models.Model):
    date = models.DateTimeField(auto_now=True)
    processed_at = models.CharField(max_length=100, null=True)
    transaction_id = models.CharField(max_length=100, null=True,unique=True)
    mode = models.CharField(max_length=100)
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()
    balance = models.PositiveIntegerField()
    user_account = models.CharField(max_length=100, null=True)
    

    def __str__(self):
        return str(self.user.email)



    

class TermFeeStructure(models.Model):
    term = models.ForeignKey(Terms, on_delete=models.CASCADE)
    grade = models.PositiveIntegerField()
    amount = models.PositiveIntegerField()

    def __str__(self):
            return str(self.term.year) + ' ' + str(self.term.term) + ' ' + str(self.grade)
    
class RawFeePayment(models.Model):
    receipt = models.CharField(max_length=100, unique=True)
    adm_no = models.CharField(max_length=10, null=True)
    amount = models.PositiveIntegerField()
    mode = models.CharField(max_length=10)
    account = models.CharField(max_length=100, null=True)
    msdn = models.CharField(max_length=15, null=True)
    processed_at = models.CharField(max_length=100)
    date = models.DateField(auto_now=True)
    status = models.BooleanField(default=False)
    def __str__(self):
            return str(self.receipt)


   
    

    
class StudentFeePayment(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    transaction_id = models.ForeignKey(RawFeePayment, on_delete=models.CASCADE)
    balance = models.IntegerField()
    date = models.DateTimeField(auto_now=True)

    def __str__(self):
            return str(self.user)
    
    
class Expenses(models.Model):
    title  = models.CharField(max_length=100)
    description = models.TextField(max_length=1000)
    date = models.DateField(auto_now=True)
    amount = models.PositiveIntegerField()
    mode = models.CharField(max_length=100)


    def __str__(self) :
        return str(self.title) + ' ' + str(self.amount)

