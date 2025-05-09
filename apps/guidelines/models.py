# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

class Trust(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=100)

    class Meta:
        managed = False
        db_table = 'tableapp_trust'


class Guideline(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=1025)
    description = models.TextField(blank=True, null=True)
    external_url = models.CharField(max_length=1025, blank=True, null=True)
    metadata = models.TextField(blank=True, null=True)
    medical_speciality = models.CharField(max_length=255, blank=True, null=True)
    trust = models.ForeignKey(Trust, models.DO_NOTHING)
    locality = models.CharField(max_length=255, blank=True, null=True)
    original_filename = models.CharField(max_length=1025, blank=True, null=True)
    viewcount = models.IntegerField(default=0)
    authors = models.CharField(max_length=1025, blank=True, null=True)
    creation_date = models.CharField(max_length=255, blank=True, null=True)
    review_date = models.CharField(max_length=255, blank=True, null=True)
    version_number = models.CharField(max_length=255, blank=True, null=True)
    last_updated_date = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tableapp_trustguideline'