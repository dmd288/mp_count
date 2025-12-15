from django.db import models
from django.contrib.auth.models import User


class ImportFile(models.Model):
    """File imported from Wildberries (Excel or API)"""
    
    SOURCE_CHOICES = [
        ('WB_STOCKS_EXCEL', 'WB Stocks Excel'),
        ('WB_REPORT_EXCEL', 'WB Report Excel'),
        ('WB_API', 'WB API'),
    ]
    
    STATUS_CHOICES = [
        ('UPLOADED', 'Uploaded'),
        ('PARSED', 'Parsed'),
        ('APPLIED', 'Applied'),
        ('ERROR', 'Error'),
    ]
    
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='wb_imports/%Y/%m/%d/')
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wb_import_files'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UPLOADED')
    error_log = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.original_filename} ({self.get_source_display()}) - {self.get_status_display()}"
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['status', 'uploaded_at']),
        ]


class ImportRow(models.Model):
    """Individual row from an import file"""
    
    import_file = models.ForeignKey(
        ImportFile,
        on_delete=models.CASCADE,
        related_name='rows'
    )
    row_number = models.IntegerField()
    raw_json = models.JSONField()
    errors = models.JSONField(blank=True, null=True)
    
    def __str__(self):
        return f"Row {self.row_number} from {self.import_file.original_filename}"
    
    class Meta:
        ordering = ['import_file', 'row_number']
        indexes = [
            models.Index(fields=['import_file', 'row_number']),
        ]


class WBProduct(models.Model):
    """Wildberries product reference"""
    
    nm_id = models.BigIntegerField(unique=True, db_index=True)
    vendor_code = models.CharField(max_length=255, db_index=True)
    title = models.CharField(max_length=500, blank=True)
    brand = models.CharField(max_length=255, blank=True)
    subject = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"{self.vendor_code} (nm_id: {self.nm_id})"
    
    class Meta:
        ordering = ['vendor_code']
        indexes = [
            models.Index(fields=['vendor_code']),
        ]


class WBBarcode(models.Model):
    """Barcode for a Wildberries product"""
    
    wb_product = models.ForeignKey(
        WBProduct,
        on_delete=models.CASCADE,
        related_name='barcodes'
    )
    tech_size = models.CharField(max_length=100, blank=True)
    barcode = models.CharField(max_length=255, unique=True, db_index=True)
    
    def __str__(self):
        return f"{self.barcode} ({self.wb_product.vendor_code})"
    
    class Meta:
        ordering = ['wb_product', 'barcode']
        indexes = [
            models.Index(fields=['barcode']),
        ]


class WBStockSnapshot(models.Model):
    """Snapshot of stock levels from Wildberries"""
    
    loaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    import_file = models.ForeignKey(
        ImportFile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_snapshots'
    )
    warehouse_name = models.CharField(max_length=255, blank=True)
    nm_id = models.BigIntegerField(db_index=True)
    vendor_code = models.CharField(max_length=255, blank=True, db_index=True)
    barcode = models.CharField(max_length=255, db_index=True)
    tech_size = models.CharField(max_length=100, blank=True)
    quantity = models.IntegerField(default=0)
    in_way_to_client = models.IntegerField(default=0)
    in_way_from_client = models.IntegerField(default=0)
    quantity_full = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.vendor_code} - {self.barcode} (qty: {self.quantity}) at {self.loaded_at}"
    
    class Meta:
        ordering = ['-loaded_at', 'vendor_code', 'barcode']
        indexes = [
            models.Index(fields=['loaded_at']),
            models.Index(fields=['nm_id', 'barcode']),
            models.Index(fields=['vendor_code']),
        ]
