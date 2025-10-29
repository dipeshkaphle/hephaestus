# pylint: disable=abstract-method
from __future__ import annotations
from copy import deepcopy, copy
from collections import defaultdict
from typing import List, Dict, Set

from src.ir.node import Node
from src.ir.decorators import two_way_subtyping


class Variance(object):
    INVARIANT = 0
    COVARIANT = 1
    CONTRAVARIANT = 2

    def __init__(self, value):
        self.value = value

    def variance_to_str(self):
        if self.value == 1:
            return 'out'
        if self.value == 2:
            return 'in'
        return ''

    def is_covariant(self):
        return self.value == 1

    def is_contravariant(self):
        return self.value == 2

    def is_invariant(self):
        return self.value == 0

    def __hash__(self):
        return hash(str(self.value))

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.value == other.value
        )


Invariant = Variance(Variance.INVARIANT)
Covariant = Variance(Variance.COVARIANT)
Contravariant = Variance(Variance.CONTRAVARIANT)


class Type(Node):
    def __init__(self, name):
        self.name = name
        self.supertypes = []

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return self.__str__()

    def has_type_variables(self):
        raise NotImplementedError("You have to implement has_type_variables()")

    def is_subtype(self, other: Type):
        raise NotImplementedError("You have to implement 'is_subtype()'")

    def two_way_subtyping(self, other: Type):
        """
        Overwritten when a certain type needs
        two-way subtyping checks.

        Eg. when checking if a string type is a subtype
        of union type 'Foo | string' we call this method
        as `union-type.two_way_subtyping(string_type)`
        to check from the union's side.

        """
        return False

    def is_assignable(self, other: Type):
        """
        Checks of a value of the current type is assignable to 'other' type.

        By default, the current type should be subtype of the other type.
        However, this is not always the case, e.g., in Groovy / Java,
        a value of type Short can be assigned to a value of type Integer,
        but Short is not subtype of Integer.
        """
        return self.is_subtype(other)

    def is_primitive(self):
        raise NotImplementedError("You have to implement 'is_primitive()'")

    def is_type_var(self):
        return False

    def is_wildcard(self):
        return False

    def is_compound(self):
        return False

    def is_parameterized(self):
        return False

    def is_type_constructor(self):
        return False

    def is_function_type(self):
        return False

    def get_supertypes(self):
        """Return self and the transitive closure of the supertypes"""
        stack = [self]
        visited = {self}
        while stack:
            source = stack.pop()
            for supertype in source.supertypes:
                if supertype not in visited:
                    visited.add(supertype)
                    stack.append(supertype)
        return visited

    def substitute_type(self, type_map,
                        cond=lambda t: t.has_type_variables()):
        return self

    def not_related(self, other: Type):
        return not(self.is_subtype(other) or other.is_subtype(self))

    def get_name(self):
        return str(self.name)


class AbstractType(Type):
    def is_subtype(self, other):
        raise TypeError("You cannot call 'is_subtype()' in an AbstractType")

    def get_supertypes(self):
        return super().get_supertypes()

    def has_type_variables(self):
        return True

    def not_related(self, other):
        raise TypeError("You cannot call 'not_related()' in an AbstractType")

    def is_primitive(self):
        return False


class Builtin(Type):
    """https://kotlinlang.org/spec/type-system.html#built-in-types
    """

    def __init__(self, name: str):
        super().__init__(name)
        self.supertypes = []

    def has_type_variables(self):
        return False

    def __str__(self):
        return str(self.name) + "(builtin)"

    def __eq__(self, other: Type):
        """Check if two Builtin objects are of the same Type"""
        return self.__class__ == other.__class__

    def __hash__(self):
        """Hash based on the Type"""
        return hash(str(self.__class__))

    @two_way_subtyping
    def is_subtype(self, other: Type) -> bool:
        return other == self or other in self.get_supertypes()

    def get_builtin_type(self):
        raise NotImplementedError("You have to implement get_builtin_type")


class Classifier(Type):
    def is_primitive(self):
        return False


class Object(Classifier):

    def __str__(self):
        return "object " + self.name


class SimpleClassifier(Classifier):
    """https://kotlinlang.org/spec/type-system.html#simple-classifier-types
    """

    def __init__(self, name: str, supertypes: List[Type] = None, check=False):
        super().__init__(name)
        self.supertypes = supertypes if supertypes is not None else []
        if check:
            self._check_supertypes()

    def has_type_variables(self):
        return False

    def __str__(self):
        return "{}{}".format(
            self.name,
            '' if not self.supertypes else " <: (" +
            ', '.join(map(str, self.supertypes)) + ")"
        )

    def __eq__(self, other: Type):
        """Check if two Builtin objects are of the same Type"""
        return (self.__class__ == other.__class__ and
                self.name == other.name and
                self.supertypes == other.supertypes)

    def __hash__(self):
        """Hash based on the Type"""
        return hash("{}{}{}".format(
            str(self.__class__), str(self.name), str(self.supertypes)))

    def _check_supertypes(self):
        """The transitive closure of supertypes must be consistent, i.e., does
        not contain two parameterized types with different type arguments.
        """
        tconst = defaultdict(list)  # Type Constructors
        for supertype in filter(
                lambda x: x.is_parameterized(),
                self.get_supertypes()):
            tconst[supertype.t_constructor] = \
                tconst[supertype.t_constructor] + [supertype]
        for t_class in tconst.values():
            for ptype in t_class:
                assert ptype.type_args == t_class[0].type_args, \
                    "The concrete types of " + \
                    str(t_class[0].t_constructor) + " " + \
                    "do not have the same types"

    @two_way_subtyping
    def is_subtype(self, other: Type) -> bool:
        supertypes = self.get_supertypes()
        # Since the subtyping relation is transitive, we must also check
        # whether any supertype of the current type is also subtype of the
        # given type.
        return other == self or any(
            st.is_subtype(other) for st in supertypes
            if st != self
        )


class FieldInfo:
    """Field signature for structural type checking."""

    def __init__(self, name: str, field_type: Type):
        self.name = name
        self.field_type = field_type

    def __eq__(self, other):
        return (isinstance(other, FieldInfo) and
                self.name == other.name and
                self.field_type == other.field_type)

    def __hash__(self):
        return hash((self.name, self.field_type))

    def __repr__(self):
        return f"FieldInfo({self.name}, {self.field_type})"


class MethodInfo:
    """Method signature for structural type checking."""

    def __init__(self, name: str, param_types: List[Type], return_type: Type):
        self.name = name
        self.param_types = param_types
        self.return_type = return_type

    def __eq__(self, other):
        return (isinstance(other, MethodInfo) and
                self.name == other.name and
                self.param_types == other.param_types and
                self.return_type == other.return_type)

    def __hash__(self):
        return hash((self.name, tuple(self.param_types), self.return_type))

    def __repr__(self):
        params_str = ', '.join(str(p) for p in self.param_types)
        return f"MethodInfo({self.name}, [{params_str}], {self.return_type})"


class StructuralClassifier(SimpleClassifier):
    def __init__(self, name: str, supertypes: List[Type] = None, check=False,
                 field_signatures: List = None, method_signatures: List = None):
        """
        A classifier that uses structural subtyping.

        Args:
            name: The name of the type
            supertypes: List of supertypes (for nominal subtyping)
            check: Whether to check supertype consistency
            field_signatures: List of FieldInfo objects
            method_signatures: List of MethodInfo objects
        """
        super().__init__(name, supertypes, check)
        self.field_signatures = field_signatures or []
        self.method_signatures = method_signatures or []

    def _method_compatible(self, self_method_sig, other_method_sig):
        """
        Check if self's method signature is compatible with other's method signature.

        For structural subtyping:
        - Method names must match
        - Parameter types are contravariant (other's params must accept self's params)
        - Return type is covariant (self's return must be subtype of other's return)

        Args:
            self_method_sig: MethodInfo object
            other_method_sig: MethodInfo object

        Returns:
            bool: True if signatures are compatible
        """
        if self_method_sig.name != other_method_sig.name:
            return False

        # Must have same number of parameters
        if len(self_method_sig.param_types) != len(other_method_sig.param_types):
            return False

        # Check parameters (contravariant: other_param <: self_param)
        for self_param, other_param in zip(self_method_sig.param_types,
                                           other_method_sig.param_types):
            if not other_param.is_subtype(self_param):
                return False

        # Check return type (covariant: self_return <: other_return)
        if not self_method_sig.return_type.is_subtype(other_method_sig.return_type):
            return False

        return True

    @two_way_subtyping
    def is_subtype(self, other: Type) -> bool:
        """
        Check if self is a subtype of other using structural typing.

        First checks nominal subtyping (inheritance), then checks structural
        compatibility. For structural subtyping:
        - self must have all fields that other has (with compatible types)
        - self must have all methods that other has (with compatible signatures)

        Args:
            other: The potential supertype

        Returns:
            bool: True if self is a subtype of other
        """
        ## Nominally subtyped implies structurally subtyped
        if super().is_subtype(other):
            return True

        # Now do structural typechecking
        # If other is not a StructuralClassifier, we can't do structural comparison
        if not isinstance(other, StructuralClassifier):
            return False

        # Check fields: self must have all of other's fields with compatible types
        other_fields_map = {f.name: f for f in other.field_signatures}
        self_fields_map = {f.name: f for f in self.field_signatures}

        for field_name, other_field_info in other_fields_map.items():
            if field_name not in self_fields_map:
                # self is missing a field that other has
                return False

            self_field_info = self_fields_map[field_name]
            # Field types must be compatible (covariant)
            if not self_field_info.field_type.is_subtype(other_field_info.field_type):
                return False

        # Check methods: self must have all of other's methods with compatible signatures
        other_methods_map = {m.name: m for m in other.method_signatures}
        self_methods_map = {m.name: m for m in self.method_signatures}

        for method_name, other_method_sig in other_methods_map.items():
            if method_name not in self_methods_map:
                # self is missing a method that other has
                return False

            self_method_sig = self_methods_map[method_name]
            # Check method signature compatibility
            if not self._method_compatible(self_method_sig, other_method_sig):
                return False

        return True



class TypeParameter(AbstractType):

    def __init__(self, name: str, variance=None, bound: Type = None):
        super().__init__(name)
        self.variance = variance or Invariant
        self.bound = bound

    def variance_to_string(self):
        return self.variance.variance_to_str()

    def is_covariant(self):
        return self.variance.is_covariant()

    def is_contravariant(self):
        return self.variance.is_contravariant()

    def is_invariant(self):
        return self.variance.is_invariant()

    def children(self):
        return []

    def is_type_var(self):
        return True

    def get_bound_rec(self, factory):
        """
        This function recursively gets the bound of the type parameter.
        """
        if not self.bound:
            return None
        t = self.bound
        if t.is_type_var():
            return t.get_bound_rec(factory)
        if not t.has_type_variables():
            return t
        # If the bound is a parameterized type that contains other type
        # variables, we have to convert this type into an equivalent type
        # that is type variable-free.
        # We do this, because the bound would contain type variables which
        # are out of scope in the context where we use this bound.
        return t.to_type_variable_free(factory)

    @two_way_subtyping
    def is_subtype(self, other):
        if not self.bound:
            return False
        return self.bound.is_subtype(other)

    def substitute_type(self, type_map,
                        cond=lambda t: t.has_type_variables()):
        t = type_map.get(self)
        if t is None or cond(t):
            # Perform type substitution on the bound of the current type
            # variable.
            if self.bound is not None:
                new_bound = self.bound.substitute_type(type_map, cond)
                return TypeParameter(self.name, self.variance, new_bound)
            # The type parameter does not correspond to an abstract type
            # so, there is nothing to substitute.
            return self
        return t

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.name == other.name and
                self.variance == other.variance and
                self.bound == other.bound)

    def __hash__(self):
        return hash(str(self.name) + str(self.variance))

    def __str__(self):
        return "{}{}{}".format(
            self.variance_to_string() +
            ' ' if self.variance != Invariant else '',
            self.name,
            ' <: ' + self.bound.get_name() if self.bound is not None else ''
        )


class WildCardType(Type):
    def __init__(self, bound=None, variance=Invariant):
        super().__init__("*")
        self.bound = bound
        self.variance = variance

    @two_way_subtyping
    def is_subtype(self, other):
        if isinstance(other, WildCardType):
            if other.bound is not None:
                if self.variance.is_covariant() and (
                        other.variance.is_covariant()):
                    return self.bound.is_subtype(other.bound)
        return False

    def has_type_variables(self):
        return self.bound and self.bound.has_type_variables()

    def get_type_variables(self, factory):
        if not self.bound:
            return {}
        if self.bound.is_wildcard():
            return self.bound.get_type_variables(factory)
        elif self.bound.is_type_var():
            return {self.bound: {self.bound.get_bound_rec(factory)}}
        elif self.bound.is_compound():
            return self.bound.get_type_variables(factory)
        else:
            return {}

    def substitute_type(self, type_map,
                        cond=lambda t: t.has_type_variables()):
        if self.bound is not None:
            new_bound = self.bound.substitute_type(type_map, cond)
            return WildCardType(new_bound, variance=self.variance)
        t = type_map.get(self)
        if t is None or cond(t):
            # The bound does not correspond to abstract type
            # so there is nothing to substitute
            return self
        return t

    def get_bound_rec(self):
        if not self.bound:
            return None
        t = self.bound
        if t.is_wildcard():
            return t.get_bound_rec()
        return t

    def is_wildcard(self):
        return True

    def is_invariant(self):
        return self.variance.is_invariant()

    def is_covariant(self):
        return self.variance.is_covariant()

    def is_contravariant(self):
        return self.variance.is_contravariant()

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.variance == other.variance and
                self.bound == other.bound)

    def __hash__(self):
        return hash(str(self.name) + str(self.variance))

    def __str__(self):
        if not self.bound:
            return "*"
        else:
            return "{}{}".format(
                self.variance.variance_to_str() +
                ' ' if self.variance != Invariant else '',
                self.bound.get_name()
            )

    def is_primitive(self):
        return False


def substitute_type(t, type_map):
    return t.substitute_type(type_map, lambda t: False)


def perform_type_substitution(etype, type_map,
                              cond=lambda t: t.has_type_variables()):
    """
    This function performs the following substitution.
    Imagine that we have the following case.

    class Y<T>
    class X<T>: Y<T>()

    When, we instantiate the type constructor X with a specific type
    argument (e.g., String), we must also substitute the type parameter
    of its supertype (i.e., Y<T>) with the given type argument.
    For example, the supertype of X<String> is Y<String> and not Y<T>.

    This also works for nested definitions. For example
    class X<T> : Y<Z<T>>()
    """
    supertypes = []
    for t in etype.supertypes:
        if t.is_parameterized():
            supertypes.append(t.substitute_type(type_map))
        else:
            supertypes.append(t)
    type_params = []
    for t_param in etype.type_parameters:
        if t_param.bound is None:
            type_params.append(t_param)
            continue

        new_bound = t_param.bound
        t_param = TypeParameter(t_param.name, t_param.variance, new_bound)
        type_params.append(t_param)

    etype = deepcopy(etype)
    etype.type_parameters = type_params
    etype.supertypes = supertypes
    return etype


class TypeConstructor(AbstractType):
    def __init__(self, name: str, type_parameters: List[TypeParameter],
                 supertypes: List[Type] = None, classifier: Classifier = None):
        super().__init__(name)
        assert len(type_parameters) != 0, "type_parameters is empty"
        self.type_parameters = list(type_parameters)

        # If classifier is provided, use it as the source of truth
        # Otherwise, fall back to legacy behavior with explicit supertypes
        self.classifier = classifier
        if classifier is not None:
            self.supertypes = classifier.supertypes
        else:
            self.supertypes = supertypes if supertypes is not None else []

    def __str__(self):
        return "{}<{}> {} {}".format(
            self.name,
            ', '.join(map(str, self.type_parameters)),
            ' <:' if self.supertypes else '',
            ', '.join(map(str, self.supertypes)))

    def __eq__(self, other: AbstractType):
        return (self.__class__ == other.__class__ and
                self.name == other.name and
                str(self.type_parameters) == str(other.type_parameters))

    def __hash__(self):
        return hash(str(self.__class__) + str(self.name) + str(self.supertypes)
                    + str(self.type_parameters))

    def is_type_constructor(self):
        return True

    @two_way_subtyping
    def is_subtype(self, other: Type):
        supertypes = self.get_supertypes()
        matched_supertype = None
        for supertype in supertypes:
            if other == supertype:
                matched_supertype = supertype
                break
        if matched_supertype is None:
            # This type constructor is not subtype of other
            return False
        if not other.is_parameterized():
            return True

        # The rationale here is the following: there might be collision
        # in the type variables introduced by the type constructor and
        # the type variables that appear in the type arguments of the given
        # parameterized type. See the following example:
        #
        # class Bar<T> extends Foo<Float, T> {}
        # fun <T> foo(Foo<Float, T> x) {
        #    In this context, the type constructor Bar<T> is not a subtype
        #    of Foo<Float, T>.
        # }
        type_vars = set(
            matched_supertype.get_type_variable_assignments().values())
        return not bool(type_vars.intersection(self.type_parameters))

    def new(self, type_args: List[Type]):
        type_map = {tp: type_args[i]
                    for i, tp in enumerate(self.type_parameters)}
        old_supertypes = self.supertypes
        type_con = perform_type_substitution(self, type_map)
        etype = ParameterizedType(type_con, type_args)
        etype.t_constructor.supertypes = old_supertypes
        return etype


def _to_type_variable_free(t: Type, t_param, factory) -> Type:
    if t.is_type_var():
        bound = t.get_bound_rec(factory)
        # If the type variable has no bound, then create
        # a variant type argument on the top type.
        # X<T> => X<? extends Object>
        #
        # If the corresponding type parameter is contravariant, then
        # use the wildcard type X<T> => X<?>
        bound, variance = (
            (None, Invariant)
            if t_param.is_contravariant()
            else (
                factory.get_any_type() if bound is None else bound,
                Covariant
            )
        )
        return WildCardType(bound, variance)
    elif t.is_compound():
        return t.to_type_variable_free(factory)
    else:
        return t


def _is_type_arg_contained(t: Type, other: Type,
                           type_param: TypeParameter) -> bool:
    # We implement this function based on the containment rules described
    # here:
    # https://kotlinlang.org/spec/type-system.html#type-containment
    is_wildcard = isinstance(t, WildCardType)
    is_wildcard2 = isinstance(other, WildCardType)
    if not is_wildcard and not is_wildcard2:
        if type_param.is_invariant():
            return t == other
        elif type_param.is_covariant():
            return t.is_subtype(other)
        else:
            return other.is_subtype(t)
    if is_wildcard2 and not is_wildcard and other.bound:
        if other.variance.is_covariant():
            return t.is_subtype(other.bound)
        elif other.variance.is_contravariant():
            return other.bound.is_subtype(t)
    elif is_wildcard and is_wildcard2 and other.bound and t.bound:
        if t.variance.is_covariant() and other.variance.is_covariant():
            return t.bound.is_subtype(other.bound)
        elif t.variance.is_contravariant() and other.variance.is_contravariant():
            return other.bound.is_subtype(t.bound)
    elif is_wildcard and not is_wildcard2 and t.bound:
        if type_param.is_covariant():
            return t.bound.is_subtype(other)
        elif type_param.is_contravariant():
            return other.is_subtype(t.bound)
    if is_wildcard2 and not other.bound:
        if not (is_wildcard and not t.bound):
            return True
    return False


def _create_substituted_structural_classifier(parameterized_type):
    """
    Create a StructuralClassifier with type parameters substituted.

    Takes a ParameterizedType with a StructuralClassifier and creates
    a new StructuralClassifier where all type parameters in field and
    method signatures are replaced with actual type arguments.

    Args:
        parameterized_type: A ParameterizedType instance

    Returns:
        StructuralClassifier with substituted type parameters
    """
    classifier = parameterized_type.t_constructor.classifier
    if not isinstance(classifier, StructuralClassifier):
        return None

    # Get type substitution map
    type_map = parameterized_type.get_type_variable_assignments()

    # Substitute types in field signatures
    substituted_fields = []
    for field in classifier.field_signatures:
        substituted_type = field.field_type.substitute_type(
            type_map, lambda t: t.has_type_variables())
        substituted_fields.append(FieldInfo(field.name, substituted_type))

    # Substitute types in method signatures
    substituted_methods = []
    for method in classifier.method_signatures:
        substituted_params = [
            param.substitute_type(type_map, lambda t: t.has_type_variables())
            for param in method.param_types
        ]
        substituted_return = method.return_type.substitute_type(
            type_map, lambda t: t.has_type_variables())
        substituted_methods.append(
            MethodInfo(method.name, substituted_params, substituted_return))

    # Create new StructuralClassifier with substituted signatures
    return StructuralClassifier(
        parameterized_type.name,
        supertypes=parameterized_type.supertypes,
        field_signatures=substituted_fields,
        method_signatures=substituted_methods
    )


class ParameterizedType(SimpleClassifier):
    def __init__(self, t_constructor: TypeConstructor,
                 type_args: List[Type],
                 can_infer_type_args=False):
        self.t_constructor = deepcopy(t_constructor)
        self.type_args = list(type_args)
        assert len(self.t_constructor.type_parameters) == len(type_args), \
            "You should provide {} types for {}".format(
                len(self.t_constructor.type_parameters), self.t_constructor)
        self._can_infer_type_args = can_infer_type_args
        super().__init__(self.t_constructor.name,
                         self.t_constructor.supertypes)
        # XXX revisit
        self.supertypes = copy(self.t_constructor.supertypes)

    def is_compound(self):
        return True

    def is_parameterized(self):
        return True

    def is_function_type(self):
        return self.t_constructor.name.startswith('Function')

    def get_type_variable_assignments(self):
        return {
            t_param: self.type_args[i]
            for i, t_param in enumerate(self.t_constructor.type_parameters)
        }

    def has_type_variables(self):
        return any(t_arg.has_type_variables() for t_arg in self.type_args)

    def has_wildcards(self):
        return any(
            t_arg.is_wildcard() or (
                t_arg.is_parameterized() and t_arg.has_wildcards()
            )
            for t_arg in self.type_args
        )

    def to_variance_free(self, type_var_map=None):
        type_args = []
        for i, t_arg in enumerate(self.type_args):
            if t_arg.is_wildcard() and t_arg.bound:
                t_param = self.t_constructor.type_parameters[i]
                bound = t_arg.get_bound_rec()
                t = bound if not type_var_map else type_var_map.get(t_param,
                                                                    bound)
            else:
                t = t_arg
            type_args.append(t)
        return self.t_constructor.new(type_args)

    def to_type_variable_free(self, factory):
        # We translate a parameterized type that contains
        # type variables into a parameterized type that is
        # type variable free.
        type_args = []
        for i, t_arg in enumerate(self.type_args):
            t_param = self.t_constructor.type_parameters[i]
            if t_arg.is_wildcard() and t_arg.is_contravariant():
                if t_arg.bound.has_type_variables():
                    bound, variance = (
                        (None, Invariant)
                        if t_param.is_contravariant()
                        else (factory.get_any_type(), Covariant)
                    )
                    type_args.append(WildCardType(bound, variance))
                else:
                    type_args.append(t_arg)
            elif t_arg.is_wildcard() and t_arg.is_covariant():
                bound = t_arg.get_bound_rec()
                if bound.has_type_variables():
                    type_args.append(
                        _to_type_variable_free(bound, t_param, factory))
                else:
                    type_args.append(t_arg)
            else:
                type_args.append(_to_type_variable_free(t_arg, t_param,
                                                        factory))
        return self.t_constructor.new(type_args)

    def get_type_variables(self, factory) -> Dict[TypeParameter, Set[Type]]:
        # This function actually returns a dict of the enclosing type variables
        # along with the set of their bounds.
        type_vars = defaultdict(set)
        for t_arg in self.type_args:
            if t_arg.is_type_var():
                type_vars[t_arg].add(
                    t_arg.get_bound_rec(factory))
            elif t_arg.is_compound() or t_arg.is_wildcard():
                for k, v in t_arg.get_type_variables(factory).items():
                    type_vars[k].update(v)
            else:
                continue
        return type_vars

    def substitute_type(self, type_map, cond=lambda t: t.has_type_variables()):
        type_args = []
        for t_arg in self.type_args:
            type_args.append(t_arg.substitute_type(type_map, cond))
        new_type_map = {
            tp: type_args[i]
            for i, tp in enumerate(self.t_constructor.type_parameters)
        }
        type_con = perform_type_substitution(
            self.t_constructor, new_type_map, cond)
        return ParameterizedType(type_con, type_args)

    @property
    def can_infer_type_args(self):
        return self._can_infer_type_args

    @can_infer_type_args.setter
    def can_infer_type_args(self, value):
        if not isinstance(value, bool):
            raise TypeError("Must be bool")
        self._can_infer_type_args = value

    def __eq__(self, other: Type):
        if not isinstance(other, ParameterizedType):
            return False
        return (self.name == other.name and
                self.supertypes == other.supertypes and
                self.t_constructor.__class__ == other.t_constructor.__class__ and
                self.t_constructor.type_parameters ==
                other.t_constructor.type_parameters and
                self.type_args == other.type_args)

    def __hash__(self):
        return hash(str(self.name) + str(self.supertypes) + str(self.type_args)
                    + str(self.t_constructor.type_parameters))

    def __str__(self):
        return "{}<{}>".format(self.name,
                               ", ".join(map(str, self.type_args)))

    def get_name(self):
        return "{}<{}>".format(self.name, ", ".join([t.get_name()
                                                     for t in self.type_args]))

    @two_way_subtyping
    def is_subtype(self, other: Type) -> bool:
        # First check nominal subtyping (inheritance)
        if super().is_subtype(other):
            return True

        # If other is parameterized with the SAME constructor, use variance rules
        if other.is_parameterized() and hasattr(other, 't_constructor'):
            if self.t_constructor == other.t_constructor:
                # Same type constructor: use variance checking on type arguments
                for tp, sarg, targ in zip(self.t_constructor.type_parameters,
                                          self.type_args, other.type_args):
                    if not _is_type_arg_contained(sarg, targ, tp):
                        return False
                return True

        # Check if both types have structural classifiers (different constructors)
        has_structural = (self.t_constructor.classifier is not None and
                         isinstance(self.t_constructor.classifier, StructuralClassifier))
        other_has_structural = (other.is_parameterized() and
                               hasattr(other, 't_constructor') and
                               other.t_constructor.classifier is not None and
                               isinstance(other.t_constructor.classifier, StructuralClassifier))

        # If both have structural classifiers (and different constructors), do structural check
        if has_structural and other_has_structural:
            # Create substituted structural classifiers
            self_structural = _create_substituted_structural_classifier(self)
            other_structural = _create_substituted_structural_classifier(other)

            if self_structural and other_structural:
                # Delegate to StructuralClassifier.is_subtype()
                return self_structural.is_subtype(other_structural)

        return False

    def is_assignable(self, other: Type):
        # Import here to prevent circular dependency.
        from src.ir import java_types as jt
        # We should handle Java primitive arrays
        # In Java Byte[] is not assignable to byte[] and vice versa.
        if (self.t_constructor == jt.Array and
                other.is_parameterized() and
                other.t_constructor == jt.Array):
            self_t = self.type_args[0]
            other_t = other.type_args[0]
            self_is_primitive = getattr(self_t, 'primitive', False)
            other_is_primitive = getattr(other_t, 'primitive', False)
            if self_is_primitive or other_is_primitive:
                if (self_t == other_t and
                        self_is_primitive and other_is_primitive):
                    return True
                return False
        return self.is_subtype(other)


class Function(Classifier):
    # FIXME: Represent function as a parameterized type
    def __init__(self, name, param_types, ret_type):
        super().__init__(name)
        self.param_types = param_types
        self.ret_type = ret_type

    def __str__(self):
        return self.name + "(" + ','.join(map(str, self.param_types)) +\
            ") -> " + str(self.ret_type)

    def is_subtype(self, other: Type):
        return False


class ParameterizedFunction(Function):
    # FIXME: Represent function as a parameterized type
    def __init__(self, name, type_parameters, param_types, ret_type):
        super().__init__(name, param_types, ret_type)
        self.type_parameters = type_parameters

    def __str__(self):
        return self.name + "<" ','.join(map(str, self.type_parameters)) + \
            ">" + "(" + ','.join(map(str, self.param_types)) + \
            ") -> " + str(self.ret_type)

    def is_subtype(self, other: Type):
        return False


class NothingType(Classifier):
    def __init__(self):
        super().__init__("Nothing")

    def is_subtype(self, other: Type):
        return True


Nothing = NothingType()
