# Get fresh data
f = open('ccbcrawl2.py', 'r')
temp = f.read()
f.close()
code = compile(temp, 'ccbcrawl2.py', 'exec')
exec(code)

# Create html table
f = open('htmltable.py', 'r')
temp = f.read()
f.close()
code = compile(temp, 'htmltable.py', 'exec')
exec(code)

# Run amended and certified cases report
f = open('amendorcertify.py', 'r')
temp = f.read()
f.close()
code = compile(temp, 'amendorcertify.py', 'exec')
exec(code)

# Run closed cases report
f = open('closedcasepdfs.py', 'r')
temp = f.read()
f.close()
code = compile(temp, 'closedcases.py', 'exec')
exec(code)
