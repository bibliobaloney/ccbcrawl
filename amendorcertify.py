import requests, bs4, re, csv
from datetime import datetime
from statistics import mean

casedata = open('casedata.csv', 'r')

reader = csv.DictReader(casedata)
casedatadict = {}
for dictionary in reader:
    casedictname = dictionary["Docket No."]
    casedatadict[casedictname] = dictionary
casedata.close()

def getdocketnum(row):
    cells = []
    cells += row.find_all('td')
    docketnum = str(cells[0].get_text(strip=True))
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

# Get the case numbers for the (first 100) cases with certified claims
print("Getting orders certifying claims")
certcasesall = []
certordersall = []
res = requests.get('https://dockets.ccb.gov/search/documents?docTypeGroup=type%3A54&max=100')
res.raise_for_status()
certlistsoup = bs4.BeautifulSoup(res.text, 'lxml')
certlistrows = certlistsoup.tbody.find_all('tr')
for row in certlistrows:
    certcasesall.append(getdocketnum(row))
    certordersall.append([getdocketnum(row), getdatefiled(row)])
res = requests.get('https://dockets.ccb.gov/search/documents?docTypeGroup=type%3A113&max=100')
res.raise_for_status()
certlistsoup = bs4.BeautifulSoup(res.text, 'lxml')
certlistrows = certlistsoup.tbody.find_all('tr')
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

# get dates of amended claims for cases with both orders to amend and certified claims
print("Getting some amended claims")
amendedclaimslatercert = {}
for case in amendedandcert:
    amendedclaimslatercert[case] = getamendedclaimdate(casedatadict[case]["Docket URL"])

# start collecting times until CCB action
ccbfirstactiontimes = []
ccbcerttimes = []
ccbotatimes = []
# for now, count times to certify amended claims separately
ccbcertamendedtimes = []

htmlreport = open("amendments.html", 'w')
htmlreport.write('<!DOCTYPE html>' + '\n' + '<html lang="en">' + '\n' +
    '<head><title>CCB data - orders to amend and certifying claims</title>' + '\n' +
    '<style>' + '\n' + 'table, th, td {' + '\n' + '    border: 1px solid #ddd;' + '\n' +
    '    border-collapse: collapse;' + '\n' + '    }' +
    '\n' + 'th, td {' + '\n' + '    padding: 6px;' + '\n' + '    }' +
    '\n' + 'tr:nth-child(odd) {' + '\n' + '    background-color: #f9f9f9;' + '\n' + '    }' +
    '\n' +
    '</style>' + '\n' + '</head>' + '\n' + '<body>' + '\n')

# summary totals
htmlreport.write('<p>Number of cases with orders to amend: ' + str(len(amendedcases)) + '</p>')
htmlreport.write('<p>Number of cases with certified complaints: ' + str(len(certifiedcases)) + '</p>')

# details - certified, did not have to amend
print("Writing the first table")
htmlreport.write('<h2>Cases with claims certified, without orders to amend: ' + str(len(certnotamended)) + '</h2>')
htmlreport.write('<table>')
htmlreport.write('<tr><th>Docket</th><th>Claim filed</th><th>Claim certified</th><th>Days</th>' +
    '<th>Last document filed</th><th>Claimant law firm</th></tr>')
certrepresented = 0
certunrepresented = 0
for case in certnotamended:
    countorders = certcasesall.count(case)
    claimdate = casedatadict[case]["Oldest doc date"][:10]
    certdate = certordersdeduped[case]
    if casedatadict[case]["Claimant law firm"] == "none":
        certunrepresented += 1
    elif casedatadict[case]["Claimant law firm"] != "Not available":
        certrepresented +=1
    if casedatadict[case]["Oldest doc"] != "Claim":
        claimdate = "Unknown"
        timediff = "Unknown"
    else:
        d1 = datetime.strptime(claimdate, "%m/%d/%Y")
        d2 = datetime.strptime(certdate, "%m/%d/%Y")
        delta = d2-d1
        ccbfirstactiontimes.append(delta.days)
        ccbcerttimes.append(delta.days)
        timediff = str(delta.days)
    htmlreport.write('<tr>' +
        '<td>' + '<a href="' + casedatadict[case]["Docket URL"] + '">' + case + '</a></td>' +
        '<td>' + claimdate + '</td>' +
        '<td>' + certdate + '</td>' +
        '<td>' + timediff + '</td>' +
        '<td>' + casedatadict[case]["Latest doc"] + '</td>' +
        '<td>' + casedatadict[case]["Claimant law firm"] + '</td>' +
        '</tr>')
htmlreport.write('</table>')

certfirminfototal = certrepresented + certunrepresented
certpctrep = (certrepresented/certfirminfototal) * 100
certpctunrep = (certunrepresented/certfirminfototal) * 100
htmlreport.write("<p>Represented: " + str(certpctrep)[:2] + "%   Unrepresented: " + str(certpctunrep)[:2] + "%</p>")

# details - ordered to amend, not certified
print("Writing the second table")
htmlreport.write('<h2>Cases with orders to amend, no claim certified yet: ' + str(len(amendednotcert)) + '</h2>')
htmlreport.write('<table>')
htmlreport.write('<tr><th>Docket</th><th>Claim date</th><th>1st order to amend</th><th>Days</th>' +
    '<th>Last document filed</th><th>Law firm</th><th>No. of orders to amend</th></tr>')
amendrepresented = 0
amendunrepresented = 0
for case in amendednotcert:
    countorders = amendedcasesall.count(case)
    claimdate = casedatadict[case]["Oldest doc date"][:10]
    orderdate = amendordersdeduped[case]
    if casedatadict[case]["Claimant law firm"] == "none":
        amendunrepresented += 1
    elif casedatadict[case]["Claimant law firm"] != "Not available":
        amendrepresented +=1
    if casedatadict[case]["Oldest doc"] != "Claim":
        claimdate = "Unknown"
        timediff = "Unknown"
    else:
        d1 = datetime.strptime(claimdate, "%m/%d/%Y")
        d2 = datetime.strptime(orderdate, "%m/%d/%Y")
        delta = d2-d1
        ccbfirstactiontimes.append(delta.days)
        ccbotatimes.append(delta.days)
        timediff = str(delta.days)
    htmlreport.write('<tr>' +
        '<td>' + '<a href="' + casedatadict[case]["Docket URL"] + '">' + case + '</a></td>' +
        '<td>' + claimdate + '</td>' +
        '<td>' + orderdate + '</td>' +
        '<td>' + timediff + '</td>' +
        '<td>' + casedatadict[case]["Latest doc"] + '</td>' +
        '<td>' + casedatadict[case]["Claimant law firm"] + '</td>' +
        '<td>' + str(countorders) + '</td>' +
        '</tr>')
htmlreport.write('</table>')

amendfirminfototal = amendrepresented + amendunrepresented
amendpctrep = (amendrepresented/amendfirminfototal) * 100
amendpctunrep = (amendunrepresented/amendfirminfototal) * 100
htmlreport.write("<p>Represented: " + str(amendpctrep)[:2] + "%   Unrepresented: " + str(amendpctunrep)[:2] + "%</p>")

# details - ordered to amend, and also certified
print("Writing the third table")
htmlreport.write('<h2>Cases with orders to amend and claims certified: ' + str(len(amendedandcert)) + '</h2>')
htmlreport.write('<table>')
htmlreport.write('<tr><th>Docket</th><th>Claim date</th><th>Order to amend</th><th>Days</th>' +
    '<th>Amended Claim</th><th>Claim certified</th><th>Days</th><th>Last doc filed</th>' +
    '<th>Law firm</th><th>No. of OTA</th><th>No. of OCC</th></tr>')
for case in amendedandcert:
    countamend = amendedcasesall.count(case)
    countcert = certcasesall.count(case)
    claimdate = casedatadict[case]["Oldest doc date"][:10]
    otadate = amendordersdeduped[case]
    occdate = certordersdeduped[case]
    amendedclaimdate = amendedclaimslatercert[case]
    if casedatadict[case]["Oldest doc"] != "Claim":
        claimdate = "Unknown"
        otatimediff = "Unknown"
        occtimediff = "Unknown"
    else:
        dclaim = datetime.strptime(claimdate, "%m/%d/%Y")
        dota = datetime.strptime(otadate, "%m/%d/%Y")
        damended = datetime.strptime(amendedclaimdate, "%m/%d/%Y")
        docc = datetime.strptime(occdate, "%m/%d/%Y")
        deltax = dota-dclaim
        ccbfirstactiontimes.append(deltax.days)
        otatimediff = str(deltax.days)
        deltay = docc-damended
        ccbcertamendedtimes.append(deltay.days)
        occtimediff = str(deltay.days)
    htmlreport.write('<tr>' +
        '<td>' + '<a href="' + casedatadict[case]["Docket URL"] + '">' + case + '</a></td>' +
        '<td>' + claimdate + '</td>' +
        '<td>' + otadate + '</td>' +
        '<td>' + otatimediff + '</td>' +
        '<td>' + amendedclaimdate + '</td>' +
        '<td>' + occdate + '</td>' +
        '<td>' + occtimediff + '</td>' +
        '<td>' + casedatadict[case]["Latest doc"] + '</td>' +
        '<td>' + casedatadict[case]["Claimant law firm"] + '</td>' +
        '<td>' + str(countamend) + '</td>' +
        '<td>' + str(countcert) + '</td>' +
        '</tr>')
htmlreport.write('</table>')

htmlreport.write('<p>Average number of days from initial claim to order to amend or order certifying claim: ' +
    str(int(mean(ccbfirstactiontimes))) + '</p>')
htmlreport.write('<ul><li>Orders certifying: ' + str(int(mean(ccbcerttimes))) + '</li><li>Orders to amend: ' +
    str(int(mean(ccbotatimes))) + '</li></ul>')
htmlreport.write('<p>Average number of days from amended claim to order certifying claim: ' +
    str(int(mean(ccbcertamendedtimes))) + '</p>')

htmlreport.write('\n' + '</body>' + '\n' + '</html>')
htmlreport.close()

# example syntax
# print(casedatadict["22-CCB-0004"]["Oldest doc"])
