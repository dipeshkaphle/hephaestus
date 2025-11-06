"""
Simplified test to verify type parameter matching bug in structural typing.
"""
from src.ir import types as tp
from src.ir.typescript_types import UndefinedType, NumberType


def test_simple_case_different_type_params():
    """
    Simplified test: Ranch<E> should NOT be subtype of Ranch<Z>
    when E and Z are unrelated type parameters.
    """
    # Create two DIFFERENT type parameters
    E = tp.TypeParameter('E')
    Z = tp.TypeParameter('Z')

    print("\n=== Simple Test: Unrelated Type Parameters ===")
    print(f"E: id={id(E)}, hash={hash(E)}")
    print(f"Z: id={id(Z)}, hash={hash(Z)}")
    print(f"E == Z? {E == Z}")
    print(f"E is Z? {E is Z}")

    # Create a simple structural type Ranch<Q>
    Q_param = tp.TypeParameter('Q')
    ranch_classifier = tp.SimpleClassifier(
        name='Ranch',
        structural=True,
        supertypes=[],
        field_signatures=[
            tp.FieldInfo('kelsey', Q_param),  # field of type Q
        ],
        is_complete=True
    )
    ranch_constructor = tp.TypeConstructor(
        'Ranch',
        [Q_param],
        ranch_classifier
    )

    # Create Ranch<E>
    ranch_E = tp.ParameterizedType(ranch_constructor, [E])
    ranch_E.supertypes = []  # Ensure supertypes is a list

    # Create Ranch<Z>
    ranch_Z = tp.ParameterizedType(ranch_constructor, [Z])
    ranch_Z.supertypes = []  # Ensure supertypes is a list

    print(f"\nTest 1: Is Ranch<E> a subtype of Ranch<Z>?")
    print(f"  (Both have SAME constructor)")
    print(f"  Expected: False (E and Z are unrelated)")

    result = ranch_E.is_subtype(ranch_Z)
    print(f"  Actual: {result}")

    # IMPORTANT: When both have the same constructor, line 1089 checks:
    # if self.t_constructor == other.t_constructor
    # This means it uses variance checking, NOT structural checking!
    # So this test might not trigger the bug.

    # The REAL bug is when we have DIFFERENT constructors but both structural
    # Let's test that scenario

    if result:
        print("\n✗ BUG CONFIRMED: Ranch<E> should NOT be subtype of Ranch<Z>")
        print("   The generator incorrectly treats unrelated type parameters as compatible!")

        # Debug: Check structural comparison
        from src.ir.types import _create_substituted_structural_classifier

        ranch_E_structural = _create_substituted_structural_classifier(ranch_E)
        ranch_Z_structural = _create_substituted_structural_classifier(ranch_Z)

        if ranch_E_structural and ranch_Z_structural:
            print("\n   Debug info:")
            print(f"   Ranch<E> fields: {[(f.name, f.field_type, id(f.field_type)) for f in ranch_E_structural.field_signatures]}")
            print(f"   Ranch<Z> fields: {[(f.name, f.field_type, id(f.field_type)) for f in ranch_Z_structural.field_signatures]}")

            e_field = ranch_E_structural.field_signatures[0].field_type
            z_field = ranch_Z_structural.field_signatures[0].field_type

            print(f"\n   Comparing field types:")
            print(f"   E.is_subtype(Z)? {e_field.is_subtype(z_field)}")
            print(f"   E.bound: {e_field.bound}")
            print(f"   Z.bound: {z_field.bound}")
    else:
        print("\n✓ TEST PASSED: Bug is fixed!")

    # =========================================================================
    # Test 2: Different constructors, both structural - THIS IS THE BUG
    # =========================================================================
    print(f"\n\nTest 2: Bronson<E> vs Ranch<Z> (DIFFERENT constructors, both structural)")
    print(f"  This is the REAL bug scenario from #109")

    # Create Bronson<U> structural type
    U_param = tp.TypeParameter('U')
    bronson_classifier = tp.SimpleClassifier(
        name='Bronson',
        structural=True,
        supertypes=[],
        field_signatures=[
            tp.FieldInfo('kelsey', U_param),  # Same field name, same type param position
        ],
        is_complete=True
    )
    bronson_constructor = tp.TypeConstructor(
        'Bronson',
        [U_param],
        bronson_classifier
    )

    # Create Bronson<E>
    bronson_E = tp.ParameterizedType(bronson_constructor, [E])
    bronson_E.supertypes = []

    print(f"\n  Is Bronson<E> a subtype of Ranch<Z>?")
    print(f"  (Different constructors, both structural)")
    print(f"  Expected: False (E and Z are unrelated, even with same structure)")

    result2 = bronson_E.is_subtype(ranch_Z)
    print(f"  Actual: {result2}")

    if result2:
        print("\n✗ BUG CONFIRMED!")
        print("  Bronson<E> should NOT be subtype of Ranch<Z>")
        print("  Even though they have the same structure, E and Z are unrelated type parameters!")
        return True
    else:
        print("\n✓ Test passed for different constructors")
        return False


if __name__ == '__main__':
    result = test_simple_case_different_type_params()

    if result:
        print("\n" + "="*80)
        print("BUG IS PRESENT IN THE CODEBASE")
        print("="*80)
        exit(1)
    else:
        print("\n" + "="*80)
        print("BUG IS FIXED")
        print("="*80)
        exit(0)
