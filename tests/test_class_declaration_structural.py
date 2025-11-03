"""
Tests for ClassDeclaration with structural typing parameter.

Tests that the `structural` parameter correctly enables structural typing
when True and maintains backward-compatible nominal typing when False.
"""

from src.ir import ast, types as tp
import src.ir.typescript_types as tst


def test_class_declaration_default_nominal_typing():
    """Test that ClassDeclaration defaults to nominal typing (structural=False)."""
    # Create a simple non-generic class without structural flag
    class_decl = ast.ClassDeclaration(
        name="MyClass",
        superclasses=[],
        fields=[ast.FieldDeclaration("x", tst.NumberType())],
        functions=[]
    )

    # Get the type
    class_type = class_decl.get_type()

    # Should be SimpleClassifier (nominal typing)
    assert isinstance(class_type, tp.SimpleClassifier)
    assert not class_type.structural
    assert class_type.name == "MyClass"


def test_class_declaration_explicit_nominal_typing():
    """Test ClassDeclaration with structural=False explicitly."""
    class_decl = ast.ClassDeclaration(
        name="MyClass",
        superclasses=[],
        fields=[ast.FieldDeclaration("x", tst.NumberType())],
        functions=[],
        structural=False
    )

    class_type = class_decl.get_type()

    # Should be SimpleClassifier (nominal typing)
    assert isinstance(class_type, tp.SimpleClassifier)
    assert not class_type.structural


def test_class_declaration_structural_typing():
    """Test ClassDeclaration with structural=True enables structural typing."""
    class_decl = ast.ClassDeclaration(
        name="MyClass",
        superclasses=[],
        fields=[ast.FieldDeclaration("x", tst.NumberType())],
        functions=[],
        structural=True
    )

    class_type = class_decl.get_type()

    # Should be SimpleClassifier with structural=True
    assert isinstance(class_type, tp.SimpleClassifier)
    assert class_type.structural
    assert class_type.name == "MyClass"

    # Should have field signatures
    assert len(class_type.field_signatures) == 1
    assert class_type.field_signatures[0].name == "x"
    assert class_type.field_signatures[0].field_type == tst.NumberType()


def test_generic_class_declaration_nominal():
    """Test generic ClassDeclaration defaults to nominal typing."""
    t_param = tp.TypeParameter("T", tp.Invariant)

    class_decl = ast.ClassDeclaration(
        name="Box",
        superclasses=[],
        fields=[ast.FieldDeclaration("value", t_param)],
        functions=[],
        type_parameters=[t_param]
    )

    class_type = class_decl.get_type()

    # Should be TypeConstructor without classifier (nominal)
    assert isinstance(class_type, tp.TypeConstructor)
    assert class_type.name == "Box"
    assert class_type.classifier is None
    assert len(class_type.type_parameters) == 1


def test_generic_class_declaration_structural():
    """Test generic ClassDeclaration with structural=True."""
    t_param = tp.TypeParameter("T", tp.Invariant)

    class_decl = ast.ClassDeclaration(
        name="Box",
        superclasses=[],
        fields=[ast.FieldDeclaration("value", t_param)],
        functions=[],
        type_parameters=[t_param],
        structural=True
    )

    class_type = class_decl.get_type()

    # Should be TypeConstructor with structural classifier
    assert isinstance(class_type, tp.TypeConstructor)
    assert class_type.name == "Box"
    assert class_type.classifier is not None
    assert class_type.classifier.structural

    # Classifier should have field signatures with type parameter
    assert len(class_type.classifier.field_signatures) == 1
    assert class_type.classifier.field_signatures[0].name == "value"
    assert class_type.classifier.field_signatures[0].field_type == t_param


def test_structural_class_with_methods():
    """Test structural ClassDeclaration with methods."""
    ret_type = tst.StringType()
    func_decl = ast.FunctionDeclaration(
        name="foo",
        params=[],
        ret_type=ret_type,
        body=ast.Block([]),
        func_type=ast.FunctionDeclaration.CLASS_METHOD
    )

    class_decl = ast.ClassDeclaration(
        name="MyClass",
        superclasses=[],
        fields=[],
        functions=[func_decl],
        structural=True
    )

    class_type = class_decl.get_type()

    # Should be SimpleClassifier with structural=True and method signatures
    assert isinstance(class_type, tp.SimpleClassifier)
    assert class_type.structural
    assert len(class_type.method_signatures) == 1
    assert class_type.method_signatures[0].name == "foo"
    assert class_type.method_signatures[0].return_type == ret_type


def test_structural_generic_instantiation():
    """Test that structural generic ClassDeclaration can be instantiated correctly."""
    t_param = tp.TypeParameter("T", tp.Invariant)

    box_decl = ast.ClassDeclaration(
        name="Box",
        superclasses=[],
        fields=[ast.FieldDeclaration("value", t_param)],
        functions=[],
        type_parameters=[t_param],
        structural=True
    )

    box_constructor = box_decl.get_type()

    # Instantiate with String
    box_of_string = box_constructor.new([tst.StringType()])

    # Should be ParameterizedType
    assert box_of_string.is_parameterized()
    assert len(box_of_string.type_args) == 1
    assert box_of_string.type_args[0] == tst.StringType()


def test_structural_equivalence_from_class_declarations():
    """Test that two structural ClassDeclarations with same structure are equivalent."""
    # Create Box<T> with structural=True
    t_param1 = tp.TypeParameter("T", tp.Invariant)
    box_decl = ast.ClassDeclaration(
        name="Box",
        superclasses=[],
        fields=[ast.FieldDeclaration("value", t_param1)],
        functions=[],
        type_parameters=[t_param1],
        structural=True
    )

    # Create Container<T> with structural=True and same structure
    t_param2 = tp.TypeParameter("T", tp.Invariant)
    container_decl = ast.ClassDeclaration(
        name="Container",
        superclasses=[],
        fields=[ast.FieldDeclaration("value", t_param2)],
        functions=[],
        type_parameters=[t_param2],
        structural=True
    )

    # Get types
    box_constructor = box_decl.get_type()
    container_constructor = container_decl.get_type()

    # Instantiate both with String
    box_of_string = box_constructor.new([tst.StringType()])
    container_of_string = container_constructor.new([tst.StringType()])

    # Should be structurally equivalent (different constructors, so structural check applies)
    assert box_of_string.is_subtype(container_of_string)
    assert container_of_string.is_subtype(box_of_string)


def test_nominal_not_structurally_equivalent():
    """Test that nominal (structural=False) classes are NOT structurally equivalent."""
    # Create Box<T> with structural=False (nominal)
    t_param1 = tp.TypeParameter("T", tp.Invariant)
    box_decl = ast.ClassDeclaration(
        name="Box",
        superclasses=[],
        fields=[ast.FieldDeclaration("value", t_param1)],
        functions=[],
        type_parameters=[t_param1],
        structural=False
    )

    # Create Container<T> with structural=False and same structure
    t_param2 = tp.TypeParameter("T", tp.Invariant)
    container_decl = ast.ClassDeclaration(
        name="Container",
        superclasses=[],
        fields=[ast.FieldDeclaration("value", t_param2)],
        functions=[],
        type_parameters=[t_param2],
        structural=False
    )

    # Get types
    box_constructor = box_decl.get_type()
    container_constructor = container_decl.get_type()

    # Instantiate both with String
    box_of_string = box_constructor.new([tst.StringType()])
    container_of_string = container_constructor.new([tst.StringType()])

    # Should NOT be subtypes (nominal typing, different constructors, no inheritance)
    assert not box_of_string.is_subtype(container_of_string)
    assert not container_of_string.is_subtype(box_of_string)


def test_backward_compatibility_with_existing_code():
    """Test that existing code without structural parameter still works."""
    # Create ClassDeclaration without structural parameter (should default to False)
    t_param = tp.TypeParameter("T", tp.Invariant)

    class_decl = ast.ClassDeclaration(
        name="LegacyClass",
        superclasses=[],
        fields=[ast.FieldDeclaration("data", t_param)],
        functions=[],
        type_parameters=[t_param]
        # Note: no structural parameter
    )

    # Should work fine and use nominal typing
    class_type = class_decl.get_type()
    assert isinstance(class_type, tp.TypeConstructor)
    assert class_type.classifier is None  # No structural classifier
