from ..client import Client
from ..provider import Provider
from ..baseprovider.base_dynamic_provider import BaseDynamicProvider


class TableProvider(BaseDynamicProvider):
    """
    Dynamic provider for Snowflake Table resources.
    """

    def __init__(self, provider_params: Provider, connection_provider: Client):
        super().__init__(provider_params, connection_provider, resource_type="Table")

    def generate_sql_create_statement(self, name, inputs, environment):
        template = environment.from_string(
"""CREATE{% if temporary %} TEMPORARY{% endif %} {{ resource_type | upper }} {{ full_name }}
{% if cluster_by -%}
CLUSTER BY ( {{ cluster_by | join(',') }} )
{% endif %}
{%- if data_retention_time_in_days %}DATA_RETENTION_TIME_IN_DAYS = {{ data_retention_time_in_days | sql }}
{% endif %}
{%- if comment %}COMMENT = {{ comment | sql }}
{% endif %}""")

        sql = template.render({
            "full_name": self._get_full_object_name(inputs, name),
            "resource_type": self.resource_type,
            **inputs
        })

        return sql

    def generate_sql_drop_statement(self, name, inputs, environment):
        template = environment.from_string("DROP {{ resource_type | upper }} {{ full_name }}")
        sql = template.render({
            "full_name": self._get_full_object_name(inputs, name),
            "resource_type": self.resource_type
        })
        return sql
