import ast
import base64
import hashlib
import marshal
import random
import zlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


class UltimateObfuscator:
    def __init__(self, source_code: str):
        self.code = source_code
        self._key_fragments = [
            b'\xe1H-\x03', b't\xfa\r]', b'SD\x9a\x95', b'\xca\xc1\t\x86',
            b'\x18\xca]\x7f', b'\xaeA\xf6\xbe', b'\xf7A\xc3\xc7', b'\xa6$\xae>'
        ]
        self._iv_bytes = b'\x10p\x8a\xefRJ\xadd\xd3\x97%\xab\xcaE\xfb\\'

    def _derive_key(self):
        return b''.join(self._key_fragments)

    class VariableCollector(ast.NodeVisitor):
        def __init__(self):
            self.assigned_vars = set()

        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Store):
                self.assigned_vars.add(node.id)
            self.generic_visit(node)

        def visit_arg(self, node):
            self.assigned_vars.add(node.arg)
            self.generic_visit(node)

    class VariableRenamer(ast.NodeTransformer):
        def __init__(self, assigned_vars):
            self.var_map = {}
            self.assigned_vars = assigned_vars

        def _obf_name(self, original):
            return f"__v_{hashlib.shake_128(original.encode()).hexdigest(8)}"

        def visit_Name(self, node):
            if node.id in self.assigned_vars:
                if node.id not in self.var_map:
                    self.var_map[node.id] = self._obf_name(node.id)
                node.id = self.var_map[node.id]
            return node

        def visit_arg(self, node):
            if node.arg in self.assigned_vars:
                if node.arg not in self.var_map:
                    self.var_map[node.arg] = self._obf_name(node.arg)
                node.arg = self.var_map[node.arg]
            return node

    class ControlFlowFlattener(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            self.generic_visit(node)
            state_var = f"__state_{random.randint(1000, 9999)}"
            new_body = [
                ast.Assign(
                    targets=[ast.Name(id=state_var, ctx=ast.Store())],
                    value=ast.Constant(value=0)
                )
            ]
            while_body = []
            for i, stmt in enumerate(node.body):
                while_body.append(
                    ast.If(
                        test=ast.Compare(
                            left=ast.Name(id=state_var, ctx=ast.Load()),
                            ops=[ast.Eq()],
                            comparators=[ast.Constant(value=i)]
                        ),
                        body=[
                            stmt,
                            ast.AugAssign(
                                target=ast.Name(id=state_var, ctx=ast.Store()),
                                op=ast.Add(),
                                value=ast.Constant(value=1)
                            )
                        ],
                        orelse=[]
                    )
                )
            new_body.append(
                ast.While(
                    test=ast.Compare(
                        left=ast.Name(id=state_var, ctx=ast.Load()),
                        ops=[ast.Lt()],
                        comparators=[ast.Constant(value=len(node.body))]
                    ),
                    body=while_body,
                    orelse=[]
                )
            )
            node.body = new_body
            return node

    class StringEncryptor(ast.NodeTransformer):
        def __init__(self, obfuscator):
            self.obfuscator = obfuscator
            self.in_fstring = False

        def visit_JoinedStr(self, node):
            self.in_fstring = True
            self.generic_visit(node)
            self.in_fstring = False
            return node

        def visit_Constant(self, node):
            if isinstance(node.value, str) and not self.in_fstring:
                cipher = AES.new(self.obfuscator._derive_key(), AES.MODE_CBC, self.obfuscator._iv_bytes)
                encrypted = cipher.encrypt(pad(node.value.encode(), 16))
                return ast.Call(
                    func=ast.Name(id='__decode_x', ctx=ast.Load()),
                    args=[ast.Constant(value=encrypted)],
                    keywords=[]
                )
            return node

    def _transform_ast(self):
        tree = ast.parse(self.code)
        collector = self.VariableCollector()
        collector.visit(tree)
        assigned_vars = collector.assigned_vars
        for transformer in [
            self.VariableRenamer(assigned_vars),
            self.ControlFlowFlattener(),
            self.StringEncryptor(self)
        ]:
            tree = transformer.visit(tree)
            ast.fix_missing_locations(tree)
        return marshal.dumps(compile(tree, "<obfuscated>", "exec"))

    def _split_payload(self, b85, size=150):
        return [b85[i:i + size] for i in range(0, len(b85), size)]

    def _build_loader(self, chunks):
        chunk_defs = "\n".join([f"__chunk{i} = \"{chunk}\"" for i, chunk in enumerate(chunks)])
        joined = ", ".join([f"__chunk{i}" for i in range(len(chunks))])
        return f'''
import sys as __s, os as __o, base64 as __b, marshal as __m, zlib as __z, traceback as __t
from Crypto.Cipher import AES as __A
from Crypto.Util.Padding import unpad as __u

def __anti_dbg():
    if __s.gettrace() or (__o.name == 'nt' and __import__('ctypes').windll.kernel32.IsDebuggerPresent()):
        __s.exit(0)
__anti_dbg()

__iv = {repr(self._iv_bytes)}
__kf = [
    b'\\xe1H-\\x03', b't\\xfa\\r]', b'SD\\x9a\\x95', b'\\xca\\xc1\\t\\x86',
    b'\\x18\\xca]\\x7f', b'\\xaeA\\xf6\\xbe', b'\\xf7A\\xc3\\xc7', b'\\xa6$\\xae>'
]
__key = b''.join(__kf)

def __decode_x(d):
    try:
        return __u(__A.new(__key, __A.MODE_CBC, __iv).decrypt(d), 16).decode()
    except: return ""

{chunk_defs}
__BLOB = "".join([{joined}])

def __boot():
    try:
        raw = __b.b85decode(__BLOB.encode())
        decrypted = __u(__A.new(__key, __A.MODE_CBC, __iv).decrypt(raw), 16)
        payload = __z.decompress(decrypted)
        exec(__m.loads(payload), {{'__name__': '__main__', '__builtins__': __builtins__, '__decode_x': __decode_x}})
    except Exception:
        __t.print_exc()
        __s.exit(1)

__boot()
'''

    def obfuscate(self) -> str:
        transformed = self._transform_ast()
        compressed = zlib.compress(transformed, level=9)
        cipher = AES.new(self._derive_key(), AES.MODE_CBC, self._iv_bytes)
        encrypted = cipher.encrypt(pad(compressed, 16))
        b85 = base64.b85encode(encrypted).decode()
        chunks = self._split_payload(b85)
        return self._build_loader(chunks)


def run_obfuxtreme(source_code: str) -> str:
    ob = UltimateObfuscator(source_code)
    return ob.obfuscate()
