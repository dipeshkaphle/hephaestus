from src import utils
from src.ir import ast, type_utils as tu, types as tp
from src.ir.typescript_ast import TypeAliasDeclaration
from src.transformations.base import Transformation, change_namespace
from src.analysis import type_dependency_analysis as tda


class TypeOverwriting(Transformation):
    CORRECTNESS_PRESERVING = False

    def __init__(self, program, language, logger=None, options={}):
        super().__init__(program, language, logger, options)
        self._namespace = ast.GLOBAL_NAMESPACE
        self.global_type_graph = {}
        self.types = program.get_types()
        self.bt_factory = program.bt_factory
        self.error_injected = None
        self._method_selection = True
        self._candidate_methods = []
        self._selected_method = None

    def get_visitors(self):
        """Override to add language-specific visitors"""
        visitors = super().get_visitors()
        visitors[TypeAliasDeclaration] = self.visit_type_alias_decl
        return visitors

    def visit_type_alias_decl (self, node):
        return node

    def visit_program(self, node):
        super().visit_program(node)
        self._method_selection = False
        if not self._candidate_methods:
            return node
        self._selected_method = utils.random.choice(self._candidate_methods)
        return super().visit_program(node)

    @change_namespace
    def visit_class_decl(self, node):
        return super().visit_class_decl(node)

    def visit_var_decl(self, node):
        if self._namespace != ast.GLOBAL_NAMESPACE:
            return super().visit_var_decl(node)

        # We need this analysis, we have to include type information of global
        # variables.
        t_an = tda.TypeDependencyAnalysis(self.program,
                                          namespace=ast.GLOBAL_NAMESPACE)
        t_an.visit(node)
        self.global_type_graph.update(t_an.result())
        return node

    def _add_candidate_method(self, node):
        t_an = tda.TypeDependencyAnalysis(self.program,
                                          namespace=self._namespace[:-1],
                                          type_graph=None)
        t_an.visit(node)
        type_graph = t_an.result()
        type_graph.update(self.global_type_graph)
        candidate_nodes = [
            n
            for n in type_graph.keys()
            if n.is_omittable() and not (
                isinstance(n, tda.DeclarationNode) and n.decl.name == tda.RET
            )
        ]
        if not candidate_nodes:
            return node
        self._candidate_methods.append((self._namespace, candidate_nodes,
                                        type_graph))
        return node

    @change_namespace
    def visit_func_decl(self, node):
        if self._method_selection:
            return self._add_candidate_method(node)
        namespace, candidate_nodes, type_graph = self._selected_method
        if namespace != self._namespace:
            return node

        # Generate a type that is irrelevant
        n = utils.random.choice(candidate_nodes)
        if isinstance(n, tda.TypeConstructorInstantiationCallNode):
            type_params = [
                n.target for n in type_graph[n]
                if any(e.is_inferred() for e in type_graph[n.target])
            ]
            if not type_params:
                return node
            type_param = utils.random.choice(type_params)
            node_type = n.t.get_type_variable_assignments()[type_param.t]
            old_type = node_type
        else:
            node_type = n.decl.get_type()
            old_type = node_type

        # Skip transformation for base types Boolean, String, BigInteger
        # but allow it for literal types (StringLiteralType, NumberLiteralType)
        try:
            from src.ir import typescript_types as tst
            is_literal_type = isinstance(node_type, (tst.StringLiteralType, tst.NumberLiteralType))
        except ImportError:
            is_literal_type = False

        if not is_literal_type and node_type.name in ["Boolean", "String", "BigInteger"]:
            return node
        
        ir_type, debug_info = tu.find_irrelevant_type(node_type, self.types, self.bt_factory)

        if ir_type is None:
            return node

        # Additional check for VariableDeclarations: ensure the replacement type
        # is also irrelevant to the actual expression's type, not just the declared type.
        # This prevents replacing with supertypes of the actual value.
        # Example: const x: string | Function = "literal"
        # Should not replace with String (supertype of "literal")
        if isinstance(n, tda.DeclarationNode) and isinstance(n.decl, ast.VariableDeclaration):
            expr = n.decl.expr
            # Get the expression's type if it has one
            expr_type = None
            if hasattr(expr, 'inferred_type') and expr.inferred_type:
                expr_type = expr.inferred_type
            elif hasattr(expr, 'get_type'):
                try:
                    expr_type = expr.get_type()
                except (AttributeError, NotImplementedError):
                    pass
            elif isinstance(expr, ast.Variable):
                # For variable references, look up the variable's type in the context
                try:
                    var_decl = self.program.context.get_var(n.decl.namespace, expr.name)
                    if var_decl:
                        expr_type = var_decl.get_type()
                except (AttributeError, KeyError):
                    pass

            # If we have an expression type different from the declared type,
            # verify the replacement is also irrelevant to it
            if expr_type and expr_type != node_type:
                try:
                    # Check if ir_type has a subtyping relationship with expr_type
                    if ir_type.is_subtype(expr_type) or expr_type.is_subtype(ir_type):
                        # ir_type is relevant to expr_type - skip this transformation
                        return node
                except (AttributeError, NotImplementedError):
                    # If we can't check, be conservative and skip
                    return node

        # Record the transformation
        if hasattr(self.program, 'transformation_tracker'):
            from src.transformations.tracker import TransformationRecord
            record = TransformationRecord(
                transformation_name=self.__class__.__name__,
                target_node_id=n.node_id,
                description=f"Replaced type of node '{n.node_id}' with an irrelevant type.",
                original_type=str(old_type),
                new_type=str(ir_type),
                available_types_pool=debug_info.get("available_types_pool"),
                relevant_types_found=debug_info.get("relevant_types_found"),
                candidate_pool=debug_info.get("candidate_pool")
            )
            self.program.transformation_tracker.record(record)

        # Perform the mutation
        if isinstance(n, tda.DeclarationNode):
            if isinstance(n.decl, ast.VariableDeclaration):
                n.decl.var_type = ir_type
            else:
                n.decl.ret_type = ir_type
            n.decl.inferred_type = ir_type
        t = getattr(n, 't', None)
        if t is not None:
            type_parameters = (
                t.t_constructor.type_parameters
                if isinstance(t, tp.ParameterizedType)
                else t.type_parameters
            )
        if isinstance(n, tda.TypeConstructorInstantiationCallNode):
            indexes = {
                t_param: i
                for i, t_param in enumerate(type_parameters)
            }

            # Validate mutation before applying for structural typing
            # Check if mutating this type argument actually creates an inequivalent type
            # This prevents ineffective mutations when type parameters are phantom (unused)
            param_index = indexes[type_param.t]
            original_type_args = list(n.t.type_args)
            candidate_type_args = list(n.t.type_args)
            candidate_type_args[param_index] = ir_type

            try:
                # Construct both types to compare
                original_type = n.t.t_constructor.new(original_type_args)
                candidate_type = n.t.t_constructor.new(candidate_type_args)

                # Check if they have a subtyping relationship (structural equivalence)
                if candidate_type.is_subtype(original_type) or original_type.is_subtype(candidate_type):
                    # Types are structurally equivalent - mutation is ineffective
                    # This happens with phantom type parameters in structural typing
                    return node
            except (AttributeError, NotImplementedError):
                # Some types may not implement is_subtype properly
                # In this case, proceed with mutation (best effort)
                pass

            # Apply the mutation (only if validation passed)
            n.t.type_args[param_index] = ir_type
            # Reset the flag so the changed type arguments are visible in output
            n.t.can_infer_type_args = False
        self.is_transformed = True
        self.error_injected = "{} expected but {} found in node {}".format(
            str(old_type), str(ir_type), n.node_id)
        return node
