import pytest
from src.ir import types as tp
from src.ir import typescript_types as tst

def test_unbounded_generic_union_subtype_issue():
    """
    This test verifies the bug where an unbounded generic in a union
    incorrectly satisfies a subtype check.

    This replicates the scenario from bug XL8EG:
    - G is an unbounded generic type parameter.
    - O is a type parameter with a bound of `G | "daffier"`.
    - The target type is `Object | "daffier"`.

    The check `O.is_subtype(Object | "daffier")` should be `False` because
    `G` is not a subtype of `Object | "daffier"`. This test asserts that
    this is the case. A failure of this test indicates a bug in the
    `is_subtype` logic.
    """
    # 1. Create the types involved
    G = tp.TypeParameter("G")
    daffier_type = tst.StringLiteralType("daffier")
    O_bound = tst.UnionType([G, daffier_type])
    O = tp.TypeParameter("O", bound=O_bound)

    object_type = tst.ObjectType()
    target_union = tst.UnionType([object_type, daffier_type])

    # 2. Perform the subtype check
    # This should resolve to O.bound.is_subtype(target_union), which is
    # (G | "daffier").is_subtype(Object | "daffier")
    is_subtype_result = O.is_subtype(target_union)

    # 3. Assert the expected outcome
    # The result should be False because G is not a subtype of (Object | "daffier").
    # The UnionType.is_subtype logic dictates that ALL members of the source
    # union must be subtypes of the target type.
    assert not is_subtype_result, \
        "BUG CONFIRMED: O was incorrectly considered a subtype of (Object | 'daffier'). " \
        "The is_subtype logic for UnionType or TypeParameter is likely flawed."
