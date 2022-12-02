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
    print('text of order ' + filename)
    pdfFileObj = open(filename, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    pageObj = pdfReader.getPage(0)
    ordertext = pageObj.extractText()
    for pageNum in range(1, pdfReader.numPages):
        pageObj = pdfReader.getPage(pageNum)
        ordertext = ordertext + pageObj.extractText()
    return ordertext

# Get the first 100 orders to amend
print("Getting list of orders to amend")
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
testing = [amendtablerows[140], amendtablerows[141], amendtablerows[142], amendtablerows[143], amendtablerows[144]]
testotasdict = {}
for row in testing:
    thisotadict = {}
    otainfo = getorderinfo(row)
    documentnum = otainfo[0]
    thisotadict["Document No."] = documentnum
    thisotadict["Document URL"] = otainfo[1]
    thisotadict["Date filed"] = otainfo[2]
    thisotadict["Docket No."] = otainfo[3]
    thisotadict["Docket URL"] = otainfo[4]
    thisotadict["PDF filename"] = 'pdfs/ota' + documentnum + '.pdf'
    testotasdict[documentnum] = thisotadict

# Save PDFs locally
print("Saving PDFs locally")
for case in testotasdict:
    print(case)
    otapdfurl = testotasdict[case]["Document URL"]
    res = requests.get(otapdfurl)
    res.raise_for_status()
    pdffile = open('pdfs/ota' + case + '.pdf', 'wb')
    for chunk in res.iter_content(100000):
        pdffile.write(chunk)
    pdffile.close()

# Get text from PDFs
for case in testotasdict:
    filename = testotasdict[case]["PDF filename"]
    pdftext = getpdftext(filename)
    print(pdftext)

# amendedcasesall = []
# amendordersall = []
# for row in amendtablerows:
#     amendedcasesall.append(getdocketnum(row))
#     amendordersall.append([getdocketnum(row), getdatefiled(row)])
# Get the next hundred
# res = requests.get('https://dockets.ccb.gov/search/documents?search=&docTypeGroup=type%3A52&offset=100&max=100')
# res.raise_for_status()
# amendlistsoup = bs4.BeautifulSoup(res.text, 'lxml')
# amendtablerows = amendlistsoup.tbody.find_all('tr')
# for row in amendtablerows:
#     amendedcasesall.append(getdocketnum(row))
#     amendordersall.append([getdocketnum(row), getdatefiled(row)])

# output list of cases w orders to amend to a text file for closedcases.py
# amendfile = open('amendfile.txt', 'w')
# for item in amendedcasesall:
#     amendfile.writelines(item + '\n')
# amendfile.close()


