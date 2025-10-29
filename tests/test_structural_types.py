from src.ir import types as tp
import src.ir.typescript_types as tst


def test_structural_classifier_basic_compatibility():
    """Test basic structural compatibility with same structure, different names"""
    # Create two types with the same structure but different names
    # Type A: { x: number, y: string }
    type_a = tp.StructuralClassifier(
        "A",
        field_signatures=[
            tp.FieldInfo("x", tst.NumberType()),
            tp.FieldInfo("y", tst.StringType())
        ]
    )

    # Type B: { x: number, y: string }
    type_b = tp.StructuralClassifier(
        "B",
        field_signatures=[
            tp.FieldInfo("x", tst.NumberType()),
            tp.FieldInfo("y", tst.StringType())
        ]
    )

    # Both should be subtypes of each other structurally
    assert type_a.is_subtype(type_b)
    assert type_b.is_subtype(type_a)


def test_structural_classifier_extra_fields():
    """Test that a type with extra fields is a subtype (more specific)"""
    # Type A: { x: number }
    type_a = tp.StructuralClassifier(
        "A",
        field_signatures=[tp.FieldInfo("x", tst.NumberType())]
    )

    # Type B: { x: number, y: string }
    type_b = tp.StructuralClassifier(
        "B",
        field_signatures=[
            tp.FieldInfo("x", tst.NumberType()),
            tp.FieldInfo("y", tst.StringType())
        ]
    )

    # B has more fields, so B <: A (more specific is subtype of less specific)
    assert type_b.is_subtype(type_a)
    # But A is NOT a subtype of B (missing field y)
    assert not type_a.is_subtype(type_b)


def test_structural_classifier_missing_fields():
    """Test that missing a required field fails subtyping"""
    # Type A: { x: number, y: string }
    type_a = tp.StructuralClassifier(
        "A",
        field_signatures=[
            tp.FieldInfo("x", tst.NumberType()),
            tp.FieldInfo("y", tst.StringType())
        ]
    )

    # Type B: { x: number }
    type_b = tp.StructuralClassifier(
        "B",
        field_signatures=[tp.FieldInfo("x", tst.NumberType())]
    )

    # B is missing field y, so B is NOT a subtype of A
    assert not type_b.is_subtype(type_a)


def test_structural_classifier_field_type_compatibility():
    """Test field type compatibility (covariant)"""
    # Type A: { x: object } (using object as top type)
    type_a = tp.StructuralClassifier(
        "A",
        field_signatures=[tp.FieldInfo("x", tst.ObjectType())]
    )

    # Type B: { x: string } (string <: object)
    type_b = tp.StructuralClassifier(
        "B",
        field_signatures=[tp.FieldInfo("x", tst.StringType())]
    )

    # B has more specific field type, so B <: A
    assert type_b.is_subtype(type_a)
    # But A is NOT a subtype of B (object is not <: string)
    assert not type_a.is_subtype(type_b)


def test_structural_classifier_method_basic():
    """Test basic method signature compatibility"""
    # Type A: { foo(number): string }
    type_a = tp.StructuralClassifier(
        "A",
        method_signatures=[tp.MethodInfo("foo", [tst.NumberType()], tst.StringType())]
    )

    # Type B: { foo(number): string }
    type_b = tp.StructuralClassifier(
        "B",
        method_signatures=[tp.MethodInfo("foo", [tst.NumberType()], tst.StringType())]
    )

    # Both should be subtypes of each other
    assert type_a.is_subtype(type_b)
    assert type_b.is_subtype(type_a)


def test_structural_classifier_method_return_covariance():
    """Test that method return types are covariant"""
    # Type A: { foo(): object }
    type_a = tp.StructuralClassifier(
        "A",
        method_signatures=[tp.MethodInfo("foo", [], tst.ObjectType())]
    )

    # Type B: { foo(): string } (string <: object)
    type_b = tp.StructuralClassifier(
        "B",
        method_signatures=[tp.MethodInfo("foo", [], tst.StringType())]
    )

    # B returns more specific type, so B <: A (covariant return)
    assert type_b.is_subtype(type_a)
    # But A is NOT a subtype of B
    assert not type_a.is_subtype(type_b)


def test_structural_classifier_method_param_contravariance():
    """Test that method parameters are contravariant"""
    # Type A: { foo(string): number }
    type_a = tp.StructuralClassifier(
        "A",
        method_signatures=[tp.MethodInfo("foo", [tst.StringType()], tst.NumberType())]
    )

    # Type B: { foo(object): number } (object >: string)
    type_b = tp.StructuralClassifier(
        "B",
        method_signatures=[tp.MethodInfo("foo", [tst.ObjectType()], tst.NumberType())]
    )

    # B accepts more general parameter, so B <: A (contravariant params)
    assert type_b.is_subtype(type_a)
    # But A is NOT a subtype of B
    assert not type_a.is_subtype(type_b)


def test_structural_classifier_missing_method():
    """Test that missing a required method fails subtyping"""
    # Type A: { foo(): number, bar(): string }
    type_a = tp.StructuralClassifier(
        "A",
        method_signatures=[
            tp.MethodInfo("foo", [], tst.NumberType()),
            tp.MethodInfo("bar", [], tst.StringType())
        ]
    )

    # Type B: { foo(): number }
    type_b = tp.StructuralClassifier(
        "B",
        method_signatures=[tp.MethodInfo("foo", [], tst.NumberType())]
    )

    # B is missing method bar, so B is NOT a subtype of A
    assert not type_b.is_subtype(type_a)
    # But A is a subtype of B (has all of B's methods)
    assert type_a.is_subtype(type_b)


def test_structural_classifier_method_wrong_param_count():
    """Test that different parameter counts make methods incompatible"""
    # Type A: { foo(number): string }
    type_a = tp.StructuralClassifier(
        "A",
        method_signatures=[tp.MethodInfo("foo", [tst.NumberType()], tst.StringType())]
    )

    # Type B: { foo(number, string): string }
    type_b = tp.StructuralClassifier(
        "B",
        method_signatures=[tp.MethodInfo("foo", [tst.NumberType(), tst.StringType()], tst.StringType())]
    )

    # Different parameter counts, not compatible
    assert not type_a.is_subtype(type_b)
    assert not type_b.is_subtype(type_a)


def test_structural_classifier_with_nominal_subtyping():
    """Test that nominal subtyping (inheritance) still works"""
    # Type A (base)
    type_a = tp.StructuralClassifier(
        "A",
        field_signatures=[tp.FieldInfo("x", tst.NumberType())]
    )

    # Type B extends A
    type_b = tp.StructuralClassifier(
        "B",
        supertypes=[type_a],
        field_signatures=[
            tp.FieldInfo("x", tst.NumberType()),
            tp.FieldInfo("y", tst.StringType())
        ]
    )

    # B should be a subtype of A both nominally and structurally
    assert type_b.is_subtype(type_a)


def test_structural_classifier_fields_and_methods():
    """Test structural compatibility with both fields and methods"""
    # Type A: { x: number, foo(): string }
    type_a = tp.StructuralClassifier(
        "A",
        field_signatures=[tp.FieldInfo("x", tst.NumberType())],
        method_signatures=[tp.MethodInfo("foo", [], tst.StringType())]
    )

    # Type B: { x: number, y: boolean, foo(): string, bar(): boolean }
    type_b = tp.StructuralClassifier(
        "B",
        field_signatures=[
            tp.FieldInfo("x", tst.NumberType()),
            tp.FieldInfo("y", tst.BooleanType())
        ],
        method_signatures=[
            tp.MethodInfo("foo", [], tst.StringType()),
            tp.MethodInfo("bar", [], tst.BooleanType())
        ]
    )

    # B has all of A's members plus more, so B <: A
    assert type_b.is_subtype(type_a)
    # But A is NOT a subtype of B
    assert not type_a.is_subtype(type_b)


def test_structural_vs_simple_classifier():
    """Test that StructuralClassifier and SimpleClassifier don't mix"""
    # Simple classifier (nominal only)
    simple = tp.SimpleClassifier("Simple")

    # Structural classifier
    structural = tp.StructuralClassifier(
        "Structural",
        field_signatures=[tp.FieldInfo("x", tst.NumberType())]
    )

    # No structural relationship (different type classes)
    assert not structural.is_subtype(simple)
    assert not simple.is_subtype(structural)
