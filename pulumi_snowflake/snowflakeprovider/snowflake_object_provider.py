from abc import ABC, abstractmethod
from typing import List

from pulumi.dynamic import ResourceProvider, CreateResult

from pulumi_snowflake import SnowflakeConnectionProvider
from pulumi_snowflake.snowflakeprovider import SnowflakeObjectAttribute
from pulumi_snowflake.validation import Validation
from pulumi_snowflake.random_id import RandomId


class SnowflakeObjectProvider(ResourceProvider, ABC):
    """
    Generic base class for a Pulumi dynamic provider which manages Snowflake objects using a SQL connection.  Objects
    are described by passing in the SQL name of the object (e.g., "STORAGE INTEGRATION) and a list of attributes
    represented as `SnowflakeObjectAttribute` instances.  This class then automatically handles the create, delete and
    diff methods by generating and executing the appropriate SQL commands.

    This class cannot be instantiated directly.  There are a couple of methods which are abstract to account
    for slight differences in the way objects are created (specifically, whether they are scoped to a schema or
    to the account).  Overriding classes should implement two methods: `generate_sql_create_header` and
    `generate_outputs`.  There are two subclasses already written, named GloballyScopedObjectProvider and
    SchemaScopedObjectProvider.
    """

    def __init__(self,
                 connection_provider: SnowflakeConnectionProvider,
                 sql_name: str,
                 attributes: List[SnowflakeObjectAttribute]):
        self.connection_provider = connection_provider
        self.sql_name = sql_name
        self.attributes = attributes
        Validation.validate_object_name(sql_name)


    @abstractmethod
    def generate_sql_create_header(self, name, inputs):
        """
        This method should be overridden by subclasses to return the first line of the SQL CREATE statement for this
        object; for example, "CREATE STORAGE INTEGRATION {name}".
        """
        pass

    @abstractmethod
    def generate_outputs(self, name, inputs, outs):
        """
        This method should be overridden by subclasses to modify the Pulumi outputs which are returned by the create
        method.  The `outs` parameter already contains an output for each of the attributes, so at least
        these values should included in the return value.
        """
        pass

    def create(self, inputs):

        # Validate inputs
        self._check_required_attributes(inputs)
        validated_name = self._get_validated_autogenerated_name(inputs)
        attributes_with_values = list(filter(lambda a: inputs.get(a.name) is not None, self.attributes))

        # Perform SQL command to create object
        sql_statements = self._generate_sql_create_statement(attributes_with_values, validated_name, inputs)
        sql_bindings = self._generate_sql_create_bindings(attributes_with_values, inputs)
        self._execute_sql(sql_statements, sql_bindings)

        # Generate outputs from attributes.  Provisional because the call to generate_outputs below allows subclasses to
        # modify them if necessary.
        provisional_outputs = {
            "name": validated_name,
            **self._generate_outputs_from_attributes(inputs)
        }

        return CreateResult(
            id_=validated_name,
            outs=self.generate_outputs(validated_name, inputs,provisional_outputs)
        )

    def _check_required_attributes(self, inputs):
        """
        Raises an exception if a required attribute (including one of "name" or "resource_name") is not given
        """
        for attribute in self.attributes:
            if attribute.is_required() and inputs[attribute.name] is None:
                raise Exception(f"Required input attribute '{attribute.name}' is not present")
        if inputs.get("name") is None and inputs.get("resource_name") is None:
            raise Exception("At least one of 'name' or 'resource_name' must be provided")

    def _get_validated_autogenerated_name(self, inputs):
        """
        If an object name is not provided, autogenerates one from the resource name, and validates the name.
        """
        name = inputs.get("name")

        if name is None:
            name = f'{inputs["resource_name"]}_{RandomId.generate(7)}'

        return Validation.validate_identifier(name)

    def _generate_outputs_from_attributes(self, inputs):
        """
        Creates an outputs dictionary which has the value of every attribute.
        """
        outputs = {a.name: inputs.get(a.name) for a in self.attributes}
        return outputs

    def _generate_sql_create_statement(self, attributesWithValues, validated_name, inputs):
        """
        Generates the SQL statement which creates the object
        """
        statements = [
            self.generate_sql_create_header(validated_name, inputs),
            *list(map(lambda a: a.generate_sql(inputs.get(a.name)), attributesWithValues))
        ]
        return statements

    def _generate_sql_create_bindings(self, attributesWithValues, inputs):
        """
        Generates the list of binding values for all attributes
        """
        bindingTuplesList = list(map(lambda a: a.generate_bindings(inputs.get(a.name)), attributesWithValues))
        bindingTuplesList = filter(lambda t: t is not None, bindingTuplesList)
        bindings = [item for sublist in bindingTuplesList for item in sublist]
        return bindings

    def _execute_sql(self, statement, bindings):
        """
        Creates a connection, executes a SQL statement, and closes the connection.
        :param List[str] statement: A single SQL statement represented as an array of lines
        :param bindings: The values for bindings which should be substituted into placeholders in the SQL statement
        """
        connection = self.connection_provider.get()
        cursor = connection.cursor()
        try:
            cursor.execute('\n'.join(statement), (*bindings,))
        finally:
            cursor.close()
        connection.close()