# Get fresh data
f = open('ccbcrawl2.py', 'r')
temp = f.read()
f.close()
code = compile(temp, 'ccbcrawl2.py', 'exec')
exec(code)

# output CSV of reasons cited in orders to amend
f = open('otareasons.py', 'r')
temp = f.read()
f.close()
code = compile(temp, 'otareasons.py', 'exec')
exec(code)

# Run amended and certified cases report
f = open('otasandoccs.py', 'r')
temp = f.read()
f.close()
code = compile(temp, 'otasandoccs.py', 'exec')
exec(code)

# Run closed cases report
f = open('closedcasepdfs.py', 'r')
temp = f.read()
f.close()
code = compile(temp, 'closedcasepdfs.py', 'exec')
exec(code)

# Run active cases report
f = open('activecases.py', 'r')
temp = f.read()
f.close()
code = compile(temp, 'activecases.py', 'exec')
exec(code)

# Create big html table
f = open('htmltable.py', 'r')
temp = f.read()
f.close()
code = compile(temp, 'htmltable.py', 'exec')
exec(code)
