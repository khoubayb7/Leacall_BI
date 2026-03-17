from rest_framework import serializers

from .models import CampaignRecord, ClientDataSource, ETLRun


class ClientDataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientDataSource
        fields = [
            "id",
            "campaign_id",
            "campaign_name",
            "campaign_type",
            "api_endpoint",
            "record_id_field",
            "field_mapping",
            "is_active",
            "last_synced_at",
            "created_at",
        ]
        read_only_fields = ["id", "last_synced_at", "created_at"]


class ETLRunSyncTriggerSerializer(serializers.Serializer):
    data_source_id = serializers.IntegerField(
        help_text="PK of the ClientDataSource to sync."
    )


class ETLRunSerializer(serializers.ModelSerializer):
    data_source_name = serializers.CharField(
        source="data_source.campaign_name", read_only=True, default=""
    )
    client_username = serializers.CharField(
        source="client.username", read_only=True
    )

    class Meta:
        model = ETLRun
        fields = [
            "id",
            "data_source",
            "data_source_name",
            "client_username",
            "status",
            "started_at",
            "completed_at",
            "raw_count",
            "transformed_count",
            "loaded_count",
            "stats",
            "error_message",
            "created_at",
        ]
        read_only_fields = fields


class CampaignRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignRecord
        fields = [
            "id",
            "data_source",
            "leacall_record_id",
            "data",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
