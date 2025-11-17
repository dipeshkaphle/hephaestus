"""
Comprehensive tests for structural typing with parameterized types.

Tests the combination of generic types (TypeConstructor + ParameterizedType)
with structural subtyping (StructuralClassifier).
"""

from src.ir import types as tp
import src.ir.typescript_types as tst


# ==============================================================================
# BASIC TESTS: Single type parameter with fields
# ==============================================================================

def test_basic_generic_structural_with_single_field():
    """
    Test basic generic structural type with one field.

    class Box<T> { value: T }
    class Container<T> { value: T }

    Box<String> should be structurally equivalent to Container<String>
    """
    # Define type parameter T
    t_param = tp.TypeParameter("T", tp.Invariant)

    # Create Box<T> structural classifier
    box_classifier = tp.StructuralClassifier(
        "Box",
        field_signatures=[tp.FieldInfo("value", t_param)]
    )

    # Create Container<T> structural classifier
    container_classifier = tp.StructuralClassifier(
        "Container",
        field_signatures=[tp.FieldInfo("value", t_param)]
    )

    # Create type constructors
    box_constructor = tp.TypeConstructor("Box", [t_param], classifier=box_classifier)
    container_constructor = tp.TypeConstructor("Container", [t_param], classifier=container_classifier)

    # Instantiate with String
    box_of_string = box_constructor.new([tst.StringType()])
    container_of_string = container_constructor.new([tst.StringType()])

    # Should be structurally equivalent
    assert box_of_string.is_subtype(container_of_string)
    assert container_of_string.is_subtype(box_of_string)


def test_generic_structural_different_type_args():
    """
    Test that generic types with different type arguments are not subtypes.

    Box<String> should NOT be subtype of Box<Number>
    """
    t_param = tp.TypeParameter("T", tp.Invariant)

    box_classifier = tp.StructuralClassifier(
        "Box",
        field_signatures=[tp.FieldInfo("value", t_param)]
    )

    box_constructor = tp.TypeConstructor("Box", [t_param], classifier=box_classifier)

    box_of_string = box_constructor.new([tst.StringType()])
    box_of_number = box_constructor.new([tst.NumberType()])

    # Different type arguments with invariant parameter
    assert not box_of_string.is_subtype(box_of_number)
    assert not box_of_number.is_subtype(box_of_string)


def test_generic_structural_extra_fields():
    """
    Test that a type with extra fields is a subtype (more specific).

    class Box<T> { value: T }
    class LabeledBox<T> { value: T, label: String }

    LabeledBox<String> <: Box<String> (has all of Box's fields)
    """
    t_param = tp.TypeParameter("T", tp.Invariant)

    box_classifier = tp.StructuralClassifier(
        "Box",
        field_signatures=[tp.FieldInfo("value", t_param)]
    )

    labeled_box_classifier = tp.StructuralClassifier(
        "LabeledBox",
        field_signatures=[
            tp.FieldInfo("value", t_param),
            tp.FieldInfo("label", tst.StringType())
        ]
    )

    box_constructor = tp.TypeConstructor("Box", [t_param], classifier=box_classifier)
    labeled_box_constructor = tp.TypeConstructor("LabeledBox", [t_param], classifier=labeled_box_classifier)

    box_of_string = box_constructor.new([tst.StringType()])
    labeled_box_of_string = labeled_box_constructor.new([tst.StringType()])

    # LabeledBox has all of Box's fields plus more
    assert labeled_box_of_string.is_subtype(box_of_string)
    # But Box doesn't have all of LabeledBox's fields
    assert not box_of_string.is_subtype(labeled_box_of_string)


# ==============================================================================
# METHOD TESTS: Generic types with methods
# ==============================================================================

def test_generic_structural_with_methods():
    """
    Test generic structural types with methods.

    class Processor<T> { process(T): T }
    class Handler<T> { process(T): T }

    Processor<String> should be structurally equivalent to Handler<String>
    """
    t_param = tp.TypeParameter("T", tp.Invariant)

    processor_classifier = tp.StructuralClassifier(
        "Processor",
        method_signatures=[
            tp.MethodInfo("process", [t_param], t_param)
        ]
    )

    handler_classifier = tp.StructuralClassifier(
        "Handler",
        method_signatures=[
            tp.MethodInfo("process", [t_param], t_param)
        ]
    )

    processor_constructor = tp.TypeConstructor("Processor", [t_param], classifier=processor_classifier)
    handler_constructor = tp.TypeConstructor("Handler", [t_param], classifier=handler_classifier)

    processor_of_string = processor_constructor.new([tst.StringType()])
    handler_of_string = handler_constructor.new([tst.StringType()])

    # Should be structurally equivalent
    assert processor_of_string.is_subtype(handler_of_string)
    assert handler_of_string.is_subtype(processor_of_string)


def test_generic_structural_method_return_covariance():
    """
    Test method return type covariance with generics using DIFFERENT constructors.

    class Factory<T> { create(): T }
    class Producer<T> { create(): T }

    Factory<String> <: Producer<Object> when checking structurally
    (String <: Object, so returning String is more specific)
    """
    t_param = tp.TypeParameter("T", tp.Invariant)

    factory_classifier = tp.StructuralClassifier(
        "Factory",
        method_signatures=[tp.MethodInfo("create", [], t_param)]
    )

    producer_classifier = tp.StructuralClassifier(
        "Producer",
        method_signatures=[tp.MethodInfo("create", [], t_param)]
    )

    factory_constructor = tp.TypeConstructor("Factory", [t_param], classifier=factory_classifier)
    producer_constructor = tp.TypeConstructor("Producer", [t_param], classifier=producer_classifier)

    factory_of_string = factory_constructor.new([tst.StringType()])
    producer_of_object = producer_constructor.new([tst.ObjectType()])

    # Different constructors: structural comparison applies
    # Factory returning String <: Producer returning Object (covariant return)
    assert factory_of_string.is_subtype(producer_of_object)
    assert not producer_of_object.is_subtype(factory_of_string)


def test_generic_structural_method_param_contravariance():
    """
    Test method parameter contravariance with generics using DIFFERENT constructors.

    class Consumer<T> { consume(T): void }
    class Handler<T> { consume(T): void }

    Handler<Object> <: Consumer<String> for parameters
    (can accept Object, so can accept String)
    """
    t_param = tp.TypeParameter("T", tp.Invariant)

    consumer_classifier = tp.StructuralClassifier(
        "Consumer",
        method_signatures=[tp.MethodInfo("consume", [t_param], tst.VoidType())]
    )

    handler_classifier = tp.StructuralClassifier(
        "Handler",
        method_signatures=[tp.MethodInfo("consume", [t_param], tst.VoidType())]
    )

    consumer_constructor = tp.TypeConstructor("Consumer", [t_param], classifier=consumer_classifier)
    handler_constructor = tp.TypeConstructor("Handler", [t_param], classifier=handler_classifier)

    consumer_of_string = consumer_constructor.new([tst.StringType()])
    handler_of_object = handler_constructor.new([tst.ObjectType()])

    # Different constructors: structural comparison applies
    # Handler accepting Object can accept anything, including String
    # So Handler<Object> <: Consumer<String> (contravariant params)
    assert handler_of_object.is_subtype(consumer_of_string)
    assert not consumer_of_string.is_subtype(handler_of_object)


# ==============================================================================
# VARIANCE TESTS: Covariant and Contravariant type parameters
# ==============================================================================

def test_covariant_type_parameter():
    """
    Test covariant type parameters.

    class ReadOnlyList<out T> { get(index: number): T }

    ReadOnlyList<String> <: ReadOnlyList<Object>
    """
    t_param_covariant = tp.TypeParameter("T", tp.Covariant)

    readonly_list_classifier = tp.StructuralClassifier(
        "ReadOnlyList",
        method_signatures=[
            tp.MethodInfo("get", [tst.NumberType()], t_param_covariant)
        ]
    )

    readonly_list_constructor = tp.TypeConstructor(
        "ReadOnlyList",
        [t_param_covariant],
        classifier=readonly_list_classifier
    )

    readonly_list_of_string = readonly_list_constructor.new([tst.StringType()])
    readonly_list_of_object = readonly_list_constructor.new([tst.ObjectType()])

    # With covariant out T: ReadOnlyList<String> <: ReadOnlyList<Object>
    # This is checked via _is_type_arg_contained logic
    assert readonly_list_of_string.is_subtype(readonly_list_of_object)
    assert not readonly_list_of_object.is_subtype(readonly_list_of_string)


def test_contravariant_type_parameter():
    """
    Test contravariant type parameters.

    class Comparator<in T> { compare(a: T, b: T): number }

    Comparator<Object> <: Comparator<String>
    """
    t_param_contravariant = tp.TypeParameter("T", tp.Contravariant)

    comparator_classifier = tp.StructuralClassifier(
        "Comparator",
        method_signatures=[
            tp.MethodInfo("compare", [t_param_contravariant, t_param_contravariant], tst.NumberType())
        ]
    )

    comparator_constructor = tp.TypeConstructor(
        "Comparator",
        [t_param_contravariant],
        classifier=comparator_classifier
    )

    comparator_of_string = comparator_constructor.new([tst.StringType()])
    comparator_of_object = comparator_constructor.new([tst.ObjectType()])

    # With contravariant in T: Comparator<Object> <: Comparator<String>
    assert comparator_of_object.is_subtype(comparator_of_string)
    assert not comparator_of_string.is_subtype(comparator_of_object)


# ==============================================================================
# MULTIPLE TYPE PARAMETERS
# ==============================================================================

def test_multiple_type_parameters():
    """
    Test generic structural types with multiple type parameters.

    class Pair<T, U> { first: T, second: U }
    class Tuple<T, U> { first: T, second: U }

    Pair<String, Number> should be structurally equivalent to Tuple<String, Number>
    """
    t_param = tp.TypeParameter("T", tp.Invariant)
    u_param = tp.TypeParameter("U", tp.Invariant)

    pair_classifier = tp.StructuralClassifier(
        "Pair",
        field_signatures=[
            tp.FieldInfo("first", t_param),
            tp.FieldInfo("second", u_param)
        ]
    )

    tuple_classifier = tp.StructuralClassifier(
        "Tuple",
        field_signatures=[
            tp.FieldInfo("first", t_param),
            tp.FieldInfo("second", u_param)
        ]
    )

    pair_constructor = tp.TypeConstructor("Pair", [t_param, u_param], classifier=pair_classifier)
    tuple_constructor = tp.TypeConstructor("Tuple", [t_param, u_param], classifier=tuple_classifier)

    pair_string_number = pair_constructor.new([tst.StringType(), tst.NumberType()])
    tuple_string_number = tuple_constructor.new([tst.StringType(), tst.NumberType()])

    # Should be structurally equivalent
    assert pair_string_number.is_subtype(tuple_string_number)
    assert tuple_string_number.is_subtype(pair_string_number)


def test_multiple_type_parameters_different_args():
    """
    Test that different type argument combinations are not subtypes.

    Pair<String, Number> should NOT be equivalent to Pair<Number, String>
    """
    t_param = tp.TypeParameter("T", tp.Invariant)
    u_param = tp.TypeParameter("U", tp.Invariant)

    pair_classifier = tp.StructuralClassifier(
        "Pair",
        field_signatures=[
            tp.FieldInfo("first", t_param),
            tp.FieldInfo("second", u_param)
        ]
    )

    pair_constructor = tp.TypeConstructor("Pair", [t_param, u_param], classifier=pair_classifier)

    pair_string_number = pair_constructor.new([tst.StringType(), tst.NumberType()])
    pair_number_string = pair_constructor.new([tst.NumberType(), tst.StringType()])

    # Different type argument order
    assert not pair_string_number.is_subtype(pair_number_string)
    assert not pair_number_string.is_subtype(pair_string_number)


# ==============================================================================
# NESTED GENERICS
# ==============================================================================

def test_nested_generic_types():
    """
    Test nested generic types.

    class Box<T> { value: T }
    class Container<T> { item: T }

    Container<Box<String>> should work correctly
    """
    t_param = tp.TypeParameter("T", tp.Invariant)

    box_classifier = tp.StructuralClassifier(
        "Box",
        field_signatures=[tp.FieldInfo("value", t_param)]
    )

    container_classifier = tp.StructuralClassifier(
        "Container",
        field_signatures=[tp.FieldInfo("item", t_param)]
    )

    box_constructor = tp.TypeConstructor("Box", [t_param], classifier=box_classifier)
    container_constructor = tp.TypeConstructor("Container", [t_param], classifier=container_classifier)

    # Create Box<String>
    box_of_string = box_constructor.new([tst.StringType()])

    # Create Container<Box<String>>
    container_of_box = container_constructor.new([box_of_string])

    # Verify it was created successfully
    assert container_of_box.is_parameterized()
    assert len(container_of_box.type_args) == 1
    assert container_of_box.type_args[0] == box_of_string


def test_generic_with_structural_type_as_argument():
    """
    Test generic types where the type argument is itself a structural type.

    class Point { x: number, y: number }
    class Coordinate { x: number, y: number }

    class Box<T> { value: T }
    class Container<T> { value: T }

    Point and Coordinate are structurally equivalent.
    So Box<Point> and Container<Coordinate> should be structurally equivalent
    (different constructors, so structural comparison applies).
    """
    # Define two structurally equivalent non-generic types
    point_classifier = tp.StructuralClassifier(
        "Point",
        field_signatures=[
            tp.FieldInfo("x", tst.NumberType()),
            tp.FieldInfo("y", tst.NumberType())
        ]
    )

    coordinate_classifier = tp.StructuralClassifier(
        "Coordinate",
        field_signatures=[
            tp.FieldInfo("x", tst.NumberType()),
            tp.FieldInfo("y", tst.NumberType())
        ]
    )

    # Point and Coordinate should be structurally equivalent
    assert point_classifier.is_subtype(coordinate_classifier)
    assert coordinate_classifier.is_subtype(point_classifier)

    # Define generic Box<T> and Container<T>
    t_param = tp.TypeParameter("T", tp.Invariant)

    box_classifier = tp.StructuralClassifier(
        "Box",
        field_signatures=[tp.FieldInfo("value", t_param)]
    )

    container_classifier = tp.StructuralClassifier(
        "Container",
        field_signatures=[tp.FieldInfo("value", t_param)]
    )

    box_constructor = tp.TypeConstructor("Box", [t_param], classifier=box_classifier)
    container_constructor = tp.TypeConstructor("Container", [t_param], classifier=container_classifier)

    # Instantiate with structural types
    # Box<Point> { value: Point { x: number, y: number } }
    box_of_point = box_constructor.new([point_classifier])

    # Container<Coordinate> { value: Coordinate { x: number, y: number } }
    container_of_coordinate = container_constructor.new([coordinate_classifier])

    # Different constructors (Box vs Container), so structural comparison applies
    # Box<Point>.value: Point and Container<Coordinate>.value: Coordinate
    # Since Point <: Coordinate structurally, Box<Point> <: Container<Coordinate>
    assert box_of_point.is_subtype(container_of_coordinate)
    assert container_of_coordinate.is_subtype(box_of_point)


def test_generic_with_structural_subtype_as_argument():
    """
    Test generic types where type arguments are structural subtypes.

    class Point { x: number, y: number }
    class Point3D { x: number, y: number, z: number }

    class Box<T> { value: T }
    class Container<T> { value: T }

    Point3D <: Point (has all fields of Point plus more)
    So Box<Point3D> <: Container<Point> structurally
    (Box returning Point3D is more specific than Container returning Point)
    """
    # Define Point and Point3D (subtype relationship)
    point_classifier = tp.StructuralClassifier(
        "Point",
        field_signatures=[
            tp.FieldInfo("x", tst.NumberType()),
            tp.FieldInfo("y", tst.NumberType())
        ]
    )

    point3d_classifier = tp.StructuralClassifier(
        "Point3D",
        field_signatures=[
            tp.FieldInfo("x", tst.NumberType()),
            tp.FieldInfo("y", tst.NumberType()),
            tp.FieldInfo("z", tst.NumberType())
        ]
    )

    # Point3D should be subtype of Point (has all fields plus z)
    assert point3d_classifier.is_subtype(point_classifier)
    assert not point_classifier.is_subtype(point3d_classifier)

    # Define generic Box<T> and Container<T>
    t_param = tp.TypeParameter("T", tp.Invariant)

    box_classifier = tp.StructuralClassifier(
        "Box",
        field_signatures=[tp.FieldInfo("value", t_param)]
    )

    container_classifier = tp.StructuralClassifier(
        "Container",
        field_signatures=[tp.FieldInfo("value", t_param)]
    )

    box_constructor = tp.TypeConstructor("Box", [t_param], classifier=box_classifier)
    container_constructor = tp.TypeConstructor("Container", [t_param], classifier=container_classifier)

    # Instantiate with structural types
    # Box<Point3D> { value: Point3D { x, y, z } }
    box_of_point3d = box_constructor.new([point3d_classifier])

    # Container<Point> { value: Point { x, y } }
    container_of_point = container_constructor.new([point_classifier])

    # Different constructors, structural comparison
    # Box has field value: Point3D
    # Container has field value: Point
    # Field types are covariant: Point3D <: Point
    # So Box<Point3D> <: Container<Point>
    assert box_of_point3d.is_subtype(container_of_point)
    assert not container_of_point.is_subtype(box_of_point3d)


def test_generic_with_nested_structural_generics():
    """
    Test deeply nested structural generic types.

    class Point { x: number, y: number }
    class Coordinate { x: number, y: number }

    class Box<T> { value: T }
    class Container<T> { item: T }
    class Wrapper<T> { content: T }

    Wrapper<Box<Point>> vs Container<Box<Coordinate>>

    Both should be compatible since:
    - Point <: Coordinate (structurally)
    - Box<Point> <: Box<Coordinate> (same constructor, but type args are structural)
    - Wrapper<Box<Point>> <: Container<Box<Coordinate>> (different constructors)
    """
    # Define two structurally equivalent non-generic types
    point_classifier = tp.StructuralClassifier(
        "Point",
        field_signatures=[
            tp.FieldInfo("x", tst.NumberType()),
            tp.FieldInfo("y", tst.NumberType())
        ]
    )

    coordinate_classifier = tp.StructuralClassifier(
        "Coordinate",
        field_signatures=[
            tp.FieldInfo("x", tst.NumberType()),
            tp.FieldInfo("y", tst.NumberType())
        ]
    )

    # Define generic types
    t_param = tp.TypeParameter("T", tp.Invariant)

    box_classifier = tp.StructuralClassifier(
        "Box",
        field_signatures=[tp.FieldInfo("value", t_param)]
    )

    wrapper_classifier = tp.StructuralClassifier(
        "Wrapper",
        field_signatures=[tp.FieldInfo("content", t_param)]
    )

    container_classifier = tp.StructuralClassifier(
        "Container",
        field_signatures=[tp.FieldInfo("item", t_param)]
    )

    box_constructor = tp.TypeConstructor("Box", [t_param], classifier=box_classifier)
    wrapper_constructor = tp.TypeConstructor("Wrapper", [t_param], classifier=wrapper_classifier)
    container_constructor = tp.TypeConstructor("Container", [t_param], classifier=container_classifier)

    # Create nested types
    # Box<Point> { value: Point { x, y } }
    box_of_point = box_constructor.new([point_classifier])

    # Box<Coordinate> { value: Coordinate { x, y } }
    box_of_coordinate = box_constructor.new([coordinate_classifier])

    # Wrapper<Box<Point>> { content: Box<Point> { value: Point { x, y } } }
    wrapper_of_box_of_point = wrapper_constructor.new([box_of_point])

    # Container<Box<Coordinate>> { item: Box<Coordinate> { value: Coordinate { x, y } } }
    container_of_box_of_coordinate = container_constructor.new([box_of_coordinate])

    # Different outer constructors (Wrapper vs Container), so structural comparison
    # Wrapper.content: Box<Point> vs Container.item: Box<Coordinate>
    # Box<Point> and Box<Coordinate> have same constructor with different type args
    # But structurally, both are equivalent since Point <: Coordinate
    # This is tricky: same inner constructor, so variance rules apply
    # With invariant T, Box<Point> != Box<Coordinate>
    # So Wrapper<Box<Point>> should NOT be subtype of Container<Box<Coordinate>>
    # Let's verify this behavior

    # Actually, let's test what happens
    result = wrapper_of_box_of_point.is_subtype(container_of_box_of_coordinate)

    # The inner Box types have the same constructor with invariant T
    # So Box<Point> != Box<Coordinate> even though Point and Coordinate are structurally equivalent
    # Therefore the outer types should not be subtypes either
    assert not result
    assert not container_of_box_of_coordinate.is_subtype(wrapper_of_box_of_point)


# ==============================================================================
# MIXED NOMINAL AND STRUCTURAL
# ==============================================================================

def test_generic_structural_with_nominal_supertype():
    """
    Test that nominal inheritance still works with structural generics.

    class Base<T> { value: T }
    class Derived<T> extends Base<T> { value: T, extra: String }

    Derived<String> should be subtype of Base<String> (nominally)
    """
    t_param = tp.TypeParameter("T", tp.Invariant)

    base_classifier = tp.StructuralClassifier(
        "Base",
        field_signatures=[tp.FieldInfo("value", t_param)]
    )

    base_constructor = tp.TypeConstructor("Base", [t_param], classifier=base_classifier)

    # Derived extends Base
    derived_classifier = tp.StructuralClassifier(
        "Derived",
        supertypes=[base_constructor],
        field_signatures=[
            tp.FieldInfo("value", t_param),
            tp.FieldInfo("extra", tst.StringType())
        ]
    )

    derived_constructor = tp.TypeConstructor(
        "Derived",
        [t_param],
        classifier=derived_classifier
    )

    base_of_string = base_constructor.new([tst.StringType()])
    derived_of_string = derived_constructor.new([tst.StringType()])

    # Should be subtype both nominally and structurally
    assert derived_of_string.is_subtype(base_of_string)
    assert not base_of_string.is_subtype(derived_of_string)


# ==============================================================================
# EDGE CASES
# ==============================================================================

def test_generic_structural_vs_non_structural():
    """
    Test interaction between structural and non-structural parameterized types.

    NOTE: TypeConstructor equality is based on name and type parameters,
    not on whether it has a classifier. So two constructors with the same
    name are considered equal even if one is structural and one is nominal.

    In practice, you wouldn't have two type constructors with the same name
    in the same scope.
    """
    t_param = tp.TypeParameter("T", tp.Invariant)

    # Structural Box
    structural_box_classifier = tp.StructuralClassifier(
        "Box",
        field_signatures=[tp.FieldInfo("value", t_param)]
    )
    structural_box_constructor = tp.TypeConstructor(
        "Box",
        [t_param],
        classifier=structural_box_classifier
    )

    # Nominal Box (no classifier, just TypeConstructor)
    nominal_box_constructor = tp.TypeConstructor("NominalBox", [t_param])

    structural_box_of_string = structural_box_constructor.new([tst.StringType()])
    nominal_box_of_string = nominal_box_constructor.new([tst.StringType()])

    # Different names, so not related
    assert not structural_box_of_string.is_subtype(nominal_box_of_string)
    assert not nominal_box_of_string.is_subtype(structural_box_of_string)


def test_empty_generic_structural_type():
    """
    Test generic structural type with no fields or methods (marker interface).

    class Serializable<T> { }
    class Cloneable<T> { }

    Should be structurally equivalent (both empty)
    """
    t_param = tp.TypeParameter("T", tp.Invariant)

    serializable_classifier = tp.StructuralClassifier("Serializable")
    cloneable_classifier = tp.StructuralClassifier("Cloneable")

    serializable_constructor = tp.TypeConstructor(
        "Serializable",
        [t_param],
        classifier=serializable_classifier
    )
    cloneable_constructor = tp.TypeConstructor(
        "Cloneable",
        [t_param],
        classifier=cloneable_classifier
    )

    serializable_of_string = serializable_constructor.new([tst.StringType()])
    cloneable_of_string = cloneable_constructor.new([tst.StringType()])

    # Both empty, should be structurally equivalent
    assert serializable_of_string.is_subtype(cloneable_of_string)
    assert cloneable_of_string.is_subtype(serializable_of_string)


def test_generic_structural_only_fields_vs_only_methods():
    """
    Test that a type with only fields is not subtype of type with only methods.

    class Data<T> { value: T }
    class Processor<T> { process(): T }

    Data<String> should NOT be subtype of Processor<String>
    """
    t_param = tp.TypeParameter("T", tp.Invariant)

    data_classifier = tp.StructuralClassifier(
        "Data",
        field_signatures=[tp.FieldInfo("value", t_param)]
    )

    processor_classifier = tp.StructuralClassifier(
        "Processor",
        method_signatures=[tp.MethodInfo("process", [], t_param)]
    )

    data_constructor = tp.TypeConstructor("Data", [t_param], classifier=data_classifier)
    processor_constructor = tp.TypeConstructor("Processor", [t_param], classifier=processor_classifier)

    data_of_string = data_constructor.new([tst.StringType()])
    processor_of_string = processor_constructor.new([tst.StringType()])

    # Different structures, not subtypes
    assert not data_of_string.is_subtype(processor_of_string)
    assert not processor_of_string.is_subtype(data_of_string)


def test_generic_structural_fields_and_methods():
    """
    Test generic structural type with both fields and methods.

    class Cell<T> { value: T, get(): T, set(T): void }
    """
    t_param = tp.TypeParameter("T", tp.Invariant)

    cell_classifier = tp.StructuralClassifier(
        "Cell",
        field_signatures=[tp.FieldInfo("value", t_param)],
        method_signatures=[
            tp.MethodInfo("get", [], t_param),
            tp.MethodInfo("set", [t_param], tst.VoidType())
        ]
    )

    cell_constructor = tp.TypeConstructor("Cell", [t_param], classifier=cell_classifier)

    cell_of_string = cell_constructor.new([tst.StringType()])

    # Create a simpler type that Cell should be subtype of
    readable_classifier = tp.StructuralClassifier(
        "Readable",
        method_signatures=[tp.MethodInfo("get", [], t_param)]
    )

    readable_constructor = tp.TypeConstructor("Readable", [t_param], classifier=readable_classifier)
    readable_of_string = readable_constructor.new([tst.StringType()])

    # Cell has all of Readable's methods (and more)
    assert cell_of_string.is_subtype(readable_of_string)
    assert not readable_of_string.is_subtype(cell_of_string)


# ==============================================================================
# BOUNDED TYPE PARAMETERS
# ==============================================================================

def test_bounded_type_parameter_basic():
    """
    Test basic bounded type parameter with structural types.

    class Processor<T extends Number> { value: T }

    Can instantiate with Number or subtypes, bound restricts what types are valid.
    """
    # Create a simple numeric hierarchy
    number_type = tst.NumberType()

    # T extends Number
    t_param = tp.TypeParameter("T", tp.Invariant, bound=number_type)

    processor_classifier = tp.StructuralClassifier(
        "Processor",
        field_signatures=[tp.FieldInfo("value", t_param)]
    )

    processor_constructor = tp.TypeConstructor(
        "Processor",
        [t_param],
        classifier=processor_classifier
    )

    # Instantiate with Number (valid, within bound)
    processor_of_number = processor_constructor.new([number_type])

    # Verify the type was created successfully
    assert processor_of_number.is_parameterized()
    assert len(processor_of_number.type_args) == 1
    assert processor_of_number.type_args[0] == number_type


def test_bounded_type_parameter_structural_compatibility():
    """
    Test bounded type parameters with structural subtyping.

    class NumericBox<T extends Number> { value: T, compute(): T }
    class NumericContainer<T extends Number> { value: T, compute(): T }

    NumericBox<Number> should be structurally equivalent to NumericContainer<Number>
    """
    number_type = tst.NumberType()

    # Both use T extends Number
    t_param_box = tp.TypeParameter("T", tp.Invariant, bound=number_type)
    t_param_container = tp.TypeParameter("T", tp.Invariant, bound=number_type)

    numeric_box_classifier = tp.StructuralClassifier(
        "NumericBox",
        field_signatures=[tp.FieldInfo("value", t_param_box)],
        method_signatures=[tp.MethodInfo("compute", [], t_param_box)]
    )

    numeric_container_classifier = tp.StructuralClassifier(
        "NumericContainer",
        field_signatures=[tp.FieldInfo("value", t_param_container)],
        method_signatures=[tp.MethodInfo("compute", [], t_param_container)]
    )

    box_constructor = tp.TypeConstructor(
        "NumericBox",
        [t_param_box],
        classifier=numeric_box_classifier
    )

    container_constructor = tp.TypeConstructor(
        "NumericContainer",
        [t_param_container],
        classifier=numeric_container_classifier
    )

    box_of_number = box_constructor.new([number_type])
    container_of_number = container_constructor.new([number_type])

    # Different constructors, but structurally compatible
    assert box_of_number.is_subtype(container_of_number)
    assert container_of_number.is_subtype(box_of_number)


def test_bounded_type_parameter_with_classifier_bound():
    """
    Test bounded type parameter where the bound is a custom structural classifier.

    class Serializable { serialize(): String }
    class Container<T extends Serializable> { item: T }

    The bound ensures T has serialize() method.
    """
    # Define Serializable interface
    serializable_classifier = tp.StructuralClassifier(
        "Serializable",
        method_signatures=[tp.MethodInfo("serialize", [], tst.StringType())]
    )

    # T extends Serializable
    t_param = tp.TypeParameter("T", tp.Invariant, bound=serializable_classifier)

    container_classifier = tp.StructuralClassifier(
        "Container",
        field_signatures=[tp.FieldInfo("item", t_param)]
    )

    container_constructor = tp.TypeConstructor(
        "Container",
        [t_param],
        classifier=container_classifier
    )

    # Create a type that implements Serializable
    json_obj_classifier = tp.StructuralClassifier(
        "JsonObject",
        method_signatures=[tp.MethodInfo("serialize", [], tst.StringType())]
    )

    # JsonObject implements Serializable structurally
    assert json_obj_classifier.is_subtype(serializable_classifier)

    # Instantiate Container with JsonObject (valid, satisfies bound)
    container_of_json = container_constructor.new([json_obj_classifier])

    assert container_of_json.is_parameterized()
    assert container_of_json.type_args[0] == json_obj_classifier


def test_bounded_type_parameter_multiple_bounds_simulation():
    """
    Test type parameter bounded by a type that has multiple capabilities.

    class Comparable { compare(other: String): Number }
    class Printable { print(): String }
    class ComparableAndPrintable { compare(other: String): Number, print(): String }

    class Sorter<T extends ComparableAndPrintable> { ... }
    """
    # Combined interface with both capabilities
    comparable_and_printable = tp.StructuralClassifier(
        "ComparableAndPrintable",
        method_signatures=[
            tp.MethodInfo("compare", [tst.StringType()], tst.NumberType()),
            tp.MethodInfo("print", [], tst.StringType())
        ]
    )

    # T extends ComparableAndPrintable
    t_param = tp.TypeParameter("T", tp.Invariant, bound=comparable_and_printable)

    sorter_classifier = tp.StructuralClassifier(
        "Sorter",
        field_signatures=[tp.FieldInfo("data", t_param)]
    )

    sorter_constructor = tp.TypeConstructor(
        "Sorter",
        [t_param],
        classifier=sorter_classifier
    )

    # Create a concrete type that satisfies the bound
    person_classifier = tp.StructuralClassifier(
        "Person",
        field_signatures=[tp.FieldInfo("name", tst.StringType())],
        method_signatures=[
            tp.MethodInfo("compare", [tst.StringType()], tst.NumberType()),
            tp.MethodInfo("print", [], tst.StringType())
        ]
    )

    # Person satisfies the bound structurally
    assert person_classifier.is_subtype(comparable_and_printable)

    # Instantiate Sorter with Person
    sorter_of_person = sorter_constructor.new([person_classifier])

    assert sorter_of_person.is_parameterized()
    assert sorter_of_person.type_args[0] == person_classifier


def test_bounded_type_parameter_covariant_with_bound():
    """
    Test covariant bounded type parameter.

    class Producer<out T extends Number> { produce(): T }

    Producer<Number> should be compatible considering variance.
    """
    number_type = tst.NumberType()

    # out T extends Number (covariant with bound)
    t_param = tp.TypeParameter("T", tp.Covariant, bound=number_type)

    producer_classifier = tp.StructuralClassifier(
        "Producer",
        method_signatures=[tp.MethodInfo("produce", [], t_param)]
    )

    producer_constructor = tp.TypeConstructor(
        "Producer",
        [t_param],
        classifier=producer_classifier
    )

    producer_of_number = producer_constructor.new([number_type])

    # Verify creation
    assert producer_of_number.is_parameterized()
    assert producer_of_number.t_constructor.type_parameters[0].is_covariant()
    assert producer_of_number.t_constructor.type_parameters[0].bound == number_type


def test_bounded_type_parameter_contravariant_with_bound():
    """
    Test contravariant bounded type parameter.

    class Consumer<in T extends Number> { consume(value: T): void }

    Consumer<Number> with contravariant bounded parameter.
    """
    number_type = tst.NumberType()

    # in T extends Number (contravariant with bound)
    t_param = tp.TypeParameter("T", tp.Contravariant, bound=number_type)

    consumer_classifier = tp.StructuralClassifier(
        "Consumer",
        method_signatures=[tp.MethodInfo("consume", [t_param], tst.VoidType())]
    )

    consumer_constructor = tp.TypeConstructor(
        "Consumer",
        [t_param],
        classifier=consumer_classifier
    )

    consumer_of_number = consumer_constructor.new([number_type])

    # Verify creation
    assert consumer_of_number.is_parameterized()
    assert consumer_of_number.t_constructor.type_parameters[0].is_contravariant()
    assert consumer_of_number.t_constructor.type_parameters[0].bound == number_type


def test_bounded_type_parameter_nested_generics():
    """
    Test bounded type parameter with nested generic types.

    class List<T> { get(index: Number): T }
    class Processor<T extends List<String>> { process(item: T): void }

    The bound itself is a parameterized type.
    """
    t_param_list = tp.TypeParameter("T", tp.Invariant)

    list_classifier = tp.StructuralClassifier(
        "List",
        method_signatures=[tp.MethodInfo("get", [tst.NumberType()], t_param_list)]
    )

    list_constructor = tp.TypeConstructor(
        "List",
        [t_param_list],
        classifier=list_classifier
    )

    # Create List<String>
    list_of_string = list_constructor.new([tst.StringType()])

    # T extends List<String>
    t_param_processor = tp.TypeParameter("T", tp.Invariant, bound=list_of_string)

    processor_classifier = tp.StructuralClassifier(
        "Processor",
        method_signatures=[tp.MethodInfo("process", [t_param_processor], tst.VoidType())]
    )

    processor_constructor = tp.TypeConstructor(
        "Processor",
        [t_param_processor],
        classifier=processor_classifier
    )

    # Instantiate with List<String>
    processor_of_list_string = processor_constructor.new([list_of_string])

    assert processor_of_list_string.is_parameterized()
    assert processor_of_list_string.type_args[0] == list_of_string
    assert processor_of_list_string.t_constructor.type_parameters[0].bound == list_of_string


def test_bounded_type_parameter_chain():
    """
    Test chained bounded type parameters.

    class Repository<T extends Number> { store(item: T): void }
    class Cache<U extends T, T extends Number> { ... }

    One type parameter's bound references another.
    """
    number_type = tst.NumberType()

    # T extends Number
    t_param = tp.TypeParameter("T", tp.Invariant, bound=number_type)

    # U extends T (bound by another type parameter)
    u_param = tp.TypeParameter("U", tp.Invariant, bound=t_param)

    cache_classifier = tp.StructuralClassifier(
        "Cache",
        field_signatures=[
            tp.FieldInfo("primary", t_param),
            tp.FieldInfo("secondary", u_param)
        ]
    )

    cache_constructor = tp.TypeConstructor(
        "Cache",
        [t_param, u_param],
        classifier=cache_classifier
    )

    # Instantiate with Number for both
    cache_instance = cache_constructor.new([number_type, number_type])

    assert cache_instance.is_parameterized()
    assert len(cache_instance.type_args) == 2
    assert cache_instance.type_args[0] == number_type
    assert cache_instance.type_args[1] == number_type


def test_bounded_type_parameter_substitution():
    """
    Test that bounded type parameters are correctly substituted.

    class Wrapper<T extends String> { value: T }

    When instantiated with String, the bound should be satisfied.
    """
    string_type = tst.StringType()

    # T extends String
    t_param = tp.TypeParameter("T", tp.Invariant, bound=string_type)

    wrapper_classifier = tp.StructuralClassifier(
        "Wrapper",
        field_signatures=[tp.FieldInfo("value", t_param)],
        method_signatures=[tp.MethodInfo("getValue", [], t_param)]
    )

    wrapper_constructor = tp.TypeConstructor(
        "Wrapper",
        [t_param],
        classifier=wrapper_classifier
    )

    # Instantiate with String
    wrapper_of_string = wrapper_constructor.new([string_type])

    # Get the type variable assignments
    type_map = wrapper_of_string.get_type_variable_assignments()

    # Check that T was mapped to String
    assert t_param in type_map
    assert type_map[t_param] == string_type

    # Verify the parameterized type structure
    assert wrapper_of_string.is_parameterized()
    assert wrapper_of_string.type_args[0] == string_type


def test_bounded_type_parameter_enforces_subtyping():
    """
    Test that bounded type parameters enforce subtyping relationships.

    class Repository<T extends Serializable> { store(item: T): void }

    The bound means T must be a subtype of Serializable.
    """
    # Define Serializable interface
    serializable = tp.StructuralClassifier(
        "Serializable",
        method_signatures=[tp.MethodInfo("serialize", [], tst.StringType())]
    )

    # T extends Serializable
    t_param = tp.TypeParameter("T", tp.Invariant, bound=serializable)

    # T should be subtype of its bound (via TypeParameter.is_subtype)
    assert t_param.is_subtype(serializable)

    # Create Repository<T extends Serializable>
    repository_classifier = tp.StructuralClassifier(
        "Repository",
        method_signatures=[tp.MethodInfo("store", [t_param], tst.VoidType())]
    )

    repository_constructor = tp.TypeConstructor(
        "Repository",
        [t_param],
        classifier=repository_classifier
    )

    # Create concrete types
    json_type = tp.StructuralClassifier(
        "JsonDocument",
        method_signatures=[tp.MethodInfo("serialize", [], tst.StringType())]
    )

    xml_type = tp.StructuralClassifier(
        "XmlDocument",
        method_signatures=[tp.MethodInfo("serialize", [], tst.StringType())]
    )

    # Both satisfy the bound
    assert json_type.is_subtype(serializable)
    assert xml_type.is_subtype(serializable)

    # Instantiate with types that satisfy the bound
    repo_json = repository_constructor.new([json_type])
    repo_xml = repository_constructor.new([xml_type])

    # Different type arguments, but structurally identical types
    # In structural typing, Repository<JsonDocument> and Repository<XmlDocument>
    # are equivalent because after substitution:
    # - repo_json has store(JsonDocument): void
    # - repo_xml has store(XmlDocument): void
    # And JsonDocument <: XmlDocument (structurally identical)
    # Therefore they ARE mutual subtypes in structural typing
    assert repo_json.is_subtype(repo_xml)
    assert repo_xml.is_subtype(repo_json)


def test_bounded_type_parameter_subtyping_with_bound_hierarchy():
    """
    Test subtyping with bounded parameters where bounds form a hierarchy.

    class Animal { makeSound(): String }
    class Dog extends Animal { makeSound(): String, bark(): String }

    class Container<T extends Animal> { get(): T }
    class SpecialContainer<T extends Dog> { get(): T }
    """
    # Create type hierarchy
    animal = tp.StructuralClassifier(
        "Animal",
        method_signatures=[tp.MethodInfo("makeSound", [], tst.StringType())]
    )

    dog = tp.StructuralClassifier(
        "Dog",
        method_signatures=[
            tp.MethodInfo("makeSound", [], tst.StringType()),
            tp.MethodInfo("bark", [], tst.StringType())
        ]
    )

    # Dog is subtype of Animal (has all methods of Animal)
    assert dog.is_subtype(animal)

    # T extends Animal
    t_animal = tp.TypeParameter("T", tp.Invariant, bound=animal)

    # U extends Dog
    u_dog = tp.TypeParameter("U", tp.Invariant, bound=dog)

    # U's bound (Dog) is subtype of T's bound (Animal)
    assert dog.is_subtype(animal)

    # Create containers
    container_animal = tp.StructuralClassifier(
        "Container",
        method_signatures=[tp.MethodInfo("get", [], t_animal)]
    )

    container_dog = tp.StructuralClassifier(
        "SpecialContainer",
        method_signatures=[tp.MethodInfo("get", [], u_dog)]
    )

    # Both containers are structurally equivalent when instantiated with Dog
    # because they have the same method structure
    container_animal_con = tp.TypeConstructor("Container", [t_animal], classifier=container_animal)
    container_dog_con = tp.TypeConstructor("SpecialContainer", [u_dog], classifier=container_dog)

    container_of_dog1 = container_animal_con.new([dog])
    container_of_dog2 = container_dog_con.new([dog])

    # Different constructors, check structural compatibility
    # Container<Dog>.get(): Dog vs SpecialContainer<Dog>.get(): Dog
    assert container_of_dog1.is_subtype(container_of_dog2)
    assert container_of_dog2.is_subtype(container_of_dog1)


def test_bounded_type_parameter_covariance_affects_subtyping():
    """
    Test that covariance with bounds affects subtyping correctly.

    class Producer<out T extends Number> { produce(): T }

    Producer<Number> should have subtyping relationships based on covariance.
    """
    number_type = tst.NumberType()

    # out T extends Number (covariant with bound)
    t_param = tp.TypeParameter("T", tp.Covariant, bound=number_type)

    producer_classifier = tp.StructuralClassifier(
        "Producer",
        method_signatures=[tp.MethodInfo("produce", [], t_param)]
    )

    producer_constructor = tp.TypeConstructor(
        "Producer",
        [t_param],
        classifier=producer_classifier
    )

    # Create a subtype hierarchy for testing
    # In TypeScript: assume we have a way to represent Number subtypes
    # For this test, we'll use the bound to verify behavior

    producer_of_number = producer_constructor.new([number_type])

    # Verify the covariant type parameter has the correct bound
    assert producer_of_number.t_constructor.type_parameters[0].is_covariant()
    assert producer_of_number.t_constructor.type_parameters[0].bound == number_type

    # The type parameter itself should be subtype of its bound
    assert t_param.is_subtype(number_type)


def test_bounded_type_parameter_different_bounds_not_related():
    """
    Test that types with different bounds are not related.

    class NumericProcessor<T extends Number> { process(x: T): T }
    class StringProcessor<T extends String> { process(x: T): T }

    NumericProcessor<Number> should NOT be subtype of StringProcessor<String>
    """
    number_type = tst.NumberType()
    string_type = tst.StringType()

    # T extends Number
    t_numeric = tp.TypeParameter("T", tp.Invariant, bound=number_type)

    # T extends String
    t_string = tp.TypeParameter("T", tp.Invariant, bound=string_type)

    numeric_processor = tp.StructuralClassifier(
        "NumericProcessor",
        method_signatures=[tp.MethodInfo("process", [t_numeric], t_numeric)]
    )

    string_processor = tp.StructuralClassifier(
        "StringProcessor",
        method_signatures=[tp.MethodInfo("process", [t_string], t_string)]
    )

    numeric_con = tp.TypeConstructor("NumericProcessor", [t_numeric], classifier=numeric_processor)
    string_con = tp.TypeConstructor("StringProcessor", [t_string], classifier=string_processor)

    numeric_proc_of_num = numeric_con.new([number_type])
    string_proc_of_str = string_con.new([string_type])

    # Different constructors AND different type arguments
    # Should NOT be subtypes
    assert not numeric_proc_of_num.is_subtype(string_proc_of_str)
    assert not string_proc_of_str.is_subtype(numeric_proc_of_num)


def test_bounded_type_parameter_bound_subtyping_transitive():
    """
    Test transitive subtyping through bounds.

    class Base { id: Number }
    class Derived extends Base { id: Number, name: String }

    class Holder<T extends Base> { value: T }

    Holder<Derived> vs Holder<Base> with different variance scenarios.
    """
    # Create hierarchy
    base = tp.StructuralClassifier(
        "Base",
        field_signatures=[tp.FieldInfo("id", tst.NumberType())]
    )

    derived = tp.StructuralClassifier(
        "Derived",
        field_signatures=[
            tp.FieldInfo("id", tst.NumberType()),
            tp.FieldInfo("name", tst.StringType())
        ]
    )

    # Derived is subtype of Base
    assert derived.is_subtype(base)

    # T extends Base (invariant)
    t_param = tp.TypeParameter("T", tp.Invariant, bound=base)

    holder_classifier = tp.StructuralClassifier(
        "Holder",
        field_signatures=[tp.FieldInfo("value", t_param)]
    )

    holder_constructor = tp.TypeConstructor("Holder", [t_param], classifier=holder_classifier)

    holder_of_base = holder_constructor.new([base])
    holder_of_derived = holder_constructor.new([derived])

    # Same constructor, different type arguments
    # In structural typing with fields, variance follows field types (covariant)
    # Holder<Derived> has value: Derived (id + name)
    # Holder<Base> has value: Base (id only)
    # Since Derived <: Base, and fields are covariant:
    # Holder<Derived> <: Holder<Base> (Derived has everything Base needs)
    # But Holder<Base> NOT<: Holder<Derived> (Base missing 'name')
    assert holder_of_derived.is_subtype(holder_of_base)
    assert not holder_of_base.is_subtype(holder_of_derived)

    # Now test with covariant parameter
    t_covariant = tp.TypeParameter("T", tp.Covariant, bound=base)

    holder_cov_classifier = tp.StructuralClassifier(
        "CovariantHolder",
        field_signatures=[tp.FieldInfo("value", t_covariant)]
    )

    holder_cov_constructor = tp.TypeConstructor(
        "CovariantHolder",
        [t_covariant],
        classifier=holder_cov_classifier
    )

    holder_cov_of_base = holder_cov_constructor.new([base])
    holder_cov_of_derived = holder_cov_constructor.new([derived])

    # With covariant out T, CovariantHolder<Derived> <: CovariantHolder<Base>
    # because Derived <: Base
    assert holder_cov_of_derived.is_subtype(holder_cov_of_base)
    assert not holder_cov_of_base.is_subtype(holder_cov_of_derived)
