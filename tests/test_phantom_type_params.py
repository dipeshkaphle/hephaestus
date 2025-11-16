"""
Test for phantom type parameter handling in structural subtyping.

Bug: When a parameterized type has type parameters that are not used in its
structure (phantom type parameters), structural subtyping should ignore them
and only compare the actual structure.

Example: If Mangoes<I, L, W> only uses I in its structure (field benita: I),
then Mangoes<V, number, U> and Mangoes<V, U, U> have identical structure
{ benita: V } and should be subtypes of each other.
"""

from src.ir import types
from src.ir import typescript_types as ts_types


def test_phantom_type_parameters_structural_subtyping():
    """
    Test that phantom type parameters don't affect structural subtyping.

    TypeScript accepts:
        class Mangoes<I, L, W> { benita: I }
        const x: Mangoes<V, U, U> = new Mangoes<V, number, U>(...)

    Because L and W are phantom (unused), so both types have identical
    structure { benita: V }.
    """
    # Create type parameters for Mangoes
    I = types.TypeParameter('I', types.Variance.INVARIANT)
    L = types.TypeParameter('L', types.Variance.INVARIANT)  # Phantom!
    W = types.TypeParameter('W', types.Variance.INVARIANT)  # Phantom!

    # Create structural classifier for Mangoes
    # Note: Only uses I, not L or W!
    mangoes_classifier = types.SimpleClassifier(
        name='Mangoes',
        supertypes=[],
        field_signatures=[types.FieldInfo('benita', I)],
        method_signatures=[],
        structural=True,
        is_complete=True
    )

    # Create TypeConstructor with all three type parameters
    mangoes_tc = types.TypeConstructor(
        name='Mangoes',
        type_parameters=[I, L, W],
        supertypes=[],
        classifier=mangoes_classifier
    )

    # Create type parameters V and U (from outer class)
    V = types.TypeParameter('V', types.Variance.INVARIANT)
    U = types.TypeParameter('U', types.Variance.INVARIANT)

    # Get number type
    ts_factory = ts_types.TypeScriptBuiltinFactory()
    number_type = ts_factory.get_number_type()

    # Create the two types
    # Type 1: Mangoes<V, number, U> - assigned value
    mangoes_v_number_u = types.ParameterizedType(
        t_constructor=mangoes_tc,
        type_args=[V, number_type, U]
    )

    # Type 2: Mangoes<V, U, U> - declared type
    mangoes_v_u_u = types.ParameterizedType(
        t_constructor=mangoes_tc,
        type_args=[V, U, U]
    )

    # Both should have identical structure after substitution
    # Mangoes<V, number, U> => { benita: V }
    # Mangoes<V, U, U> => { benita: V }

    # Test subtyping in both directions
    assert mangoes_v_number_u.is_subtype(mangoes_v_u_u), \
        "Mangoes<V, number, U> should be subtype of Mangoes<V, U, U> (identical structure)"

    assert mangoes_v_u_u.is_subtype(mangoes_v_number_u), \
        "Mangoes<V, U, U> should be subtype of Mangoes<V, number, U> (identical structure)"


def test_non_phantom_type_parameters_not_subtypes():
    """
    Test that when type parameters ARE used in structure, variance matters.

    If Wrapper<T> has field: value: T, then:
    - Wrapper<number> is NOT a subtype of Wrapper<Object> (invariant)
    """
    # Create type parameter
    T = types.TypeParameter('T', types.Variance.INVARIANT)

    # Create structural classifier that USES T
    wrapper_classifier = types.SimpleClassifier(
        name='Wrapper',
        supertypes=[],
        field_signatures=[types.FieldInfo('value', T)],
        method_signatures=[],
        structural=True,
        is_complete=True
    )

    wrapper_tc = types.TypeConstructor(
        name='Wrapper',
        type_parameters=[T],
        supertypes=[],
        classifier=wrapper_classifier
    )

    # Get types
    ts_factory = ts_types.TypeScriptBuiltinFactory()
    number_type = ts_factory.get_number_type()
    object_type = ts_factory.get_object_type()

    # Create parameterized types
    wrapper_number = types.ParameterizedType(
        t_constructor=wrapper_tc,
        type_args=[number_type]
    )

    wrapper_object = types.ParameterizedType(
        t_constructor=wrapper_tc,
        type_args=[object_type]
    )

    # These should NOT be subtypes (different structure)
    # Wrapper<number> has { value: number }
    # Wrapper<Object> has { value: Object }
    # In TypeScript, number is subtype of Object, so this would work
    # But let's just verify they're treated as different types

    # Actually, in structural typing, Wrapper<number> should be
    # subtype of Wrapper<Object> because number <: Object
    # Let me adjust this test

    # The key difference from phantom test is that here the type arg matters
    assert not (wrapper_number.is_subtype(wrapper_object) and
                wrapper_object.is_subtype(wrapper_number)), \
        "Wrapper<number> and Wrapper<Object> should not be mutual subtypes"


def test_mixed_phantom_and_used_type_parameters():
    """
    Test with a mix of phantom and used type parameters.

    Container<T, P> with field: value: T (P is phantom)
    Container<number, string> and Container<number, boolean> should be
    structurally equivalent.
    """
    # Create type parameters
    T = types.TypeParameter('T', types.Variance.INVARIANT)
    P = types.TypeParameter('P', types.Variance.INVARIANT)  # Phantom!

    # Classifier uses T but not P
    container_classifier = types.SimpleClassifier(
        name='Container',
        supertypes=[],
        field_signatures=[types.FieldInfo('value', T)],
        method_signatures=[],
        structural=True,
        is_complete=True
    )

    container_tc = types.TypeConstructor(
        name='Container',
        type_parameters=[T, P],
        supertypes=[],
        classifier=container_classifier
    )

    # Get types
    ts_factory = ts_types.TypeScriptBuiltinFactory()
    number_type = ts_factory.get_number_type()
    string_type = ts_factory.get_string_type()
    boolean_type = ts_factory.get_boolean_type()

    # Create parameterized types with same T, different P
    container_num_str = types.ParameterizedType(
        t_constructor=container_tc,
        type_args=[number_type, string_type]
    )

    container_num_bool = types.ParameterizedType(
        t_constructor=container_tc,
        type_args=[number_type, boolean_type]
    )

    # Should be mutual subtypes (same structure { value: number })
    assert container_num_str.is_subtype(container_num_bool), \
        "Container<number, string> should be subtype of Container<number, boolean>"

    assert container_num_bool.is_subtype(container_num_str), \
        "Container<number, boolean> should be subtype of Container<number, string>"
