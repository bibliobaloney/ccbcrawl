import csv, requests, bs4, PyPDF2

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
allclosedcases.sort()

newclosedcases = []
for case in allclosedcases:
    if case not in caseswehave:
        newclosedcases.append(case)

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
    res = requests.get(dismissalpdfurl)
    res.raise_for_status()
    pdffile = open('pdfs/' + case + 'dismissalorder.pdf', 'wb')
    for chunk in res.iter_content(100000):
        pdffile.write(chunk)
    pdffile.close()

# Get text from first page of PDF
print("Extracting text from dismissal order PDFs")
for case in newclosedcases:
    filename = closedcasesdict[case]["PDF filename"]
    pdftext = getpdftext(filename)
    if 'opt-out' in pdftext:
        pdfreason = "Respondent(s) opted out"
    elif 'second amended claim' in pdftext:
        pdfreason = "3 tries and still noncompliant"
    elif 'provide the respondent’s address' in pdftext:
        pdfreason = "Failure to provide respondent address"
    elif 'payment for the claim failed' in pdftext:
        pdfreason = "Payment for the claim failed"
    elif 'request from the claimant' in pdftext:
        pdfreason = "Request from claimant"
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

# summary total
htmlreport.write('<p>Number of closed cases: ' + str(len(closedcasesdatalist)) + '</p>')
htmlreport.write('<table>' + '\n' +
    '<tr><th>Docket</th><th>Caption</th><th>Orders to amend</th><th>Orders certifying claim</th><th>Opt outs</th>' +
    '<th>Inferred reason</th><th>PDF reason</th><th>Tallied reason</th><th>Claimant law firm</th></tr>')

allreasons = []
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
    allreasons.append(closedcasesdict[case]["Tallied reason"])
htmlreport.write('</table> \n')

htmlreport.write('<p>Totals</p>')

setofreasons = set(allreasons)
dedupedreasons = list(setofreasons)
htmlreport.write('<table>' + '\n')
for reason in dedupedreasons:
    htmlreport.write('<tr>' +
    '<td>' + reason + '</td>' +
    '<td>' + str(allreasons.count(reason)) + '</td>'
    '</tr> \n')
htmlreport.write('</table> \n')

htmlreport.write('\n' + '</body>' + '\n' + '</html>')
htmlreport.close()

with open('closedcases.csv', 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames = closedcasesdatalist[0].keys())
    writer.writeheader()
    writer.writerows(closedcasesdatalist)
csvfile.close()
