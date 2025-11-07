"""
Test to verify the hypothesis about type parameter comparison bug in structural typing.

This test reproduces the bug found in bug #109 where the generator incorrectly
determines that Ranch<E, undefined, number> is a subtype of Ranch<Z, T, number>
when E, Z, and T are unrelated type parameters from different scopes.
"""
import pytest
from src.ir import types as tp
from src.ir import typescript_types as tst
from src.ir.typescript_types import UndefinedType


def test_type_parameters_from_different_scopes_should_not_match():
    """
    Test that type parameters from different scopes are not considered equal.

    Bug scenario from #109:
    - Brickbat<E, Z, T> has field: hence: Bronson<E, undefined, E>
    - Bronson<E, undefined, E> extends Ranch<E, undefined, number>
    - In Brickbat.proboscis(), we try: Ranch<Z, T, number> = this.hence
    - This should FAIL because E != Z and undefined != T
    """
    factory = tst.TypeScriptBuiltinFactory()

    # Create type parameters from different scopes
    E = tp.TypeParameter('E')  # From Brickbat scope (used in hence field)
    Z = tp.TypeParameter('Z')  # From Brickbat scope (used in local var)
    T = tp.TypeParameter('T')  # From Brickbat scope (used in local var)

    undefined_type = UndefinedType(primitive=False)
    number_type = factory.get_number_type()

    # Verify they're different objects
    assert E is not Z, "E and Z should be different objects"
    assert E is not T, "E and T should be different objects"

    # But they compare equal by name/bound if we don't track identity
    print(f"\nE == Z? {E == Z}")
    print(f"E: {E}, hash={hash(E)}, id={id(E)}")
    print(f"Z: {Z}, hash={hash(Z)}, id={id(Z)}")


def test_structural_subtyping_with_unrelated_type_params():
    """
    Test the actual bug: structural subtyping incorrectly allows unrelated type params.
    """
    factory = tst.TypeScriptBuiltinFactory()

    # Create type parameters
    E = tp.TypeParameter('E')
    Z = tp.TypeParameter('Z')
    T = tp.TypeParameter('T')
    undefined_type = UndefinedType(primitive=False)
    number_type = factory.get_number_type()

    # Create Ranch<Q, W, Z extends number> structural type constructor
    Q_param = tp.TypeParameter('Q')
    W_param = tp.TypeParameter('W')
    Z_param = tp.TypeParameter('Z', bound=number_type)

    ranch_classifier = tp.SimpleClassifier(
        name='Ranch',
        structural=True,
        field_signatures=[
            tp.FieldInfo('kelsey', Q_param),
            tp.FieldInfo('smothers', number_type),
        ],
        is_complete=True
    )
    # Ranch <Q,W,Z <: number >  = (kelsey: Q, smothers: number )
    ranch_constructor = tp.TypeConstructor(
        'Ranch',
        [Q_param, W_param, Z_param],
        classifier = ranch_classifier
    )

    # Create Bronson<U, J, T> structural type constructor that extends Ranch
    U_param = tp.TypeParameter('U')
    J_param = tp.TypeParameter('J')
    T_param = tp.TypeParameter('T')

    # Set up the inheritance: Bronson extends Ranch
    # Create Ranch<T_param, J_param, number> parameterized type as supertype template
    ranch_supertype = ranch_constructor.new([T_param, J_param, number_type])

    bronson_classifier = tp.SimpleClassifier(
        name='Bronson',
        structural=True,
        field_signatures=[
            tp.FieldInfo('smothers', number_type),
            tp.FieldInfo('gentlest', U_param),
        ],
        is_complete=True,
        supertypes=[ranch_supertype]
    )
    # Bronson <U,J,T> extends Ranch<Q=T,W=J, Z=number> = (smothers: number, gentlest: U, kelsey: T)
    bronson_constructor = tp.TypeConstructor(
        'Bronson',
        [U_param, J_param, T_param],
        classifier=bronson_classifier
    )


    # Create Bronson<E, undefined, E> (<: Ranch<E, undefined, number> ) = (smothers: number, gentlest : E, kelsey: E)
    bronson_E_undef_E = bronson_constructor.new([E, undefined_type, E])

    # Ranch <Q,W,Z>  = (kelsey: Q, smothers: number )
    # Create Ranch<Q=Z, W=T, Z=number> (what we're trying to assign to) = ( kelsey: Z, smothers : number )
    ranch_Z_T_num = ranch_constructor.new([Z, T, number_type])

    print("\n=== BUG TEST ===")
    print(f"Checking: Is Bronson<E, undefined, E> <: Ranch<Z, T, number>?")
    print(f"  Bronson extends Ranch<E, undefined, number>")
    print(f"  So really: Is Ranch<E, undefined, number> <: Ranch<Z, T, number>?")
    print(f"  Expected: False (E!=Z, undefined!=T)")

    result = bronson_E_undef_E.is_subtype(ranch_Z_T_num)
    print(f"  Actual result: {result}")

    # THIS IS THE BUG: It returns True when it should return False
    assert result == False, \
        "BUG CONFIRMED: Bronson<E, undefined, E> should NOT be subtype of Ranch<Z, T, number>"


def test_structural_classifier_substitution():
    """
    Test what happens when we create substituted structural classifiers.
    """
    factory = tst.TypeScriptBuiltinFactory()

    E = tp.TypeParameter('E')
    Z = tp.TypeParameter('Z')
    undefined_type = UndefinedType(primitive=False)
    number_type = factory.get_number_type()

    # Create a simple Ranch type
    Q_param = tp.TypeParameter('Q')
    ranch_classifier = tp.SimpleClassifier(
        name='Ranch',
        structural=True,
        field_signatures=[
            tp.FieldInfo('kelsey', Q_param),
        ],
        is_complete=True
    )
    ranch_constructor = tp.TypeConstructor(
        'Ranch',
        [Q_param],
        ranch_classifier
    )

    # Ranch<E>
    ranch_E = tp.ParameterizedType(ranch_constructor, [E])

    # Ranch<Z>
    ranch_Z = tp.ParameterizedType(ranch_constructor, [Z])

    print("\n=== Structural Classifier Substitution ===")

    # Get substituted classifiers
    from src.ir.types import _create_substituted_structural_classifier

    ranch_E_structural = _create_substituted_structural_classifier(ranch_E)
    ranch_Z_structural = _create_substituted_structural_classifier(ranch_Z)

    if ranch_E_structural and ranch_Z_structural:
        print(f"Ranch<E> structural fields: {[(f.name, str(f.field_type)) for f in ranch_E_structural.field_signatures]}")
        print(f"Ranch<Z> structural fields: {[(f.name, str(f.field_type)) for f in ranch_Z_structural.field_signatures]}")

        # The field types should be E and Z respectively
        e_field_type = ranch_E_structural.field_signatures[0].field_type
        z_field_type = ranch_Z_structural.field_signatures[0].field_type

        print(f"\nField type in Ranch<E>: {e_field_type} (id={id(e_field_type)})")
        print(f"Field type in Ranch<Z>: {z_field_type} (id={id(z_field_type)})")
        print(f"Are they the same object? {e_field_type is z_field_type}")
        print(f"Are they equal? {e_field_type == z_field_type}")

        # Now check structural subtyping
        structural_result = ranch_E_structural.is_subtype(ranch_Z_structural)
        print(f"\nIs Ranch<E> structurally <: Ranch<Z>? {structural_result}")
        print(f"Expected: False (E and Z are unrelated)")

        # Check what happens in field type comparison
        if structural_result:
            print("\nDEBUG: Checking why it returned True")
            print(f"  e_field_type.is_subtype(z_field_type): {e_field_type.is_subtype(z_field_type)}")
            print(f"  E has bound: {E.bound}")
            print(f"  Z has bound: {Z.bound}")


if __name__ == '__main__':
    print("Running structural typing bug tests...\n")

    print("=" * 80)
    print("TEST 1: Type parameters from different scopes")
    print("=" * 80)
    test_type_parameters_from_different_scopes_should_not_match()

    print("\n" + "=" * 80)
    print("TEST 2: Structural subtyping with unrelated type params")
    print("=" * 80)
    try:
        test_structural_subtyping_with_unrelated_type_params()
        print("\n✓ TEST PASSED (bug is fixed)")
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        print("BUG IS PRESENT")

    print("\n" + "=" * 80)
    print("TEST 3: Structural classifier substitution")
    print("=" * 80)
    test_structural_classifier_substitution()
