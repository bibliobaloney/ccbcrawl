import requests, bs4, re, csv
from datetime import date

newdata = open('casedata.csv', 'r')

def getdocketnumclosedlist(row):
    cells = []
    cells += row.find_all('td')
    docketnum = str(cells[1].get_text(strip=True))
    return docketnum

reader = csv.DictReader(newdata)
casedatalist = list()
for dictionary in reader:
    casedatalist.append(dictionary)
newdata.close()

statusdata = open('otasandoccs.csv', 'r')
reader = csv.DictReader(statusdata)
casestatusdict = {}
caseswithstatus = []
for dictionary in reader:
    casedictname = dictionary["Docket No."]
    casestatusdict[casedictname] = dictionary
    caseswithstatus.append(casedictname)
statusdata.close()

# Get list of closed cases from closedcases.csv (created by closedcasepdf.py)
closedcasedata = open('closedcases.csv', 'r')
reader = csv.reader(closedcasedata)
closedcases = []
for record in reader:
    closedcases.append(record[0])
closedcasedata.close()
closedcases.pop(0)

# Get the case numbers for the (first 100) cases from the closed case list
# print("Getting closed cases")
# allclosedcases = []
# res = requests.get('https://dockets.ccb.gov/search/closed?max=100')
# res.raise_for_status()
# closedlistsoup = bs4.BeautifulSoup(res.text, 'lxml')
# closedtablerows = closedlistsoup.tbody.find_all('tr')
# for row in closedtablerows:
#     allclosedcases.append(getdocketnumclosedlist(row))
# allclosedcases.sort()

tabledoc = open("infringementtable.html", 'w')
tabledoc.write('<!DOCTYPE html>' + '\n' + '<html lang="en">' + '\n' +
    '<head><title>CCB cases weekly snapshot </title>' + '\n' +
    '<style>' + '\n' + 'table, th, td {' + '\n' + '    border: 1px solid #ddd;' + '\n' +
    '    border-collapse: collapse;' + '\n' + '    }' +
    '\n' + 'td {' + '\n' + '    word-wrap: break-word;' + '\n' + '    max-width: 1px;' +
    '\n' + '    padding: 6px;' + '\n' + '    }' +
    '\n' + 'th {' + '\n' + '    padding: 6px;' + '\n' + '    }' +
    '\n' + 'tr:nth-child(odd) {' + '\n' + '    background-color: #f9f9f9;' + '\n' + '    }' +
    '\n' + '</style>' + '\n' + '</head>' + '\n' + '<body>' +
    '<p>Run date: ' + str(date.today()) + '</p>' +
    '\n' +'<table>' + '\n' +
    '<thead><tr><th>Case</th><th>Claim type</th><th>Description of Work</th><th>Description of Infringement (Truncated at 1200 characters if longer)</th>' +
    '<th>Description of harm suffered and relief sought (Truncated at 1200)</th><th>Status</th>'
    '<th>Claimant</th><th>Claimant Law Firm</th><th>Respondent</th><th>Most recent filing</th></tr></thead>')

for case in casedatalist:
    status =  "No claim certified, no orders to amend"
    docketnum = case["Docket No."]
    color = "#ffffff"
    if docketnum == "22-CCB-0045":
        status = '<a href="/orderstoamendorcertify.html">Active; transferred to CCB</a>'
        color = "#baffc9"
    if docketnum in caseswithstatus:
        grabbedstatus = casestatusdict[docketnum]["Current status"]
        if grabbedstatus == "Certified":
            status = '<a href="/orderstoamendorcertify.html">Certified</a>'
            color = "#baffc9"
        elif grabbedstatus == "Closed":
            status = '<a href="/closedcases.html">Closed</a>'
            color = "#ffdfba"
        elif grabbedstatus == "Final Determination filed":
            status = 'Final Determination filed'
            color = "#bae1ff"
        elif grabbedstatus == "Awaiting amendment/certification":
            status = '<a href="/orderstoamendorcertify.html">Awaiting amendment/certification</a>'
            color = "#ffffba"
    elif docketnum in closedcases:
        status = '<a href="/closedcases.html">Closed</a>'
        color = "#ffdfba"
    tabledoc.write('<tr>' +
        '<td>' + '<a href="' + case["Docket URL"] + '">' + case["Docket No."] + '</a>' '</td>' +
        '<td>' + case["Claim types"] + '</td>' +
        '<td>' + case["Description of work"] + '</td>' +
        '<td>' + case["Description of infringement"] + '</td>' +
        '<td>' + case["Relief sought"] + '</td>' +
        '<td style = "background-color: ' + color + '">' + status + '</td>' +
        '<td>' + case["Claimant"] + '</td>' +
        '<td>' + case["Claimant law firm"] + '</td>' +
        '<td>' + case["Respondent"] + '</td>' +
        '<td>' + case["Latest doc"] + '</td>' +
        '</tr>')

tabledoc.write('</table>' + '\n' + '</body>' + '\n' + '</html>')
tabledoc.close()
