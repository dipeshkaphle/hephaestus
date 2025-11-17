"""
Test empty structural types and their relationship with Object in TypeScript.

Key TypeScript behavior to test:
1. Empty interfaces are mutual subtypes with Object and {}
2. Empty interfaces are SUPERTYPES of all object types (anything can be assigned to them)
3. Empty interfaces CANNOT be assigned to types with required members
4. Multiple empty interfaces are mutual subtypes of each other
5. Primitive types AND their literal types are assignable to empty interfaces
"""
import pytest
from src.ir import types as tp
from src.ir.typescript_types import (
    ObjectType, ObjectLowercaseType, StringType, NumberType,
    BooleanType, NumberLiteralType, StringLiteralType,
    BooleanLiteralType, BigIntegerType, SymbolType,
    ArrayType, FunctionType,
    TypeScriptBuiltinFactory
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

    def test_non_empty_structural_subtype_of_object(self):
        """Non-empty structural types (classes with fields) should be subtypes of Object"""
        person = tp.SimpleClassifier(
            name="Person",
            structural=True,
            field_signatures=[
                tp.FieldInfo("name", StringType()),
                tp.FieldInfo("age", NumberType())
            ],
            method_signatures=[],
            is_complete=True
        )
        obj = ObjectType()

        # Person <: Object (all class instances are subtypes of Object)
        assert person.is_subtype(obj), "Person should be subtype of Object"

    def test_object_not_subtype_of_non_empty_structural(self):
        """Object should NOT be subtype of non-empty structural types"""
        person = tp.SimpleClassifier(
            name="Person",
            structural=True,
            field_signatures=[
                tp.FieldInfo("name", StringType()),
                tp.FieldInfo("age", NumberType())
            ],
            method_signatures=[],
            is_complete=True
        )
        obj = ObjectType()

        # Object is NOT a subtype of Person (Object lacks required fields)
        assert not obj.is_subtype(person), "Object should NOT be subtype of Person"


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

    def test_string_type_subtype_of_empty(self):
        """String <: Empty should be True (TypeScript structural typing)"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        string_type = StringType()

        # In TypeScript, primitive types (string, number, boolean) are assignable
        # to empty interfaces because empty interfaces have no structural requirements
        assert string_type.is_subtype(empty), "String should be subtype of Empty (TS behavior)"

    def test_number_type_subtype_of_empty(self):
        """Number <: Empty should be True (TypeScript structural typing)"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        number_type = NumberType()

        # Primitives are assignable to empty interfaces in TypeScript
        assert number_type.is_subtype(empty), "Number should be subtype of Empty (TS behavior)"

    def test_boolean_type_subtype_of_empty(self):
        """Boolean <: Empty should be True (TypeScript structural typing)"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        boolean_type = BooleanType()

        # Primitives are assignable to empty interfaces in TypeScript
        assert boolean_type.is_subtype(empty), "Boolean should be subtype of Empty (TS behavior)"

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

        # Empty doesn't have String's specific type identity
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

        # Empty doesn't have Number's specific type identity
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

        # Empty doesn't have Boolean's specific type identity
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


class TestLiteralTypesVsEmptyStructural:
    """Test that literal types are assignable to empty interfaces"""

    def test_number_literal_subtype_of_empty(self):
        """NumberLiteral(42) <: Empty should be True"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        num_lit = NumberLiteralType(42)

        # Literal types should be assignable to empty interfaces
        assert num_lit.is_subtype(empty), \
            "NumberLiteralType should be subtype of Empty"

    def test_string_literal_subtype_of_empty(self):
        """StringLiteral("foo") <: Empty should be True"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        str_lit = StringLiteralType("foo")

        assert str_lit.is_subtype(empty), \
            "StringLiteralType should be subtype of Empty"

    def test_boolean_literal_subtype_of_empty(self):
        """BooleanLiteral(true) <: Empty should be True"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        bool_lit = BooleanLiteralType(True)

        assert bool_lit.is_subtype(empty), \
            "BooleanLiteralType should be subtype of Empty"

    def test_bigint_subtype_of_empty(self):
        """BigInt <: Empty should be True"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        bigint = BigIntegerType()

        assert bigint.is_subtype(empty), \
            "BigIntegerType should be subtype of Empty"

    def test_symbol_subtype_of_empty(self):
        """Symbol <: Empty should be True"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        symbol = SymbolType()

        assert symbol.is_subtype(empty), \
            "SymbolType should be subtype of Empty"


class TestParameterizedTypesVsEmptyStructural:
    """Test that parameterized types (Array, Function) are assignable to empty interfaces"""

    def test_array_number_subtype_of_empty(self):
        """Array<number> <: Empty should be True"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        array_constructor = ArrayType()
        array_of_number = array_constructor.new([NumberType()])

        assert array_of_number.is_subtype(empty), \
            "Array<number> should be subtype of Empty"

    def test_array_string_subtype_of_empty(self):
        """Array<string> <: Empty should be True"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        array_constructor = ArrayType()
        array_of_string = array_constructor.new([StringType()])

        assert array_of_string.is_subtype(empty), \
            "Array<string> should be subtype of Empty"

    def test_array_subtype_of_object(self):
        """Array<T> <: Object should be True"""
        array_constructor = ArrayType()
        array_of_number = array_constructor.new([NumberType()])
        obj = ObjectType()

        assert array_of_number.is_subtype(obj), \
            "Array<number> should be subtype of Object"

    def test_function_subtype_of_empty(self):
        """Function<Args, Return> <: Empty should be True"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        # Function with 1 argument: (String) => Number
        # FunctionType(1) creates type params [A1, R]
        func_constructor = FunctionType(1)
        func_type = func_constructor.new([StringType(), NumberType()])

        assert func_type.is_subtype(empty), \
            "Function<String, Number> should be subtype of Empty"

    def test_function_subtype_of_object(self):
        """Function<Args, Return> <: Object should be True"""
        func_constructor = FunctionType(2)
        func_type = func_constructor.new([StringType(), NumberType(), BooleanType()])
        obj = ObjectType()

        assert func_type.is_subtype(obj), \
            "Function should be subtype of Object"

    def test_nested_array_subtype_of_empty(self):
        """Array<Array<number>> <: Empty should be True"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        array_constructor = ArrayType()
        inner_array = array_constructor.new([NumberType()])
        nested_array = array_constructor.new([inner_array])

        assert nested_array.is_subtype(empty), \
            "Array<Array<number>> should be subtype of Empty"


class TestVarianceWithStructuralTypes:
    """Test that variance rules work correctly with structural types"""

    def test_array_covariance_with_empty(self):
        """Array<number> <: Array<Empty> via covariance"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        array_constructor = ArrayType()

        # Array<number>
        array_of_number = array_constructor.new([NumberType()])

        # Array<Empty> - represented as parameterized type with Empty
        array_of_empty = array_constructor.new([empty])

        # Since number <: Empty, and Array is covariant,
        # Array<number> <: Array<Empty>
        assert array_of_number.is_subtype(array_of_empty), \
            "Array<number> should be subtype of Array<Empty> via covariance"

    def test_nested_array_covariance(self):
        """Array<Array<number>> <: Array<Array<Empty>> via double covariance"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        array_constructor = ArrayType()

        # Array<Array<number>>
        inner_number = array_constructor.new([NumberType()])
        nested_number = array_constructor.new([inner_number])

        # Array<Array<Empty>>
        inner_empty = array_constructor.new([empty])
        nested_empty = array_constructor.new([inner_empty])

        # Double covariance: Array<Array<number>> <: Array<Array<Empty>>
        assert nested_number.is_subtype(nested_empty), \
            "Array<Array<number>> should be subtype of Array<Array<Empty>>"

    def test_structural_type_with_array_field(self):
        """Structural type with Array<number> field accepts Array<NumberLiteral>"""
        # Interface with array field
        interface_with_array = tp.SimpleClassifier(
            name="HasArrayField",
            structural=True,
            field_signatures=[
                tp.FieldInfo("arr", ArrayType().new([NumberType()]))
            ],
            method_signatures=[],
            is_complete=True
        )

        # Object with Array<NumberLiteral(42)>
        obj_with_literal_array = tp.SimpleClassifier(
            name="ObjWithLiteralArray",
            structural=True,
            field_signatures=[
                tp.FieldInfo("arr", ArrayType().new([NumberLiteralType(42)]))
            ],
            method_signatures=[],
            is_complete=True
        )

        # NumberLiteral(42) <: Number, and Array is covariant,
        # so Array<NumberLiteral(42)> <: Array<Number>
        # Therefore obj should be subtype of interface
        assert obj_with_literal_array.is_subtype(interface_with_array), \
            "Object with Array<NumberLiteral> should satisfy interface requiring Array<Number>"

    def test_array_of_empty_accepts_array_of_primitives(self):
        """Array<Empty> accepts Array<number>, Array<string>, etc."""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        array_constructor = ArrayType()
        array_of_empty = array_constructor.new([empty])

        # All these should be subtypes via covariance
        array_of_number = array_constructor.new([NumberType()])
        array_of_string = array_constructor.new([StringType()])
        array_of_boolean = array_constructor.new([BooleanType()])

        assert array_of_number.is_subtype(array_of_empty), \
            "Array<number> should be subtype of Array<Empty>"
        assert array_of_string.is_subtype(array_of_empty), \
            "Array<string> should be subtype of Array<Empty>"
        assert array_of_boolean.is_subtype(array_of_empty), \
            "Array<boolean> should be subtype of Array<Empty>"

    def test_function_covariance_in_return_with_empty(self):
        """Function returning number can be assigned to function returning Empty"""
        empty = tp.SimpleClassifier(
            name="Empty",
            structural=True,
            field_signatures=[],
            method_signatures=[],
            is_complete=True
        )

        # Function1<Arg, Return> has 2 type params: [A1 (contravariant), R (covariant)]
        func_constructor = FunctionType(1)

        # () => number (using Empty as dummy arg type for simplicity)
        func_returns_number = func_constructor.new([empty, NumberType()])

        # () => Empty
        func_returns_empty = func_constructor.new([empty, empty])

        # Since number <: Empty, and return is covariant,
        # (() => number) <: (() => Empty)
        assert func_returns_number.is_subtype(func_returns_empty), \
            "Function returning number should be subtype of function returning Empty"
