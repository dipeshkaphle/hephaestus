from collections import defaultdict

import src.ir.ast as ast
import src.ir.typescript_ast as ts_ast
import src.ir.builtins as bt
import src.ir.types as tp
import src.ir.ast as ast
import src.utils as ut
from src.ir.decorators import two_way_subtyping


class TypeScriptBuiltinFactory(bt.BuiltinFactory):
    def __init__(self, max_union_types=10, max_types_in_union=4,
                 max_string_literal_types=10, max_num_literal_types=10):
        self._literal_type_factory = LiteralTypeFactory(
            max_string_literal_types, max_num_literal_types)
        self._union_type_factory = UnionTypeFactory(max_union_types,
                                                    max_types_in_union)

    def get_language(self):
        return "typescript"

    def get_builtin(self):
        return TypeScriptBuiltin

    def get_void_type(self):
        return VoidType()

    def get_any_type(self):
        return ObjectType()

    def get_number_type(self):
        return NumberType(primitive=False)

    def get_boolean_type(self):
        return BooleanType(primitive=False)

    def get_char_type(self):
        return StringType(primitive=False)

    def get_string_type(self):
        return StringType(primitive=False)

    def get_big_integer_type(self):
        return BigIntegerType(primitive=False)

    def get_array_type(self):
        return ArrayType()

    def get_function_type(self, nr_parameters=0):
        return FunctionType(nr_parameters)

    def get_object_type(self):
        return ObjectLowercaseType()

    def get_primitive_types(self):
        return [
            NumberType(primitive=False),
            StringType(primitive=False),
            SymbolType(primitive=False),
            BooleanType(primitive=False),
            BigIntegerType(primitive=False),
            NullType(primitive=False),
            UndefinedType(primitive=False)
        ]

    def get_integer_type(self):
        return NumberType(primitive=False)

    def get_byte_type(self):
        return NumberType(primitive=False)

    def get_short_type(self):
        return NumberType(primitive=False)

    def get_long_type(self):
        return NumberType(primitive=False)

    def get_float_type(self):
        return NumberType(primitive=False)

    def get_double_type(self):
        return NumberType(primitive=False)

    def get_big_decimal_type(self):
        return NumberType(primitive=False)

    def get_null_type(self):
        return NullType(primitive=False)

    def get_non_nothing_types(self):
        #  Overwriting Parent method to add TS-specific types
        types = super().get_non_nothing_types()
        types.extend([
            self.get_null_type(),
            UndefinedType(primitive=False),
            ] + self._literal_type_factory.get_literal_types())
        return types

    def get_decl_candidates(self):
        return [gen_type_alias_decl, ]

    def update_add_node_to_parent(self):
        return {
            ts_ast.TypeAliasDeclaration: add_type_alias,
        }
    
    def get_indexed_access_type(self, object_type, index_type):
        """Create an indexed access type T[K]

        Args:
            object_type: The type being indexed
            index_type: The index type (usually string literal or number)

        Returns:
            An IndexedAccessType instance
        """
        return IndexedAccessType(object_type, index_type)

    def _can_generate_indexed_access(self, gen_object):
        """Check if we can generate an indexed access type

        We need at least one class/interface with fields to index
        """
        try:
            classes = list(gen_object.context.get_classes(gen_object.namespace).values())
            return any(hasattr(c, 'fields') and len(c.fields) > 0 for c in classes)
        except:
            return False

    def _generate_indexed_access_type(self, gen_object):
        """Generate an indexed access type T[K]

        Returns:
            An IndexedAccessType instance or None if generation fails
        """
        try:
            # Get classes with fields
            classes = list(gen_object.context.get_classes(gen_object.namespace).values())
            indexable_classes = [c for c in classes
                                if hasattr(c, 'fields') and len(c.fields) > 0]

            if not indexable_classes:
                return None

            # Select a random class
            target_class = ut.random.choice(indexable_classes)
            object_type = target_class.get_type()

            # If the class is generic (has type parameters), we need to instantiate it first
            # because TypeScript requires: GenericClass<Type>["field"], not GenericClass["field"]
            if object_type.is_type_constructor():
                # Import here to avoid circular dependency
                from src.ir import type_utils as tu
                # Get available types for instantiation
                available_types = gen_object.get_types(exclude_arrays=True, exclude_covariants=True)
                # Instantiate the type constructor with random types
                object_type, _ = tu.instantiate_type_constructor(
                    object_type, available_types, gen_object.bt_factory
                )

            # Decide whether to generate single key or union of keys
            # 50% chance to generate union key if there are 2+ fields
            use_union_key = len(target_class.fields) >= 2 and ut.random.bool()

            if use_union_key:
                # Generate union of 2-3 field keys: T["field1" | "field2" | ...]
                num_keys = min(ut.random.integer(2, 4), len(target_class.fields))
                selected_fields = ut.random.sample(target_class.fields, num_keys)

                # Create union of string literal types
                index_types = [StringLiteralType(f.name) for f in selected_fields]
                index_type = UnionType(index_types)

                # Resolve to union of field types
                resolved_types = []
                for field in selected_fields:
                    field_type = field.field_type
                    if object_type.is_parameterized():
                        type_var_map = object_type.get_type_variable_assignments()
                        field_type = tp.substitute_type(field_type, type_var_map)
                    resolved_types.append(field_type)

                # Deduplicate types
                seen = set()
                unique_resolved = []
                for t in resolved_types:
                    t_key = (type(t), getattr(t, 'name', None), getattr(t, 'literal', None))
                    if t_key not in seen:
                        seen.add(t_key)
                        unique_resolved.append(t)

                # Create union if multiple types, otherwise use single type
                if len(unique_resolved) > 1:
                    resolved_type = UnionType(unique_resolved)
                else:
                    resolved_type = unique_resolved[0]
            else:
                # Generate single key: T["field"]
                field = ut.random.choice(target_class.fields)
                index_type = StringLiteralType(field.name)

                # Cache the resolved type (the field's type) for accurate type checking
                # If object_type is parameterized, we need to substitute type variables in field type
                resolved_type = field.field_type
                if object_type.is_parameterized():
                    type_var_map = object_type.get_type_variable_assignments()
                    resolved_type = tp.substitute_type(resolved_type, type_var_map)

            return IndexedAccessType(object_type, index_type, resolved_type=resolved_type)
        except:
            return None

    def get_compound_types(self, gen_object):
        types = []

        # Add union type
        union_type = self._union_type_factory.get_union_type(gen_object)
        if union_type:
            types.append(union_type)

        # Try to generate IndexedAccessType with 30% probability
        if self._can_generate_indexed_access(gen_object):
            indexed_type = self._generate_indexed_access_type(gen_object)
            if indexed_type:
                types.append(indexed_type)

        # Filter out any None values that might have slipped through
        return [t for t in types if t is not None]


    def get_constant_candidates(self, constants):
        """ Updates the constant candidates of the generator
        with the type-constant pairs for language-specific features.

        Args:
            gen_object: The generator instance
            constants: The dictionary of constant candidates
                       at the time of the method call
        Returns:
            A dictionary where the keys are strings of type names and
            values are functions that return the appropriate constant
            node for the type.

            The constants dictionary is updated at the generator-side
            with the method's returned key-value pairs.

            This method is called at src.ir.generator.get_generators()

        """
        return {
            "NumberLiteralType": lambda etype: ast.IntegerConstant(
                etype.literal, NumberLiteralType(etype.literal)),
            "StringLiteralType": lambda etype: ast.StringConstant(
                etype.literal),
            "UnionType": lambda etype: self._union_type_factory.get_union_constant(
                etype, constants),
        }


class TypeScriptBuiltin(tp.Builtin):
    def __init__(self, name, primitive):
        super().__init__(name)
        self.primitive = primitive

    def __str__(self):
        if not self.is_primitive():
            return str(self.name) + "(typescript-builtin)"
        return str(self.name).lower() + "(typescript-primitive)"

    def is_primitive(self):
        return self.primitive


class ObjectType(TypeScriptBuiltin):
    def __init__(self, name="Object"):
        super().__init__(name, False)


class ObjectLowercaseType(TypeScriptBuiltin):
    def __init__(self, name="object"):
        super().__init__(name, False)
        self.supertypes.append(ObjectType())


class VoidType(TypeScriptBuiltin):
    def __init__(self, name="void"):
        super().__init__(name, False)
        self.supertypes.append(ObjectType())


class NumberType(TypeScriptBuiltin):
    def __init__(self, name="Number", primitive=False):
        super().__init__(name, primitive)
        self.supertypes.append(ObjectType())

    def box_type(self):
        return NumberType(self.name, primitive=False)

    def get_name(self):
        if self.is_primitive:
            return "number"
        return super().get_name()


class BigIntegerType(TypeScriptBuiltin):
    def __init__(self, name="BigInt", primitive=False):
        super().__init__(name, primitive)
        self.supertypes.append(ObjectType())

    def is_assignable(self, other):
        assignable_types= [BigIntegerType]
        return self.is_subtype(other) or type(other) in assignable_types

    def box_type(self):
        return BigIntegerType(self.name, primitive=False)

    def get_name(self):
        if self.is_primitive:
            return "bigint"
        return super().get_name()


class BooleanType(TypeScriptBuiltin):
    def __init__(self, name="Boolean", primitive=False):
        super().__init__(name, primitive)
        self.supertypes.append(ObjectType())

    def box_type(self):
        return BooleanType(self.name, primitive=False)

    def get_name(self):
        if self.is_primitive:
            return "boolean"
        return super().get_name()


class StringType(TypeScriptBuiltin):
    def __init__(self, name="String", primitive=False):
        super().__init__(name, primitive)
        self.supertypes.append(ObjectType())

    def box_type(self):
        return StringType(self.name, primitive=False)

    def get_name(self):
        if self.is_primitive:
            return "string"
        return super().get_name()


class SymbolType(TypeScriptBuiltin):
    def __init__(self, name="Symbol", primitive=False):
        super().__init__(name, primitive)
        self.supertypes.append(ObjectType())

    def box_type(self):
        return SymbolType(self.name, primitive=False)

    def get_name(self):
        if self.is_primitive():
            return "symbol"
        return super().get_name()


class NullType(ObjectType):
    def __init__(self, name="null", primitive=False):
        super().__init__(name)
        self.primitive = primitive

    def box_type(self):
        return NullType(self.name)

    def get_name(self):
        return 'null'


class UndefinedType(ObjectType):
    def __init__(self, name="undefined", primitive=False):
        super().__init__(name)
        self.primitive = primitive

    def box_type(self):
        return UndefinedType(self.name)

    def get_name(self):
        return 'undefined'


class AliasType(ObjectType):
    def __init__(self, alias, name="AliasType", primitive=False):
        super().__init__()
        self.alias = alias
        self.name = name
        self.primitive = primitive

    def get_type(self):
        return self.alias

    @two_way_subtyping
    def is_subtype(self, other):
        if isinstance(other, AliasType):
            return self.alias.is_subtype(other.alias)
        return self.alias.is_subtype(other)

    def box_type(self):
        return AliasType(self.alias, self.name)

    def get_name(self):
        return self.name

    def __eq__(self, other):
        return (isinstance(other, AliasType) and
                 self.alias == other.alias)

    def __hash__(self):
        return hash(str(self.name) + str(self.alias))


class NumberLiteralType(TypeScriptBuiltin):
    def __init__(self, literal, name="NumberLiteralType", primitive=False):
        super().__init__(name, primitive)
        self.literal = literal
        self.supertypes.append(NumberType())

    def get_literal(self):
        return self.literal

    @two_way_subtyping
    def is_subtype(self, other):
        """ A number literal type is assignable to any
            supertype of type 'number'.

            It is also assignable to other number literal types,
            as long as the other type's literal is the same.

            eg. let num: number
                let litA: 23 = 23
                let litB: 23
                num = litA (correct)
                litB = litA (correct)

            litA is assignable to litB because their literal
            is the same, 23.

        """
        if (isinstance(other, AliasType) and isinstance(other.alias, NumberLiteralType)):
            other = other.alias
        elif isinstance(other, AliasType):
            return isinstance(other.alias, NumberType)

        return ((isinstance(other, NumberLiteralType) and
                  other.get_literal() == self.get_literal()) or
                  isinstance(other, NumberType))

    def get_name(self):
        return self.name

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                 self.name == other.name and
                 self.literal == other.literal)

    def __hash__(self):
        return hash(str(self.name) + str(self.literal))


class StringLiteralType(TypeScriptBuiltin):
    def __init__(self, literal, name="StringLiteralType", primitive=False):
        super().__init__(name, primitive)
        self.literal = literal
        self.supertypes.append(StringType())

    def get_literal(self):
        return '"' + self.literal + '"'

    @two_way_subtyping
    def is_subtype(self, other):
        """ A string literal type is assignable to any
            supertype of type 'string'.

            It is also assignablde to other string literal types,
            as long as the other type's literal is the same.

            eg. let str: string
                let litA: "PULL" = "PULL"
                let litB: "PULL"
                str = litA (correct)
                litB = litA (correct)

            litA is assignable to litB because their literal
            is the same, "PULL".

        """
        if (isinstance(other, AliasType) and isinstance(other.alias, StringLiteralType)):
            other = other.alias
        elif isinstance(other, AliasType):
            return isinstance(other.alias, StringType)

        return ((isinstance(other, StringLiteralType) and
                  other.get_literal() == self.get_literal()) or
                  isinstance(other, StringType))

    def get_name(self):
        return self.name

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                 self.name == other.name and
                 self.literal == other.literal)

    def __hash__(self):
        return hash(str(self.name) + str(self.literal))


class LiteralTypeFactory:
    def __init__(self, str_limit, num_limit):
        self.str_literals = []
        self.num_literals = []
        # Define max number for generated literals
        self.str_limit = str_limit
        self.num_limit = num_limit

    def get_literal_types(self):
        sl = self.gen_string_literal()
        nl = self.gen_number_literal()
        return [sl, nl]

    def gen_string_literal(self):
        lit = None
        if (len(self.str_literals) == 0 or
                (len(self.str_literals) < self.str_limit and
                ut.random.bool())):
            # If the limit for generated literals
            # has not been surpassed, we can randomly
            # generate a new one.
            lit = StringLiteralType(ut.random.word().lower())
            self.str_literals.append(lit)
        else:
            lit = ut.random.choice(self.str_literals)
        return lit

    def gen_number_literal(self):
        lit = None
        if (len(self.num_literals) == 0 or
                (len(self.num_literals) < self.num_limit and
                ut.random.bool())):
            # If the limit for generated literals
            # has not been surpassed, we can randomly
            # generate a new one.
            lit = NumberLiteralType(ut.random.integer(-100, 100))
            self.num_literals.append(lit)
        else:
            lit = ut.random.choice(self.num_literals)
        return lit


class UnionType(TypeScriptBuiltin):
    def __init__(self, types, name="UnionType", primitive=False):
        super().__init__(name, primitive)
        self.types = types

    def get_types(self):
        return self.types

    def is_compound(self):
        return True

    @two_way_subtyping
    def is_subtype(self, other):
        if isinstance(other, UnionType):
            for t in self.types:
                if not any(t.is_subtype(other_t) for other_t in other.types):
                    return False
            return True
        return other.name == 'Object'

    def two_way_subtyping(self, other):
        return other in set(self.types)

    def substitute_type(self, type_map,
                        cond=lambda t: t.has_type_variables()):
        new_types = []
        for t in self.types:
            new_t = (t.substitute_type(type_map, cond)
                     if t.has_type_variables()
                     else t)
            new_types.append(new_t)
        return UnionType(new_types)

    def has_type_variables(self):
        return any(t.has_type_variables() for t in self.types)

    def get_type_variables(self, factory):
        # This function actually returns a dict of the enclosing type variables
        # along with the set of their bounds.
        type_vars = defaultdict(set)
        for t in self.types:
            if t.is_type_var():
                type_vars[t].add(
                    t.get_bound_rec(factory))
            elif t.is_compound() or t.is_wildcard():
                for k, v in t.get_type_variables(factory).items():
                    type_vars[k].update(v)
            else:
                continue
        return type_vars

    def to_variance_free(self, type_var_map=None):
        new_types = []
        for t in self.types:
            new_types.append(t.to_variance_free(type_var_map)
                             if t.is_compound()
                             else t)
        return UnionType(new_types)

    def to_type_variable_free(self, factory):
        # We translate a union type that contains
        # type variables into a parameterized type that is
        # type variable free.
        new_types = []
        for t in self.types:
            if t.is_compound():
                new_type = t.to_type_variable_free(factory)
            elif t.is_type_var():
                bound = t.get_bound_rec(factory)
                new_type = factory.get_any_type() if bound is None else bound
            else:
                new_type = t
            new_types.append(new_type)
        return UnionType(new_types)

    def unify_types(self, t1, factory, same_type=True):
        """
        This is used in src.ir.type_utils in the function
        unify_types.

        We delegate work here when the first of the two
        types that are passed to that function is a union type.

        For more information on the function see the detailed
        explanation at the unify_types function definition.
        """
        t2 = self
        type_var_map = {}

        if not t2.has_type_variables():
            return {}

        # If T1 is a union type, then get all its types.
        # Note: IndexedAccessType is also compound but doesn't have .types
        t1_types = (t1.types if isinstance(t1, UnionType)
                     else [t1])

        if not t1.is_subtype(t2):
            # Get the Type Variables of T2
            t_vars = dict(t2.get_type_variables(factory))

            # Find which types of t1 are not already in t2
            add_to_t2 = set(t1_types) - set(t2.types)

            # If T1 is a union type like 100 | number | string,
            # we do not need to substitute both 100 and number
            # in the type variables of T2.
            # Since number is a supertype of 100, if we only
            # substitute number, then we have also covered
            # the subtypes of 100 too!
            # Hence, we only substitute necessary types in T2
            # by ensuring that the T1 type we will subtitute
            # is NOT a subtype of any other types in the T1 union type.
            for t1_t in list(add_to_t2):
                if any(t1_t.is_subtype(other_t1_t)
                        and t1_t is not other_t1_t
                        for other_t1_t in t1_types):
                    add_to_t2.remove(t1_t)

            # If T1 is a union type, and its types that we need
            # to substitute in T2 are more than the type variables of T2,
            # then there is no substitution that ensures T1 <: T2.
            if len(add_to_t2) > len(t_vars):
                return {}

            # Get bounds of type variables of T2
            bounds = [b for b in t_vars.values() if b != {None}]

            # If the type variables have no bounds, then we can just assign
            # the types from T1 to any type variable.
            if not bounds:
                temp = list(t_vars.keys())
                for t in add_to_t2:
                    tv = temp.pop(0)
                    type_var_map[tv] = t
                return type_var_map

            # Get all the possible substitutions between T1 types (add_to_t2)
            # and type variables of T2. A type variable can be substituted
            # with a type in T1 if the type variable has no bound or
            # if the type is a subtype of a bound.
            possible_substitutions = {}
            for t in add_to_t2:
                subs = set()
                # Below remember that:
                #   - k is the type variable
                #   - v is a set containing its bounds
                for k,v in t_vars.items():
                    if v == {None} or any(t.is_subtype(b) for b in v):
                        subs.add(k)

                # If there are no possible substitutions with type variables
                # for any given type in T1 (add_to_t2) then there is no
                # substitution that ensures T1 <: T2.
                if not subs:
                    return {}
                possible_substitutions[t] = subs

            # Decide the order of assignments (if possible)
            assignments, flag = self.assign_types_to_type_vars(possible_substitutions)
            if not flag:
                return {}
            type_var_map.update(assignments)


        # Instantiate any not-utilized T2 type variables with their bound (if they have one).
        # If they don't have a bound instantiate them with a type from T1.
        leftover_type_vars = [t for t in t2.types if t.is_type_var() and t not in type_var_map]
        for type_var in leftover_type_vars:
            type_var_map[type_var] = type_var.bound if type_var.bound else t1_types[0]

        return type_var_map

    def assign_types_to_type_vars(self, possible_subs):
        """
        This method is a helper for the method unify_types of union types (see above)

        Args:
            - possible_subs: A dict containing (types.Type: set) pairs, which represents possible
                             T2 type variable (value) susbstitutions with a T1 type (key).
                             The set values contain compatible type vars of T2.

            - t2_t_vars:     The type variables of T2

            - t1_types:      The types of T1 that we want to substitute in T2

        Returns:
            - A dict of (TypeVariable: types.Type) pairs representing the substitutions in T2

        This method is needed because we need to find the correct substitutions
        of the type variables in the T2 union type, in order for all T1 types (T1 can be a union type itself)
        to be substituted in T2 (if possible).

        Consider the following case:

        T1: number | string
        T2: boolean | X | Y extends number

        In this case, if we first substituted X with the type number from T1,
        we would have been left with the type variable Y, which is not compatible
        with the type string.

        As a result we would falsely conclude that we can not unify the types T1 and T2,
        when in reality, had we just substituted Y with number and X with string,
        we would have been ably to correctly unify the two types.

        A naive solution would be to find all the possible substitution permutations
        between T1 types and T2 type variables.

        Using our approach, after first creating the possible_subs dict,
        which contains all compatible T2 type variables for each T1 type,
        we first substitute the T1 type that is compatible with the FEWEST
        T2 type variables at any given moment.

        Going back two the above case, here is how we tackle it with our new approach:

        T1: number | string
        T2: boolean | X | Y extends number

        (1) We find the possible substitutions for each T1 type (done outside this method)
                possible_subs = {number: {X, Y},
                                string: {X}
                                }

        (2) We sort the dict based on the length of the type variable sets corresponding to each type
                sorted_type_subs = [(string, {X}), (number, {X, Y})]

        (3) Now we work on the first element, the pair of string and {X}. We assign the substitution
            X: string. We remove X from all possible substitutions for other T1 types and then
            delete the pair with key string from our possible_subs dict.

        (4) We sort the dict again, it now looks like this:
                sorted_type_subs = [(number, {Y})]

        (5) Assign the substitution Y: number and repeat the rest of step (3)

        (6) The possible_subs dict is now empty, so we return our substitution dictionary
                return {X: string, Y: number}
        """
        type_var_map = {}

        # Continue trying to find type variable susbstitutions until
        # all T1 types are substituted in T2.
        while possible_subs:
            # Sort the possible_subs dict, in order to first find a substitution for the T1
            # type with the fewest compatible T2 type variables.
            sorted_type_subs = sorted(list(possible_subs.items()), key=lambda x: len(x[1]), reverse=False)

            # Get the first (T1 type, T2 type variable) pair (sorted_type_subs is a tuples list)
            type_to_substitute, compatible_tvars = sorted_type_subs[0]

            # If there aren't any compatible_tvars, then that means that there is no possible
            # order of substitutions that ensures all types in T1 are substituted in T2.
            # Hence, we return a False flag to indicate that the type unification is not possible.
            # Note: at this point this happens if at previous iterations of the while loop
            # we substituted all the type variables that are compatible with this specific type_to_substitute.
            if not compatible_tvars:
                return ({}, False)

            # Get any of the compatible type variables and substitute it with the T1 type
            chosen_tvar = compatible_tvars.pop()
            type_var_map[chosen_tvar] = type_to_substitute

            # Remove the substituted type variable from the possible substitutions
            # of all other T1 types.
            for k in list(possible_subs.keys()):
                if chosen_tvar in possible_subs[k]:
                    possible_subs[k].remove(chosen_tvar)

            # Delete the possible substitutions of the T1 type we just substituted in T2
            del possible_subs[type_to_substitute]

        # Return the substitutions we found and a flag confirming that there is a possible
        # order of substitutions that gurantees type unification.
        return (type_var_map, True)

    def get_name(self):
        return self.name

    def __str__(self):
        return f'UnionType(TS)({" | ".join([str(t) for t in self.types])})'

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.name == other.name and
                set(self.types) == set(other.types))

    def __hash__(self):
        return hash(str(self.name) + str(self.types))

class IndexedAccessType(TypeScriptBuiltin):
    """Represents TypeScript's indexed access type T[K]

    Examples:
        Person["name"]  -> string
        T[K]            -> depends on T and K
        Array<T>[number] -> T
    """
    def __init__(self, object_type: tp.Type, index_type: tp.Type,
                 name="IndexedAccessType", primitive=False, resolved_type=None):
        super().__init__(name, primitive)
        self.object_type = object_type  # The type being indexed
        self.index_type = index_type    # The index type (usually string literal or number)
        self._resolved_type = resolved_type  # Cache the resolved type if known

    def is_compound(self):
        return True

    def has_type_variables(self):
        return (self.object_type.has_type_variables() or
                self.index_type.has_type_variables())

    @two_way_subtyping
    def is_subtype(self, other: tp.Type):
        """
        Subtype checking for indexed access types requires resolving the actual type.
        For example: Person["name"] is a subtype of string
        """
        # Try to resolve the indexed access type
        resolved = self._try_resolve()
        if resolved:
            return resolved.is_subtype(other)

        # If unable to resolve, use conservative strategy
        # Assume indexed access type may return Object
        return isinstance(other, ObjectType)

    def _try_resolve(self):
        """Try to resolve T[K] to a concrete type

        Attempts to statically resolve the indexed access type to its actual type.
        For example:
        - Person["name"] -> string (if Person has a name field of type string)
        - Array<number>[number] -> number
        - Person["age" | "name"] -> number | string (union of field types)

        Returns:
            The resolved type if successful, None otherwise
        """
        # If we cached the resolved type during generation, use it
        if self._resolved_type is not None:
            return self._resolved_type

        # Case 1: Array<T>[number] -> T
        # When indexing an array with a number, return the element type
        if (self.object_type.is_parameterized() and
            self.object_type.t_constructor.name == "Array"):
            # Check if index_type is number or a number literal
            if isinstance(self.index_type, (NumberType, NumberLiteralType)):
                # Return the element type (first type argument of Array<T>)
                return self.object_type.type_args[0]

        # Case 2: T["K1" | "K2" | ...] -> T["K1"] | T["K2"] | ...
        # When the index is a union of string literals, resolve each and create a union
        if isinstance(self.index_type, UnionType):
            resolved_types = []
            for index_member in self.index_type.types:
                # Create a new IndexedAccessType for each member of the union
                member_indexed = IndexedAccessType(
                    self.object_type,
                    index_member,
                    resolved_type=self._resolved_type
                )
                # Try to resolve this individual indexed access
                resolved = member_indexed._try_resolve()
                if resolved is not None:
                    resolved_types.append(resolved)
                else:
                    # If we can't resolve one of the members, we can't resolve the whole union
                    return None

            # If we successfully resolved all members, return a union of the results
            if resolved_types:
                # Flatten if any resolved type is already a union
                flattened = []
                for t in resolved_types:
                    if isinstance(t, UnionType):
                        flattened.extend(t.types)
                    else:
                        flattened.append(t)

                # Remove duplicates while preserving order
                seen = set()
                unique_types = []
                for t in flattened:
                    t_key = (type(t), getattr(t, 'name', None), getattr(t, 'literal', None))
                    if t_key not in seen:
                        seen.add(t_key)
                        unique_types.append(t)

                # If only one type remains after deduplication, return it directly
                if len(unique_types) == 1:
                    return unique_types[0]

                return UnionType(unique_types)

        # Case 3: For class/interface types with string literal index
        # We cannot fully resolve this without context (class definitions)
        # This would require passing context into this method or caching
        # field type information in the IndexedAccessType itself
        # For now, we return None and rely on conservative subtyping

        return None

    def substitute_type(self, type_map, cond=lambda t: t.has_type_variables()):
        """Substitute both object type and index type during type substitution"""
        new_object = self.object_type.substitute_type(type_map, cond)
        new_index = self.index_type.substitute_type(type_map, cond)
        # Also substitute the resolved type if it exists
        new_resolved = None
        if self._resolved_type is not None:
            new_resolved = self._resolved_type.substitute_type(type_map, cond)
        return IndexedAccessType(new_object, new_index, resolved_type=new_resolved)

    def get_type_variables(self, factory):
        """Collect type variables from both object and index types"""
        type_vars = defaultdict(set)

        if self.object_type.is_type_var():
            type_vars[self.object_type].add(
                self.object_type.get_bound_rec(factory))
        elif self.object_type.is_compound() or self.object_type.is_wildcard():
            for k, v in self.object_type.get_type_variables(factory).items():
                type_vars[k].update(v)

        if self.index_type.is_type_var():
            type_vars[self.index_type].add(
                self.index_type.get_bound_rec(factory))
        elif self.index_type.is_compound() or self.index_type.is_wildcard():
            for k, v in self.index_type.get_type_variables(factory).items():
                type_vars[k].update(v)

        return type_vars

    def to_type_variable_free(self, factory):
        """Convert to a type without type variables"""
        new_object = (self.object_type.to_type_variable_free(factory)
                      if self.object_type.has_type_variables()
                      else self.object_type)
        new_index = (self.index_type.to_type_variable_free(factory)
                     if self.index_type.has_type_variables()
                     else self.index_type)
        new_resolved = None
        if self._resolved_type is not None:
            new_resolved = (self._resolved_type.to_type_variable_free(factory)
                           if self._resolved_type.has_type_variables()
                           else self._resolved_type)
        return IndexedAccessType(new_object, new_index, resolved_type=new_resolved)

    def get_type_variable_assignments(self):
        """
        Get type variable assignments for IndexedAccessType.

        IndexedAccessType is not itself a parameterized type, but if it resolves
        to a parameterized type, we can delegate to that type.
        Otherwise, return an empty dictionary.
        """
        resolved = self._try_resolve()
        if resolved and hasattr(resolved, 'get_type_variable_assignments'):
            return resolved.get_type_variable_assignments()
        return {}

    def unify_types(self, t1, factory, same_type=True):
        """
        Unify types for IndexedAccessType.

        Since IndexedAccessType is a computed type (T[K] resolves to some type),
        we use a conservative approach: return empty dict (no unification)
        unless we can resolve the indexed access type.
        """
        # Try to resolve the indexed access to a concrete type
        resolved = self._try_resolve()
        if resolved:
            # Delegate to the resolved type
            from src.ir import type_utils as tu
            return tu.unify_types(t1, resolved, factory, same_type)

        # Cannot resolve, no unification possible
        return {}

    def get_name(self):
        return f"{self.object_type.get_name()}[{self.index_type.get_name()}]"

    def __str__(self):
        return f"IndexedAccessType({self.object_type}[{self.index_type}])"

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.object_type == other.object_type and
                self.index_type == other.index_type and
                self._resolved_type == getattr(other, '_resolved_type', None))

    def __hash__(self):
        return hash(str(self.name) + str(self.object_type) + str(self.index_type))


class UnionTypeFactory(object):
    def __init__(self, max_ut, max_in_union):
        self.max_ut = max_ut
        self.unions = []
        self.max_in_union = max_in_union

    def get_number_of_types(self):
        return ut.random.integer(2, self.max_in_union)

    def get_types_for_union(self, gen):
        num_of_types = self.get_number_of_types()
        types = set()
        while len(types) < num_of_types:
            t = gen.select_type(exclude_native_compound_types=True)
            types.add(t)
        return list(types)

    def gen_union_type(self, gen):
        """ Generates a union type that consists of N types
            where N is a number in [2, self.max_in_union].

            Args:
                gen - Instance of Hephaestus' generator

        """
        types = self.get_types_for_union(gen)
        gen_union = UnionType(types)
        self.unions.append(gen_union)
        return gen_union

    def get_union_type(self, gen_object):
        """ Returns a previously created union type
            or a newly generated at random.

            If there are previously generated union types
            and they have not exceeded the limit, we make a
            probabilistic choice on whether to pick one of
            the already generated types or create a new one.

        """
        generated = len(self.unions)
        if generated == 0:
            return self.gen_union_type(gen_object)
        if generated >= self.max_ut or ut.random.bool():
            union_t = ut.random.choice(self.unions)
            if union_t.has_type_variables():
                # We might have selected a union type that holds a type
                # variable. However, we must be careful because it might be
                # no possible to use the selected union type since it uses
                # a type variable that is out of context.
                return self.gen_union_type(gen_object)
            else:
                return union_t
        return self.gen_union_type(gen_object)

    def get_union_constant(self, utype, constants):
        """ This method randomly chooses one of the types in a type's
        union and then assigns the union a constant value that matches
        the randomly selected type.

        A union type can have types like 'Object' or 'undefined'
        as part of its union, which however do not have a respective
        constant equivalent.

        Hence, we only consider types that we can generate a constant
        from. If there is none, we revert to a bottom constant.

        TODO revisit this after implementing structural types.

        """
        type_candidates = [t for t in utype.types if t.name in constants]
        if len(type_candidates) == 0:
            return ast.BottomConstant(utype.types[0])
        t = ut.random.choice(type_candidates)
        return constants[t.name](t)


class ArrayType(tp.TypeConstructor, ObjectType):
    def __init__(self, name="Array"):
        # In TypeScript, arrays are covariant.
        super().__init__(name, [tp.TypeParameter(
            "T", variance=tp.Covariant)])


class FunctionType(tp.TypeConstructor):
    def __init__(self, nr_type_parameters: int):
        name = "Function" + str(nr_type_parameters)

        # In Typescript, type parameters are covariant as to the return type
        # and contravariant as to the arguments.

        type_parameters = [
            tp.TypeParameter("A" + str(i), tp.Contravariant)
            for i in range(1, nr_type_parameters + 1)
        ] + [tp.TypeParameter("R", tp.Covariant)]
        self.nr_type_parameters = nr_type_parameters
        super().__init__(name, type_parameters)
        self.supertypes.append(ObjectType())


# Generator Extension

""" The below functions are all passed as candidate
generation functions to the Hephaestus generator
in order for it to be able to work with language-specific
features of typescript.
"""


def gen_type_alias_decl(gen,
                        etype=None) -> ts_ast.TypeAliasDeclaration:
    """ Generate a Type Declaration (Type Alias)

    Args:
       etype: the type(s) that the type alias describes

    Returns:
        An AST node that describes a type alias declaration
        as defined in src.ir.typescript_ast.py

    """
    alias_type = (etype if etype else
                  gen.select_type())
    initial_depth = gen.depth
    gen.depth += 1
    gen.depth = initial_depth
    type_alias_decl = ts_ast.TypeAliasDeclaration(
        name=ut.random.identifier('lower'),
        alias=alias_type
    )
    gen._add_node_to_parent(gen.namespace, type_alias_decl)
    return type_alias_decl


def add_type_alias(gen, namespace, type_name, ta_decl):
    gen.context._add_entity(namespace, 'types', type_name, ta_decl.get_type())
    gen.context._add_entity(namespace, 'decls', type_name, ta_decl)
