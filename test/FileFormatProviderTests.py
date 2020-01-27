import unittest
from unittest.mock import Mock, call

from pulumi_snowflake.FileFormatProvider import FileFormatProvider
from pulumi_snowflake.FileFormatType import FileFormatType


class FileFormatProviderTests(unittest.TestCase):

    def testWhenCallCreateWithNameAndTypeThenSqlIsGenerated(self):
        mockCursor = Mock()
        mockConnectionProvider = self.getMockConnectionProvider(mockCursor)

        provider = FileFormatProvider(mockConnectionProvider)
        provider.create(self.getStandardInputs())

        mockCursor.execute.assert_has_calls([
            call(f"USE DATABASE {self.getStandardInputs()['database']}"),
            call("\n".join([
                f"CREATE FILE FORMAT {self.getStandardInputs()['name']}",
                f"TYPE = {FileFormatType.CSV}"
            ]))
        ])

    def testWhenCallCreateWithNameAndTypeThenOutputsAreReturned(self):
        mockCursor = Mock()
        mockConnectionProvider = self.getMockConnectionProvider(mockCursor)

        provider = FileFormatProvider(mockConnectionProvider)
        result = provider.create(self.getStandardInputs())

        self.assertDictEqual(result.outs, {
            "name": self.getStandardInputs()["name"],
            "type": self.getStandardInputs()["type"]
        })

    def testWhenCallCreateWithNameAndTypeThenDatabaseNameIsReturnedAsId(self):
        mockCursor = Mock()
        mockConnectionProvider = self.getMockConnectionProvider(mockCursor)

        provider = FileFormatProvider(mockConnectionProvider)
        result = provider.create(self.getStandardInputs())

        self.assertEqual(result.id, self.getStandardInputs()["database"])

    def testWhenCallCreateWithoutNameThenNameIsAutoGenerated(self):
        mockCursor = Mock()
        mockConnectionProvider = self.getMockConnectionProvider(mockCursor)

        provider = FileFormatProvider(mockConnectionProvider)
        result = provider.create({
            **self.getStandardInputs(),
            'name': None,
        })

        resourceName = self.getStandardInputs()["resource_name"]
        self.assertRegex(result.outs["name"], resourceName + '_[a-f,0-9]{7}')

    def testWhenGiveInvalidDbThenErrorThrown(self):
        mockConnectionProvider = self.getMockConnectionProvider(Mock())
        provider = FileFormatProvider(mockConnectionProvider)

        self.assertRaises(Exception, provider.create, {
            **self.getStandardInputs(),
            'database': 'invalid-db-name',
        })

    def testWhenGiveInvalidNameThenErrorThrown(self):
        mockConnectionProvider = self.getMockConnectionProvider(Mock())
        provider = FileFormatProvider(mockConnectionProvider)

        self.assertRaises(Exception, provider.create, {
            **self.getStandardInputs(),
            'name': 'invalid-format',
        })

    def testWhenGiveInvalidTypeThenErrorThrown(self):
        mockConnectionProvider = self.getMockConnectionProvider(Mock())
        provider = FileFormatProvider(mockConnectionProvider)

        self.assertRaises(Exception, provider.create, {
            **self.getStandardInputs(),
            'type': "C-SV"
        })

    def testWhenNoTypeGivenThenErrorThrown(self):
        mockConnectionProvider = self.getMockConnectionProvider(Mock())
        provider = FileFormatProvider(mockConnectionProvider)

        self.assertRaises(Exception, provider.create, {
            **self.getStandardInputs(),
            'type': None
        })

    def testWhenInvalidResourceNameGivenAndNameIsAutoGeneratedThenErrorThrown(self):
        mockConnectionProvider = self.getMockConnectionProvider(Mock())
        provider = FileFormatProvider(mockConnectionProvider)

        self.assertRaises(Exception, provider.create, {
            **self.getStandardInputs(),
            'name': None,
            'resource_name': 'invalid-name'
        })

    # HELPERS

    def getStandardInputs(self):
        return {
            'database': 'test_database_name',
            'type': FileFormatType.CSV,
            'resource_name': 'pulumi_test_file_format',
            'name': 'test_file_format',
            'snowflakeUsername': 'testUsername',
            'snowflakePassword': 'testPassword',
            'snowflakeAccountName': 'testAccountName',
        }

    def getMockConnectionProvider(self, mockCursor):
        mockConnection = Mock()
        mockConnection.cursor.return_value = mockCursor
        mockConnectionProvider = Mock()
        mockConnectionProvider.get.return_value = mockConnection
        return mockConnectionProvider