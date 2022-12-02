import requests, bs4, re, csv, math

# casedata = open('casedata.csv', 'r')
# reader = csv.DictReader(casedata)
# casedatadict = {}
# for dictionary in reader:
#     casedictname = dictionary["Docket No."]
#     casedatadict[casedictname] = dictionary
# casedata.close()

def getdocketnum(row):
    cells = []
    cells += row.find_all('td')
    docketnum = str(cells[0].get_text(strip=True))
    return docketnum

# def getdocketnumclosedlist(row):
#     cells = []
#     cells += row.find_all('td')
#     docketnum = str(cells[1].get_text(strip=True))
#     return docketnum

def getdatefiled(row):
    cells = []
    cells += row.find_all('td')
    datefiled = str(cells[5].get_text(strip=True))
    return datefiled

def getamendedclaimdate(docketurl):
    res = requests.get(docketurl + '?max=100')
    res.raise_for_status()
    casedocketsoup = bs4.BeautifulSoup(res.text, 'lxml')
    amendedclaimtd = casedocketsoup.find_all(text=re.compile('Amended Claim'))[2].parent
    amendedclaimtr = amendedclaimtd.parent
    fileddatetd = amendedclaimtr.find(attrs={'data-cell-heading' : 'Filed date'})
    fileddate = fileddatetd.get_text(strip=True)
    return fileddate[:10]

# Get the case numbers for the (first 100) cases with orders dismissing (3 kinds)
print("Getting orders dismissing claims")
dismissedcasesall = []
dismissalordersall = []
res = requests.get('https://dockets.ccb.gov/search/documents?search=&docTypeGroup=type%3A53&docTypeGroup=type%3A57&docTypeGroup=type%3A56&max=100')
res.raise_for_status()
dismisslistsoup = bs4.BeautifulSoup(res.text, 'lxml')
dismisstablerows = dismisslistsoup.tbody.find_all('tr')
for row in dismisstablerows:
    dismissedcasesall.append(getdocketnum(row))
    dismissalordersall.append([getdocketnum(row), getdatefiled(row)])

setdismissedcases = set(dismissedcasesall)
dismissedcases = list(setdismissedcases)
dismissedcases.sort()
print(len(dismissedcases))
