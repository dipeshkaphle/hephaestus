
import unittest
from src.ir.typescript_types import AliasType, ObjectType, NumberType, StringType

class TestAliasSubtyping(unittest.TestCase):

    def test_alias_subtyping(self):
        number_type = NumberType()
        string_type = StringType()
        object_type = ObjectType()
        
        # Create an alias to a NumberType
        number_alias = AliasType(number_type, "NumberAlias")

        # The alias should be a subtype of NumberType
        self.assertTrue(number_alias.is_subtype(number_type))

        # The alias should be a subtype of ObjectType
        self.assertTrue(number_alias.is_subtype(object_type))

        # The alias should NOT be a subtype of StringType
        self.assertFalse(number_alias.is_subtype(string_type))

if __name__ == '__main__':
    unittest.main()
