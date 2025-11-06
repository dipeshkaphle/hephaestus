"""
Integration tests for ParameterizedType with structural typing.

These tests ensure that ParameterizedType correctly exposes field and method
signatures from its structural classifier, which is critical for:
1. Structural subtyping checks
2. Code generation (finding types with specific methods/fields)
3. Type compatibility during expression generation

The bug this catches: ParameterizedType inheriting from SimpleClassifier but
not properly delegating to its classifier's signatures.
"""

from src.ir import types as tp, typescript_types as tst
from src.ir.types import is_structural_type


def test_parameterized_type_exposes_classifier_methods():
    """
    Test that ParameterizedType._get_all_methods() returns methods from classifier.

    This is critical for code generation - if ParameterizedType doesn't expose
    its methods, the generator can't find types with specific methods.
    """
    # Create a generic structural type: Box<T> with getValue() method
    t_param = tp.TypeParameter("T", tp.Invariant)

    classifier = tp.SimpleClassifier(
        "Box",
        structural=True,
        method_signatures=[
            tp.MethodInfo("getValue", [], t_param),
            tp.MethodInfo("setValue", [t_param], tst.TypeScriptBuiltinFactory().get_void_type())
        ]
    )

    box_constructor = tp.TypeConstructor("Box", [t_param], classifier=classifier)
    box_of_number = box_constructor.new([tst.NumberType()])

    # Get methods from the parameterized type
    methods = box_of_number._get_all_methods()

    assert len(methods) == 2, f"Expected 2 methods, got {len(methods)}"
    assert "getValue" in methods, "Missing getValue method"
    assert "setValue" in methods, "Missing setValue method"

    # Verify type substitution happened
    get_value = methods["getValue"]
    assert get_value.return_type == tst.NumberType(), \
        f"Expected Number return type, got {get_value.return_type}"

    set_value = methods["setValue"]
    assert len(set_value.param_types) == 1, "setValue should have 1 parameter"
    assert set_value.param_types[0] == tst.NumberType(), \
        f"Expected Number parameter, got {set_value.param_types[0]}"


def test_parameterized_type_exposes_classifier_fields():
    """
    Test that ParameterizedType._get_all_fields() returns fields from classifier.
    """
    t_param = tp.TypeParameter("T", tp.Invariant)

    classifier = tp.SimpleClassifier(
        "Container",
        structural=True,
        field_signatures=[
            tp.FieldInfo("value", t_param),
            tp.FieldInfo("count", tst.NumberType())
        ]
    )

    container_constructor = tp.TypeConstructor("Container", [t_param], classifier=classifier)
    container_of_string = container_constructor.new([tst.StringType()])

    # Get fields from the parameterized type
    fields = container_of_string._get_all_fields()

    assert len(fields) == 2, f"Expected 2 fields, got {len(fields)}"
    assert "value" in fields, "Missing value field"
    assert "count" in fields, "Missing count field"

    # Verify type substitution
    assert fields["value"].field_type == tst.StringType(), \
        f"Expected String field type, got {fields['value'].field_type}"
    assert fields["count"].field_type == tst.NumberType()


def test_parameterized_structural_subtyping_with_methods():
    """
    Test that structural subtyping works correctly for ParameterizedType.

    This tests the full integration: is_structural_type() + _get_all_methods() + is_subtype()
    """
    t_param = tp.TypeParameter("T", tp.Invariant)

    # Create Box<T> with getValue() method
    box_classifier = tp.SimpleClassifier(
        "Box",
        structural=True,
        method_signatures=[tp.MethodInfo("getValue", [], t_param)],
        is_complete = True
    )
    box_constructor = tp.TypeConstructor("Box", [t_param], classifier=box_classifier)

    # Create Container<T> with getValue() and setValue() methods
    container_classifier = tp.SimpleClassifier(
        "Container",
        structural=True,
        method_signatures=[
            tp.MethodInfo("getValue", [], t_param),
            tp.MethodInfo("setValue", [t_param], tst.TypeScriptBuiltinFactory().get_void_type())
        ],
        is_complete = True
    )
    container_constructor = tp.TypeConstructor("Container", [t_param], classifier=container_classifier)

    # Instantiate both
    box_of_number = box_constructor.new([tst.NumberType()])
    container_of_number = container_constructor.new([tst.NumberType()])

    # Container should be a subtype of Box (has all methods Box has)
    assert container_of_number.is_subtype(box_of_number), \
        "Container<Number> should be subtype of Box<Number> (has getValue)"

    # Box should NOT be a subtype of Container (missing setValue)
    assert not box_of_number.is_subtype(container_of_number), \
        "Box<Number> should NOT be subtype of Container<Number> (missing setValue)"


def test_parameterized_type_not_subtype_without_matching_methods():
    """
    Test that ParameterizedType with no matching methods is NOT a subtype.

    This is the vAH50 bug scenario: a type without a method should not
    be considered a subtype of a type requiring that method.
    """
    t_param = tp.TypeParameter("T", tp.Invariant)

    # Create TypeWithMethod<T> that has a decimal() method
    type_with_method = tp.SimpleClassifier(
        "TypeWithMethod",
        structural=True,
        method_signatures=[tp.MethodInfo("decimal", [], tst.NumberType())]
    )
    with_method_constructor = tp.TypeConstructor("TypeWithMethod", [t_param], classifier=type_with_method)

    # Create TypeWithoutMethod<T> that has NO methods
    type_without_method = tp.SimpleClassifier(
        "TypeWithoutMethod",
        structural=True,
        field_signatures=[tp.FieldInfo("value", t_param)],
        method_signatures=[]  # NO METHODS
    )
    without_method_constructor = tp.TypeConstructor("TypeWithoutMethod", [t_param], classifier=type_without_method)

    # Instantiate both
    with_method_inst = with_method_constructor.new([tst.NumberType()])
    without_method_inst = without_method_constructor.new([tst.NumberType()])

    # The type without the method should NOT be a subtype
    assert not without_method_inst.is_subtype(with_method_inst), \
        "TypeWithoutMethod should NOT be subtype of TypeWithMethod (missing decimal method)"


def test_is_structural_type_on_parameterized_type():
    """
    Test that is_structural_type() correctly identifies structural ParameterizedTypes.

    Regression test for the bug where is_structural_type() checked the
    ParameterizedType's own 'structural' attribute (False) before checking
    the classifier.
    """
    t_param = tp.TypeParameter("T", tp.Invariant)

    # Create structural classifier
    structural_classifier = tp.SimpleClassifier(
        "Structural",
        structural=True,
        method_signatures=[tp.MethodInfo("foo", [], tst.NumberType())]
    )
    structural_constructor = tp.TypeConstructor("Structural", [t_param], classifier=structural_classifier)
    structural_inst = structural_constructor.new([tst.NumberType()])

    # Create nominal classifier
    nominal_classifier = tp.SimpleClassifier(
        "Nominal",
        structural=False
    )
    nominal_constructor = tp.TypeConstructor("Nominal", [t_param], classifier=nominal_classifier)
    nominal_inst = nominal_constructor.new([tst.NumberType()])

    # Check is_structural_type
    assert is_structural_type(structural_inst), \
        "ParameterizedType with structural classifier should be structural"
    assert not is_structural_type(nominal_inst), \
        "ParameterizedType with nominal classifier should not be structural"


def test_mixed_parameterized_and_simple_structural_subtyping():
    """
    Test structural subtyping between ParameterizedType and SimpleClassifier.

    This tests the case where we compare a ParameterizedType with a
    non-parameterized SimpleClassifier, which was causing AttributeError
    in _create_substituted_structural_classifier.
    """
    # Create a non-generic structural type
    simple_structural = tp.SimpleClassifier(
        "SimpleType",
        structural=True,
        method_signatures=[tp.MethodInfo("getValue", [], tst.NumberType())],
    )

    # Create a generic structural type
    t_param = tp.TypeParameter("T", tp.Invariant)
    generic_classifier = tp.SimpleClassifier(
        "GenericType",
        structural=True,
        method_signatures=[
            tp.MethodInfo("getValue", [], tst.NumberType()),
            tp.MethodInfo("setValue", [tst.NumberType()], tst.TypeScriptBuiltinFactory().get_void_type())
        ]
    )
    generic_constructor = tp.TypeConstructor("GenericType", [t_param], classifier=generic_classifier)
    generic_inst = generic_constructor.new([tst.StringType()])

    # Generic should be subtype of simple (has getValue)
    assert generic_inst.is_subtype(simple_structural), \
        "GenericType<String> should be subtype of SimpleType (has getValue)"

    # Simple should NOT be subtype of generic (missing setValue)
    assert not simple_structural.is_subtype(generic_inst), \
        "SimpleType should NOT be subtype of GenericType (missing setValue)"


def test_empty_structural_parameterized_types():
    """
    Test that empty structural ParameterizedTypes (no fields/methods) work correctly.

    This is important because many generated classes start empty and get
    methods/fields added later.
    """
    t_param = tp.TypeParameter("T", tp.Invariant)

    empty_classifier = tp.SimpleClassifier(
        "Empty",
        structural=True,
        field_signatures=[],
        method_signatures=[]
    )
    empty_constructor = tp.TypeConstructor("Empty", [t_param], classifier=empty_classifier)
    empty_inst = empty_constructor.new([tst.NumberType()])

    # Should be identified as structural
    assert is_structural_type(empty_inst)

    # Should have no methods/fields
    assert len(empty_inst._get_all_methods()) == 0
    assert len(empty_inst._get_all_fields()) == 0

    # Should be subtype of itself
    assert empty_inst.is_subtype(empty_inst)


def test_multiple_type_parameters_with_structural():
    """
    Test structural typing with multiple type parameters.
    """
    t1 = tp.TypeParameter("T1", tp.Invariant)
    t2 = tp.TypeParameter("T2", tp.Invariant)

    classifier = tp.SimpleClassifier(
        "Pair",
        structural=True,
        field_signatures=[
            tp.FieldInfo("first", t1),
            tp.FieldInfo("second", t2)
        ],
        method_signatures=[
            tp.MethodInfo("swap", [], tst.VoidType())  # Returns Pair<T2, T1> but we simplify here
        ]
    )

    pair_constructor = tp.TypeConstructor("Pair", [t1, t2], classifier=classifier)
    pair_inst = pair_constructor.new([tst.NumberType(), tst.StringType()])

    # Check fields are properly substituted
    fields = pair_inst._get_all_fields()
    assert fields["first"].field_type == tst.NumberType()
    assert fields["second"].field_type == tst.StringType()

    # Check methods exist
    methods = pair_inst._get_all_methods()
    assert "swap" in methods


def test_generator_scenario_find_type_with_method():
    """
    Simulate the generator scenario: finding a type that has a specific method.

    This is what was failing in vAH50 - the generator couldn't find types
    with specific methods because _get_all_methods() returned empty.
    """
    t_param = tp.TypeParameter("T", tp.Invariant)

    # Create several types
    type1_classifier = tp.SimpleClassifier(
        "Type1",
        structural=True,
        method_signatures=[tp.MethodInfo("decimal", [], tst.NumberType())]
    )
    type1_constructor = tp.TypeConstructor("Type1", [t_param], classifier=type1_classifier)
    type1_inst = type1_constructor.new([tst.NumberType()])

    type2_classifier = tp.SimpleClassifier(
        "Type2",
        structural=True,
        method_signatures=[tp.MethodInfo("getValue", [], t_param)]
    )
    type2_constructor = tp.TypeConstructor("Type2", [t_param], classifier=type2_classifier)
    type2_inst = type2_constructor.new([tst.NumberType()])

    type3_classifier = tp.SimpleClassifier(
        "Type3",
        structural=True,
        method_signatures=[]  # No methods
    )
    type3_constructor = tp.TypeConstructor("Type3", [t_param], classifier=type3_classifier)
    type3_inst = type3_constructor.new([tst.NumberType()])

    # Simulate generator finding types with 'decimal' method
    all_types = [type1_inst, type2_inst, type3_inst]
    types_with_decimal = [
        t for t in all_types
        if "decimal" in t._get_all_methods()
    ]

    assert len(types_with_decimal) == 1, \
        "Should find exactly one type with 'decimal' method"
    assert types_with_decimal[0] == type1_inst, \
        "Should find Type1 as the type with 'decimal' method"


def test_parameterized_type_inherits_interface_methods():
    """
    Test that ParameterizedType inherits methods from interface supertypes.

    This is the KvOc1 bug scenario: interface Angering<D> extends Roils,
    where Roils has methods firetraps() and monkey(). When we instantiate
    Angering<string>, it should have those methods.

    Regression test for bug where _get_all_methods() only returned classifier
    methods, ignoring inherited interface methods.
    """
    t_param = tp.TypeParameter("D", tp.Invariant)

    # Create base interface with methods (like Roils)
    base_interface = tp.SimpleClassifier(
        "Roils",
        structural=True,
        method_signatures=[
            tp.MethodInfo("firetraps", [], tst.NumberType()),
            tp.MethodInfo("monkey", [tst.NumberType()], tst.StringType())
        ]
    )

    # Create extending interface with no additional methods (like Angering<D> extends Roils)
    extending_classifier = tp.SimpleClassifier(
        "Angering",
        supertypes=[base_interface],
        structural=True,
        method_signatures=[]  # No additional methods
    )
    extending_constructor = tp.TypeConstructor("Angering", [t_param], classifier=extending_classifier)

    # Instantiate the extending interface
    angering_of_string = extending_constructor.new([tst.StringType()])

    # Should have methods from base interface
    methods = angering_of_string._get_all_methods()
    assert "firetraps" in methods, "Should inherit firetraps() from Roils"
    assert "monkey" in methods, "Should inherit monkey() from Roils"

    # Now create a class that doesn't implement those methods
    toast = tp.SimpleClassifier(
        "Toast",
        structural=True,
        field_signatures=[
            tp.FieldInfo("obscurest", tst.NumberType()),
            tp.FieldInfo("marmot", tst.NumberType())
        ],
        method_signatures=[tp.MethodInfo("equals", [tst.NumberType()], tst.TypeScriptBuiltinFactory().get_void_type())]
    )

    # Toast should NOT be a subtype of Angering<string> (missing firetraps, monkey)
    assert not toast.is_subtype(angering_of_string), \
        "Toast should NOT be subtype of Angering<string> (missing interface methods)"
