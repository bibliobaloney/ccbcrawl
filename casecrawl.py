import requests, bs4, re, csv

res = requests.get('https://dockets.ccb.gov/search/cases')
res.raise_for_status()
caselistsoup = bs4.BeautifulSoup(res.text, 'lxml')

def getcaseurls(row):
    cells = []
    cells += row.find_all('td')
    docketnum = str(cells[1].contents[0])
    link = row.a
    casedocketpage = link['href']
    casedocketurl = 'https://dockets.ccb.gov' + casedocketpage
    caseurls = [docketnum, casedocketurl]
    return caseurls

def getdocketinfo(case):
    caselink = case[1]
    docketinfo = []
    res2 = requests.get(caselink)
    res2.raise_for_status()
    casedocketsoup = bs4.BeautifulSoup(res2.text, 'lxml')
    captionhook = casedocketsoup.find(text=re.compile('Caption')).parent
    captionparentdiv = captionhook.parent
    caption = captionparentdiv.find(class_='detail-value').get_text(strip=True)
    docketinfo.append(caption)
    caselinksortasc = caselink + '?sort=submittedDate&max=10&order=asc'
    res3 = requests.get(caselinksortasc)
    res3.raise_for_status()
    ascendingsoup = bs4.BeautifulSoup(res3.text, 'lxml')
    docstable = casedocketsoup.find_all('tbody')
    firstdoc = ''
    if len(docstable) == 0:
        firstdoc = 'None'
        docketinfo.append(firstdoc)
    else:
        firstdocrow = ascendingsoup.find_all('tr')[1]
        firstdoccell = firstdocrow.find_all('td')[1]
        firstdoc = ''
        if len(firstdoccell.find_all("span", class_=re.compile("document-restricted"))) != 0:
            ourspan = firstdoccell.find("span", class_=re.compile("document-restricted"))
            firstdoc = ourspan.get_text(strip=True)
        else:
            ourspan = firstdoccell.find("span", class_=re.compile("document-link-title"))
            srspan = ourspan.find(class_='sr-only')
            srspan.decompose()
            firstdoc = ourspan.get_text(strip=True)
        docketinfo.append(firstdoc)
        firstdocdate = firstdocrow.find_all('td')[-1].get_text(strip=True)
        docketinfo.append(firstdocdate)
        mostrecentrow = casedocketsoup.find_all('tr')[1]
        lastdoccell = mostrecentrow.find_all('td')[1]
        lastdoc = ''
        if len(lastdoccell.find_all("span", class_=re.compile("document-restricted"))) != 0:
            ourspan = lastdoccell.find("span", class_=re.compile("document-restricted"))
            lastdoc = ourspan.get_text(strip=True)
        else:
            ourspan = lastdoccell.find("span", class_=re.compile("document-link-title"))
            srspan = ourspan.find(class_='sr-only')
            srspan.decompose()
            lastdoc = ourspan.get_text(strip=True)
        docketinfo.append(lastdoc)
        lastdocdate = mostrecentrow.find_all('td')[-1].get_text(strip=True)
        docketinfo.append(lastdocdate)
    if docketinfo[1] == 'Claim':
        claimrow = ascendingsoup.find_all('tr')[1]
        claimcell = claimrow.find_all('td')[1]
        claimlink = claimcell.a
        claimpage = claimlink.get('href')
        claimurl = 'https://dockets.ccb.gov' + claimpage
        docketinfo.append(claimurl)
    return docketinfo

def getcasedetails(case):
    claimlink = case[7]
    details = []
    res4 = requests.get(claimlink)
    res4.raise_for_status()
    claimsoup = bs4.BeautifulSoup(res4.text, 'lxml')
    typesdiv = claimsoup.find(attrs={'data-field' : 'typeFlags'})
    claims = ''
    stringoftypes = typesdiv.get_text(strip=True)
    if 'for infringement' in stringoftypes:
        claims = claims + 'infringement'
    if '512' in stringoftypes:
        claims = claims + '-DMCA-'
    if 'noninfringe' in stringoftypes:
        claims = claims + '-noninfringement'
    details.append(claims)
    smallerdiv = claimsoup.find(attrs={'data-field' : 'smallClaim'})
    smaller = smallerdiv.get_text(strip=True)
    details.append(smaller)
    fullcaption = case[2]
    caption = ''
    if 'et al' in fullcaption:
        caption = fullcaption.replace(', et al', '')
    else:
        caption = fullcaption
    splitcaption = caption.partition(' v. ')
    fullcapclaimant = splitcaption[0]
    fullcaprespondent = splitcaption[2]
    if '(' in fullcapclaimant:
        capclaimant = fullcapclaimant.split('(')[0]
    else:
        capclaimant = fullcapclaimant
    claimant = claimsoup.find(text=re.compile(capclaimant)).parent.get_text(strip=True)
    details.append(claimant)
    claimantlawfirm = 'none'
    if claimsoup.find_all(text=re.compile('Law firm')):
        lawfirmhook = claimsoup.find(text=re.compile('Law firm'))
        lawfirmdiv = lawfirmhook.parent.parent.find(attrs={'data-field' : 'organization'})
        claimantlawfirm = lawfirmdiv.get_text(strip=True)
    details.append(claimantlawfirm)
    if '(' in fullcaprespondent:
        caprespondent = fullcaprespondent.split('(')[0]
    else:
        caprespondent = fullcaprespondent
    respondent = claimsoup.find(text=re.compile(caprespondent)).parent.get_text(strip=True)
    details.append(respondent)
    return details

def getinfringementdetails(case):
    claimlink = case[7]
    infrdetails = []
    res4 = requests.get(claimlink)
    res4.raise_for_status()
    claimsoup = bs4.BeautifulSoup(res4.text, 'lxml')
    regstatusdiv = claimsoup.find(attrs={'data-field' : 'registered'})
    regstatus = regstatusdiv.get_text(strip=True)
    infrdetails.append(regstatus)
    regdate = 'NA'
    if regstatus == 'Yes':
        regdatediv = claimsoup.find(attrs={'data-field' : 'registrationEffectiveDate'})
        regdate = regdatediv.get_text(strip=True)
    infrdetails.append(regdate)
    worktypediv = claimsoup.find(attrs={'data-field' : 'workType'})
    fullworktype = worktypediv.get_text(strip=True)
    if len(fullworktype) > 20:
        worktype = fullworktype[:20] + '...'
    else:
        worktype = fullworktype
    infrdetails.append(worktype)
    description = 'None given'
    if len(claimsoup.find_all(attrs={'data-field' : 'workDescription'})) != 0:
        descriptiondiv = claimsoup.find(attrs={'data-field' : 'workDescription'})
        description = descriptiondiv.get_text(strip=True)
    infrdetails.append(description)
    infrdescriptionparentdiv = claimsoup.find(attrs={'data-field' : 'description'})
    infrdescriptiondiv = infrdescriptionparentdiv.contents[1]
    infrdescription = infrdescriptiondiv.get_text(strip=True)
    infrdetails.append(infrdescription[:1200])
    return infrdetails

casetablerows = caselistsoup.tbody.find_all('tr')
casedatalist = []
for row in casetablerows:
    casedatalist += [getcaseurls(row)]

# -------for a subset------
# samplecaselist = []
# samplecaselist.append(casedatalist[-92])
# samplecaselist.append(casedatalist[-67])
# samplecaselist.append(casedatalist[-59])
# samplecaselist.append(casedatalist[-58])
# samplecaselist.append(casedatalist[-52])
# samplecaselist.append(casedatalist[-42])
# samplecaselist.append(casedatalist[-39])
# samplecaselist.append(casedatalist[-34])
# samplecaselist.append(casedatalist[-30])
# samplecaselist.append(casedatalist[-20])
# samplecaselist.append(casedatalist[-19])
# samplecaselist.append(casedatalist[-16])
# samplecaselist.append(casedatalist[-15])
# samplecaselist.append(casedatalist[-1])

# for case in samplecaselist:
#     case.extend(getdocketinfo(case))
#     print(case)
# for case in samplecaselist:
#     if case[3] == 'Claim':
#         case.extend(getcasedetails(case))
#         print(case)
# for case in samplecaselist:
#     if case[3] == 'Claim':
#         if case[8][0] == 'i':
#             case.extend(getinfringementdetails(case))
#             print(case)

# csvheader = (['Docket No.', 'Docket URL', 'Caption', 'Oldest doc', 'Oldest doc date', 'Latest doc',
#     'Latest doc date', 'Claim URL', 'Claim types', 'Smaller?', 'Claimant', 'Claimant law firm', 'Respondent',
#     'Work registered?', 'Reg effective date', 'Work type', 'Description of work', 'Description of infringement'])
# with open('ccbcasedata.csv', 'w') as casedatacsv:
#     write = csv.writer(casedatacsv)
#     write.writerow(csvheader)
#     write.writerows(samplecaselist)
# casedatacsv.close()

# for case in samplecaselist:
#     while len(case) < 18:
#         case.append('NA')

# tabledoc = open("infringementtable.html", 'w')
# tabledoc.write('<!DOCTYPE html>' + '\n' + '<html lang="en">' + '\n' +
#     '<head>' + '\n' + '<style>' + '\n' + 'table, th, td {' + '\n' +
#     'border: 1px solid black;' + '\n' + '}' +
#     '\n' + '</style>' + '\n' + '</head>' + '\n' + '<body>' +
#     '\n' +'<table>' + '/n' +
#     '<thead><tr><th>Case</th><th>Claim type</th><th>Description of Work</th><th>Description of Infringement</th>' + '\n' +
#     '<th>Claimant</th><th>Claimant Law Firm</th><th>Respondent</th><th>Most recent filing</th></tr></thead>')

# for case in samplecaselist:
#     tabledoc.write('<tr>' +
#         '<td>' + '<a href="' + case[1] + '">' + case[0] + '</a>' '</td>' +
#         '<td>' + case[8] + '</td>' +
#         '<td>' + case[16] + '</td>' +
#         '<td>' + case[17] + '</td>' +
#         '<td>' + case[10] + '</td>' +
#         '<td>' + case[11] + '</td>' +
#         '<td>' + case[12] + '</td>' +
#         '<td>' + case[5] + '</td>' +
#         '</tr>')

# tabledoc.write('</table>' + '\n' + '</body>' + '\n' + '</html>')
# tabledoc.close()

#### --------for all cases
for case in casedatalist:
    case.extend(getdocketinfo(case))
    print(case)
for case in casedatalist:
    if case[3] == 'Claim':
        case.extend(getcasedetails(case))
        print(case)
for case in casedatalist:
    if case[3] == 'Claim':
        if case[8][0] == 'i':
            case.extend(getinfringementdetails(case))
            print(case)

csvheader = (['Docket No.', 'Docket URL', 'Caption', 'Oldest doc', 'Oldest doc date', 'Latest doc',
    'Latest doc date', 'Claim URL', 'Claim types', 'Smaller?', 'Claimant', 'Claimant law firm', 'Respondent',
    'Work registered?', 'Reg effective date', 'Work type', 'Description of work', 'Description of infringement'])
with open('ccbcasedata.csv', 'w') as casedatacsv:
    write = csv.writer(casedatacsv)
    write.writerow(csvheader)
    write.writerows(casedatalist)
casedatacsv.close()

for case in casedatalist:
    while len(case) < 18:
        case.append('NA')

tabledoc = open("infringementtable.html", 'w')
tabledoc.write('<!DOCTYPE html>' + '\n' + '<html lang="en">' + '\n' +
    '<head>' + '\n' +
    '<style>' + '\n' + 'table, th, td {' + '\n' + '    border: 1px solid black;' + '\n' + '    }' +
    '\n' + 'td {' + '\n' + '    word-wrap: break-word;' + '\n'+ '    max-width: 1px;' + '\n' + '    }' +
    '\n' + '</style>' + '\n' + '</head>' + '\n' + '<body>' +
    '\n' +'<table>' + '\n' +
    '<thead><tr><th>Case</th><th>Claim type</th><th>Description of Work</th><th>Description of Infringement (up to 1200 characters)</th>' + '\n' +
    '<th>Claimant</th><th>Claimant Law Firm</th><th>Respondent</th><th>Most recent filing</th></tr></thead>')

for case in casedatalist:
    tabledoc.write('<tr>' +
        '<td>' + '<a href="' + case[1] + '">' + case[0] + '</a>' '</td>' +
        '<td>' + case[8] + '</td>' +
        '<td>' + case[16] + '</td>' +
        '<td>' + case[17] + '</td>' +
        '<td>' + case[10] + '</td>' +
        '<td>' + case[11] + '</td>' +
        '<td>' + case[12] + '</td>' +
        '<td>' + case[5] + '</td>' +
        '</tr>')

tabledoc.write('</table>' + '\n' + '</body>' + '\n' + '</html>')
tabledoc.close()
