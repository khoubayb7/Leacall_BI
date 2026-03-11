from django.contrib import admin

from .models import CampaignRecord, ClientDataSource, ETLRawRecord, ETLRun


@admin.register(ClientDataSource)
class ClientDataSourceAdmin(admin.ModelAdmin):
    list_display = ("client", "campaign_id", "campaign_name", "campaign_type", "is_active", "last_synced_at")
    list_filter = ("campaign_type", "is_active")
    search_fields = ("campaign_id", "campaign_name", "client__username")


@admin.register(ETLRun)
class ETLRunAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "data_source", "status", "raw_count", "transformed_count", "loaded_count", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("client__username", "error_message")
    readonly_fields = ("created_at",)


@admin.register(ETLRawRecord)
class ETLRawRecordAdmin(admin.ModelAdmin):
    list_display = ("run", "row_index", "created_at")


@admin.register(CampaignRecord)
class CampaignRecordAdmin(admin.ModelAdmin):
    list_display = ("data_source", "leacall_record_id", "updated_at")
    search_fields = ("leacall_record_id",)
    list_filter = ("data_source",)
