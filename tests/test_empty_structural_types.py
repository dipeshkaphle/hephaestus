"""
Test empty structural types and their relationship with Object in TypeScript.

Key TypeScript behavior to test:
1. Empty interfaces are mutual subtypes with Object and {}
2. Empty interfaces are SUPERTYPES of all object types (anything can be assigned to them)
3. Empty interfaces CANNOT be assigned to types with required members
4. Multiple empty interfaces are mutual subtypes of each other
"""
import pytest
from src.ir import types as tp
from src.ir.typescript_types import (
    ObjectType, ObjectLowercaseType, StringType, NumberType,
    BooleanType, TypeScriptBuiltinFactory
)


@pytest.fixture
def ts_factory():
    return TypeScriptBuiltinFactory()


class TestEmptyStructuralTypes:
    """Test empty structural types (interfaces/classes with no members)"""

    def test_empty_structural_is_complete(self):
        """Empty structural types should be marked as complete"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )
        assert tp.is_complete(empty)
        assert tp.is_structural_type(empty)

    def test_empty_structural_incomplete_during_generation(self):
        """Incomplete empty structural types should not be treated as complete"""
        incomplete_empty = tp.SimpleClassifier(
            name="IncompleteEmpty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=False
        )
        assert not tp.is_complete(incomplete_empty)
        assert tp.is_structural_type(incomplete_empty)


class TestEmptyStructuralVsObject:
    """Test the relationship between empty structural types and Object"""

    def test_empty_structural_subtype_of_object(self):
        """Empty <: Object should be True"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )
        obj = ObjectType()

        # Empty <: Object
        assert empty.is_subtype(obj), "Empty should be subtype of Object"

    def test_object_subtype_of_empty_structural(self):
        """Object <: Empty should be True (mutual subtyping)"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )
        obj = ObjectType()

        # Object <: Empty
        assert obj.is_subtype(empty), "Object should be subtype of Empty"

    def test_empty_structural_mutual_with_object_lowercase(self):
        """Empty and object (lowercase) should be mutual subtypes"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )
        obj_lower = ObjectLowercaseType()

        # Empty <: object and object <: Empty
        assert empty.is_subtype(obj_lower), "Empty should be subtype of object"
        assert obj_lower.is_subtype(empty), "object should be subtype of Empty"

    def test_two_empty_structurals_mutual_subtypes(self):
        """Two different empty structural types should be mutual subtypes"""
        empty1 = tp.SimpleClassifier(
            name="Empty1",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )
        empty2 = tp.SimpleClassifier(
            name="Empty2",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        # Empty1 <: Empty2 and Empty2 <: Empty1
        assert empty1.is_subtype(empty2), "Empty1 should be subtype of Empty2"
        assert empty2.is_subtype(empty1), "Empty2 should be subtype of Empty1"


class TestEmptyStructuralAsSupertype:
    """Test that empty structural types act as SUPERTYPES of object types"""

    def test_type_with_field_subtype_of_empty(self):
        """HasX <: Empty should be True"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        has_x = tp.SimpleClassifier(
            name="HasX",
            structural=True,
            field_signatures=[
                tp.FieldInfo("x", NumberType())
            ],
            method_signatures=[],
            is_complete=True
        )

        # HasX <: Empty (anything is subtype of empty requirement)
        assert has_x.is_subtype(empty), "Type with field should be subtype of Empty"

    def test_empty_NOT_subtype_of_type_with_field(self):
        """Empty <: HasX should be False"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        has_x = tp.SimpleClassifier(
            name="HasX",
            structural=True,
            field_signatures=[
                tp.FieldInfo("x", NumberType())
            ],
            method_signatures=[],
            is_complete=True
        )

        # Empty <: HasX should be False (Empty doesn't guarantee 'x' field)
        assert not empty.is_subtype(has_x), "Empty should NOT be subtype of type with field"

    def test_type_with_method_subtype_of_empty(self):
        """Type with method <: Empty should be True"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        has_method = tp.SimpleClassifier(
            name="HasMethod",
            structural=True,
            field_signatures=[],
            method_signatures=[
                tp.MethodInfo("foo", [], NumberType())
            ],
            is_complete=True
        )

        # HasMethod <: Empty
        assert has_method.is_subtype(empty), "Type with method should be subtype of Empty"

    def test_empty_NOT_subtype_of_type_with_method(self):
        """Empty <: HasMethod should be False"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        has_method = tp.SimpleClassifier(
            name="HasMethod",
            structural=True,
            field_signatures=[],
            method_signatures=[
                tp.MethodInfo("foo", [], NumberType())
            ],
            is_complete=True
        )

        # Empty <: HasMethod should be False
        assert not empty.is_subtype(has_method), "Empty should NOT be subtype of type with method"


class TestEmptyStructuralVsBuiltinTypes:
    """Test empty structural types vs TypeScript builtin types"""

    def test_string_type_NOT_subtype_of_empty(self):
        """String <: Empty should be False (String is a builtin, not structural)"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        string_type = StringType()

        # String has methods (charAt, etc.), but it's a builtin not a structural type
        # So String <: Empty should be False in our current system
        # (TypeScript allows it, but we model builtins differently)
        assert not string_type.is_subtype(empty), "String should NOT be subtype of Empty in our model"

    def test_empty_NOT_subtype_of_string(self):
        """Empty <: String should be False"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        string_type = StringType()

        # Empty doesn't have String's methods
        assert not empty.is_subtype(string_type), "Empty should NOT be subtype of String"

    def test_empty_NOT_subtype_of_number(self):
        """Empty <: Number should be False"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        number_type = NumberType()

        # Empty doesn't have Number's methods
        assert not empty.is_subtype(number_type), "Empty should NOT be subtype of Number"

    def test_empty_NOT_subtype_of_boolean(self):
        """Empty <: Boolean should be False"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        boolean_type = BooleanType()

        # Empty doesn't have Boolean's methods
        assert not empty.is_subtype(boolean_type), "Empty should NOT be subtype of Boolean"


class TestIncompleteEmptyStructural:
    """Test that incomplete empty structural types are NOT treated as equivalent to Object"""

    def test_incomplete_empty_NOT_subtype_of_object(self):
        """Incomplete Empty <: Object should be False during generation"""
        incomplete_empty = tp.SimpleClassifier(
            name="IncompleteEmpty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=False  # Still being generated
        )
        obj = ObjectType()

        # Incomplete empty types should not be treated as complete
        assert not incomplete_empty.is_subtype(obj), \
            "Incomplete empty should NOT be subtype of Object"

    def test_object_NOT_subtype_of_incomplete_empty(self):
        """Object <: Incomplete Empty should be False during generation"""
        incomplete_empty = tp.SimpleClassifier(
            name="IncompleteEmpty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=False
        )
        obj = ObjectType()

        # Object should not be subtype of incomplete types
        assert not obj.is_subtype(incomplete_empty), \
            "Object should NOT be subtype of incomplete Empty"


class TestEmptyStructuralWithInheritance:
    """Test empty structural types with inheritance"""

    def test_empty_with_object_supertype(self):
        """Empty structural type with Object as supertype"""
        obj = ObjectType()
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            supertypes=[obj],
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        # Empty <: Object (via nominal inheritance)
        assert empty.is_subtype(obj), "Empty with Object supertype should be subtype of Object"
        # Object <: Empty (via structural equivalence)
        assert obj.is_subtype(empty), "Object should be subtype of empty Empty"

    def test_empty_extending_empty(self):
        """One empty structural type extending another"""
        empty1 = tp.SimpleClassifier(
            name="Empty1",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        empty2 = tp.SimpleClassifier(
            name="Empty2",
            structural=True,
            supertypes=[empty1],
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        # Empty2 <: Empty1 (both nominal and structural)
        assert empty2.is_subtype(empty1), "Empty2 should be subtype of Empty1"
        # Empty1 <: Empty2 (structural equivalence)
        assert empty1.is_subtype(empty2), "Empty1 should be subtype of Empty2"


class TestParameterizedEmptyStructural:
    """Test parameterized types with empty structural classifiers"""

    def test_parameterized_empty_structural(self):
        """Test Foo<T> where Foo is an empty structural type"""
        # Create empty structural type constructor
        empty_classifier = tp.SimpleClassifier(
            name="EmptyGeneric",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        type_param = tp.TypeParameter("T")
        empty_constructor = tp.TypeConstructor(
            name="EmptyGeneric",
            type_parameters=[type_param],
            classifier=empty_classifier
        )

        # EmptyGeneric<String>
        empty_string = empty_constructor.new([StringType()])

        # EmptyGeneric<Number>
        empty_number = empty_constructor.new([NumberType()])

        # Both should be empty structurally, so they should be mutual subtypes
        assert empty_string.is_subtype(empty_number), \
            "EmptyGeneric<String> should be subtype of EmptyGeneric<Number>"
        assert empty_number.is_subtype(empty_string), \
            "EmptyGeneric<Number> should be subtype of EmptyGeneric<String>"

    def test_parameterized_empty_vs_object(self):
        """Test Foo<T> (empty) vs Object"""
        empty_classifier = tp.SimpleClassifier(
            name="EmptyGeneric",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        type_param = tp.TypeParameter("T")
        empty_constructor = tp.TypeConstructor(
            name="EmptyGeneric",
            type_parameters=[type_param],
            classifier=empty_classifier
        )

        empty_string = empty_constructor.new([StringType()])
        obj = ObjectType()

        # EmptyGeneric<String> <: Object
        assert empty_string.is_subtype(obj), \
            "EmptyGeneric<String> should be subtype of Object"
        # Object <: EmptyGeneric<String>
        assert obj.is_subtype(empty_string), \
            "Object should be subtype of EmptyGeneric<String>"


class TestEdgeCases:
    """Test edge cases and corner scenarios"""

    def test_nominal_empty_not_structural(self):
        """Nominal (non-structural) empty type should NOT be equivalent to Object"""
        nominal_empty = tp.SimpleClassifier(
            name="NominalEmpty",
            structural=False,  # Not structural
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )
        obj = ObjectType()

        # Nominal empty should NOT be treated the same as structural empty
        # It only has nominal subtyping
        assert not nominal_empty.is_subtype(obj), \
            "Nominal empty should NOT be subtype of Object (no inheritance)"
        assert not obj.is_subtype(nominal_empty), \
            "Object should NOT be subtype of nominal empty"

    def test_object_self_subtyping(self):
        """Object <: Object should be True"""
        obj1 = ObjectType()
        obj2 = ObjectType()

        assert obj1.is_subtype(obj2), "Object should be subtype of itself"

    def test_empty_self_subtyping(self):
        """Empty <: Empty (same instance) should be True"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        assert empty.is_subtype(empty), "Empty should be subtype of itself"
