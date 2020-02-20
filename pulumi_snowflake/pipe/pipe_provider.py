from typing import Tuple

from .. import Client
from ..baseprovider import BaseDynamicProvider
from ..provider import Provider


class PipeProvider(BaseDynamicProvider):
    """
    Dynamic provider for Snowflake Pipe resources.
    """

    def __init__(self, provider_params: Provider, connection_provider: Client):
        super().__init__(provider_params, connection_provider, logging_name="Pipe")

    def generate_sql_create_statement(self, name, inputs, environment):
        template = environment.from_string(
"""CREATE PIPE {{ full_name }}
{% if auto_ingest is boolean %}AUTO_INGEST = {{ auto_ingest | sql }}
{% endif %}
{%- if aws_sns_topic %}AWS_SNS_TOPIC = {{ aws_sns_topic | sql }}
{% endif %}
{%- if integration %}INTEGRATION = {{ integration | sql }}
{% endif %}
{%- if comment %}COMMENT = {{ comment | sql }}
{% endif -%}
AS {{ code }}
""")

        sql = template.render({
            "full_name": self._get_full_object_name(inputs, name),
            **inputs
        })

        return sql

    def generate_sql_drop_statement(self, name, inputs, environment):
        template = environment.from_string("DROP PIPE {{ full_name }}")
        sql = template.render({
            "full_name": self._get_full_object_name(inputs, name)
        })
        return sql
