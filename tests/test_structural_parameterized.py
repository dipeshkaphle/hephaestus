"""
Tests for parameterized types with structural subtyping.

This test file explores whether we can combine:
1. Type parameters (generics) - TypeConstructor + ParameterizedType
2. Structural subtyping - StructuralClassifier

The goal is to test if we can have something like:
    class Box<T> { value: T }
where Box uses structural typing.
"""

from src.ir import types as tp
import src.ir.typescript_types as tst


def test_type_constructor_basic():
    """Verify TypeConstructor basics work"""
    t_param = tp.TypeParameter("T", tp.Invariant)
    box_constructor = tp.TypeConstructor("Box", [t_param])

    # Instantiate Box<number>
    box_of_numbers = box_constructor.new([tst.NumberType()])

    assert box_of_numbers.is_parameterized()
    assert box_of_numbers.name == "Box"
    assert len(box_of_numbers.type_args) == 1
    assert box_of_numbers.type_args[0] == tst.NumberType()


def test_parameterized_type_nominal_subtyping():
    """Test that ParameterizedType uses nominal subtyping by default"""
    # Create Box<T> and SubBox<T> where SubBox extends Box
    t_param = tp.TypeParameter("T", tp.Invariant)

    box_constructor = tp.TypeConstructor("Box", [t_param])
    box_of_numbers = box_constructor.new([tst.NumberType()])

    # Create SubBox<T> : Box<T>
    t_param2 = tp.TypeParameter("T", tp.Invariant)
    subbox_constructor = tp.TypeConstructor(
        "SubBox",
        [t_param2],
        supertypes=[box_constructor]
    )
    subbox_of_numbers = subbox_constructor.new([tst.NumberType()])

    # SubBox<number> might NOT be subtype of Box<number> with type constructors
    # because the type parameter T in SubBox is different from T in Box
    # Let's check what actually happens
    print(f"SubBox<number> <: Box<number>? {subbox_of_numbers.is_subtype(box_of_numbers)}")

    # But if we create another type with same structure, it's NOT a subtype
    other_box_constructor = tp.TypeConstructor("OtherBox", [t_param])
    other_box_of_numbers = other_box_constructor.new([tst.NumberType()])

    # Not subtypes (different type constructors, no inheritance)
    assert not other_box_of_numbers.is_subtype(box_of_numbers)
    assert not box_of_numbers.is_subtype(other_box_of_numbers)


def test_structural_classifier_as_type_constructor_base():
    """
    Test if we can use StructuralClassifier in a TypeConstructor's supertypes.

    Idea: Maybe we can create a non-generic StructuralClassifier and have
    a TypeConstructor inherit from it?
    """
    # Create a structural interface: IHasValue with field value: number
    has_value_interface = tp.StructuralClassifier(
        "IHasValue",
        field_signatures=[tp.FieldInfo("value", tst.NumberType())]
    )

    # Create a generic Box<T> that extends IHasValue (but this doesn't make sense
    # because IHasValue expects number, not T)
    t_param = tp.TypeParameter("T", tp.Invariant)
    box_constructor = tp.TypeConstructor(
        "Box",
        [t_param],
        supertypes=[has_value_interface]
    )

    # Create Box<number>
    box_of_numbers = box_constructor.new([tst.NumberType()])

    # Box<number> should be subtype of IHasValue nominally (via inheritance)
    assert box_of_numbers.is_subtype(has_value_interface)

    # But this doesn't help us - we want Box to be STRUCTURALLY checked
    # against other types with the same structure


def test_check_if_parameterized_type_has_field_signatures():
    """Check if ParameterizedType can have field_signatures attribute"""
    t_param = tp.TypeParameter("T", tp.Invariant)
    box_constructor = tp.TypeConstructor("Box", [t_param])
    box_of_numbers = box_constructor.new([tst.NumberType()])

    # Check if it has structural typing attributes
    has_field_sigs = hasattr(box_of_numbers, 'field_signatures')
    has_method_sigs = hasattr(box_of_numbers, 'method_signatures')

    print(f"ParameterizedType has field_signatures: {has_field_sigs}")
    print(f"ParameterizedType has method_signatures: {has_method_sigs}")

    # ParameterizedType inherits from SimpleClassifier, not StructuralClassifier
    # So it likely doesn't have these attributes
    assert not has_field_sigs
    assert not has_method_sigs


def test_attempt_structural_parameterized_hybrid():
    """
    Attempt to create a hybrid: a class that is both parameterized AND structural.

    This will likely fail because the class hierarchy doesn't support it.
    """
    # We'd want something like:
    # class StructuralParameterizedType(StructuralClassifier, ParameterizedType)

    # But both inherit from SimpleClassifier in incompatible ways
    # StructuralClassifier: takes field_signatures, method_signatures
    # ParameterizedType: takes t_constructor, type_args

    # Let's try to manually create what we'd want:
    t_param = tp.TypeParameter("T", tp.Invariant)

    # Create a TypeConstructor for Box
    box_constructor = tp.TypeConstructor("Box", [t_param])

    # Try to create Box<number> as a ParameterizedType
    box_of_numbers = box_constructor.new([tst.NumberType()])

    # Now try to manually add field signatures (monkey patching)
    # This is a hack to test if the structural is_subtype logic would work
    try:
        box_of_numbers.field_signatures = [
            tp.FieldInfo("value", tst.NumberType())
        ]
        box_of_numbers.method_signatures = []

        # Create another similar type
        container_constructor = tp.TypeConstructor("Container", [t_param])
        container_of_numbers = container_constructor.new([tst.NumberType()])
        container_of_numbers.field_signatures = [
            tp.FieldInfo("value", tst.NumberType())
        ]
        container_of_numbers.method_signatures = []

        # Now try structural subtyping
        # But ParameterizedType.is_subtype doesn't check field_signatures
        # It only checks type constructors and type arguments
        result = box_of_numbers.is_subtype(container_of_numbers)

        print(f"Structural subtype check result: {result}")

        # This will be False because ParameterizedType.is_subtype
        # doesn't implement structural checking
        assert not result

    except Exception as e:
        print(f"Error during monkey patching: {e}")
        raise


def test_current_limitation_summary():
    """
    Document the current limitation:

    - TypeConstructor + ParameterizedType: Supports generics, uses NOMINAL subtyping
    - StructuralClassifier: Supports structural subtyping, NO generics

    We CANNOT currently have both:
    - A generic type that uses structural subtyping

    Example we can't express:
        interface Box<T> { value: T }
        interface Container<T> { value: T }

        Box<number> should be structurally equivalent to Container<number>
    """

    # Setup test scenario
    t_param = tp.TypeParameter("T", tp.Invariant)

    box_constructor = tp.TypeConstructor("Box", [t_param])
    container_constructor = tp.TypeConstructor("Container", [t_param])

    box_of_numbers = box_constructor.new([tst.NumberType()])
    container_of_numbers = container_constructor.new([tst.NumberType()])

    # Even though they might have the same structure, they're not subtypes
    # because ParameterizedType uses nominal typing
    assert not box_of_numbers.is_subtype(container_of_numbers)
    assert not container_of_numbers.is_subtype(box_of_numbers)

    print("CONFIRMED: Cannot currently do structural subtyping with ParameterizedType")
