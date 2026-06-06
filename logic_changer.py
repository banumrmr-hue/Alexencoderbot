import ast
from typing import List, Union

try:
    from ast import unparse as _unparse
except ImportError:
    _unparse = None


class FlattenTransformer(ast.NodeTransformer):
    def __init__(self):
        super().__init__()
        self._counter = 0

    def _new_state(self) -> int:
        self._counter += 1
        return self._counter

    def visit_FunctionDef(self, node):
        node.body = self._flatten_body(node.body)
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node):
        node.body = self._flatten_body(node.body)
        self.generic_visit(node)
        return node

    def _flatten_body(self, body: List[ast.stmt]) -> List[ast.stmt]:
        if not body or (len(body) == 1 and isinstance(body[0], ast.Pass)):
            return body
        blocks = self._build_blocks(body)
        state_var = ast.Name('__cf_state__', ast.Store())
        init_state = ast.Assign(targets=[state_var], value=ast.Constant(0))
        while_body = self._create_dispatcher(blocks, '__cf_state__')
        while_loop = ast.While(test=ast.Constant(True), body=while_body, orelse=[])
        return [init_state, while_loop]

    def _build_blocks(self, stmts: List[ast.stmt]) -> List[List[ast.stmt]]:
        blocks = []
        current = []
        for stmt in stmts:
            if self._is_branch_or_jump(stmt):
                if current:
                    blocks.append(current)
                    current = []
                transformed = self._transform_branch(stmt)
                if isinstance(transformed, list):
                    blocks.append(transformed)
                else:
                    blocks.append([transformed])
            else:
                current.append(stmt)
        if current:
            blocks.append(current)
        return blocks

    def _is_branch_or_jump(self, stmt: ast.stmt) -> bool:
        return isinstance(stmt, (
            ast.If, ast.While, ast.For, ast.Try,
            ast.Break, ast.Continue, ast.Return, ast.Raise
        ))

    def _transform_branch(self, stmt: ast.stmt) -> Union[ast.stmt, List[ast.stmt]]:
        if isinstance(stmt, ast.If):
            return self._flatten_if(stmt)
        elif isinstance(stmt, ast.While):
            return self._flatten_while(stmt)
        elif isinstance(stmt, ast.For):
            return self._flatten_for(stmt)
        return stmt

    def _flatten_if(self, node: ast.If) -> ast.Assign:
        then_state = self._new_state()
        else_state = self._new_state()
        cond_expr = ast.IfExp(
            test=node.test,
            body=ast.Constant(then_state),
            orelse=ast.Constant(else_state)
        )
        assign = ast.Assign(
            targets=[ast.Name('__cf_state__', ast.Store())],
            value=cond_expr
        )
        node._then_state = then_state
        node._else_state = else_state
        node._then_body = self._flatten_body(node.body)
        node._else_body = self._flatten_body(node.orelse) if node.orelse else []
        return assign

    def _flatten_while(self, node: ast.While) -> ast.Assign:
        loop_state = self._new_state()
        exit_state = self._new_state()
        cond_expr = ast.IfExp(
            test=node.test,
            body=ast.Constant(loop_state),
            orelse=ast.Constant(exit_state)
        )
        assign = ast.Assign(
            targets=[ast.Name('__cf_state__', ast.Store())],
            value=cond_expr
        )
        node._loop_state = loop_state
        node._exit_state = exit_state
        node._loop_body = self._flatten_body(node.body)
        return assign

    def _flatten_for(self, node: ast.For) -> List[ast.stmt]:
        iter_assign = ast.Assign(
            targets=[ast.Name('__cf_iter__', ast.Store())],
            value=ast.Call(
                func=ast.Name('iter', ast.Load()),
                args=[node.iter],
                keywords=[]
            )
        )
        try_body = [
            ast.Assign(
                targets=[node.target],
                value=ast.Call(
                    func=ast.Name('next', ast.Load()),
                    args=[ast.Name('__cf_iter__', ast.Load())],
                    keywords=[]
                )
            )
        ]
        except_handler = ast.ExceptHandler(
            type=ast.Name('StopIteration', ast.Load()),
            name=None,
            body=[ast.Break()]
        )
        try_stmt = ast.Try(
            body=try_body,
            handlers=[except_handler],
            orelse=[],
            finalbody=[]
        )
        while_body = [try_stmt] + node.body
        while_node = ast.While(test=ast.Constant(True), body=while_body, orelse=[])
        return [iter_assign, self._transform_branch(while_node)]

    def _create_dispatcher(self, blocks: List[List[ast.stmt]], state_var_name: str) -> List[ast.stmt]:
        state_var = ast.Name(state_var_name, ast.Load())
        dispatcher = []
        if blocks:
            dispatcher.append(
                ast.If(
                    test=ast.Compare(
                        left=state_var,
                        ops=[ast.Eq()],
                        comparators=[ast.Constant(0)]
                    ),
                    body=[ast.Assign(
                        targets=[ast.Name(state_var_name, ast.Store())],
                        value=ast.Constant(1)
                    )],
                    orelse=[]
                )
            )
        for idx, block in enumerate(blocks, start=1):
            state_num = idx
            block_stmts = list(block)
            if not any(isinstance(s, (ast.Return, ast.Break, ast.Continue, ast.Raise)) for s in block_stmts):
                next_state = idx + 1 if idx < len(blocks) else len(blocks) + 1
                block_stmts.append(
                    ast.Assign(
                        targets=[ast.Name(state_var_name, ast.Store())],
                        value=ast.Constant(next_state)
                    )
                )
            if_test = ast.Compare(
                left=state_var,
                ops=[ast.Eq()],
                comparators=[ast.Constant(state_num)]
            )
            dispatcher.append(ast.If(test=if_test, body=block_stmts, orelse=[]))
        final_state = len(blocks) + 1
        dispatcher.append(
            ast.If(
                test=ast.Compare(
                    left=state_var,
                    ops=[ast.Eq()],
                    comparators=[ast.Constant(final_state)]
                ),
                body=[ast.Break()],
                orelse=[]
            )
        )
        return dispatcher


def run_logic_changer(source_code: str) -> str:
    tree = ast.parse(source_code)
    transformer = FlattenTransformer()
    transformed = transformer.visit(tree)
    ast.fix_missing_locations(transformed)
    if _unparse:
        return _unparse(transformed)
    else:
        try:
            import astor
            return astor.to_source(transformed)
        except ImportError:
            raise RuntimeError("ast.unparse not available (Python < 3.9) and astor not installed.")
