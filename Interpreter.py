
import AST
import SymbolTable
from Memory import *
from Exceptions import  *
from visit import *
from operator import *

operators = {}
operators['+'] = add
operators['-'] = sub
operators['*'] = mul
operators['/'] = div
operators['%'] = mod
operators['|'] = or_
operators['&'] = and_
operators['&&'] = and_
operators['||'] = or_
operators['<<'] = lshift
operators['>>'] = rshift
operators['=='] = eq
operators['!='] = ne
operators['>'] = lt
operators['<'] = gt
operators['<='] = le
operators['>='] = ge

class Interpreter(object):
    
    def __init__(self):
        self.globalMemory = MemoryStack(Memory("global"))
        self.functionMemories = []

    @on('node')
    def visit(self, node):
        pass
    
    @when(AST.Node)
    def visit(self, node):
        pass

    @when(AST.Program)
    def visit(self, node):
        print "PROGRAM"
        node.declarations.accept(self)
        node.fundefs.accept(self)
        node.instructions.accept(self)
    
    @when(AST.Declarations)
    def visit(self, node):
        print "DECLARATIONS"
        for declaration in node.declarations:
            declaration.accept(self)
    
    @when(AST.Declaration)
    def visit(self, node):
        print "DECLARATION"
        node.inits.accept(self)
    
    @when(AST.Inits)
    def visit(self, node):
        print "INITS"
        for init in node.inits:
            init.accept(self)
    
    @when(AST.Init)
    def visit(self, node):
        print "INIT"
        if len(self.functionMemories) == 0:
            self.globalMemory.put(node.id, node.expression.accept(self))
        else:
            self.functionMemories[len(self.functionMemories) - 1].put(node.id, node.expression.accept(self))
    
    @when(AST.Instructions)
    def visit(self, node):
        print "INSTRUCTIONS"
        for instruction in node.instructions:
            instruction.accept(self)
    
    @when(AST.Instruction)
    def visit(self, node):
        pass
    
    @when(AST.Print)
    def visit(self, node):
        print "PRINT"
        value = node.expression.accept(self)
        if type(node.expression) is AST.Id:
            value = self._get_id_value_from_memory(value)
        print value
    
    @when(AST.Labeled)
    def visit(self, node):
        node.instruction.accept(self)
    
    @when(AST.Assignment)
    def visit(self, node):
        print "ASSIGNMENT"
        if len(self.functionMemories) == 0 or self.functionMemories[len(self.functionMemories) - 1].put_existing(node.id, node.expression.accept(self)) is False:
            self.globalMemory.put_existing(node.id, node.expression.accept(self))

    @when(AST.Choice)
    def visit(self, node):
        print "CHOICE"
        if not node._if.accept(self):
            node._else.accept(self) #return?
    
    @when(AST.If)
    def visit(self, node):
        print "IF"
        if node.cond.accept(self):
            node.statement.accept(self)
            return True     #co z returnem powyzszego, czy potrzebny?
        else:
            return False
    
    @when(AST.Else)
    def visit(self, node):
        print "ELSE"
        return node.statement.accept(self) #czy tu potrzebny return?
    
    @when(AST.While)
    def visit(self, node):
        print "WHILE"
        r = None
        while node.cond.accept(self):
            try:
                r = node.statement.accept(self)
            except BreakException:
                break
            except ContinueException:
                continue
        return r    #co tutaj daje return?
    
    @when(AST.RepeatUntil)
    def visit(self, node):
        print "REPEAT"
        r = None
        try:
            r = node.statement.accept(self)
        except BreakException:
            return r
        except ContinueException:
            pass
        while node.cond.accept(self):
            try:
                r = node.statement.accept(self)
            except BreakException:
                break
            except ContinueException:
                continue
        return r
    
    @when(AST.Return)
    def visit(self, node):
        print "RETURN"
        raise ReturnValueException(node.expression.accept(self))
    
    @when(AST.Continue)
    def visit(self, node):
        print "CONTINUE"
        raise ContinueException()
    
    @when(AST.Break)
    def visit(self, node):
        print "BREAK"
        raise BreakException()
    
    @when(AST.Compound)
    def visit(self, node):
        print "COMPOUND"
        function = False
        if len(self.functionMemories) == 0:
            self.globalMemory.push(Memory("compound"))
        else:
            function = True
            self.functionMemories[len(self.functionMemories) - 1].push(Memory("compound"))
            
        node.declarations.accept(self)
        node.instructions.accept(self)
        
        if function is False:
            self.globalMemory.pop()
        else:
            self.functionMemories[len(self.functionMemories) - 1].pop()
    
    @when(AST.Condition)
    def visit(self, node):
        pass

    @when(AST.Expression)
    def visit(self, node):
        pass
    
    @when(AST.Const)
    def visit(self, node):
        print "CONST"
        return self._value_as_proper_type(node.value)
    
    def _value_as_proper_type(self, value):
        for type_name in [int, float]:
            try:
                return type_name(value)
            except Exception:
                pass
        return value
    
    @when(AST.Id)
    def visit(self, node):
        print "ID"
        return node.id
    
    @when(AST.BinExpr)
    def visit(self, node):
        print "BINEXPR"
        left = node.expr1.accept(self)
        right = node.expr2.accept(self)
        if type(node.expr1) is AST.Id:
            left = self._get_id_value_from_memory(left)
            print "CONVERTED LEFT"
        if type(node.expr2) is AST.Id:
            right = self._get_id_value_from_memory(right)
            print "CONVERTED RIGHT"
        print type(node.expr1)
        print type(node.expr2)
        print "  LEFT:", left, type(left)
        print "  RIGHT:", right, type(right)
        return operators[node.operator](left, right)

    def _get_id_value_from_memory(self, id):
        value = None
        if self._currently_inside_a_function():
            value = self.functionMemories[-1].get(id)
        if value == None:
            value = self.globalMemory.get(id)
        return value

    def _currently_inside_a_function(self):
        return len(self.functionMemories) > 0

    @when(AST.ExpressionInParentheses)
    def visit(self, node):
        print "EXPRESSION IN PARENTHESES"
        return node.expression.accept(self)
    
    @when(AST.IdWithParentheses)
    def visit(self, node):
        print "ID WITH PARENTHESES"
        fundef = self.globalMemory.get(node.id.accept(self))
        functionMemory = Memory(node.id)
        print map(lambda name, value: functionMemory.put(name, value), fundef.arglist.accept(self), node.expression_list.accept(self))  #print is debug output
        self.functionMemories.append(functionMemory)
        try:
            fundef.accept(self)
            self.functionMemories.pop()
        except ReturnValueException as e:
            self.functionMemories.pop()
            return e.value
    
    @when(AST.ExpressionList)
    def visit(self, node):
        print "EXPRESSION LIST"
        expressionResults = []
        for expression in node.expressions:
            expressionResults.append(expression.accept(self))
        return expressionResults
    
    @when(AST.FunctionDefinitions)
    def visit(self, node):
        print "FUNCTION DEFINITIONS"
        for fundef in node.fundefs:
            self.globalMemory.put(fundef.id, fundef)
    
    @when(AST.FunctionDefinition)
    def visit(self, node):
        print "FUNCTION DEFINITION"
        node.compound_instr.accept(self)
    
    @when(AST.ArgumentList)
    def visit(self, node):
        print "ARGUMENT LIST"
        args = []
        for arg in node.arg_list:
            args.append(arg.accept(self))
        return args
    
    @when(AST.Argument)
    def visit(self, node):
        print "ARGUMENT"
        return node.id
