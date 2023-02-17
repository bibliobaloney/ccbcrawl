import csv, requests, bs4, PyPDF2
from datetime import date

def getdocketnum(row):
    cells = []
    cells += row.find_all('td')
    docketnum = str(cells[1].get_text(strip=True))
    return docketnum

def getnumamendclaims(docketurl):
    res3 = requests.get(docketurl + '?max=100')
    res3.raise_for_status()
    casedocketsoup = bs4.BeautifulSoup(res3.text, 'lxml')
    docketrows = casedocketsoup.find_all('tr')
    currentrow = 0
    numberofacs = 0
    while currentrow < len(docketrows):
        tds = []
        cells = docketrows[currentrow].find_all('td')
        for cell in cells:
            tds.append(cell.get_text(strip=True))
        if len(tds) > 2 and tds[2] == "Amended Claim":
            numberofacs += 1
        currentrow += 1
    return numberofacs

def getoptouts(case):
    partiesurl = 'https://dockets.ccb.gov/case/participants/' + case
    resparties = requests.get(partiesurl)
    resparties.raise_for_status()
    partiessoup = bs4.BeautifulSoup(resparties.text, 'lxml')
    partiestd = partiessoup.find_all(attrs={'headers' : 'colHeaderOptOutParty rowHeaderOPT_OUT'})
    return len(partiestd)

def getdismissalpdfurl(docketurl):
    res2 = requests.get(docketurl + '?max=100')
    res2.raise_for_status()
    casedocketsoup = bs4.BeautifulSoup(res2.text, 'lxml')
    docketrows = casedocketsoup.find_all('tr')
    dismissalrow = 'No dismissal order row found'
    currentrow = 0
    while dismissalrow == 'No dismissal order row found' and currentrow < len(docketrows):
        tds = []
        cells = docketrows[currentrow].find_all('td')
        for cell in cells:
            tds.append(cell.get_text(strip=True))
        if len(tds) > 2 and (tds[2] == "Order Dismissing Claim"):
            dismissalrow = docketrows[currentrow]
        elif len(tds) > 2 and (tds[1] == "DownloadOrder Closing Case"):
            dismissalrow = docketrows[currentrow]
        else:
            currentrow += 1
    if dismissalrow == 'No dismissal order row found':
        return 'No dismissal order found'
    dismissalcell = dismissalrow.find_all('td')[1]
    dismissallink = dismissalcell.a
    dismissalpdf = dismissallink.get('href')
    pdfurl = 'https://dockets.ccb.gov' + dismissalpdf
    return pdfurl

def getpdftext(filename):
    pdfFileObj = open(filename, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    pageObj = pdfReader.getPage(0)
    ordertext = pageObj.extractText()
    return ordertext

# import data for all cases, as created by ccbcrawl2.py
print("Importing claims")
casedata = open('casedata.csv', 'r')
reader = csv.DictReader(casedata)
casedatadict = {}
for dictionary in reader:
    casedictname = dictionary["Docket No."]
    casedatadict[casedictname] = dictionary
casedata.close()

# import data about closed cases from last week
print("Importing closed cases data")
closedcasescsv = open('closedcases.csv', 'r')
reader = csv.DictReader(closedcasescsv)
closedcasesdict = {}
for dictionary in reader:
    casedictname = dictionary["Docket No."]
    closedcasesdict[casedictname] = dictionary
closedcasescsv.close()

# Import the data from the reasons/orders to amend report
print("Importing OTA info from CSV")
otareasonscsv = open('otareasons.csv', 'r')
reader = csv.DictReader(otareasonscsv)
otasdict = {}
for dictionary in reader:
    documentnum = dictionary["Document No."]
    otasdict[documentnum] = dictionary
otareasonscsv.close()

# get list of last week's closed cases
caseswehave = []
for case in closedcasesdict:
    caseswehave.append(case)

# import cases with orders to amend or certify, as created by amendorcertify.py
amends = []
amendfile = open('amendfile.txt', 'r')
for line in amendfile.readlines():
    amends.append(line[:11])
amendfile.close()
certs = []
certfile = open('certfile.txt', 'r')
for line in certfile.readlines():
    certs.append(line[:11])
certfile.close()

# Get the case numbers for the (first 100) cases from the closed case list
print("Getting closed cases")
allclosedcases = []
res = requests.get('https://dockets.ccb.gov/search/closed?max=100')
res.raise_for_status()
closedlistsoup = bs4.BeautifulSoup(res.text, 'lxml')
closedtablerows = closedlistsoup.tbody.find_all('tr')
for row in closedtablerows:
    allclosedcases.append(getdocketnum(row))
# Get the next 100
res = requests.get('https://dockets.ccb.gov/search/closed?&offset=100&max=100')
res.raise_for_status()
closedlistsoup = bs4.BeautifulSoup(res.text, 'lxml')
closedtablerows = closedlistsoup.tbody.find_all('tr')
for row in closedtablerows:
    allclosedcases.append(getdocketnum(row))
allclosedcases.sort()

newclosedcases = []
for case in allclosedcases:
    if case not in caseswehave:
        newclosedcases.append(case)
print("New closed cases:")
print(newclosedcases)

# start collecting info about new closed cases in the closed cases dictionary
for case in newclosedcases:
    docketurl = 'https://dockets.ccb.gov/case/detail/' + case
    lawfirm = casedatadict[case]["Claimant law firm"]
    closedcasesdict[case] = {"Docket No." : case, "Docket URL" : docketurl, "Claimant law firm" : lawfirm}

# add info to the dictionary about orders to amend and orders certifying claims; infer reasons where possible
print("Counting amended claims and opt outs")
for case in newclosedcases:
    print(case)
    closedcasesdict[case]["Amend orders"] = amends.count(case)
    closedcasesdict[case]["Certifying orders"] = certs.count(case)
    docketurl = closedcasesdict[case]["Docket URL"]
    if amends.count(case) > 0:
        closedcasesdict[case]["Amended claims"] = getnumamendclaims(docketurl)
    else:
        closedcasesdict[case]["Amended claims"] = "Didn't count"
    if case in certs:
        closedcasesdict[case]["Opt outs"] = getoptouts(case)
    else:
        closedcasesdict[case]["Opt outs"] = "-"
    if closedcasesdict[case]["Certifying orders"] > 0 and closedcasesdict[case]["Opt outs"] > 0:
        closedcasesdict[case]["Inferred reason"] = "Respondent(s) opted out"
    elif closedcasesdict[case]["Amended claims"] == 2 and closedcasesdict[case]["Amend orders"] == 2:
        closedcasesdict[case]["Inferred reason"] = "3 tries and still noncompliant"
    elif closedcasesdict[case]["Amend orders"] > 0 and closedcasesdict[case]["Certifying orders"] == 0:
        closedcasesdict[case]["Inferred reason"] = "Failure to amend"
    else:
        closedcasesdict[case]["Inferred reason"] = "Unknown"

# Get PDF URLs for each closed case
print("Getting PDF URLs, designating (future) local filenames")
for case in newclosedcases:
    print(case)
    dismissalpdfurl = getdismissalpdfurl('https://dockets.ccb.gov/case/detail/' + case)
    closedcasesdict[case]["Dismissal PDF URL"] = dismissalpdfurl
    closedcasesdict[case]["PDF filename"] = 'pdfs/' + case + 'dismissalorder.pdf'

# Save PDFs locally
print("Saving PDFs locally")
for case in newclosedcases:
    print(case)
    dismissalpdfurl = closedcasesdict[case]["Dismissal PDF URL"]
    if dismissalpdfurl != "No dismissal order found":
        res = requests.get(dismissalpdfurl)
        res.raise_for_status()
        pdffile = open('pdfs/' + case + 'dismissalorder.pdf', 'wb')
        for chunk in res.iter_content(100000):
            pdffile.write(chunk)
        pdffile.close()
    else:
        print(dismissalpdfurl + " for case " + case)

# Get text from first page of PDF
print("Extracting text from dismissal order PDFs")
for case in newclosedcases:
    filename = closedcasesdict[case]["PDF filename"]
    pdftext = ''
    if closedcasesdict[case]["Dismissal PDF URL"] != "No dismissal order found":
        pdftext = getpdftext(filename)
    print(pdftext)
    if 'opt-out' in pdftext:
        pdfreason = "Respondent(s) opted out"
    elif 'second amended claim' in pdftext:
        pdfreason = "3 tries and still noncompliant"
    elif "did not receive  the respondent's address" in pdftext or "did not receive the respondent's address" in pdftext:
        pdfreason = "Failure to provide respondent address"
    elif 'payment for the claim failed' in pdftext:
        pdfreason = "Payment for the claim failed"
    elif 'request from the claimant' or 'request to dismiss from' in pdftext:
        pdfreason = "Request from claimant"
    elif 'did not file a proof of service or waiver of service' in pdftext:
        pdfreason = "Proof of service not filed"
    elif 'No amended claim was filed in the time allowed' in pdftext:
        pdfreason = "Failure to amend"
    elif 'applied to register the copyright in the work and had filed a new' in pdftext:
        pdfreason = "Work wasn't registered before; claimant has filed new claim"
    else:
        pdfreason = "Unknown/cannot extract"
    closedcasesdict[case]["PDF reason"] = pdfreason

# Assign a reason for tallying at the end of the report
for case in newclosedcases:
    if closedcasesdict[case]["PDF reason"] != "Unknown/cannot extract":
        closedcasesdict[case]["Tallied reason"] = closedcasesdict[case]["PDF reason"]
    else:
        closedcasesdict[case]["Tallied reason"] = closedcasesdict[case]["Inferred reason"]

closedcasesdatalist = [value for value in closedcasesdict.values()]
closedcasesdatalist.sort(key=lambda x: x['Docket No.'])

htmlreport = open("closedcases.html", 'w')
htmlreport.write('<!DOCTYPE html>' + '\n' + '<html lang="en">' + '\n' +
    '<head><title>CCB data - closed cases</title>' + '\n' +
    '<style>' + '\n' + 'table, th, td {' + '\n' + '    border: 1px solid #ddd;' + '\n' +
    '    border-collapse: collapse;' + '\n' + '    }' +
    '\n' + 'th, td {' + '\n' + '    padding: 6px;' + '\n' + '    }' +
    '\n' + 'tr:nth-child(odd) {' + '\n' + '    background-color: #f9f9f9;' + '\n' + '    }' +
    '\n' +
    '</style>' + '\n' + '</head>' + '\n' + '<body>' + '\n')

htmlreport.write('<p>Run date: ' + str(date.today()) + '</p>')

# summary total
htmlreport.write('<p>Number of <a href="https://dockets.ccb.gov/search/closed?max=100">closed cases</a>: ' +
    str(len(closedcasesdatalist)) + '</p>')

# Check to make sure numnbers match
print("number of closed cases from initial allclosedcases list: " + str(len(allclosedcases)))
fromdictlist = []
for case in closedcasesdict:
    fromdictlist.append(closedcasesdict[case]["Docket No."])
print("number of closed cases from closedcasesdict: " + str(len(closedcasesdict)))
print("Check to see if 107 is back in the closed case docket on CCB site; if so comment out line 249 etc")
if '22-CCB-0107' not in allclosedcases:
    allclosedcases.append('22-CCB-0107')
    allclosedcases.sort()

# compare with active cases
res = requests.get('https://dockets.ccb.gov/search/documents?search=&docTypeGroup=type%3A16&max=100')
res.raise_for_status()
activecasesoup = bs4.BeautifulSoup(res.text, 'lxml')
activecaserows = activecasesoup.find_all('tr')
activecases = len(activecaserows) - 1
htmlreport.write('<p>Number of <a href="https://dockets.ccb.gov/search/documents?search=&docTypeGroup=type%3A16&max=100"> cases ' +
    'where a scheduling order has been filed</a>: ' +
    str(activecases) + '</p>')

# table of reasons for dismissal
allreasons = []
for case in allclosedcases:
    allreasons.append(closedcasesdict[case]["Tallied reason"])

htmlreport.write('<p>Total number of claims dismissed for each reason</p>')
setofreasons = set(allreasons)
dedupedreasons = list(setofreasons)
dedupedreasons.sort(reverse = True)
htmlreport.write('<table>' + '\n')
for reason in dedupedreasons:
    htmlreport.write('<tr>' +
    '<td>' + reason + '</td>' +
    '<td>' + str(allreasons.count(reason)) + '</td>'
    '</tr> \n')
htmlreport.write('</table> \n')

# table of reasons in orders to amend
foreignrespondent = 0
registration = 0
impermissibleclaim = 0
relief = 0
access = 0
similarity = 0
ownership = 0
clarity = 0
for case in otasdict:
    if otasdict[case]["Foreign Respondent"] == '1':
        foreignrespondent += 1
    if otasdict[case]["Registration"] == '1':
        registration += 1
    if otasdict[case]["Impermissible Claim"] == '1':
        impermissibleclaim += 1
    if otasdict[case]["Relief Sought"] == '1':
        relief += 1
    if otasdict[case]["Access"] == '1':
        access += 1
    if otasdict[case]["Substantial Similarity"] == '1':
        similarity += 1
    if otasdict[case]["Ownership"] =='1':
        ownership += 1
    if otasdict[case]["Clarity"] == '1':
        clarity += 1
htmlreport.write('<p>Some common problems with claims from orders to amend (Note: more info is available in "otareasons" CSV files in ' +
    '<a href="">Google Drive</a>.)</p>')
htmlreport.write('<table>' + '\n' +
    '<tr><th>Problem</th><th>Number of orders to amend citing the problem</th></tr>' +
    '<tr><td>Claim filed against a foreign respondent</td><td>' + str(foreignrespondent) + '</td></tr>' +
    '<tr><td>Infringement claim, lack of copyright registration</td><td>' + str(registration) + '</td></tr>' +
    '<tr><td>Impermissible claim, e.g. patent or contract</td><td>' + str(impermissibleclaim) + '</td></tr>' +
    '<tr><td>Problem with type or amount of relief sought</td><td>' + str(relief) + '</td></tr>' +
    '<tr><td>Infringement claim, insufficient information about Access to allegedly infringed work</td><td>' + str(access) + '</td></tr>' +
    '<tr><td>Infringement claim, insufficient allegation of Substantial Similarity</td><td>' + str(similarity) + '</td></tr>' +
    '<tr><td>Infringement claim, insufficient allegation of Legal or Beneficial Ownership by claimant</td><td>' + str(ownership) + '</td></tr>' +
    '<tr><td>Clarity (about some element, or the claim generally)</td><td>' + str(clarity) + '</td></tr>' +
    '</table> \n')

# table of cases
htmlreport.write('<p>Cases</p>')
htmlreport.write('<table>' + '\n' +
    '<tr><th>Docket</th><th>Caption</th><th>Orders to amend</th><th>Orders certifying claim</th><th>Opt outs</th>' +
    '<th>Inferred reason</th><th>PDF reason</th><th>Tallied reason</th><th>Claimant law firm</th></tr>')
for case in allclosedcases:
    htmlreport.write('<tr>' +
    '<td>' + '<a href="' + closedcasesdict[case]["Docket URL"] + '">' + case + '</a></td>' +
    '<td>' + casedatadict[case]["Caption"] + '</a></td>' +
    '<td>' + str(closedcasesdict[case]["Amend orders"]) + '</a></td>' +
    '<td>' + str(closedcasesdict[case]["Certifying orders"]) + '</a></td>' +
    '<td>' + str(closedcasesdict[case]["Opt outs"]) + '</a></td>' +
    '<td>' + closedcasesdict[case]["Inferred reason"] + '</a></td>' +
    '<td>' + closedcasesdict[case]["PDF reason"] + '</a></td>' +
    '<td>' + closedcasesdict[case]["Tallied reason"] + '</a></td>' +
    '<td>' + closedcasesdict[case]["Claimant law firm"] + '</a></td>' +
    '</tr> \n')
htmlreport.write('</table> \n')

htmlreport.write('\n' + '</body>' + '\n' + '</html>')
htmlreport.close()

with open('closedcases.csv', 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames = closedcasesdatalist[0].keys())
    writer.writeheader()
    writer.writerows(closedcasesdatalist)
csvfile.close()
