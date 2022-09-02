import requests, bs4, re, csv

newdata = open('casedata.csv', 'r')

reader = csv.DictReader(newdata)
casedatalist = list()
for dictionary in reader:
    casedatalist.append(dictionary)
newdata.close()

tabledoc = open("infringementtable.html", 'w')
tabledoc.write('<!DOCTYPE html>' + '\n' + '<html lang="en">' + '\n' +
    '<head>' + '\n' +
    '<style>' + '\n' + 'table, th, td {' + '\n' + '    border: 1px solid #ddd;' + '\n' +
    '    border-collapse: collapse;' + '\n' + '    }' +
    '\n' + 'td {' + '\n' + '    word-wrap: break-word;' + '\n' + '    max-width: 1px;' +
    '\n' + '    padding: 6px;' + '\n' + '    }' +
    '\n' + 'th {' + '\n' + '    padding: 6px;' + '\n' + '    }' +
    '\n' + 'tr:nth-child(odd) {' + '\n' + '    background-color: #f9f9f9;' + '\n' + '    }' +
    '\n' + '</style>' + '\n' + '</head>' + '\n' + '<body>' +
    '\n' +'<table>' + '\n' +
    '<thead><tr><th>Case</th><th>Claim type</th><th>Description of Work</th><th>Description of Infringement (Truncated at 1200 characters if longer)</th>' +
    '<th>Description of harm suffered and relief sought (Truncated at 1200)</th>'
    '<th>Claimant</th><th>Claimant Law Firm</th><th>Respondent</th><th>Most recent filing</th></tr></thead>')

for case in casedatalist:
    tabledoc.write('<tr>' +
        '<td>' + '<a href="' + case["Docket URL"] + '">' + case["Docket No."] + '</a>' '</td>' +
        '<td>' + case["Claim types"] + '</td>' +
        '<td>' + case["Description of work"] + '</td>' +
        '<td>' + case["Description of infringement"] + '</td>' +
        '<td>' + case["Relief sought"] + '</td>' +
        '<td>' + case["Claimant"] + '</td>' +
        '<td>' + case["Claimant law firm"] + '</td>' +
        '<td>' + case["Respondent"] + '</td>' +
        '<td>' + case["Latest doc"] + '</td>' +
        '</tr>')

tabledoc.write('</table>' + '\n' + '</body>' + '\n' + '</html>')
tabledoc.close()
