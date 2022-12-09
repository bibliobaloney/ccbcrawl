import requests, bs4, re, csv, PyPDF2

# get document number, url, date filed, docket number, and docket url for each document row
def getorderinfo(row):
    info = []
    cells = row.find_all('td')
    commanum = cells[1].get_text(strip=True)
    documentnum = commanum.replace(",", "")
    info.append(documentnum)
    documenturl = "https://dockets.ccb.gov/document/download/" + documentnum
    info.append(documenturl)
    datefiledlong = str(cells[5].get_text(strip=True))
    datefiled = datefiledlong[:10]
    info.append(datefiled)
    docketnum = str(cells[0].get_text(strip=True))
    info.append(docketnum)
    docketurl = "https://dockets.ccb.gov/case/detail/" + docketnum
    info.append(docketurl)
    return info

def getpdftext(filename):
    pdfFileObj = open(filename, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    pageObj = pdfReader.getPage(0)
    ordertext = pageObj.extractText()
    for pageNum in range(1, pdfReader.numPages):
        pageObj = pdfReader.getPage(pageNum)
        ordertext = ordertext + pageObj.extractText()
    return ordertext

# Import the data from the last time we ran this script
print("Importing OTA info from CSV")
otareasonscsv = open('otareasons.csv', 'r')
reader = csv.DictReader(otareasonscsv)
otasdict = {}
for dictionary in reader:
    documentnum = dictionary["Document No."]
    otasdict[documentnum] = dictionary
otareasonscsv.close()

# Get list of orders we had as of the last run
orderswehave = []
for order in otasdict:
    orderswehave.append(order)
ordersweneed = []

# Get the first 100 orders to amend
print("Getting list of all orders to amend")
res = requests.get('https://dockets.ccb.gov/search/documents?search=&docTypeGroup=type%3A52&max=100')
res.raise_for_status()
amendlistsoup = bs4.BeautifulSoup(res.text, 'lxml')
amendtablerows = amendlistsoup.tbody.find_all('tr')
# Get the next 100
res = requests.get('https://dockets.ccb.gov/search/documents?search=&docTypeGroup=type%3A52&offset=100&max=100')
res.raise_for_status()
amendlistsoup = bs4.BeautifulSoup(res.text, 'lxml')
amendtablerows.extend(amendlistsoup.tbody.find_all('tr'))
print('Total number of OTAs found: ' + str(len(amendtablerows)))

# Get the basic info for each order to amend
print("Getting basic info for each order")
for row in amendtablerows:
    thisotadict = {}
    otainfo = getorderinfo(row)
    documentnum = otainfo[0]
    if documentnum not in orderswehave:
        ordersweneed.append(documentnum)
        thisotadict["Document No."] = documentnum
        thisotadict["Document URL"] = otainfo[1]
        thisotadict["Date filed"] = otainfo[2]
        thisotadict["Docket No."] = otainfo[3]
        thisotadict["Docket URL"] = otainfo[4]
        thisotadict["PDF filename"] = 'pdfs/ota' + documentnum + '.pdf'
        otasdict[documentnum] = thisotadict

# Save PDFs locally
print("Saving PDFs locally")
for order in ordersweneed:
    print(order)
    otapdfurl = otasdict[order]["Document URL"]
    res = requests.get(otapdfurl)
    res.raise_for_status()
    pdffile = open('pdfs/ota' + order + '.pdf', 'wb')
    for chunk in res.iter_content(100000):
        pdffile.write(chunk)
    pdffile.close()

# Get text from PDFs
print("Checking for reasons in PDF text")
for order in ordersweneed:
    filename = otasdict[order]["PDF filename"]
    print('Getting text of ' + filename)
    pdftext = getpdftext(filename)
    pdftext = pdftext.replace(' ', '')
    otasdict[order]["Foreign Respondent"] = 0
    otasdict[order]["Gov Entity Respondent"] = 0
    otasdict[order]["OSP"] = 0
    otasdict[order]["Impermissible Claim"] = 0
    otasdict[order]["Relief Sought"] = 0
    otasdict[order]["Improper Pleading Form"] = 0
    otasdict[order]["Clarity"] = 0
    otasdict[order]["Access"] = 0
    otasdict[order]["Ownership"] = 0
    otasdict[order]["Registration"] = 0
    otasdict[order]["Substantial Similarity"] = 0
    otasdict[order]["Misrep - False Statement"] = 0
    otasdict[order]["Misrep - No Notice Sent"] = 0
    otasdict[order]["Noninfringement - No Accusation"] = 0
    if "ForeignRespondent" in pdftext:
        otasdict[order]["Foreign Respondent"] = 1
    if "FederalorState" in pdftext:
        otasdict[order]["Gov Entity Respondent"] = 1
    if "OnlineServiceProvider" in pdftext:
        otasdict[order]["OSP"] = 1
    if "ermissibleClaim" in pdftext:
        otasdict[order]["Impermissible Claim"] = 1
    if "ReliefSought" in pdftext or "PermissibleRemedies" in pdftext or "ReliefRequested" in pdftext:
        otasdict[order]["Relief Sought"] = 1
    if "ImproperPleadingForm" in pdftext:
        otasdict[order]["Improper Pleading Form"] = 1
    if "Clarity" in pdftext:
        otasdict[order]["Clarity"] = 1
    if "Access" in pdftext:
        otasdict[order]["Access"] = 1
    if "BeneficialOwner" in pdftext or "CopyrightOwnership" in pdftext:
        otasdict[order]["Ownership"] = 1
    if "Registration" in pdftext:
        otasdict[order]["Registration"] = 1
    if "SubstantialSimilarity" in pdftext:
        otasdict[order]["Substantial Similarity"] = 1
    if "FalseStatement" in pdftext:
        otasdict[order]["Misrep - False Statement"] = 1
    if "NoDMCA" in pdftext:
        otasdict[order]["Misrep - No Notice Sent"] = 1
    if "NoAccusationbyRespondent" in pdftext:
        otasdict[order]["Noninfringement - No Accusation"] = 1

# Output dictionaries as csv
otaslist = [value for value in otasdict.values()]
otaslist.sort(key=lambda x: x["Document No."])
with open('otareasons.csv', 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames = otaslist[0].keys())
    writer.writeheader()
    writer.writerows(otaslist)
csvfile.close()

