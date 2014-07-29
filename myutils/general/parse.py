# http://blog.smitec.net/posts/parsing-bool-in-python/
def parse(statement):
    arg = ""
    stack = []
    output = [""]
    consume = False
    ops = ["and", "or"]
    for g in statement.split(" "):
        slashquote = (len(g) - len(g.replace("\\\"","")))/2
        quote = (len(g) - len(g.replace("\"","")))-slashquote
        
        if quote % 2 == 1:
            consume = not consume
            
        if not consume:
            if g in ops:
                while len(stack) > 0 and stack[0] in ops:
                    output = output + [stack.pop(0)]
                output = output + [""]
                stack = [g] + stack
            elif g == "(":
                stack = [g] + stack
            elif g == ")":
                while stack[0] != "(":
                    temp = stack.pop(0)
                    if len(stack) == 0:
                        print "Error Line", i - 1, "Unmatched parenteses"
                        return None
                    output = output + [temp]
                stack.pop(0)
            else:
                #combine everything else into a single token ("i" ">" "16" -> "i>16")
                output[-1] = output[-1] + g
        else:
            output[-1] = output[-1] + " " +  g
    while len(stack) > 0:
        output = output + [stack.pop(0)]
    return output