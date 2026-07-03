
import re

# 1. ANALISIS LEKSIKAL

class Token:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"<{self.type}:{self.value}>"


TOKEN_SPEC = [
    ("NUMBER",   r"\d+"),
    ("IDENT",    r"[A-Za-z_][A-Za-z0-9_]*"),
    ("OP",       r"==|!=|<=|>=|<|>|\+|-|\*|/"),
    ("ASSIGN",   r"="),
    ("LPAREN",   r"\("),
    ("RPAREN",   r"\)"),
    ("LBRACE",   r"\{"),
    ("RBRACE",   r"\}"),
    ("SEMI",     r";"),
    ("SKIP",     r"[ \t\n]+"),
]

MASTER_PATTERN = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC))

KEYWORDS = {"for"}


def lexical_analysis(source_code):
    tokens = []
    for match in MASTER_PATTERN.finditer(source_code):
        kind = match.lastgroup
        value = match.group()
        if kind == "SKIP":
            continue
        if kind == "IDENT" and value in KEYWORDS:
            kind = "KEYWORD"
        tokens.append(Token(kind, value))
    return tokens


# 2. ANALISIS SINTAKSIS (Membentuk AST)

class ForNode:
    def __init__(self, init, condition, update, body):
        self.init = init
        self.condition = condition
        self.update = update
        self.body = body

    def __repr__(self):
        return (f"ForNode(\n  init={self.init},\n  condition={self.condition},"
                f"\n  update={self.update},\n  body={self.body}\n)")


class AssignNode:
    def __init__(self, target, expr):
        self.target = target
        self.expr = expr

    def __repr__(self):
        return f"Assign({self.target} = {self.expr})"


class BinOpNode:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f"({self.left} {self.op} {self.right})"


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def eat(self, expected_type=None):
        tok = self.current()
        if tok is None:
            raise SyntaxError("Input berakhir lebih awal dari yang diharapkan.")
        if expected_type and tok.type != expected_type:
            raise SyntaxError(f"Diharapkan token {expected_type}, tapi ditemukan {tok.type} ('{tok.value}')")
        self.pos += 1
        return tok

    def parse_assignment(self):
        target = self.eat("IDENT").value
        self.eat("ASSIGN")
        expr = self.parse_expression()
        return AssignNode(target, expr)

    def parse_expression(self):
        left = self.eat().value  # operand pertama (IDENT atau NUMBER)
        if self.current() and self.current().type == "OP":
            op = self.eat("OP").value
            right = self.eat().value
            return BinOpNode(left, op, right)
        return left

    def parse_condition(self):
        left = self.eat().value
        op = self.eat("OP").value
        right = self.eat().value
        return BinOpNode(left, op, right)

    def parse_for(self):
        self.eat("KEYWORD")   # 'for'
        self.eat("LPAREN")
        init = self.parse_assignment()
        self.eat("SEMI")
        condition = self.parse_condition()
        self.eat("SEMI")
        update = self.parse_assignment()
        self.eat("RPAREN")

        self.eat("LBRACE")
        body = []
        while self.current() and self.current().type != "RBRACE":
            body.append(self.parse_assignment())
        self.eat("RBRACE")

        return ForNode(init, condition, update, body)


# 3. ANALISIS SEMANTIK

class SemanticError(Exception):
    pass


def semantic_analysis(ast, symbol_table):
    """
    Memeriksa apakah semua variabel yang dipakai sudah 'dideklarasikan'
    (ada di symbol_table) dan bertipe numerik (int), sebelum kode TAC dibuat.
    """
    def check_operand(operand):
        if isinstance(operand, str) and not operand.isdigit():
            if operand not in symbol_table:
                raise SemanticError(f"Variabel '{operand}' belum dideklarasikan.")

    def check_expr(expr):
        if isinstance(expr, BinOpNode):
            check_operand(expr.left)
            check_operand(expr.right)
        else:
            check_operand(expr)

    # variabel dari init otomatis "dideklarasikan" sebagai int
    symbol_table[ast.init.target] = "int"

    check_expr(ast.init.expr)
    check_expr(ast.condition)
    check_expr(ast.update.expr)
    check_operand(ast.update.target)

    for stmt in ast.body:
        check_operand(stmt.target)
        check_expr(stmt.expr)

    return True



# 4. GENERASI KODE ANTARA (THREE-ADDRESS CODE)

class TACGenerator:
    def __init__(self):
        self.temp_counter = 1
        self.label_counter = 1
        self.code = []

    def new_temp(self):
        t = f"t{self.temp_counter}"
        self.temp_counter += 1
        return t

    def new_label(self):
        l = f"L{self.label_counter}"
        self.label_counter += 1
        return l

    def gen_expr(self, expr):
        """Mengembalikan nama variabel/temp yang menampung hasil ekspresi."""
        if isinstance(expr, BinOpNode):
            temp = self.new_temp()
            self.code.append(f"{temp} = {expr.left} {expr.op} {expr.right}")
            return temp
        return expr  # sudah berupa nilai/identifier tunggal

    def gen_assign(self, node):
        result = self.gen_expr(node.expr)
        self.code.append(f"{node.target} = {result}")

    def generate(self, ast):
        # inisialisasi
        self.gen_assign(ast.init)

        label_start = self.new_label()
        label_end = self.new_label()

        self.code.append(f"{label_start}:")
        cond = ast.condition
        self.code.append(f"ifFalse {cond.left} {cond.op} {cond.right} goto {label_end}")

        for stmt in ast.body:
            self.gen_assign(stmt)

        self.gen_assign(ast.update)
        self.code.append(f"goto {label_start}")
        self.code.append(f"{label_end}:")

        return "\n".join(self.code)


# PROGRAM UTAMA

if __name__ == "__main__":
    source = "for ( i = 0 ; i < 5 ; i = i + 1 ) { sum = sum + i }"

    # variabel yang dianggap sudah ada di scope luar sebelum loop dijalankan
    symbol_table = {"sum": "int"}

    print("Source code:")
    print(source)

    print("\n--- 1. Tahap Leksikal (Tokenisasi) ---")
    tokens = lexical_analysis(source)
    print(tokens)

    print("\n--- 2. Tahap Sintaksis (AST) ---")
    parser = Parser(tokens)
    ast = parser.parse_for()
    print(ast)

    print("\n--- 3. Tahap Semantik ---")
    try:
        semantic_analysis(ast, symbol_table)
        print("Semua variabel valid. Tabel simbol akhir:", symbol_table)
    except SemanticError as e:
        print("Error semantik:", e)
        exit(1)

    print("\n--- 4. Tahap Generasi Kode (Three-Address Code) ---")
    generator = TACGenerator()
    tac = generator.generate(ast)
    print(tac)

    # Contoh kasus gagal semantik: variabel 'total' belum dideklarasikan
    print("\n--- Contoh Kasus Gagal (Uji Semantik) ---")
    source_error = "for ( j = 0 ; j < 3 ; j = j + 1 ) { total = total + j }"
    tokens_err = lexical_analysis(source_error)
    ast_err = Parser(tokens_err).parse_for()
    try:
        semantic_analysis(ast_err, {"sum": "int"})
    except SemanticError as e:
        print("Error semantik (sesuai dugaan):", e)
