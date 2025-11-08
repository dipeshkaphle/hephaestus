"""
Test that reproduces EXACT scenario from bug #109.

The key insight: Bronson<E, undefined, E> EXTENDS Ranch<T, J, number>
So when we access a field of type Bronson<E, undefined, E>, the system
might use the supertype Ranch<T, J, number> where T and J are from Bronson's scope.

Then it checks if Ranch<T, J, number> (where T=E, J=undefined) is assignable
to Ranch<Z, T, number> (where Z and T are from Brickbat's scope).

This should fail because the type parameters are from different scopes!
"""
from src.ir import types as tp
from src.ir.typescript_types import UndefinedType, NumberType


def test_bug_109_exact():
    """
    Reproduce the exact bug scenario:
    - Brickbat<E, Z, T> has field: hence: Bronson<E, undefined, E>
    - Bronson<U, J extends undefined, T extends U> extends Ranch<T, J, number>
    - So Bronson<E, undefined, E> extends Ranch<E, undefined, number>
    - In proboscis(), we try: Ranch<Z, T, number> = this.hence
    - this.hence has supertype Ranch<E, undefined, number>
    - Is Ranch<E, undefined, number> <: Ranch<Z, T, number>? Should be FALSE!
    """
    number_type = NumberType(primitive=False)
    undef_type = UndefinedType(primitive=False)

    # Type parameters from Brickbat scope
    E_brickbat = tp.TypeParameter('E')
    Z_brickbat = tp.TypeParameter('Z')
    T_brickbat = tp.TypeParameter('T')

    # Ranch<Q, W, Z> type constructor
    Q_param = tp.TypeParameter('Q')
    W_param = tp.TypeParameter('W')
    Z_param = tp.TypeParameter('Z', bound=number_type)

    ranch_classifier = tp.SimpleClassifier(
        name='Ranch',
        structural=True,
        supertypes=[],
        field_signatures=[
            tp.FieldInfo('kelsey', Q_param),
        ],
        is_complete=True
    )
    ranch_constructor = tp.TypeConstructor(
        'Ranch',
        [Q_param, W_param, Z_param],
        classifier=ranch_classifier
    )

    # Create Ranch<E, undefined, number> - this is the SUPERTYPE of Bronson<E, undefined, E>
    # where E is from Brickbat scope
    ranch_E_undef_num = tp.ParameterizedType(
        ranch_constructor,
        [E_brickbat, undef_type, number_type]
    )
    ranch_E_undef_num.supertypes = []

    # Create Ranch<Z, T, number> - this is what we're trying to assign to
    # where Z and T are ALSO from Brickbat scope but DIFFERENT parameters than E
    ranch_Z_T_num = tp.ParameterizedType(
        ranch_constructor,
        [Z_brickbat, T_brickbat, number_type]
    )
    ranch_Z_T_num.supertypes = []

    print("\n=== Bug #109 Exact Scenario ===")
    print("Type parameters (all from Brickbat scope):")
    print(f"  E: id={id(E_brickbat)}")
    print(f"  Z: id={id(Z_brickbat)}")
    print(f"  T: id={id(T_brickbat)}")
    print(f"  E == Z? {E_brickbat == Z_brickbat}")
    print(f"  E == T? {E_brickbat == T_brickbat}")

    print("\nChecking: Is Ranch<E, undefined, number> <: Ranch<Z, T, number>?")
    print("  (Both have SAME constructor: Ranch)")
    print("  Expected: False (E != Z, undefined != T)")

    # Before checking, let's see what the type args are
    print(f"\nType args comparison:")
    print(f"  Ranch<E, undefined, number>.type_args:")
    for i, arg in enumerate(ranch_E_undef_num.type_args):
        print(f"    [{i}] {arg} (type={type(arg).__name__}, id={id(arg)})")
    print(f"  Ranch<Z, T, number>.type_args:")
    for i, arg in enumerate(ranch_Z_T_num.type_args):
        print(f"    [{i}] {arg} (type={type(arg).__name__}, id={id(arg)})")

    print(f"\nChecking type parameter equality:")
    print(f"  type_args[0]: E_brickbat == Z_brickbat? {ranch_E_undef_num.type_args[0] == ranch_Z_T_num.type_args[0]}")
    print(f"  type_args[1]: undef == T_brickbat? {ranch_E_undef_num.type_args[1] == ranch_Z_T_num.type_args[1]}")
    print(f"  type_args[2]: number == number? {ranch_E_undef_num.type_args[2] == ranch_Z_T_num.type_args[2]}")

    result = ranch_E_undef_num.is_subtype(ranch_Z_T_num)
    print(f"\n  Actual result: {result}")

    if result:
        print("\n✗✗✗ BUG CONFIRMED! ✗✗✗")
        print("  Ranch<E, undefined, number> should NOT be subtype of Ranch<Z, T, number>")
        print("  E, Z, and T are DIFFERENT type parameters from the same scope!")
        print("\n  This is exactly what's happening in bug #109!")
        print("  The generator thinks this.hence (Bronson<E, undef, E> ~ Ranch<E, undef, num>)")
        print("  is assignable to Ranch<Z, T, number>")
        return True
    else:
        print("\n✓ Test passed - bug is fixed")
        return False


if __name__ == '__main__':
    bug_present = test_bug_109_exact()

    if bug_present:
        print("\n" + "="*80)
        print("BUG #109 IS REPRODUCED")
        print("="*80)
        exit(1)
    else:
        print("\n" + "="*80)
        print("BUG IS FIXED")
        print("="*80)
        exit(0)
