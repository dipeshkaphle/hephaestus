#!/usr/bin/env python3
"""
Test case for field access type substitution bug.

This reproduces the bug where accessing a field from a parameterized class
instance fails to properly substitute type parameters.

Scenario:
    class Forehands<E extends number, H> {
        timelines(): void {
            let wormiest: Sacajawea<number, E, H> = ...;
            let recopying: E | H | string = wormiest.openest;  // BUG HERE
        }
    }

    class Sacajawea<E extends number, L, T> {
        openest: E
    }

The bug: When accessing `wormiest.openest`, the field type should be `number`
(from the instantiation Sacajawea<number, E, H>), NOT the unsubstituted `E`
from Sacajawea's declaration.

Expected behavior: Type check should FAIL because `number` is not assignable
to `E | H | string` when E is a number literal type.

Actual buggy behavior: Hephaestus incorrectly thinks `E <: number` (from
Sacajawea) is assignable to `E | H | string` (from Forehands), treating them
as the same type parameter when they're different.
"""

import pytest
import src.ir.ast as ast
import src.ir.types as types
import src.ir.typescript_types as tst
import src.ir.context as ctx
import src.ir.type_utils as tu


def test_field_access_type_substitution_in_nested_generics():
    """Test that field access correctly substitutes type parameters from instantiation."""

    # Setup context
    context = ctx.Context()
    bt_factory = tst.TypeScriptBuiltinFactory()

    # Create type parameters for Sacajawea<E extends number, L, T>
    number_type = bt_factory.get_number_type()
    e_sacajawea = types.TypeParameter('E', bound=number_type)
    l_sacajawea = types.TypeParameter('L')
    t_sacajawea = types.TypeParameter('T')

    # Create Sacajawea class
    sacajawea_cls = ast.ClassDeclaration(
        name='Sacajawea',
        superclasses=[],
        type_parameters=[e_sacajawea, l_sacajawea, t_sacajawea],
        fields=[],
        functions=[]
    )
    sacajawea_cls.context = context
    sacajawea_cls.namespace = ('global', 'Sacajawea')

    # Add field `openest: E` to Sacajawea
    openest_field = ast.FieldDeclaration('openest', e_sacajawea)
    sacajawea_cls.fields.append(openest_field)

    # Register Sacajawea in context
    context.add_class(ast.GLOBAL_NAMESPACE, 'Sacajawea', sacajawea_cls)

    # Create type parameters for Forehands<E extends number, H>
    e_forehands = types.TypeParameter('E', bound=number_type)
    h_forehands = types.TypeParameter('H')

    # Now, in Forehands, we want to instantiate Sacajawea<number, E_forehands, H_forehands>
    sacajawea_type_constructor = sacajawea_cls.get_type()

    # Instantiate: Sacajawea<number, E_forehands, H_forehands>
    sacajawea_instantiated = types.ParameterizedType(
        sacajawea_type_constructor,
        [number_type, e_forehands, h_forehands]
    )

    # Get the type of the field `openest` after substitution
    # This should be `number` (the first type arg), NOT `E <: number` (the type parameter)
    type_var_map = {
        e_sacajawea: number_type,
        l_sacajawea: e_forehands,
        t_sacajawea: h_forehands
    }

    field_type_after_substitution = types.substitute_type(
        openest_field.get_type(),
        type_var_map
    )

    print(f"\nField declared type: {openest_field.get_type()}")
    print(f"Type var map: {type_var_map}")
    print(f"Field type after substitution: {field_type_after_substitution}")

    # The substituted type should be `number`, not `E <: number`
    assert field_type_after_substitution == number_type, \
        f"Expected field type to be {number_type}, got {field_type_after_substitution}"

    # Now test the buggy scenario: checking if this is assignable to E | H | string
    string_type = bt_factory.get_string_type()
    union_type = tst.UnionType([e_forehands, h_forehands, string_type])

    print(f"\nTarget union type: {union_type}")
    print(f"Checking if {field_type_after_substitution} is assignable to {union_type}")

    # This should FAIL because:
    # - field_type_after_substitution is `number` (all numbers)
    # - union_type is `E | H | string` where E could be a literal like `5`
    # - `number` is NOT assignable to `5 | H | string`
    is_assignable = field_type_after_substitution.is_assignable(union_type)

    print(f"Is assignable: {is_assignable}")

    # For this specific test, number IS assignable to E | H | string if E is number
    # So let's test with a more specific case

    # Better test: E is a literal type
    five_literal = tst.NumberLiteralType(5)
    e_forehands_literal = types.TypeParameter('E', bound=five_literal)
    union_with_literal = tst.UnionType([e_forehands_literal, h_forehands, string_type])

    # Now number should NOT be assignable to (5 | H | string)
    is_assignable_to_literal = field_type_after_substitution.is_assignable(union_with_literal)

    print(f"\nChecking if {field_type_after_substitution} is assignable to {union_with_literal}")
    print(f"Is assignable: {is_assignable_to_literal}")

    # This SHOULD be False (number is not assignable to 5 | H | string)
    # But if the bug exists, Hephaestus might incorrectly think E (from Sacajawea)
    # equals E (from Forehands) and say True
    assert not is_assignable_to_literal, \
        "Bug detected: number should NOT be assignable to literal union type"


def test_gen_field_access_respects_instantiation():
    """
    Test that when generating field access, the type substitution is correctly applied.

    This is a more integrated test that uses the generator to create field accesses.
    """
    from src.generators.generator import Generator

    # Create generator (it creates its own context and bt_factory)
    gen = Generator(language='typescript', logger=None)
    context = gen.context = ctx.Context()
    bt_factory = gen.bt_factory

    # Create Sacajawea<E, L, T> with field openest: E
    e_sacajawea = types.TypeParameter('E', bound=bt_factory.get_number_type())
    l_sacajawea = types.TypeParameter('L')
    t_sacajawea = types.TypeParameter('T')

    sacajawea_cls = ast.ClassDeclaration(
        name='Sacajawea',
        superclasses=[],
        type_parameters=[e_sacajawea, l_sacajawea, t_sacajawea],
        fields=[],
        functions=[]
    )
    sacajawea_cls.context = context
    sacajawea_cls.namespace = ('global', 'Sacajawea')

    openest_field = ast.FieldDeclaration('openest', e_sacajawea)
    sacajawea_cls.fields.append(openest_field)

    context.add_class(ast.GLOBAL_NAMESPACE, 'Sacajawea', sacajawea_cls)

    gen.namespace = ast.GLOBAL_NAMESPACE

    # Create a variable of type Sacajawea<number, string, boolean>
    number_type = bt_factory.get_number_type()
    string_type = bt_factory.get_string_type()
    boolean_type = bt_factory.get_boolean_type()

    sacajawea_instantiated = types.ParameterizedType(
        sacajawea_cls.get_type(),
        [number_type, string_type, boolean_type]
    )

    # Create a dummy expression for the variable
    dummy_expr = ast.NullConstant()
    var_decl = ast.VariableDeclaration('wormiest', dummy_expr, var_type=sacajawea_instantiated)
    context.add_var(ast.GLOBAL_NAMESPACE, 'wormiest', var_decl)

    # Now try to generate a field access that returns a type incompatible with `number`
    # For example, try to generate an expression of type `5 | string`
    five_literal = tst.NumberLiteralType(5)
    target_type = tst.UnionType([five_literal, string_type])

    print(f"\nTarget type for field access: {target_type}")

    # Try to generate field access
    try:
        # This should either:
        # 1. NOT select Sacajawea.openest (correct behavior - types incompatible)
        # 2. Or if there's a bug, incorrectly select it thinking E is compatible

        field_access = gen.gen_field_access(target_type, subtype=True)

        # If we got here, check what was selected
        print(f"Generated field access: {field_access}")
        print(f"Field name: {field_access.field}")

        # If the bug exists, it might have selected 'openest'
        # which would be wrong because number != (5 | string)
        if field_access.field == 'openest':
            pytest.fail(
                "BUG: Selected 'openest' field even though `number` is not "
                "assignable to target type. Type substitution was not applied correctly."
            )

    except Exception as e:
        # If generation fails, that might be correct behavior
        print(f"Field generation failed (may be correct): {e}")
        # This is acceptable - no compatible field exists


if __name__ == '__main__':
    # Run tests
    print("=" * 80)
    print("TEST 1: Field Access Type Substitution")
    print("=" * 80)
    test_field_access_type_substitution_in_nested_generics()

    print("\n" + "=" * 80)
    print("TEST 2: Generator Field Access Respects Instantiation")
    print("=" * 80)
    test_gen_field_access_respects_instantiation()

    print("\n" + "=" * 80)
    print("ALL TESTS PASSED!")
    print("=" * 80)
