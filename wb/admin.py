from django.contrib import admin
from .models import ImportFile, ImportRow, WBProduct, WBBarcode, WBStockSnapshot


@admin.register(ImportFile)
class ImportFileAdmin(admin.ModelAdmin):
    list_display = (
        'original_filename',
        'source',
        'status',
        'uploaded_by',
        'uploaded_at',
        'row_count',
    )
    list_filter = ('status', 'source', 'uploaded_at')
    search_fields = ('original_filename', 'error_log')
    date_hierarchy = 'uploaded_at'
    readonly_fields = ('uploaded_at',)
    
    def row_count(self, obj):
        return obj.rows.count()
    row_count.short_description = 'Rows'


@admin.register(WBStockSnapshot)
class WBStockSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        'vendor_code',
        'nm_id',
        'barcode',
        'warehouse_name',
        'quantity',
        'quantity_full',
        'in_way_to_client',
        'in_way_from_client',
        'loaded_at',
    )
    list_filter = ('loaded_at', 'warehouse_name', 'nm_id', 'vendor_code')
    search_fields = ('vendor_code', 'nm_id', 'barcode')
    date_hierarchy = 'loaded_at'
    readonly_fields = ('loaded_at',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('import_file')


@admin.register(WBProduct)
class WBProductAdmin(admin.ModelAdmin):
    list_display = ('vendor_code', 'nm_id', 'brand', 'subject', 'title')
    list_filter = ('brand', 'subject')
    search_fields = ('vendor_code', 'nm_id', 'title', 'brand')
    readonly_fields = ('nm_id',)


@admin.register(WBBarcode)
class WBBarcodeAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'wb_product', 'tech_size')
    list_filter = ('tech_size',)
    search_fields = ('barcode', 'wb_product__vendor_code', 'wb_product__nm_id')
    readonly_fields = ('barcode',)


@admin.register(ImportRow)
class ImportRowAdmin(admin.ModelAdmin):
    list_display = ('import_file', 'row_number', 'has_errors')
    list_filter = ('import_file',)
    search_fields = ('import_file__original_filename',)
    readonly_fields = ('raw_json', 'errors')
    
    def has_errors(self, obj):
        return bool(obj.errors)
    has_errors.boolean = True
    has_errors.short_description = 'Has Errors'
