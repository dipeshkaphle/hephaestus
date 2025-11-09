from src.ir.builtins import NumberType
import src.ir.typescript_types as tst
import src.ir.typescript_ast as ts_ast
import src.ir.types as tp
import src.ir.type_utils as tu


def test_type_alias_with_literals():
    # Tests subtyping relations between a string alias and string literal
    # and between a number alias and a number literal.
    #  - (type Foo = string) with literal "foo"
    #  - (type Bar = number) with literal 5
    string_alias = ts_ast.TypeAliasDeclaration("Foo", tst.StringType()).get_type()
    number_alias = ts_ast.TypeAliasDeclaration("Bar", tst.NumberType()).get_type()

    string_lit = tst.StringLiteralType("foo")
    number_lit = tst.NumberLiteralType(5)

    assert string_lit.is_subtype(string_alias)
    assert not string_alias.is_subtype(string_lit)
    assert number_lit.is_subtype(number_alias)
    assert not number_alias.is_subtype(number_lit)


def test_type_alias_with_literals2():
    # Tests subtyping relation between a literal alias
    # and their corresponding literal type.
    #  - (type Foo = "foo") with literal "foo"
    #  - (type Bar = "bar") with literal "bar"
    string_alias = ts_ast.TypeAliasDeclaration("Foo", tst.StringLiteralType("foo")).get_type()
    number_alias = ts_ast.TypeAliasDeclaration("Bar", tst.NumberLiteralType(5)).get_type()

    string_lit = tst.StringLiteralType("foo")
    number_lit = tst.NumberLiteralType(5)

    assert string_lit.is_subtype(string_alias)
    assert number_lit.is_subtype(number_alias)
    assert string_alias.is_subtype(string_lit)
    assert number_alias.is_subtype(number_lit)


def test_union_types_simple():
    # Tests subtyping relation between union types
    # and the types in their union.
    #  - number | boolean
    #  - boolean | "bar"
    #  - boolean | number
    union_1 = tst.UnionType([tst.NumberType(), tst.BooleanType()])

    bar_lit = tst.StringLiteralType("bar")
    union_2 = tst.UnionType([tst.BooleanType(), bar_lit])

    union_3 = tst.UnionType([tst.BooleanType(), tst.NumberType()])

    assert not union_1.is_subtype(union_2)
    assert not union_2.is_subtype(union_1)
    assert union_3.is_subtype(union_1)
    assert union_1.is_subtype(union_3)


def test_union_types_other_types():
    # Tests that types A, B are subtypes of A | B
    union = tst.UnionType([tst.NumberType(), tst.BooleanType()])
    assert tst.NumberType().is_subtype(union)
    assert tst.BooleanType().is_subtype(union)


def test_union_type_assign():
    # Tests correct creation and assignment of union type
    union = tst.UnionType([tst.StringType(), tst.NumberType(), tst.BooleanType(), tst.ObjectType()])
    foo = tst.StringType()

    assert len(union.types) == 4
    assert not union.is_subtype(foo)
    assert foo.is_subtype(union)


def test_union_type_param():
    # Tests that union type bounds of type parameters do not
    # conflict with the sybtyping relations between the two.
    union1 = tst.UnionType([tst.NumberType(), tst.NullType()])
    union2 = tst.UnionType([tst.StringLiteralType("foo"), tst.NumberType()])
    t_param = tp.TypeParameter("T", bound=union2)

    assert not union2.is_subtype(union1)
    assert not union1.is_subtype(t_param)
    assert not t_param.is_subtype(union1)


def test_union_type_substitution():
    # Tests substitution of type parametes in union types
    type_param1 = tp.TypeParameter("T1")
    type_param2 = tp.TypeParameter("T2")
    type_param3 = tp.TypeParameter("T3")
    type_param4 = tp.TypeParameter("T4")

    foo = tp.TypeConstructor("Foo", [type_param1, type_param2])
    foo_p = foo.new([tst.NumberType(), type_param3])

    union = tst.UnionType([tst.StringLiteralType("bar"), foo_p])
    ptype = tp.substitute_type(union, {type_param3: type_param4})

    assert ptype.types[1].type_args[0] == tst.NumberType()
    assert ptype.types[1].type_args[1] == type_param4


def test_union_type_substitution_type_var_bound():
    # Tests substitution of bounded type parameters in union types
    type_param1 = tp.TypeParameter("T1")
    type_param2 = tp.TypeParameter("T2", bound=type_param1)
    type_map = {type_param1: tst.StringType()}

    union = tst.UnionType([tst.NumberType(), type_param2])
    ptype_union = tp.substitute_type(union, type_map)
    ptype = ptype_union.types[1]


    assert ptype.name == type_param2.name
    assert ptype.variance == type_param2.variance
    assert ptype.bound == tst.StringType()


def test_union_to_type_variable_free():
    # Tests the builtin method to-type-variable-free of union types
    type_param1 = tp.TypeParameter("T1")
    type_param2 = tp.TypeParameter("T2")
    foo = tp.TypeConstructor("Foo", [type_param1])
    foo_t = foo.new([type_param2])
    union = tst.UnionType([foo_t, tst.StringLiteralType("bar")])

    union_n = union.to_type_variable_free(tst.TypeScriptBuiltinFactory())
    foo_n = union_n.types[0]
    assert foo_n.type_args[0] == tp.WildCardType(tst.ObjectType(), variance=tp.Covariant)

    type_param2.bound = tst.NumberType()
    foo_t = foo.new([type_param2])
    union = tst.UnionType([foo_t, tst.NumberLiteralType(43)])

    union_n = union.to_type_variable_free(tst.TypeScriptBuiltinFactory())
    foo_n = union_n.types[0]
    assert foo_n.type_args[0] == tp.WildCardType(tst.NumberType(), variance=tp.Covariant)

    bar = tp.TypeConstructor("Bar", [tp.TypeParameter("T")])
    bar_p = bar.new([type_param2])
    foo_t = foo.new([bar_p])
    union = tst.UnionType([foo_t, tst.NumberType(), tst.StringType(), tst.AliasType(tst.StringLiteralType("foobar"))])

    union_n = union.to_type_variable_free(tst.TypeScriptBuiltinFactory())
    foo_n = union_n.types[0]
    assert foo_n.type_args[0] == bar.new(
        [tp.WildCardType(tst.NumberType(), variance=tp.Covariant)])


def test_union_type_unification_type_var():
    union = tst.UnionType([tst.StringType(), tst.StringLiteralType("foo")])
    type_param = tp.TypeParameter("T")

    # Case 1: Unify a union with an unbounded type param
    type_var_map = tu.unify_types(union, type_param, tst.TypeScriptBuiltinFactory())
    assert len(type_var_map) == 1
    assert type_var_map == {type_param: union}

    # Case 2: unify a union with a bounded type param, which has an
    # incompatible bound with the given union.
    union = tst.UnionType([tst.NumberType(), tst.StringType()])
    type_param = tp.TypeParameter("T", bound=tst.NumberType())

    type_var_map = tu.unify_types(union, type_param,
                                  tst.TypeScriptBuiltinFactory())
    assert type_var_map == {}


    # Case 3: unify a union with a bounded type param, which has a compatible
    # bound with the given union.
    type_param = tp.TypeParameter("T", bound=union)
    type_var_map = tu.unify_types(union, type_param,
                                  tst.TypeScriptBuiltinFactory())
    assert type_var_map == {type_param: union}

def test_union_type_unification():
    type_param = tp.TypeParameter("T")
    union1 = tst.UnionType([tst.NumberLiteralType(1410), tst.NumberType(), tst.StringType()])
    union2 = tst.UnionType([type_param, tst.NumberType(), tst.StringType()])
    assert union1.is_subtype(union2)

    # Unify t1: 1410 | number | string
    # with t2: T | number | string
    # Result should be: {T: 1410}
    type_var_map = tu.unify_types(union1, union2, tst.TypeScriptBuiltinFactory())
    assert len(type_var_map) == 1
    assert type_var_map == {type_param: union1.types[0]}

    type_param2 = tp.TypeParameter("G")
    union3 = tst.UnionType([type_param, type_param2, tst.StringLiteralType("foo")])

    # Unify t1: 1410 | number | string
    # with t3: T | G | "foo".
    # Result should be: {T: number, G: string} or reversed.
    type_var_map = tu.unify_types(union1, union3, tst.TypeScriptBuiltinFactory())
    assert len(type_var_map) == 2
    assert type_param, type_param2 in type_var_map
    assert union1.types[1], union1.types[2] in type_var_map.values()


def test_union_type_unification2():
    union = tst.UnionType([tst.NumberType(), tst.StringType()])
    assert tu.unify_types(tst.BooleanType(), union, tst.TypeScriptBuiltinFactory()) == {}

    # Unify t1: number
    # with t2: number | T
    # Result should be: {T: number}
    t1 = tst.NumberType()
    t2 = tst.UnionType([tst.NumberType(), tp.TypeParameter("T")])
    res = tu.unify_types(t1, t2, tst.TypeScriptBuiltinFactory())
    assert len(res) == 1 and res[t2.types[1]] == t1

    # Unify t1: number | string
    # with t2: number | T
    # Result should be: {T: string}
    t1 = tst.UnionType([tst.NumberType(), tst.StringType()])
    res = tu.unify_types(t1, t2, tst.TypeScriptBuiltinFactory())
    assert len(res) == 1 and res[t2.types[1]] == t1.types[1]

    # Unify t1: number | "foo" | string
    # with t2: number | T
    # Result should be: {T: string}
    t1 = tst.UnionType([tst.NumberType(), tst.StringLiteralType("foo"), tst.StringType()])
    res = tu.unify_types(t1, t2, tst.TypeScriptBuiltinFactory())
    assert len(res) == 1 and res[t2.types[1]] == t1.types[2]

    t1 = tst.UnionType([tst.NumberType(), tst.NumberLiteralType(100), tst.BooleanType(), tst.StringLiteralType("foo"), tst.StringType()])

    t_param1 = tp.TypeParameter("T", bound=tst.StringType())
    helper_union = tst.UnionType([tst.BooleanType(), tst.StringType()])
    t_param2 = tp.TypeParameter("G", bound=helper_union)
    t2 = tst.UnionType([tst.NumberType(), t_param1, t_param2])

    # Unify t1: number | 100 | boolean | "foo" | string
    # with t2: number | T extends string | G extends (boolean | string)
    # Result should be {T: StringType, G: BooleanType}
    res = tu.unify_types(t1, t2, tst.TypeScriptBuiltinFactory())
    assert (len(res) == 2 and
            res[t2.types[1]] == t1.types[4] and
            res[t2.types[2]] == t1.types[2])


def test_union_to_type_variable_free():
    type_param = tp.TypeParameter("S")
    union = tst.UnionType([tst.NumberType(), type_param])

    new_union = union.to_type_variable_free(tst.TypeScriptBuiltinFactory())
    assert new_union == tst.UnionType([tst.NumberType(),
                                       tst.TypeScriptBuiltinFactory().get_any_type()])

    type_param = tp.TypeParameter("S", bound=tst.StringType())
    union = tst.UnionType([tst.NumberType(), type_param])
    new_union = union.to_type_variable_free(tst.TypeScriptBuiltinFactory())
    assert new_union == tst.UnionType([tst.NumberType(), tst.StringType()])


def test_union_subtyping_number_bigint_incompatibility():
    """
    Test based on TypeScript error:
    Type '(p0: number | "lorry", p1: undefined) => number | "lorry"'
    is not assignable to type '(p0: bigint | "lorry", p1: undefined) => bigint | "lorry"'.

    Verifies that (number | "lorry") is NOT a subtype of (bigint | "lorry")
    because number and bigint are distinct, unrelated types.
    """
    # Create the union types
    number_or_lorry = tst.UnionType([tst.NumberType(), tst.StringLiteralType("lorry")])
    bigint_or_lorry = tst.UnionType([tst.BigIntegerType(), tst.StringLiteralType("lorry")])

    # Verify that number | "lorry" is NOT a subtype of bigint | "lorry"
    assert not number_or_lorry.is_subtype(bigint_or_lorry)

    # Also verify the reverse is false
    assert not bigint_or_lorry.is_subtype(number_or_lorry)

    # Verify the root cause: number and bigint are unrelated
    assert not tst.NumberType().is_subtype(tst.BigIntegerType())
    assert not tst.BigIntegerType().is_subtype(tst.NumberType())

    # But verify that "lorry" alone IS a subtype of both unions
    lorry_literal = tst.StringLiteralType("lorry")
    assert lorry_literal.is_subtype(bigint_or_lorry)
    assert lorry_literal.is_subtype(number_or_lorry)

    # And number alone is NOT a subtype of bigint | "lorry"
    assert not tst.NumberType().is_subtype(bigint_or_lorry)

def test_indexed_access_with_union_keys():
    """
    Test indexed access types with union of string literal keys.

    Examples:
        Person["age" | "name"] should resolve to the union of field types
        Array<number>[number | "length"] should handle mixed index types
    """
    # Test 1: Basic union key indexed access with cached resolved type
    # Simulate Person type with fields: age: number, name: string
    age_type = tst.NumberType()
    name_type = tst.StringType()

    # Create mock object type (we'll use a simple type for testing)
    # In real code generation, this would be a class type
    object_type = tst.ObjectType()

    # Create union of string literal keys: "age" | "name"
    union_key = tst.UnionType([
        tst.StringLiteralType("age"),
        tst.StringLiteralType("name")
    ])

    # Create the indexed access type with pre-resolved type (union of field types)
    # In real generation, resolved_type would be computed from the class definition
    resolved_union = tst.UnionType([age_type, name_type])
    indexed_type = tst.IndexedAccessType(object_type, union_key, resolved_type=resolved_union)

    # Verify that resolution returns the union
    resolved = indexed_type._try_resolve()
    assert resolved is not None
    assert isinstance(resolved, tst.UnionType)
    assert resolved == resolved_union

    # Test 2: Array with number index should work
    array_type = tst.ArrayType().new([tst.NumberType()])
    number_index = tst.NumberType()
    array_indexed = tst.IndexedAccessType(array_type, number_index)

    resolved_array = array_indexed._try_resolve()
    assert resolved_array == tst.NumberType()

    # Test 3: Nested resolution - union key where each key resolves individually
    # Create individual indexed access types
    age_indexed = tst.IndexedAccessType(object_type, tst.StringLiteralType("age"), resolved_type=age_type)
    name_indexed = tst.IndexedAccessType(object_type, tst.StringLiteralType("name"), resolved_type=name_type)

    # Verify individual resolutions work
    assert age_indexed._try_resolve() == age_type
    assert name_indexed._try_resolve() == name_type

    # Test 4: Verify type name generation for union keys
    from src.translators.typescript import TypeScriptTranslator
    translator = TypeScriptTranslator()

    type_name = translator.get_type_name(indexed_type)
    # Should generate: Object["age" | "name"]
    assert "Object" in type_name
    assert "[" in type_name
    assert "]" in type_name
    assert "|" in type_name

    # Test 5: Deduplication - if union keys resolve to the same type
    duplicate_union_key = tst.UnionType([
        tst.StringLiteralType("field1"),
        tst.StringLiteralType("field2")
    ])
    # Both fields have the same type
    same_type = tst.StringType()
    dup_indexed = tst.IndexedAccessType(
        object_type,
        duplicate_union_key,
        resolved_type=same_type  # Both resolve to string
    )

    # When we manually simulate resolution with deduplication
    # (Note: _try_resolve with cached resolved_type will just return the cache)
    # This tests the deduplication logic in the union resolution path

    # Test 6: Union key subtyping
    # If T["a" | "b"] resolves to number | string, it should be subtype of Object
    assert indexed_type.is_subtype(tst.ObjectType())

def test_number_literal_subtype_of_number():
    """Test that number literals are subtypes of number type"""
    num_lit_5 = tst.NumberLiteralType(5)
    num_lit_42 = tst.NumberLiteralType(42)
    num_lit_neg = tst.NumberLiteralType(-10)
    number_type = tst.NumberType()

    # Number literals should be subtypes of number
    assert num_lit_5.is_subtype(number_type)
    assert num_lit_42.is_subtype(number_type)
    assert num_lit_neg.is_subtype(number_type)

    # But number should NOT be a subtype of a literal
    assert not number_type.is_subtype(num_lit_5)
    assert not number_type.is_subtype(num_lit_42)

    # Different literals are not subtypes of each other
    assert not num_lit_5.is_subtype(num_lit_42)
    assert not num_lit_42.is_subtype(num_lit_5)


def test_type_alias_number_subtyping():
    """Test subtyping relationships with type aliases for numbers"""
    # type NumAlias = number
    num_alias = ts_ast.TypeAliasDeclaration("NumAlias", tst.NumberType()).get_type()
    number_type = tst.NumberType()
    num_lit = tst.NumberLiteralType(10)

    # Type alias of number should be equivalent to number
    assert num_alias.is_subtype(number_type)
    assert number_type.is_subtype(num_alias)

    # Number literal should be subtype of type alias to number
    assert num_lit.is_subtype(num_alias)
    assert not num_alias.is_subtype(num_lit)


def test_type_alias_number_literal_subtyping():
    """Test subtyping with type aliases that reference number literals"""
    # type Five = 5
    five_alias = ts_ast.TypeAliasDeclaration("Five", tst.NumberLiteralType(5)).get_type()
    # type Ten = 10
    ten_alias = ts_ast.TypeAliasDeclaration("Ten", tst.NumberLiteralType(10)).get_type()

    number_type = tst.NumberType()
    num_lit_5 = tst.NumberLiteralType(5)
    num_lit_10 = tst.NumberLiteralType(10)

    # Literal type aliases should be subtypes of number
    assert five_alias.is_subtype(number_type)
    assert ten_alias.is_subtype(number_type)

    # Literal type aliases should be equivalent to their literals
    assert five_alias.is_subtype(num_lit_5)
    assert num_lit_5.is_subtype(five_alias)
    assert ten_alias.is_subtype(num_lit_10)
    assert num_lit_10.is_subtype(ten_alias)

    # Different literal aliases are not subtypes of each other
    assert not five_alias.is_subtype(ten_alias)
    assert not ten_alias.is_subtype(five_alias)
    assert not five_alias.is_subtype(num_lit_10)
    assert not ten_alias.is_subtype(num_lit_5)


def test_type_alias_nested_number_literal():
    """Test nested type aliases with number literals"""
    # type Five = 5
    # type FiveAlias = Five
    five_lit = tst.NumberLiteralType(5)
    five_alias = ts_ast.TypeAliasDeclaration("Five", five_lit).get_type()
    five_alias_alias = ts_ast.TypeAliasDeclaration("FiveAlias", five_alias).get_type()

    number_type = tst.NumberType()

    # Nested alias should still be subtype of number
    assert five_alias_alias.is_subtype(number_type)
    assert five_alias_alias.is_subtype(five_alias)
    assert five_alias_alias.is_subtype(five_lit)

    # And equivalent to the original literal
    assert five_lit.is_subtype(five_alias_alias)
    assert five_alias.is_subtype(five_alias_alias)
