import re


class Token:
    
    def __init__(self, type: str, value: str, ):
        self.type = type
        self.value = value
        
    def show(self):
        return f"Токен({self.type}, '{self.value}')"
    

SPACE = re.compile("[ \t]+")
NUMBER = re.compile("[0-9]+")
ID = re.compile("[A-Za-z_][A-Za-z0-9_]*")
ADD = re.compile("\\+")
SUB= re.compile("-")
MUL = re.compile("\\*")
DIV = re.compile("/")
LPAREN = re.compile("\\(")
RPAREN = re.compile("\\)")
    
def tokenize(text):
    
    tokens = []
    position = 0
    
    while position < len(text):
        
        t = SPACE.match(text, position)
        if t is not None:
            position = t.end()
            continue
        
        t = NUMBER.match(text, position)
        if t is not None:
            tokens.append(Token("NUMBER", t.group()))
            position = t.end()
            continue
        
        t = ID.match(text, position)
        if t is not None:
            tokens.append(Token("ID", t.group()))
            position = t.end()
            continue
        
        t = ADD.match(text, position)
        if t is not None:
            tokens.append(Token("ADD", t.group()))
            position = t.end()
            continue
        
        t = SUB.match(text, position)
        if t is not None:
            tokens.append(Token("SUB", t.group()))
            position = t.end()
            continue
        
        t = MUL.match(text, position)
        if t is not None:
            tokens.append(Token("MUL", t.group()))
            position = t.end()
            continue

        t = DIV.match(text, position)
        if t is not None:
            tokens.append(Token("DIV", t.group()))
            position = t.end()
            continue

        t = LPAREN.match(text, position)
        if t is not None:
            tokens.append(Token("LPAREN", t.group()))
            position = t.end()
            continue
        
        t = RPAREN.match(text, position)
        if t is not None:
            tokens.append(Token("RPAREN", t.group()))
            position = t.end()
            continue
        
        c = text[position]
        raise ValueError("Ошибка! Недопустимый символ: " + '(c)')
    
    tokens.append(Token("EOF", ""))
    
    return tokens

class ParserError(Exception):
    pass


#Как я понял из задания там крч все из S(как всегда на практиках было)
#F - там явно прописан как раскрытие F -> ( S ) | num | id
# странно, что про E забыли, ну добавил - хотя от перехода S -> E толку ноль
# тогда:
# S -> E
# E -> T E'              - в T запихнули умножение, т к оно идет первее всегда, чем сложение и т д
# E' -> + T E' | - T E' | лямбда
# T -> F T'                         - например число и действие
# T' -> * F T' | / F T' | лямбда    - умнож/деление число и потом пусто
# F -> ( E ) | number | id       - выражение в скобках будет как полное новое
#

class Parser:
    
    TOKEN_TEXT = {
        "ADD": "+",
        "SUB": "-",
        "MUL": "*",
        "DIV": "/",
        "LPAREN": "(",
        "RPAREN": ")",
        "NUMBER": "number",
        "ID": "id",
        "EOF": "конец строки",
    }
    
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0
        
    def current(self):
        
        return self.tokens[self.position]
    
    def getNextToken(self):
        
        tok = self.tokens[self.position]
        if tok.type != "EOF":
            self.position = self.position + 1
        return tok
    
    def match(self, expected_token):
        
        tok = self.current()
        if tok.type != expected_token:
            expected_text = self.TOKEN_TEXT.get(expected_token, expected_token)
            raise ParserError("Ошибка! Ожидалось: '" + expected_text + "'")
        return self.getNextToken()
    
    
    
    def parseS(self):
        self.parseE()

    def parseE(self):
        self.parseT()
        self.parseEPrime()

    def parseEPrime(self):
        while True:
            tok = self.current()
            if tok.type == "ADD" or tok.type == "SUB":
                self.getNextToken()
                self.parseT()
            else:
                break

    def parseT(self):
        self.parseF()
        self.parseTPrime()

    def parseTPrime(self):
        while True:
            tok = self.current()
            if tok.type == "MUL" or tok.type == "DIV":
                self.getNextToken()
                self.parseF()
            else:
                break

    def parseF(self):
        
        tok = self.current()

        if tok.type == "LPAREN":
            self.match("LPAREN")
            self.parseS()
            self.match("RPAREN")

        elif tok.type == "NUMBER" or tok.type == "ID":
            self.getNextToken()

        else:
            raise ParserError("Ошибка! Ожидалось: number, id или '('")

    def parse(self):
        
        self.parseS()
        if self.current().type != "EOF":
            raise ParserError("Ошибка! Ожидалось: конец строки") # проблема двух вариантов подобного примера 2 + 3 ( 66 - 9 ) - либо же писать что после 2 + 3 конец строки и найдена скобка, либо же, что там могли быть арифм.символы а появилась скобка - тип оба правильные варики, но отловить можно только здесь
        

def analyze(text):
    try:
        tokens = tokenize(text)
    except ValueError as e:
        return str(e)

    parser = Parser(tokens)
    try:
        parser.parse()
    except ParserError as e:
        return str(e)

    return "Выражение корректно."

def main():
    text = input("Ввод: ")
    print("Вывод: " + analyze(text))

if __name__ == "__main__":
    main()