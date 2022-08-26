import requests, bs4, re, csv, math

def getcaseurls(row):
    cells = []
    cells += row.find_all('td')
    docketnum = str(cells[1].get_text(strip=True))
    link = row.a
    casedocketpage = link['href']
    casedocketurl = 'https://dockets.ccb.gov' + casedocketpage
    caseurls = [docketnum, casedocketurl]
    print(caseurls)
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
    if len(claimsoup.find_all(text=re.compile(capclaimant))) > 1:
        claimant = claimsoup.find_all(text=re.compile(capclaimant))[1].parent.get_text(strip=True)
    else:
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
    if len(claimsoup.find_all(text=re.compile(caprespondent))) > 1:
        respondent = claimsoup.find_all(text=re.compile(caprespondent))[1].parent.get_text(strip=True)
    else:
        respondent = claimsoup.find(text=re.compile(capclaimant)).parent.get_text(strip=True)
    details.append(respondent)
    damagesparentdiv = claimsoup.find(attrs={'data-field' : 'harm'})
    damagesdiv = damagesparentdiv.contents[1]
    damages = damagesdiv.get_text(strip=True)
    details.append(damages[:1200])
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

casedatalist = []

# Get the 20 latest cases
res = requests.get('https://dockets.ccb.gov/search/cases')
res.raise_for_status()
caselistsoup = bs4.BeautifulSoup(res.text, 'lxml')
casetablerows = caselistsoup.tbody.find_all('tr')
for row in casetablerows:
    casedatalist += [getcaseurls(row)]

# Get the number of pages, with 20 cases each
latestdocket = casedatalist[0][0]
lastdocketend = latestdocket[7:]
lastdocketnum = int(lastdocketend)
divtwenty = lastdocketnum / 20
pages = math.ceil(divtwenty)

# Get the rest of the pages and add their docket numbers and captions to casedatalist
currentpage = 2
offset = 20
while currentpage <= pages:
    caselisturl = ('https://dockets.ccb.gov/search/cases?closed=false&columns=longCaption&columns=code&columns=parties&columns=actions&offset=' +
    str(offset) + '&max=20&sort=code&order=desc')
    res5 = requests.get(caselisturl)
    nextcaselistsoup = bs4.BeautifulSoup(res5.text, 'lxml')
    nextcasetablerows = nextcaselistsoup.tbody.find_all('tr')
    for row in nextcasetablerows:
        casedatalist += [getcaseurls(row)]
    currentpage += 1
    offset += 20


# -------for a subset------
# samplecaselist = []
# samplecaselist.append(casedatalist[-92])
# samplecaselist.append(casedatalist[-67])
# samplecaselist.append(casedatalist[-59])
# samplecaselist.append(casedatalist[-52])
# samplecaselist.append(casedatalist[-39])
# samplecaselist.append(casedatalist[-30])
# samplecaselist.append(casedatalist[-20])
# samplecaselist.append(casedatalist[-16])
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
#     'Latest doc date', 'Claim URL', 'Claim types', 'Smaller?', 'Claimant', 'Claimant law firm', 'Respondent', 'Relief sought',
#     'Work registered?', 'Reg effective date', 'Work type', 'Description of work', 'Description of infringement'])
# with open('ccbcasedata.csv', 'w') as casedatacsv:
#     write = csv.writer(casedatacsv)
#     write.writerow(csvheader)
#     write.writerows(samplecaselist)
# casedatacsv.close()

# for case in samplecaselist:
#     while len(case) < 19:
#         case.append('NA')

# tabledoc = open("infringementtable.html", 'w')
# tabledoc.write('<!DOCTYPE html>' + '\n' + '<html lang="en">' + '\n' +
#     '<head>' + '\n' + '<style>' + '\n' + 'table, th, td {' + '\n' +
#     'border: 1px solid black;' + '\n' + '}' +
#     '\n' + '</style>' + '\n' + '</head>' + '\n' + '<body>' +
#     '\n' +'<table>' + '/n' +
#     '<thead><tr><th>Case</th><th>Claim type</th><th>Description of Work</th><th>Description of Infringement (Truncted at 1200 characters)</th>' +
#     '<th>Description of relief sought (first 1200 characters)</th>'
#     '<th>Claimant</th><th>Claimant Law Firm</th><th>Respondent</th><th>Most recent filing</th></tr></thead>')

# for case in samplecaselist:
#     tabledoc.write('<tr>' +
#         '<td>' + '<a href="' + case[1] + '">' + case[0] + '</a>' '</td>' +
#         '<td>' + case[8] + '</td>' +
#         '<td>' + case[17] + '</td>' +
#         '<td>' + case[18] + '</td>' +
#         '<td>' + case[13] + '</td>' +
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
    'Latest doc date', 'Claim URL', 'Claim types', 'Smaller?', 'Claimant', 'Claimant law firm', 'Respondent', 'Relief sought',
    'Work registered?', 'Reg effective date', 'Work type', 'Description of work', 'Description of infringement'])
with open('ccbcasedata.csv', 'w') as casedatacsv:
    write = csv.writer(casedatacsv)
    write.writerow(csvheader)
    write.writerows(casedatalist)
casedatacsv.close()

for case in casedatalist:
    while len(case) < 19:
        case.append('NA')

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
        '<td>' + '<a href="' + case[1] + '">' + case[0] + '</a>' '</td>' +
        '<td>' + case[8] + '</td>' +
        '<td>' + case[17] + '</td>' +
        '<td>' + case[18] + '</td>' +
        '<td>' + case[13] + '</td>' +
        '<td>' + case[10] + '</td>' +
        '<td>' + case[11] + '</td>' +
        '<td>' + case[12] + '</td>' +
        '<td>' + case[5] + '</td>' +
        '</tr>')

tabledoc.write('</table>' + '\n' + '</body>' + '\n' + '</html>')
tabledoc.close()
