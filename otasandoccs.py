import requests, bs4, re, csv, math
from datetime import datetime, date
from statistics import mean

# Import the big pile of case data
casedata = open('casedata.csv', 'r')
reader = csv.DictReader(casedata)
casedatadict = {}
for dictionary in reader:
    casedictname = dictionary["Docket No."]
    casedatadict[casedictname] = dictionary
casedata.close()

# Import the data about problems cited in orders to amend
otareasonscsv = open('otareasons.csv', 'r')
reader = csv.DictReader(otareasonscsv)
otareasonsdict = {}
for dictionary in reader:
    documentnum = dictionary["Document No."]
    otareasonsdict[documentnum] = dictionary
otareasonscsv.close()

def getdocketnum(row):
    cells = []
    cells += row.find_all('td')
    docketnum = str(cells[0].get_text(strip=True))
    return docketnum

def getdocketnumclosedlist(row):
    cells = []
    cells += row.find_all('td')
    docketnum = str(cells[1].get_text(strip=True))
    return docketnum

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

# Get the case numbers for the (first 100) cases with orders to amend
print("Getting orders to amend")
amendedcasesall = []
amendordersall = []
res = requests.get('https://dockets.ccb.gov/search/documents?search=&docTypeGroup=type%3A52&max=100')
res.raise_for_status()
amendlistsoup = bs4.BeautifulSoup(res.text, 'lxml')
amendtablerows = amendlistsoup.tbody.find_all('tr')
for row in amendtablerows:
    amendedcasesall.append(getdocketnum(row))
    amendordersall.append([getdocketnum(row), getdatefiled(row)])
# Get the next hundred
res = requests.get('https://dockets.ccb.gov/search/documents?search=&docTypeGroup=type%3A52&offset=100&max=100')
res.raise_for_status()
amendlistsoup = bs4.BeautifulSoup(res.text, 'lxml')
amendtablerows = amendlistsoup.tbody.find_all('tr')
for row in amendtablerows:
    amendedcasesall.append(getdocketnum(row))
    amendordersall.append([getdocketnum(row), getdatefiled(row)])

# output list of cases w orders to amend to a text file for closedcases.py
amendfile = open('amendfile.txt', 'w')
for item in amendedcasesall:
    amendfile.writelines(item + '\n')
amendfile.close()

# create deduped list of cases with orders to amend
setamendedcases = set(amendedcasesall)
amendedcases = list(setamendedcases)
amendedcases.sort()

# create list of earliest cert order for each case
amendordersall.sort()
amendorderschecking = []
amendordersdeduped = {}
for order in amendordersall:
    if order[0] not in amendorderschecking:
        amendordersdeduped[order[0]] = order[1][:10]
        amendorderschecking.append(order[0])

# Get the case numbers for the (first 100) cases with certified claims, orders of each type
print("Getting orders certifying claims")
certcasesall = []
certordersall = []
res = requests.get('https://dockets.ccb.gov/search/documents?docTypeGroup=type%3A54&max=100')
res.raise_for_status()
certlistsoup = bs4.BeautifulSoup(res.text, 'lxml')
certlistrows = certlistsoup.tbody.find_all('tr')
print("Number of orders at first OCC URL")
print(str(len(certlistrows)))
for row in certlistrows:
    certcasesall.append(getdocketnum(row))
    certordersall.append([getdocketnum(row), getdatefiled(row)])
res = requests.get('https://dockets.ccb.gov/search/documents?docTypeGroup=type%3A113&max=100')
res.raise_for_status()
certlistsoup = bs4.BeautifulSoup(res.text, 'lxml')
certlistrows = certlistsoup.tbody.find_all('tr')
print("Number of orders at second OCC URL")
print(str(len(certlistrows)))
for row in certlistrows:
    certcasesall.append(getdocketnum(row))
    certordersall.append([getdocketnum(row), getdatefiled(row)])
res = requests.get('https://dockets.ccb.gov/search/documents?docTypeGroup=type%3A113&offset=100&max=100')
res.raise_for_status()
certlistsoup = bs4.BeautifulSoup(res.text, 'lxml')
certlistrows = certlistsoup.tbody.find_all('tr')
print("Number of orders at third OCC URL")
print(str(len(certlistrows)))
for row in certlistrows:
    certcasesall.append(getdocketnum(row))
    certordersall.append([getdocketnum(row), getdatefiled(row)])

# output list of cases w orders to cert to a text file for closedcases.py
certfile = open('certfile.txt', 'w')
for item in certcasesall:
    certfile.writelines(item + '\n')
certfile.close()

# create deduped list of cases with certified claims
setcertcases = set(certcasesall)
certifiedcases = list(setcertcases)
certifiedcases.sort()

# create list of earliest cert order for each case
certordersall.sort()
certorderschecking = []
certordersdeduped = {}
for order in certordersall:
    if order[0] not in certorderschecking:
        certordersdeduped[order[0]] = order[1][:10]
        certorderschecking.append(order[0])

# make more lists
amendednotcert = [case for case in amendedcases if case not in certifiedcases]
certnotamended = [case for case in certifiedcases if case not in amendedcases]
amendedandcert = [case for case in amendedcases if case in certifiedcases]
allcases = amendednotcert + certnotamended + amendedandcert
allcases.sort()
latestcasewithorder = int(allcases[-1][7:])

# Get dates of amended claims for cases with both orders to amend and certified claims
#Commented out because no longer reporting on time between amended claim and order certifying claim
# print("Getting some amended claims")
# amendedclaimslatercert = {}
# for case in amendedandcert:
#     amendedclaimslatercert[case] = getamendedclaimdate(casedatadict[case]["Docket URL"])

# Get the case numbers for the (first 100) cases from the closed case list
print("Getting closed cases")
allclosedcases = []
res = requests.get('https://dockets.ccb.gov/search/closed?max=100')
res.raise_for_status()
closedlistsoup = bs4.BeautifulSoup(res.text, 'lxml')
closedtablerows = closedlistsoup.tbody.find_all('tr')
for row in closedtablerows:
    allclosedcases.append(getdocketnumclosedlist(row))
# Get the next 100
res = requests.get('https://dockets.ccb.gov/search/closed?&offset=100&max=100')
res.raise_for_status()
closedlistsoup = bs4.BeautifulSoup(res.text, 'lxml')
closedtablerows = closedlistsoup.tbody.find_all('tr')
for row in closedtablerows:
    allclosedcases.append(getdocketnumclosedlist(row))
allclosedcases.sort()
# Temporary fix for 141 not being in the closed case list on the CCB site. Can delete when this number matches html
# print("number of closed cases from allclosedcases list: " + str(len(allclosedcases)))
# if '22-CCB-0141' not in allclosedcases:
#     allclosedcases.append('22-CCB-0141')
allclosedcases.sort()

# Get a list of cases that have OTAs or OCCs that are now closed
statusclosed = []
for case in allclosedcases:
    if case in allcases:
        statusclosed.append(case)

# Get some new lists ready
statuscert = []
statuswaiting = []
represented = []
unrepresented = []
timestoota = []
timestoocc = []
julota = 0
julocc = 0
augota = 0
augocc = 0
sepota = 0
sepocc = 0
octota = 0
octocc = 0
novota = 0
novocc = 0

# Build the list of dictionaries, and populate the lists
otasandoccsdicts = []
timestoaction = {}
for case in allcases:
    newcase = {}
    newcase["Docket No."] = casedatadict[case]["Docket No."]
    newcase["Caption"] = casedatadict[case]["Caption"]
    actiondates = []
    if casedatadict[case]["Oldest doc"] != "Claim":
        newcase["Claim date"] = "Unknown"
    else:
        claimdate = casedatadict[case]["Oldest doc date"][:10]
        newcase["Claim date"] = claimdate
    if case in amendedcases:
        amendorderdate = amendordersdeduped[case]
        newcase["1st OTA"] = amendorderdate
        actiondates.append([amendorderdate, "Amend"])
    else:
        newcase["1st OTA"] = "None"
    if case in certifiedcases:
        certorderdate = certordersdeduped[case]
        newcase["1st OCC"] = certorderdate
        actiondates.append([certorderdate, "Certify"])
    else:
        newcase["1st OCC"] = "None"
    actiondates.sort()
    firstorderdate = actiondates[0][0]
    firstordertype = actiondates[0][1]
    if newcase["Claim date"] == "Unknown":
        newcase["Time to 1st action"] = "Unknown"
    else:
        d1 = datetime.strptime(claimdate, "%m/%d/%Y")
        d2 = datetime.strptime(firstorderdate, "%m/%d/%Y")
        delta = d2-d1
        if firstordertype == "Amend":
            timestoota.append(delta.days)
        else:
            timestoocc.append(delta.days)
        newcase["Time to 1st action"] = delta.days
        timestoaction[case] = delta.days
    if firstorderdate[:2] == "07":
        if firstordertype == "Amend":
            julota += 1
        else:
            julocc += 1
    elif firstorderdate[:2] == "08":
        if firstordertype == "Amend":
            augota += 1
        else:
            augocc += 1
    elif firstorderdate[:2] == "09":
        if firstordertype == "Amend":
            sepota += 1
        else:
            sepocc += 1
    elif firstorderdate[:2] == "10":
        if firstordertype == "Amend":
            octota += 1
        else:
            octocc += 1
    elif firstorderdate[:2] == "11":
        if firstordertype == "Amend":
            novota += 1
        else:
            novocc += 1
    if case in statusclosed:
        newcase["Current status"] = "Closed"
    elif case in certifiedcases:
        newcase["Current status"] = "Certified"
        statuscert.append(case)
    else:
        newcase["Current status"] = "Awaiting amendment/certification"
        statuswaiting.append(case)
    newcase["Latest doc"] = casedatadict[case]["Latest doc"]
    newcase["Claimant law firm"] = casedatadict[case]["Claimant law firm"]
    if newcase["Claimant law firm"] == "none" or newcase["Claimant law firm"] == "Not available":
        unrepresented.append(case)
    else:
        represented.append(case)
    otasandoccsdicts.append(newcase)

# Do some math about times to 1st action
latestcasewithorder = int(allcases[-1][7:])
divfifty = latestcasewithorder / 50
numberofbatches = math.ceil(divfifty)
averagesbybatch = []
batchsizes = []
batchnum = 0
while batchnum < numberofbatches:
    batchnum += 1
    listend = batchnum * 50
    listname = 'batch' + str(batchnum)
    listname = []
    for case in allcases:
        docketnum = casedatadict[case]["Docket No."]
        docketnumint = int(docketnum[7:])
        if docketnumint > (listend - 49) and docketnumint <= listend:
            if casedatadict[case]["Oldest doc"] == "Claim":
                listname.append(timestoaction[case])
    batchavg = mean(listname)
    averagesbybatch.append(batchavg)
    sizeofbatch = len(listname)
    batchsizes.append(sizeofbatch)

# Get lists of cases with foreign claimants and respondents
foreignclaimants = []
for case in casedatadict:
    notnecessarilyforeign = ['USA', 'Not available']
    if casedatadict[case]["Claimant country"] not in notnecessarilyforeign:
        foreignclaimants.append(casedatadict[case]["Docket No."])
foreignrespondentswithdupes = []
for order in otareasonsdict:
    if otareasonsdict[order]["Foreign Respondent"] == '1':
        foreignrespondentswithdupes.append(otareasonsdict[order]["Docket No."])
foreignset = set(foreignrespondentswithdupes)
foreignrespondents = list(foreignset)
foreignboth = [x for x in foreignclaimants if x in foreignrespondents]
foreignboth.sort()

# Output dictionaries as csv
with open('otasandoccs.csv', 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames = otasandoccsdicts[0].keys())
    writer.writeheader()
    writer.writerows(otasandoccsdicts)
csvfile.close()

# Begin writing html report
htmlreport = open("orderstoamendorcertify.html", 'w')
htmlreport.write('<!DOCTYPE html>' + '\n' + '<html lang="en">' + '\n' +
    '<head><title>CCB data - orders to amend and orders certifying claims</title>' + '\n' +
    '<style>' + '\n' + 'table, th, td {' + '\n' + '    border: 1px solid #ddd;' + '\n' +
    '    border-collapse: collapse;' + '\n' + '    }' +
    '\n' + 'th, td {' + '\n' + '    padding: 6px;' + '\n' + '    }' +
    '\n' + 'tr:nth-child(odd) {' + '\n' + '    background-color: #f9f9f9;' + '\n' + '    }' +
    '\n' +
    '</style>' + '\n' + '</head>' + '\n' + '<body>' + '\n')

htmlreport.write('<p>Run date: ' + str(date.today()) + '</p>')
htmlreport.write('<p>Number of claims filed: ' + str(len(casedatadict)) + '</p>')

# summary totals
htmlreport.write('<table>' +
    '<tr><td>Orders certifying claims (OCCs)</td><td>' + str(len(certordersall)) + '</td></tr>' +
    '<tr><td>Cases with OCCs</td><td>' + str(len(certifiedcases)) + '</td></tr>' +
    '<tr><td>Orders to amend (OTAs)</td><td>' + str(len(amendordersall)) + '</td></tr>' +
    '<tr><td>Cases with OTAS</td><td>' + str(len(amendedcases)) + '</td></tr>' +
    '<tr><td>Cases with both</td><td>' + str(len(amendedandcert)) + '</td></tr>' +
    '</table>')

numstatuscert = len(statuscert)
numstatuswaiting = len(statuswaiting)
numstatusclosed = len(statusclosed)
numall = len(allcases)
pctcert = (numstatuscert/numall) * 100
pctwaiting = (numstatuswaiting/numall) * 100
pctclosed = (numstatusclosed/numall) * 100
htmlreport.write('<p>Current status of the subset of cases with an OTA or OCC (' + str(numall) + ') :</p>' +
    '<table><td>Certified, still open</td><td>' + str(numstatuscert) + '</td><td>' + str(pctcert)[:2] + '%</td></tr>' +
    '<td>Awaiting claimant amendment or CCB certification</td><td>' + str(numstatuswaiting) + '</td><td>' + str(pctwaiting)[:2] + '%</td></tr>' +
    '<td>Closed</td><td>' + str(numstatusclosed) + '</td><td>' + str(pctclosed)[:2] + '%</td></tr>' +
    '</table>')

# How many unrepresented folks are getting claims certified? Represented folks?
numrepresented = len(represented)
numunrepresented = len(unrepresented)
repandcert = 0
unrepandcert = 0
for case in certifiedcases:
    if case in represented:
        repandcert += 1
    else:
        unrepandcert += 1
pctofrepcertified = (repandcert/numrepresented) * 100
pctofunrepcertified = (unrepandcert/numunrepresented) * 100
htmlreport.write('<p>Cases with represented claimants: ' + str(numrepresented) +
    '&emsp; | &emsp; with certified claims: ' + str(repandcert) + ' (' + str(pctofrepcertified)[:2] + '%)<br/>' +
    'Cases with unrepresented claimants: ' + str(numunrepresented) +
    '&emsp; | &emsp; with certified claims: ' + str(unrepandcert) + ' (' + str(pctofunrepcertified)[:2] + '%)' +
    '</p>')

avgotatime = int(mean(timestoota))
avgocctime = int(mean(timestoocc))
timestoall = timestoota + timestoocc
avgtimesall = int(mean(timestoall))
htmlreport.write('<p>Average number of days from claim to first OTA or OCC: ' + str(avgtimesall) + '<br/>' +
    'Just orders to amend: ' + str(avgotatime) + '<br/>' +
    'Just orders certifying claim: ' + str(avgocctime) + '</p>' +
    '<p>By order of claim:</p>' + '<ul>' +
    '<li>Claims 1-50 (based on ' + str(batchsizes[0]) + ' of 50 cases*): ' + str(int(averagesbybatch[0])) + ' days</li>' +
    '<li>Claims 51-100 (' + str(batchsizes[1]) + ' of 50 cases): ' + str(int(averagesbybatch[1])) + ' days</li>' +
    '<li>Claims 101-150 (' + str(batchsizes[2]) + ' of 50 cases): ' + str(int(averagesbybatch[2])) + ' days</li>' +
    '<li>Claims 151-200 (' + str(batchsizes[3]) + ' of 50 cases): ' + str(int(averagesbybatch[3])) + ' days</li>' +
    '<li>Claims 201-250 (' + str(batchsizes[4]) + ' of 50 cases): ' + str(int(averagesbybatch[4])) + ' days</li>' +
    "</ul><p>*For cases where a time could be calculated. A time can't be calculated if no OTA or OCC has been filed yet, " +
    "or if an OTA or OCC was filed but the claim wasn't made public. Some cases are closed before an OTA or OCC is filed, e.g. at the " +
    "request of the claimant, for failure to provide respondent address, etc.</p>")

# Closed cases
htmlreport.write('<p>Number of <a href="/closedcases.html">closed cases</a> ' +
    '(so far, all have been dismissed without prejudice): ' +
    str(len(allclosedcases)) + '</p>')

htmlreport.write('<p>Number of cases with a foreign claimant: ' + str(len(foreignclaimants)) +
    '<br/>Number of cases with a foreign respondent: ' + str(len(foreignrespondents)) +
    '<br/>Number of cases with both: ' + str(len(foreignboth)) + '&emsp;' + str(foreignboth) +
    '<br/>Info on claimaint country is from the weekly casedata CSVs, foreign respondent info is from the ' +
    'otareasons CSVs. CSVs are available in <a href="https://drive.google.com/drive/folders/1lPheWjD9ZIOLd_ZVKUu8RcoaAt9C05iE">Google Drive</a>.</p>')

htmlreport.write('<table><tr><th>Docket No.</th><th>Caption</th><th>Claim date</th>' +
    '<th>1st OTA</th><th>1st OCC</th><th>Days to 1st action</th><th>Current status</th>' +
    '<th>Last doc filed</th><th>Claimant law firm</th>'
    '</tr>')
for case in otasandoccsdicts:
    color = "#ffffba"
    status = "Awaiting amendment/certification"
    if case["Current status"] == "Closed":
        status = '<a href="/closedcases.html">Closed</a>'
        color = "#ffdfba"
    elif case["Current status"] == "Certified":
        color = "#baffc9"
        status = "Certified"
    docketnum = case["Docket No."]
    htmlreport.write('<tr>' +
    '<td>' + '<a href="' + casedatadict[docketnum]["Docket URL"] + '">' + docketnum + '</a></td>' +
    '<td>' + case["Caption"] + '</td>' +
    '<td>' + case["Claim date"] + '</td>' +
    '<td>' + case["1st OTA"] + '</td>' +
    '<td>' + case["1st OCC"] + '</td>' +
    '<td>' + str(case["Time to 1st action"]) + '</td>' +
    '<td style = "background-color: ' + color + '">' + status + '</td>' +
    '<td>' + case["Latest doc"] + '</td>' +
    '<td>' + case["Claimant law firm"] + '</td>' +
    '</tr>')
htmlreport.write('</table>')

alljulorders = julota + julocc
allaugorders = augota + augocc
allseporders = sepota + sepocc
alloctorders = octota + octocc
allnovorders = novota + novocc
htmlreport.write('<p>Types of first action by month</p>')
htmlreport.write('<table><tr><th>Month</th><th>OTAs</th><th>OCCs</th></tr>' +
    '<tr><td>July</td><td>' + str(julota) + ' (' + str((julota/alljulorders) * 100)[:2] + '%)</td><td>' +
    str(julocc) + ' (' + str((julocc/alljulorders) * 100)[:2] + '%)</td></tr>' +
    '<tr><td>August</td><td>' + str(augota) + ' (' + str((augota/allaugorders) * 100)[:2] + '%)</td><td>' +
    str(augocc) + ' (' + str((augocc/allaugorders) * 100)[:2] + '%)</td></tr>' +
    '<tr><td>September</td><td>' + str(sepota) + ' (' + str((sepota/allseporders) * 100)[:2] + '%)</td><td>' +
    str(sepocc) + ' (' + str((sepocc/allseporders) * 100)[:2] + '%)</td></tr>' +
    '<tr><td>October</td><td>' + str(octota) + ' (' + str((octota/alloctorders) * 100)[:2] + '%)</td><td>' +
    str(octocc) + ' (' + str((octocc/alloctorders) * 100)[:2] + '%)</td></tr>' +
    '<tr><td>November</td><td>' + str(novota) + ' (' + str((novota/allnovorders) * 100)[:2] + '%)</td><td>' +
    str(novocc) + ' (' + str((novocc/allnovorders) * 100)[:2] + '%)</td></tr>' +
    '</table>')

htmlreport.write('\n' + '</body>' + '\n' + '</html>')
htmlreport.close()
