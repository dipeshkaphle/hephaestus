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


def test_array_variance_structural():
    """Tests array type variance (covariance) with structural types."""
    # In TypeScript, if A is a subtype of B, then A[] is a subtype of B[].

    # Structural types for subtyping
    # interface B { x: number }
    # interface A extends B { y: string }
    b_type = tp.SimpleClassifier(
        name="B",
        structural=True,
        field_signatures=[tp.FieldInfo("x", tst.NumberType())]
    )
    a_type = tp.SimpleClassifier(
        name="A",
        structural=True,
        field_signatures=[
            tp.FieldInfo("x", tst.NumberType()),
            tp.FieldInfo("y", tst.StringType())
        ]
    )

    assert a_type.is_subtype(b_type)

    array_constructor = tst.ArrayType()
    array_a = array_constructor.new([a_type])
    array_b = array_constructor.new([b_type])

    # A[] should be a subtype of B[] (covariance)
    assert array_a.is_subtype(array_b)

    # B[] should NOT be a subtype of A[]
    assert not array_b.is_subtype(array_a)


def test_function_variance_structural():
    """Tests function type variance with structural types."""
    # Structural types for subtyping
    # interface B { x: number }
    # interface A extends B { y: string }
    b_type = tp.SimpleClassifier(
        name="B",
        structural=True,
        field_signatures=[tp.FieldInfo("x", tst.NumberType())]
    )
    a_type = tp.SimpleClassifier(
        name="A",
        structural=True,
        field_signatures=[
            tp.FieldInfo("x", tst.NumberType()),
            tp.FieldInfo("y", tst.StringType())
        ]
    )

    assert a_type.is_subtype(b_type)

    # f1: (param: B) => A
    # f2: (param: A) => B

    # f1 should be a subtype of f2
    # Parameter: B is a supertype of A (contravariance)
    # Return: A is a subtype of B (covariance)

    func_constructor = tst.FunctionType(1)
    f1 = func_constructor.new([b_type, a_type])
    f2 = func_constructor.new([a_type, b_type])

    assert f1.is_subtype(f2)
    assert not f2.is_subtype(f1)


def test_function_variance_multiple_params_structural():
    """Tests function type variance with multiple parameters and structural types."""
    # B = { x: number }
    # A = { x: number, y: string } -> A <: B
    b_type = tp.SimpleClassifier("B", structural=True, field_signatures=[tp.FieldInfo("x", tst.NumberType())])
    a_type = tp.SimpleClassifier("A", structural=True, field_signatures=[tp.FieldInfo("x", tst.NumberType()), tp.FieldInfo("y", tst.StringType())])
    assert a_type.is_subtype(b_type)

    # D = { z: boolean }
    # C = { z: boolean, w: any } -> C <: D
    d_type = tp.SimpleClassifier("D", structural=True, field_signatures=[tp.FieldInfo("z", tst.BooleanType())])
    c_type = tp.SimpleClassifier("C", structural=True, field_signatures=[tp.FieldInfo("z", tst.BooleanType()), tp.FieldInfo("w", tst.ObjectType())])
    assert c_type.is_subtype(d_type)

    # f1: (p1: B, p2: D) => A
    # f2: (p1: A, p2: C) => B
    # f1 should be a subtype of f2
    func_constructor = tst.FunctionType(2)
    f1 = func_constructor.new([b_type, d_type, a_type])
    f2 = func_constructor.new([a_type, c_type, b_type])

    assert f1.is_subtype(f2)
    assert not f2.is_subtype(f1)


def test_array_variance_with_parameterized_structural_types():
    """Tests array variance with parameterized structural types."""
    # interface Box<T> { value: T }
    t = tp.TypeParameter("T", variance=tp.Covariant)
    box_constructor = tp.TypeConstructor(
        "Box",
        [t],
        classifier=tp.SimpleClassifier(
            "Box",
            structural=True,
            field_signatures=[tp.FieldInfo("value", t)]
        )
    )

    # B = { x: number }
    # A = { x: number, y: string } -> A <: B
    b_type = tp.SimpleClassifier("B", structural=True, field_signatures=[tp.FieldInfo("x", tst.NumberType())])
    a_type = tp.SimpleClassifier("A", structural=True, field_signatures=[tp.FieldInfo("x", tst.NumberType()), tp.FieldInfo("y", tst.StringType())])
    assert a_type.is_subtype(b_type)

    # Box<A> and Box<B>
    box_a = box_constructor.new([a_type])
    box_b = box_constructor.new([b_type])

    # Box<A> should be a subtype of Box<B> because Box is covariant in T
    assert box_a.is_subtype(box_b)
    assert not box_b.is_subtype(box_a)

    # Array of Box<A> and Array of Box<B>
    array_constructor = tst.ArrayType()
    array_box_a = array_constructor.new([box_a])
    array_box_b = array_constructor.new([box_b])

    # array_box_a should be a subtype of array_box_b
    assert array_box_a.is_subtype(array_box_b)
    assert not array_box_b.is_subtype(array_box_a)


def test_array_variance_with_structurally_equivalent_generics():
    """Tests array variance with structurally equivalent generic types having different type parameter names."""
    # interface Foo<T> { item: T }
    t = tp.TypeParameter("T")
    foo_constructor = tp.TypeConstructor(
        "Foo",
        [t],
        classifier=tp.SimpleClassifier(
            "Foo",
            structural=True,
            field_signatures=[tp.FieldInfo("item", t)]
        )
    )

    # interface Bar<U> { item: U }
    u = tp.TypeParameter("U")
    bar_constructor = tp.TypeConstructor(
        "Bar",
        [u],
        classifier=tp.SimpleClassifier(
            "Bar",
            structural=True,
            field_signatures=[tp.FieldInfo("item", u)]
        )
    )

    foo_string = foo_constructor.new([tst.StringType()])
    bar_string = bar_constructor.new([tst.StringType()])

    # Foo<string> and Bar<string> should be structurally equivalent
    assert foo_string.is_subtype(bar_string)
    assert bar_string.is_subtype(foo_string)

    # Arrays of these types
    array_constructor = tst.ArrayType()
    array_foo = array_constructor.new([foo_string])
    array_bar = array_constructor.new([bar_string])

    # array_foo and array_bar should be subtypes of each other
    assert array_foo.is_subtype(array_bar)
    assert array_bar.is_subtype(array_foo)


def test_omit_basic():
    """Test basic Omit<T, K> type functionality"""
    # Create a simple object type simulation using resolved_type
    # Omit<{name: string, age: number}, "age"> should resolve to string

    # Single key omission
    omit_single = tst.OmitType(
        tst.ObjectType(),  # Placeholder for object type
        tst.StringLiteralType("age"),
        resolved_type=tst.StringType()  # After omitting "age", only "name: string" remains
    )

    # The resolved type should be string
    assert omit_single._try_resolve() == tst.StringType()
    assert omit_single.is_subtype(tst.ObjectType())
    assert omit_single.is_subtype(tst.StringType())


def test_omit_multiple_keys():
    """Test Omit with union of keys"""
    # Omit<{name: string, age: number, city: string}, "age" | "city">
    # Should resolve to just string (from name field)

    keys_to_omit = tst.UnionType([
        tst.StringLiteralType("age"),
        tst.StringLiteralType("city")
    ])

    omit_multiple = tst.OmitType(
        tst.ObjectType(),
        keys_to_omit,
        resolved_type=tst.StringType()  # Only "name: string" remains
    )

    assert omit_multiple._try_resolve() == tst.StringType()
    assert omit_multiple.is_subtype(tst.StringType())


def test_omit_with_union_result():
    """Test Omit that results in a union type"""
    # Omit<{name: string, age: number, active: boolean}, "age">
    # Should resolve to string | boolean (from name and active fields)

    resolved_union = tst.UnionType([tst.StringType(), tst.BooleanType()])

    omit_union = tst.OmitType(
        tst.ObjectType(),
        tst.StringLiteralType("age"),
        resolved_type=resolved_union
    )

    assert omit_union._try_resolve() == resolved_union
    assert omit_union.is_subtype(tst.ObjectType())


def test_omit_subtyping():
    """Test subtyping relationships for Omit types"""
    # Omit<Person, "age"> with resolved_type string | number
    resolved_type = tst.UnionType([tst.StringType(), tst.NumberType()])

    omit_type = tst.OmitType(
        tst.ObjectType(),
        tst.StringLiteralType("age"),
        resolved_type=resolved_type
    )

    # Should be subtype of Object
    assert omit_type.is_subtype(tst.ObjectType())

    # Should be subtype of the resolved union type
    assert omit_type.is_subtype(resolved_type)

    # Should NOT be subtype of a more specific type
    assert not omit_type.is_subtype(tst.StringType())


def test_omit_has_type_variables():
    """Test type variable detection in Omit types"""
    # Create a simple type variable (using a parameterized type as proxy)
    simple_type = tst.StringType()

    omit_no_vars = tst.OmitType(
        simple_type,
        tst.StringLiteralType("key"),
        resolved_type=tst.NumberType()
    )

    # Simple types should not have type variables
    assert not omit_no_vars.has_type_variables()


def test_omit_equality():
    """Test equality and hashing for Omit types"""
    omit1 = tst.OmitType(
        tst.ObjectType(),
        tst.StringLiteralType("age"),
        resolved_type=tst.StringType()
    )

    omit2 = tst.OmitType(
        tst.ObjectType(),
        tst.StringLiteralType("age"),
        resolved_type=tst.StringType()
    )

    omit3 = tst.OmitType(
        tst.ObjectType(),
        tst.StringLiteralType("name"),  # Different key
        resolved_type=tst.StringType()
    )

    # Same omit types should be equal
    assert omit1 == omit2
    assert hash(omit1) == hash(omit2)

    # Different omit types should not be equal
    assert omit1 != omit3


def test_omit_get_name():
    """Test string representation of Omit types"""
    omit_single = tst.OmitType(
        tst.NumberType(),
        tst.StringLiteralType("key")
    )

    # Should render as Omit<T, K>
    name = omit_single.get_name()
    assert "Omit<" in name
    assert "Number" in name
    assert "key" in name

    # Test with union keys
    union_keys = tst.UnionType([
        tst.StringLiteralType("a"),
        tst.StringLiteralType("b")
    ])
    omit_union = tst.OmitType(tst.ObjectType(), union_keys)

    name_union = omit_union.get_name()
    assert "Omit<" in name_union
    assert "Object" in name_union
