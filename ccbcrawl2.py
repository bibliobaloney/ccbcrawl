import requests, bs4, re, csv, math

# Save list of states to compare to what's after the comma in Claimant city in getcasedetails
listofstates = (["AK", "AL", "AR", "AZ", "CA", "CO", "CT", "DE", "FL", "GA", "HI",
    "IA", "ID", "IL", "IN", "KS", "KY", "LA", "MA", "MD", "ME", "MI", "MN", "MO",
    "MS", "MT", "NC", "ND", "NE", "NH", "NJ", "NM", "NV", "NY", "OH", "OK", "OR",
    "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VA", "VT", "WA", "WI", "WV", "WY", "DC"])

# Save list of cases to stop looking at, even though no claim available
donotcheck = ['22-CCB-0016', '22-CCB-0092', '22-CCB-0096', '22-CCB-0105', '22-CCB-0175']

lastweek = open('casedata.csv', 'r')
# Grab cases where claim details have already been collected in local file
reader = csv.DictReader(lastweek)
casedatalist = list()
for case in reader:
    if case["Claim URL"][:4] == "http" or case["Docket No."] in donotcheck:
        casedatalist.append(case)
lastweek.close()

# Get latest docket number
res = requests.get('https://dockets.ccb.gov/search/cases')
res.raise_for_status()
caselistsoup = bs4.BeautifulSoup(res.text, 'lxml')
toprow = caselistsoup.tbody.find('tr')
lastdocket = toprow.find_all('td')[1].get_text(strip=True)
lastdocketnum = int(lastdocket[7:])

# Get a list of the dockets we already have, or that are closed
docketswehave = []
for case in casedatalist:
        docketswehave.append(case.get("Docket No."))

# Get a list of closed cases from last week
closedcasescsv = open('closedcases.csv', 'r')
reader = csv.DictReader(closedcasescsv)
closedcaseslist = []
for dictionary in reader:
    closedcaseslist.append(dictionary["Docket No."])

#Get a list of dockets we need
docketsweneed = []
currentcheck = 1
while currentcheck <= lastdocketnum:
    fourdigits = "{0:0>4}".format(currentcheck)
    docketnum = "22-CCB-" + fourdigits
    if docketnum not in docketswehave:
        docketsweneed.append(docketnum)
    currentcheck += 1

# for weird edge cases where there are documents, but the claim isn't first, like 22-CCB-0015
def digforclaimurl(docketurl):
    res5 = requests.get(docketurl + '?sort=submittedDate&max=100&order=asc')
    res5.raise_for_status()
    docketsoup = bs4.BeautifulSoup(res5.text, 'lxml')
    docketrows = docketsoup.find_all('tr')
    claimrow = 'No claim row found'
    currentrow = 0
    while claimrow == 'No claim row found' and currentrow < len(docketrows):
        tds = []
        cells = docketrows[currentrow].find_all('td')
        for cell in cells:
            tds.append(cell.get_text(strip=True))
        if len(tds) > 2 and (tds[2] == "Claim" or tds[2] == "Amended Claim"):
            claimrow = docketrows[currentrow]
        else:
            currentrow += 1
    if claimrow == 'No claim row found':
        return 'No claim found'
    claimcell = claimrow.find_all('td')[1]
    claimlink = claimcell.a
    claimpage = claimlink.get('href')
    claimurl = 'https://dockets.ccb.gov' + claimpage
    return claimurl

# to retrieve caption, oldest document, oldest document date, and claim URL if available
def getcapandclaim(docketurl):
    capandclaim = []
    res2 = requests.get(docketurl + '?max=100')
    res2.raise_for_status()
    casedocketsoup = bs4.BeautifulSoup(res2.text, 'lxml')
    captionhook = casedocketsoup.find(text=re.compile('Caption')).parent
    captionparentdiv = captionhook.parent
    caption = captionparentdiv.find(class_='detail-value').get_text(strip=True)
    capandclaim.append(caption)
    firstdoc = ''
    docstable = casedocketsoup.find_all('tbody')
    if len(docstable) == 0:
        capandclaim.append("None")
        capandclaim.append("None")
        capandclaim.append("Not available")
    else:
        firstdocrow = casedocketsoup.find_all('tr')[-1]
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
        if '(Opens new window)' in firstdoc:
            firstdoc = firstdoc.replace('(Opens new window)', '')
        capandclaim.append(firstdoc)
        firstdocdate = firstdocrow.find_all('td')[-1].get_text(strip=True)
        capandclaim.append(firstdocdate)
    if capandclaim[1] == 'Claim':
        claimrow = casedocketsoup.find_all('tr')[-1]
        claimcell = claimrow.find_all('td')[1]
        claimlink = claimcell.a
        claimpage = claimlink.get('href')
        claimurl = 'https://dockets.ccb.gov' + claimpage
        capandclaim.append(claimurl)
    else:
        capandclaim.append(digforclaimurl(docketurl))
    return capandclaim

# to retrieve claimant, respondent, law firm, etc.
def getcasedetails(claimurl, fullcaption):
    details = []
    res4 = requests.get(claimurl)
    res4.raise_for_status()
    claimsoup = bs4.BeautifulSoup(res4.text, 'lxml')
    typesdiv = claimsoup.find(attrs={'data-field' : 'typeFlags'})
    claims = ''
    stringoftypes = typesdiv.get_text(strip=True)
    if 'for infringement' in stringoftypes:
        claims = claims + 'infringement'
    if '512' in stringoftypes:
        claims = claims + '-DMCA'
    if 'noninfringe' in stringoftypes:
        claims = claims + '-noninfringement'
    details.append(claims)
    smallerdiv = claimsoup.find(attrs={'data-field' : 'smallClaim'})
    smaller = smallerdiv.get_text(strip=True)
    details.append(smaller)
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
    citydiv = claimsoup.find(attrs={'data-field' : 'partialAddress'})
    if len(citydiv.find_all('br')) > 0:
        cityplusjunk = citydiv.contents
        claimantcity = cityplusjunk[0].get_text(strip=True) + ", " + cityplusjunk[2].get_text(strip=True)
    else:
        claimantcity = citydiv.get_text(strip=True)
    details.append(claimantcity)
    splitcity = claimantcity.split(",")
    if splitcity[1][1:] in listofstates:
        claimantcountry = "USA"
    else:
        claimantcountry = splitcity[1][1:]
    details.append(claimantcountry)
    return details

# to retrieve details that are only asked of the claimant in infringement claims
def getinfringementdetails(claimurl):
    infrdetails = []
    res4 = requests.get(claimurl)
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

# to get the latest doc filed in a case, and the date of its filing
def getlatest(docketurl):
    res = requests.get(docketurl)
    res.raise_for_status()
    casedocketsoup = bs4.BeautifulSoup(res.text, 'lxml')
    latestinfo = []
    docstable = casedocketsoup.find_all('tbody')
    if len(docstable) == 0:
        latestinfo = ["None", "None"]
    else:
        mostrecentrow = casedocketsoup.find_all('tr')[1]
        lastdoccell = mostrecentrow.find_all('td')[1]
        lastdoc = ''
        if len(lastdoccell.find_all("span", class_=re.compile("document-restricted"))) != 0:
            ourspan = lastdoccell.find("span", class_=re.compile("document-restricted"))
            lastdoc = ourspan.get_text(strip=True)
        elif len(lastdoccell.find_all("span", class_=re.compile("document-link-title"))) !=0:
            ourspan = lastdoccell.find("span", class_=re.compile("document-link-title"))
            srspan = ourspan.find(class_='sr-only')
            srspan.decompose()
            lastdoc = ourspan.get_text(strip=True)
        else:
            lastdoc = lastdoccell.get_text(strip=True)
        if '(Opens new window)' in lastdoc:
            lastdoc = lastdoc.replace('(Opens new window)', '')
        if 'Toggle tooltip (Keyboard shortcut: "Crtl+Enter" opens and "Escape" or "Delete" dismiss)' in lastdoc:
            lastdoc = lastdoc.replace('Toggle tooltip (Keyboard shortcut: "Crtl+Enter" opens and "Escape" or "Delete" dismiss)', '')
        latestinfo.append(lastdoc)
        lastdocdate = mostrecentrow.find_all('td')[-1].get_text(strip=True)
        latestinfo.append(lastdocdate)
    return latestinfo

print("Getting new cases")

# Collect data for cases new this week, and recent cases where we dedn't have a claim for before
for docket in docketsweneed:
    print(docket)
    newcase = {}
    newcase["Docket No."] = docket
    docketurl = "https://dockets.ccb.gov/case/detail/" + docket
    newcase["Docket URL"] = docketurl
    capandclaiminfo = getcapandclaim(docketurl)
    newcase["Caption"] = capandclaiminfo[0]
    newcase["Oldest doc"] = capandclaiminfo[1]
    newcase["Oldest doc date"] = capandclaiminfo[2]
    newcase["Latest doc"] = 'temp'
    newcase["Latest doc date"] = 'temp'
    newcase["Claim URL"] = capandclaiminfo[3]
    # Make sure we have a claim link before trying to go to it
    if capandclaiminfo[3][0:4] == 'http':
        casedetails = getcasedetails(capandclaiminfo[3], capandclaiminfo[0])
    else:
        casedetails = ["Not available", "Not available", "See caption", "Not available", "See caption", "Not available", "Not available", "Not available"]
    newcase["Claim types"] = casedetails[0]
    newcase["Smaller?"] = casedetails[1]
    newcase["Claimant"] = casedetails[2]
    newcase["Claimant law firm"] = casedetails[3]
    newcase["Respondent"] = casedetails[4]
    newcase["Relief sought"] = casedetails[5]
    newcase["Claimant city"] = casedetails[6]
    newcase["Claimant country"] = casedetails[7]
    if newcase["Claim types"][0:12] == "infringement":
        infrdetails = getinfringementdetails(capandclaiminfo[3])
    else:
        infrdetails = ["NA", "NA", "NA", "NA", "NA"]
    newcase["Work registered?"] = infrdetails[0]
    newcase["Reg effective date"] = infrdetails[1]
    newcase["Work type"] = infrdetails[2]
    newcase["Description of work"] = infrdetails[3]
    newcase["Description of infringement"] = infrdetails[4]
    casedatalist.append(newcase)

# Sort, to slot in the newly grabbed cases in the expected order
casedatalist.sort(key=lambda x: x['Docket No.'], reverse=True)

print("Fetching latest docs filed")
# Update Latest doc
for case in casedatalist:
    if case["Docket No."] not in closedcaseslist:
        print(case["Docket No."])
        latestinfo = getlatest(case["Docket URL"])
        case["Latest doc"] = latestinfo[0]
        case["Latest doc date"] = latestinfo[1]

with open('casedata.csv', 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames = casedatalist[0].keys())
    writer.writeheader()
    writer.writerows(casedatalist)
csvfile.close()
