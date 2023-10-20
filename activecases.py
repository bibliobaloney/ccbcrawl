import requests, bs4, re, csv
from datetime import date

# Import the big pile of case data
casedata = open('casedata.csv', 'r')
reader = csv.DictReader(casedata)
casedatadict = {}
for dictionary in reader:
    casedictname = dictionary["Docket No."]
    casedatadict[casedictname] = dictionary
casedata.close()

# Get list of closed cases from closedcases.csv (created by closedcasepdf.py)
closedcasedata = open('closedcases.csv', 'r')
reader = csv.reader(closedcasedata)
closedcases = []
for record in reader:
    if len(record) != 0:
        closedcases.append(record[0])
closedcasedata.close()

# import cases with final determinations, as created by otasandoccs.py
finals = []
finalfile = open('finalfile.txt', 'r')
for line in finalfile.readlines():
    finals.append(line[:11])
finalfile.close()

def getdocketnum(row):
    cells = []
    cells += row.find_all('td')
    docketnum = str(cells[0].get_text(strip=True))
    return docketnum

def getdocumnenturl(row):
    documentcell = row.find_all('td')[2]
    documentatag = documentcell.a
    documentlocation = documentatag.get('href')
    documenturl = 'https://dockets.ccb.gov' + documentlocation
    return documenturl

def getdatefiled(row):
    cells = []
    cells += row.find_all('td')
    datefiled = str(cells[5].get_text(strip=True))
    return datefiled

# This returns 1) rows (minus a header) for a table of parties,
# and 2) a boolean for whether any respondents in the case have registered
def striptable(partieslisturl):
    res = requests.get(partieslisturl)
    res.raise_for_status()
    partieslistsoup = bs4.BeautifulSoup(res.text, 'lxml')
    partieslistrows = partieslistsoup.find_all('tr')
    partieslistrows.pop(0)
    strippedrows = ''
    tablesection = 'Claimaint'
    respondentregistered = False
    for row in partieslistrows:
        datacells = row.find_all('td')
        headings = row.find_all('th')
        if len(headings) == 1:
            headingtext = headings[0].get_text(strip=True)
            headerrow = '<tr><th colspan="3">' + headingtext + '</th></tr>'
            strippedrows += headerrow
            strippedrows += '\n'
            if headingtext == 'Respondent':
                tablesection = 'Respondent'
        if len(datacells) > 0:
            party = ''
            partycells = row.find_all('td', attrs={'data-cell-heading' : 'Party'})
            if len(partycells) !=0:
                partycell = partycells[0]
                party = partycell.get_text(strip=True)
            rep = ''
            repcells = row.find_all('td', attrs={'data-cell-heading' : 'Representative'})
            if len(repcells) !=0:
                repcell = repcells[0]
                rep = repcell.get_text(strip=True)
            firm = ''
            firmcells = row.find_all('td', attrs={'data-cell-heading' : 'Firm'})
            if len(firmcells) !=0:
                firmcell = firmcells[0]
                firm = firmcell.get_text(strip=True)
            thisrow = '<tr><td>' + party + '</td><td>' + rep + '</td><td>' + firm + '</td></tr>'
            strippedrows += thisrow
            strippedrows += '\n'
            if tablesection == 'Respondent' and firm != '':
                respondentregistered = True
    return strippedrows, respondentregistered

def textshave(celltext):
    if 'Download' in celltext:
        celltext = celltext.replace('Download', '')
    if '(Opens new window)' in celltext:
        celltext = celltext.replace('(Opens new window)', '')
    if 'Toggle tooltip (Keyboard shortcut: "Crtl+Enter" opens and "Escape" or "Delete" dismiss)' in celltext:
        celltext = celltext.replace('Toggle tooltip (Keyboard shortcut: "Crtl+Enter" opens and "Escape" or "Delete" dismiss)', '')
    return celltext

def stripdockettable(docketurl):
    defaultcheck = False
    longurl = docketurl + '?max=100'
    res = requests.get(longurl)
    res.raise_for_status()
    docketsoup = bs4.BeautifulSoup(res.text, 'lxml')
    docketrows = docketsoup.find_all('tr')
    docketrows.pop(0)
    if len(docketsoup.find_all(text=re.compile('Default'))) != 0:
        defaultcheck = True
    recentrows = docketrows[:5]
    strippedrows = ''
    for row in recentrows:
        strippedrows += '<tr>'
        for cell in row.find_all('td'):
            anylinks = cell.find_all('a')
            link = 'None'
            if len(anylinks) != 0:
                linktag = anylinks[0]
                link = str(linktag.get('href'))
            if len(anylinks) !=0 and link != 'None':
                longcelltext = cell.get_text(strip=True)
                newcelltext = textshave(longcelltext)
                newcell = '<td><a href="https://dockets.ccb.gov' + link + '">' + newcelltext + '</a></td>'
            else:
                longcelltext = cell.get_text(strip=True)
                newcelltext = textshave(longcelltext)
                newcell = '<td>' + newcelltext + '</td>'
            strippedrows += newcell
        strippedrows += '</tr>'
    return strippedrows, defaultcheck

# Get cases with scheduling orders, oldest to newest
print("Getting list of cases with scheduling orders (in activecases.py)")
res = requests.get('https://dockets.ccb.gov/search/documents?search=&docTypeGroup=type%3A16&sort=submittedDate&order=asc&max=100')
res.raise_for_status()
schedulingordercasesoup = bs4.BeautifulSoup(res.text, 'lxml')
schedulingordercaserows = schedulingordercasesoup.find_all('tr')
caseswithschedulingorders = []
# for some reason this one is grabbing the header rows and the others didn't, so pop the header
schedulingordercaserows.pop(0)
print("Scheduling orders found: " + str(len(schedulingordercaserows)))
for row in schedulingordercaserows:
    caseswithschedulingorders.append(getdocketnum(row))
withordersset = set(caseswithschedulingorders)
caseswithschedulingorders = list(withordersset)
caseswithschedulingorders.sort()

activecases = []
subseqclosed = []
for case in caseswithschedulingorders:
    if case in closedcases:
        subseqclosed.append(case)
    else:
        if case not in finals:
            activecases.append(case)

activecasesset = set(activecases)
activecases = list(activecasesset)
activecases.sort()
print(str(len(activecases)) + " active cases")
print(activecases)

activecasesdict = {}
anyonehome = 0
defaultmentioned = 0
defaultmentionlist = []

for case in activecases:
    print(case)
    newcase = {}
    newcase["Docket No."] = case
    handle = schedulingordercasesoup.find(string=re.compile(case))
    cellcontents = handle.parent
    cell = cellcontents.parent
    ourrow = cell.parent
    schedulingorderurl = getdocumnenturl(ourrow)
    schedulingorderdate = getdatefiled(ourrow)
    newcase["Scheduling order URL"] = schedulingorderurl
    newcase["Scheduling order date"] = schedulingorderdate
    partieslisturl = "https://dockets.ccb.gov/case/participants/" + case
    newcase["Parties list URL"] = partieslisturl
    strippedrows, respondentregistered = striptable(partieslisturl)
    newcase["Parties HTML"] = strippedrows
    newcase["Any respondents registered"] = respondentregistered
    if respondentregistered:
        anyonehome += 1
    docketurl = casedatadict[case]["Docket URL"]
    checkfilings = stripdockettable(docketurl)
    filingshtml = checkfilings[0]
    newcase["Filings HTML"] = filingshtml
    defaultcheck = checkfilings[1]
    if defaultcheck:
        defaultmentioned += 1
        defaultmentionlist.append(case)
    activecasesdict[case] = newcase

activecasesreport = open("activecases.html", 'w')
activecasesreport.write('<!DOCTYPE html>' + '\n' + '<html lang="en">' + '\n' +
    '<head><title>CCB data - active cases</title>' + '\n' +
    '<style>' + '\n' + 'table, th, td {' + '\n' + '    border: 1px solid #ddd;' + '\n' +
    '    border-collapse: collapse;' + '\n' + '    }' +
    '\n' + 'td {' + '\n' +
    '\n' + '    padding: 6px;' + '\n' + '    }' +
    '\n' + 'th {' + '\n' + '    padding: 6px;' + '\n' + '    }' +
    '\n' + 'tr:nth-child(odd) {' + '\n' + '    background-color: #f9f9f9;' + '\n' + '    }' +
    '\n' + '</style>' + '\n' + '</head>' + '\n' + '<body>' +
    '\n')

activecasesreport.write('<p>Run date: ' + str(date.today()) + '</p>')
activecasesreport.write('<p>Number of cases with scheduling orders: ' + str(len(caseswithschedulingorders)) + '</p>')
activecasesreport.write('<p>Number of cases with scheduling orders showing up in the <a href="https://dockets.ccb.gov/search/closed">' +
    'closed cases list</a>: ' + str(len(subseqclosed)) + '</p>')
activecasesreport.write('<p>Number of those cases with <a href="https://dockets.ccb.gov/search/documents?search=&docTypeGroup=type%3A19&docTypeGroup=type%3A78&docTypeGroup=type%3A194&docTypeGroup=type%3A80&max=100">' +
    'Final Determinations filed</a>: ' + str(len(finals)) + '</p><ul>')
for case in finals:
    activecasesreport.write('<li><a href="https://dockets.ccb.gov/case/detail/' + case + '">' + case + '</a></li>')
activecasesreport.write('</ul>')
activecasesreport.write('<p>Number of active cases,* listed below with further details: ' + str(len(activecases)) + '</p>')
# For some reason people are showing up as self-represented even when the CCB is issuing default notices saying they haven't
# registered with the CCB. So skip this line for now.
# activecasesreport.write('<p>Number of active cases where it looks like at least one respondent has registered for eCCB: ' + str(anyonehome) + '</p>')
activecasesreport.write('<p>Cases where a recent filing mentions "Default": ' + str(defaultmentioned) + '&emsp;' + str(defaultmentionlist) + '</p>')
intropara = "*"
intropara += str(len(casedatadict))
intropara += " claims have been filed, and only "
intropara += str(len(closedcases) + len(finals))
intropara += ' cases have been closed. Technically, the rest are open. The cases listed here as "active" are those that '
intropara += "have had a scheduling order issued and have not subsequently settled or otherwise been closed. To reach this point, 1) the claim must "
intropara += "be certified by the CCB, 2) the claimant must serve the respondent and file the proof of service, 3) the opt out "
intropara += 'window must elapse without all respondents opting out (or, as in the case of <a href='
intropara += '"https://dockets.ccb.gov/case/detail/22-CCB-0045">22-CCB-0045</a>, the respondent waived their right to opt out as part'
intropara += "of being referred from a district court), and 4) the claimant must pay their second filing fee to the CCB."
activecasesreport.write('<p>' + intropara + '</p>')

for case in activecases:
    registered = 'no'
    if activecasesdict[case]["Any respondents registered"]:
        registered = 'yes'
    activecasesreport.write('<h2>' + case + '</h2>' + '\n')
    activecasesreport.write('<p>Date of <a href="' + casedatadict[case]["Claim URL"] + '">earliest public filing</a> (usually the claim): ' +
    casedatadict[case]["Oldest doc date"] + '<br /> '+
    'Type(s) of claim: ' + casedatadict[case]["Claim types"] + '<br />' +
    'Type of work (for first or only listed work): ' + casedatadict[case]["Work type"] + '<br />' +
    'Date of <a href="' + activecasesdict[case]["Scheduling order URL"] + '">(initial) scheduling order</a>: ' +
    activecasesdict[case]["Scheduling order date"] + '<br /></p>' +
    '<table>' + '\n' + '<thead><tr><th>Party</th><th>Representative</th><th>Firm</th></tr>' +
    activecasesdict[case]["Parties HTML"] + '</table>')
# Remove when you figure out how the "self-represented" note is popping up for folks on the default track
#    '<p>Does it appear that at least one respondent has registered for eCCB?  ' + registered + '</p>')
    docketurl = casedatadict[case]["Docket URL"]
    activecasesreport.write('<p><a href="' + docketurl + '">Recent filings</a></p>')
    activecasesreport.write('<table><tr><th>Case doc. #</th><th>Title</th><th>Document type</th><th>Party</th><th>Filed date</th></tr>')
    activecasesreport.write(activecasesdict[case]["Filings HTML"])
    activecasesreport.write('</table>')

activecasesreport.write('</body>' + '\n' + '</html>')
activecasesreport.close()
