#!/usr/bin/python3

#Creater Sam Smedts
from GmailWrapper import GmailWrapper

import RPi.GPIO as GPIO
import time
import serial
import email
import json
import time
import timeit
import pickle

time.sleep(1)

version = '1.2 - 060522'

ser = serial.Serial(port='/dev/serial0', baudrate=19200)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

buttonPin = 23
GPIO.setup(buttonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

HOSTNAME = 'imap.gmail.com'
USERNAME = 'foodbarbrechtbestelling@gmail.com'
PASSWORD = 'jwfj vckp qpeq jema'# App code aangemaakt in Gmail settings

gmailWrapper = GmailWrapper(HOSTNAME, USERNAME, PASSWORD)

algemeneBestellingCounter = 30
papierOp = 400
huidigeDiameterRol = 30
pickle.dump((algemeneBestellingCounter, huidigeDiameterRol, papierOp), open("newsave.p","wb"))

PickleFileVar = pickle.load( open("newsave.p","rb")) # read the counter from file
#print(PickleFileVar)
algemeneBestellingCounter = PickleFileVar[0]
#print('algemeneBestellingCounter: ')
#print(algemeneBestellingCounter)
#papierOp = 960 # gemiddelde lengte per bestelling en klant info 5cm --> papier = 50m => 5000 cm => 1000 bestellingen per rol ongeveer 
#pickle.dump(papierOp, open("save.p","wb"))
huidigeDiameterRol = PickleFileVar[1]
#print('huidigeDiameterRol: ')
#print(huidigeDiameterRol)

papierOp = PickleFileVar[2]
#print('papierOp: ')
#print(papierOp)

volleDiameterRol = 36 # diameter rol
#huidigeDiameterRol = 36


overigeBestellingMogelijk = papierOp - algemeneBestellingCounter
print('overigeBestellingMogelijk: ')
print(overigeBestellingMogelijk)


papierFlag = False # om te voorkomen dat de papier waarschuwing meer dan één keer uit de printer komt

startMessage = False # om te verkomen dat de start message elke keer geprint wordt 


def printLine(textVar):
    
    textVarSize = len(textVar)
    
    if textVarSize < 32:
        # de text is kleiner al één regel op de printer
        overigChar = 32-textVarSize   #hoeveel buffer is er nog over
        ser.write(textVar.encode()) # print de eerst regel text
        for i in range(overigChar):
            ser.write(b' ')           #opvullen met lege spaties in de buffer
    elif textVarSize == 32:
        # de text is exact de buffer grote 
        ser.write(textVar.encode()) # De text kan meteen worden geprint
    else:
        # de text is groter dan de buffer opsplitsen
        
        # test over twee lijnen
        overigText = textVarSize-32  #Hoeveel karaters op de volgende lijn
        overigChar = 32-overigText  #hoeveel buffer is er nog over
        ser.write(textVar.encode()) # De text kan worden geprint eerst een volle lijn maar dan nog een stuk in de buffer
        for i in range(overigChar):
            ser.write(b' ')           #opvullen met lege spaties in de buffer zodat de tweede lijn ook zichtbaar wordt
    
    #ser.write(b'                                ') # buffer volmaken
            
def printSterLijn(aantal):
    for i in range(aantal):
        sterLijn = '********************************'
        printLine(sterLijn)
        
def printCijferLijn(aantal):
    for i in range(aantal):
        cijferLijn = '12345678901234567890123456789012'
        printLine(cijferLijn)
        
def printLegeLijnen(aantal):
    for i in range(aantal):
        legeLijn = '                                '
        printLine(legeLijn)
    
def DebugBuffer(aantal):
    global algemeneBestellingCounter
    # Er is iets mis met de buffer
    
    #algemene counter optellenh
    algemeneBestellingCounter += 1
    
    print("debugbuffer start")
    printCijferLijn(1)
    printLegeLijnen(3)
    for i in range(aantal):
        ser.write(b' ')           #opvullen met lege spaties in de buffer zodat de tweede lijn ook zichtbaar wordt
        
    ser.write(b'                                ') # buffer volmaken
    printCijferLijn(1)
    printLegeLijnen(4)
    ser.write(b'                                ') # buffer volmaken
    
def EmailAlignment():
    #gmailAlignment = GmailWrapper(HOSTNAME, USERNAME, PASSWORD)
    #id_debug = gmailAlignment.getIdsBySubject('debug')
    id_debug = gmailWrapper.getIdsBySubject('debug')
    
    if(len(id_debug)>0):
        #Er is debug code ontvangen
        print('debug code aangekomen')
        for debugId in id_debug:
            
            debugmessage = gmailWrapper.getResponsById(debugId)
            debugmessageBody = str(debugmessage[debugId][b'RFC822']) #SPLIT20
            
            print(debugmessageBody)
            #Splitsen op SPLIT - opdelen in verschillende blokken eerste blok klant info en dan bestelling blokken 
            debugmessageSplit_1 = debugmessageBody.split('SPLIT')
            debugmessageSplit_1.pop(0) # Eerst deel met onnodige info verwijderen
            debugInfo = str(debugmessageSplit_1[0])
            print(debugInfo)
            debugInfo = int(debugInfo)
            
            DebugBuffer(debugInfo)
    else:
        print('Geen debug code aangekomen')
            
def printMessagedecoder(messageID):
    global algemeneBestellingCounter
    
    message = gmailWrapper.getResponsById(messageID)
    messageBody = str(message[messageID][b'RFC822'])
    #print(messageBody)
    
    #Splitsen op SPLIT - opdelen in verschillende blokken eerste blok klant info en dan bestelling blokken 
    messageSplit_1 = messageBody.split('SPLIT')
    #print(messageSplit_1)
    messageSplit_1.pop(0) # Eerst deel met onnodige info verwijderen
    #print(len(messageSplit_1))
    #print(messageSplit_1[0])  # voorbeeld {"Naam":Jan,"Achternaam":,"Adres":{"Straat":Schotensteenweg,"Huisnummer":219,"Zip":,"Gemeente":},"Telefoon":0485638019,"Email":samsmedts@gmail.com,"BTW":,"Leveringsmethode":Afhalen in de zaak,"Leveringsdatum":28/04/2022,"Uur":11u,"Omschrijving":test jan,"Totaal":0.00}\r\n\r\n\t\t{"ProductAantal":1,"ProductNaam":Jonge kaas,"ProductType":undefined,"BroodType":(meergranen),"ProductPrijs":2.70,"ProductTotaal":2.70,"ProductGeen":-,"ProductExtra":Mayonaise}\r\n\t\t\t\t{"ProductAantal":1,"ProductNaam":Philadelphia,"ProductType":broodje klein,"BroodType":(),"ProductPrijs":2.80,"ProductTotaal":2.80,"ProductGeen":-,"ProductExtra":tomaat}\r\n\t\t\r\n\r\n'
    
    #klanten info
    klantInfo = str(messageSplit_1[0])
    klantInfo = klantInfo[:-12]
    print(klantInfo) #voorbeeld {"Naam":pat,"Achternaam":,"Adres":{"Straat":Schotensteenweg,"Huisnummer":219,"Zip":,"Gemeente":},"Telefoon":02343499445,"Email":samsmedts@gmail.com,"BTW":,"Leveringsmethode":Afhalen in de zaak,"Leveringsdatum":28/04/2022,"Uur":10u,"Omschrijving":test,"Totaal":0.00}
    
    messageSplit_1.pop(0) # Klanten info verwijderen uit de lijst
    #print(messageSplit_1)
    #bestellingen
    bestellingen = []
    counter = 1
    for bestelling in messageSplit_1:
        bestelInfo = str(bestelling)
        if counter == len(messageSplit_1):
            bestelInfo = bestelInfo[:-17]
        else:
            bestelInfo = bestelInfo[:-12]
        #print(bestelInfo) # voorbeeld {"ProductAantal":1,"ProductNaam":Jonge kaas,"ProductType":undefined,"BroodType":(wit),"ProductPrijs":2.70,"ProductTotaal":2.70,"ProductGeen":-,"ProductExtra":-}
        bestellingen.append(bestelInfo) # elke bestelling toevoegen aan de lijst bestellingen 
        counter += 1
    print(bestellingen)
    
    #Json omzetten - klant en info er uit halen 
    klantObject = json.loads(klantInfo)
    #print(klantObject)
    klantOrderid = klantObject["Orderid"]
    klantOrderidZin = 'OrderID: ' + klantOrderid
    klantNaam = klantObject["Naam"]
    klantAchternaam = klantObject["Achternaam"]
    klantStraat = klantObject["Adres"]["Straat"]
    klantHuisnummer = klantObject["Adres"]["Huisnummer"]
    klantAdresZin = klantStraat + ' ' + klantHuisnummer
    klantZip = klantObject["Adres"]["Zip"]
    klantGemeente = klantObject["Adres"]["Gemeente"]
    klantGemeenteZin = klantZip + ' ' + klantGemeente
    klantTelefoon = klantObject["Telefoon"]
    klantEmail = klantObject["Email"]
    klantBTW = klantObject["BTW"]
    klantLeveringsmethode = klantObject["Leveringsmethode"]
    klantLeveringsdatum = klantObject["Leveringsdatum"]
    klantUur = klantObject["Uur"]
    klantUurZin = 'Uur: '+ klantUur
    klantOmschrijving = klantObject["Omschrijving"]
    klantTotaal = klantObject["Totaal"]
    KlantTotaalZin = 'Eindtotaal: ' + klantTotaal
    stippelLijn = '--------------------------------'
    halfStippelLijn = '      -------------------       '
    volleLijn = '________________________________'
    halfVolleLijn= '      ___________________       '
    hashLijn = '################################'
    legeLijn = '                                '
    sterLijn = '********************************'
    
    printLine(hashLijn)
    #printLine(legeLijn)
    printLine(klantOrderidZin)
    printLine(klantNaam)
    printLine(klantTelefoon)
    printLine(sterLijn)
    #printLine(legeLijn)
    
    printLine(klantLeveringsmethode)
    printLine(klantAdresZin)
    printLine(klantGemeenteZin)
    printLine(klantLeveringsdatum)
    printLine(klantUurZin)
    if(klantOmschrijving == "1"):
        print("Er is een melding")
        OmschrijvingsVlag = "!!! MET BIJHORENDE MELDING !!!"
        printLine(OmschrijvingsVlag)
    printLine(sterLijn)
    #printLine(legeLijn)
    
    #algemene counter optellen
    algemeneBestellingCounter += 1
    
    #bestellingen printen
    counterBestelling = 1
    for bestelling in bestellingen:
        bestellingObject = json.loads(bestelling)
        productAantal = bestellingObject["ProductAantal"]
        productNaam = bestellingObject["ProductNaam"]
        productType = bestellingObject["ProductType"]
        
        if productType == 'undefined':
            productType = 'broodje groot'
            
        productBroodType = bestellingObject["BroodType"]
        productPrijs = bestellingObject["ProductPrijs"]
        productTotaal = bestellingObject["ProductTotaal"]
        productGeen = bestellingObject["ProductGeen"]
        productExtra = bestellingObject["ProductExtra"]
        
        productZin = productAantal + 'x ' + productNaam
        productTypeZin = productType + ' ' + productBroodType
        productGeenZin = 'Geen: ' + productGeen
        productExtraZin = 'Extra: ' + productExtra
        productEenheidPrijs = 'Prijs: ' + productPrijs
        productTotaalPrijs = 'Totaal: ' + productTotaal
        
        
        printLine(legeLijn)
        printLine(productZin)
        printLine(productTypeZin)
        printLine(productGeenZin)
        printLine(productExtraZin)
        printLine(productEenheidPrijs)
        printLine(productTotaalPrijs)
        #printLine(legeLijn)
        
        #algemene counter optellen
        algemeneBestellingCounter += 1
        
        if counterBestelling < len(bestellingen):
            printLine(volleLijn)
        
        counterBestelling += 1
    
    printLine(volleLijn)
    printLine(KlantTotaalZin)
    printLegeLijnen(4)
    
    time.sleep(1)

    
def EmailByGmail():
    #gmailWrapper = GmailWrapper(HOSTNAME, USERNAME, PASSWORD)
    ids = gmailWrapper.getIdsBySubject('Nieuwe Bestelling')

    
    if(len(ids)>0):
        #Er is een nieuwe bestelling binnengekomen
        print('Een nieuwe bestelling gevonden')
        for bestelId in ids:
            printMessagedecoder(bestelId)
    else:
        # Er zijn geen nieuwe bestellingen
        print("Geen nieuwe bestelling gevonden")
    
def knopEersteKeerIngedrukt():
    printLine('knop is ingedrukt')
    aantalLijnen = 1
    for i in range(aantalLijnen):
        legeLijn = '                                '
        printLine(legeLijn)
        time.sleep(1)
        if (i == aantalLijnen-1):
            printLine('60sec knop registratie')
            printLegeLijnen(1)
            
def eindeDebug():
    #het heeft geprint maar er zit nog éé karakter in de buffer dus nu een debug
    DebugBuffer(31)
    sterLijn = '********************************'
    printLine('Uitlijning correct**************')
    printLegeLijnen(5)

def uitlijningProcedure():
    startTimer = timeit.default_timer()
    waitTime = 60
    counterKaraters=0 #de hoeveelheid karakters de lijn moet opschuiven
    stopTimer = timeit.default_timer()
    diffTime = stopTimer-startTimer
    while diffTime <= waitTime:
        buttonValue = GPIO.input(buttonPin)
        # zolang de timer niet op 60 seconden komt zal de drukknop geteld worden   
        if(buttonValue == False):
            while buttonValue == False:
                buttonValue = GPIO.input(buttonPin)
                #ga pas verder als de knop wordt losgelaten
                #print('wacht tot de knop wordt losgelaten')
            counterKaraters += 1
            print(counterKaraters)
            ser.write(b' ') # bij elke drukknop een karakter in de buffer bij
                
        stopTimer = timeit.default_timer()
        diffTime = stopTimer-startTimer
        time.sleep(0.2)
            
    eindeDebug()

def CheckLastmessage(aantalBerichtTerug):
    #gmailWrapper = GmailWrapper(HOSTNAME, USERNAME, PASSWORD)
    ids = gmailWrapper.getIdsBySubjectSeen('Nieuwe Bestelling')
  
    if(len(ids)>0):
        #Er is een nieuwe bestelling binnengekomen
        print('Gevraagde bestelling met ID gevonden')
        print(ids)
        lastmessage = ids[-aantalBerichtTerug]
        printMessagedecoder(lastmessage)
    else:
        print('Gevraagde bestelling met ID niet gevonden')


def EmailLastMessageChecker():
    print('Check de laatste bestelling')
    id_debug = gmailWrapper.getIdsBySubject('terughalen')
    #print(id_debug)
    
    if(len(id_debug)>0):
        #Er is debug code ontvangen
        print('Er is een laatste bestelling aanvraag gevonden')
        for debugId in id_debug:
            
            debugmessage = gmailWrapper.getResponsById(debugId)
            debugmessageBody = str(debugmessage[debugId][b'RFC822']) #SPLIT20SPLIT
            
            #print(debugmessageBody)
            #Splitsen op SPLIT - opdelen in verschillende blokken eerste blok klant info en dan bestelling blokken 
            debugmessageSplit_1 = debugmessageBody.split('SPLIT')
            debugmessageSplit_1.pop(0) # Eerst deel met onnodige info verwijderen
            debugInfo = str(debugmessageSplit_1[0])
            print(debugInfo)
            debugInfo = int(debugInfo)
            
            CheckLastmessage(debugInfo)
    else:
        print('Er is geen laatste bestelling aanvraag gevonden')
    
def EmailDiameterRol():
    global huidigeDiameterRol
    print('Check email op papier rol diameter')
    id_diameter = gmailWrapper.getIdsBySubject('diameter')
    #print(id_debug)
    
    if(len(id_diameter)>0):
        #Er is debug code ontvangen
        print('Er is een email met diameter gevonden')
        for diameterId in id_diameter:
            
            diametermessage = gmailWrapper.getResponsById(diameterId)
            diametermessageBody = str(diametermessage[diameterId][b'RFC822']) #SPLIT15SPLIT 15 is de diameter 
            
            #print(debugmessageBody)
            #Splitsen op SPLIT - opdelen in verschillende blokken eerste blok klant info en dan bestelling blokken 
            diametermessageSplit_1 = diametermessageBody.split('SPLIT')
            diametermessageSplit_1.pop(0) # Eerst deel met onnodige info verwijderen
            diameterInfo = str(diametermessageSplit_1[0])
            #print(diameterInfo)
            diameterInfo = int(diameterInfo)
            
            #update de huidige diameterstand
            huidigeDiameterRol = diameterInfo
            
            print('Nieuwe diameter:')
            print(huidigeDiameterRol)
            # nieuwe papierOp berekenen en updaten
            OverigeBestellingenBerekenen()
            
    else:
        print('Er is geen diameter mail gevonden')

def PaperCheck():
    global papierFlag
    global algemeneBestellingCounter
    # is de huidige counter gelijk of groter dan de variabele
    if (algemeneBestellingCounter >= papierOp):
        print('Papier is bijna op!!')
        # print een waarschuwing als de paperFlag niet gelijk is aan True
        if (papierFlag == False):
            # print de waarschuwing
            printSterLijn(2)
            printLine('!!! PAPIER BIJNA OP !!!')
            printLine('Kijk het papier na!')
            printSterLijn(2)
            printLegeLijnen(4)
            
            # zet de Flag op 
            papierFlag = True
            
        else:
            # waarschuwing is al een keer geprint - Flag staat op True 
            print('Waarschuwing is al een keer geprint')
        
    else:
        print('Nog voldoende papier')


def OverigeBestellingenBerekenen():
    global papierOp
    global algemeneBestellingCounter
    # 1mm doorsnede => 27 bestellingen
    bestellingPerMm = 27
    print('Bestelling over op rol worden berekend a.d.h.v. nieuwe diameter')
    huidigeBestellingOver = huidigeDiameterRol * bestellingPerMm # vb 20mm diameter * 27 bestelling => 540 bestellingen
    
    #update de variabel papierOp dat de couter steeds checkt
    print('papierOp variabele wordt geupdate')
    papierOp = huidigeBestellingOver
    
    #bestellings counter terug resetten omdat het papier is geupdate
    print('algemeneBestellingCounter wordt terug op 0 gezet')
    algemeneBestellingCounter = 0
    
    if (huidigeDiameterRol == 36):
        printSterLijn(2)
        printLine('PAPIER UPDATE')
        printLine('Nieuwe volle rol (36 mm')
        printLine('Bestellings counter reset')
        printLine('Aantal Prints over:')
        printLine(str(papierOp))
        printSterLijn(2)
        printLegeLijnen(4)
    else:
        printSterLijn(2)
        printLine('PAPIER UPDATE')
        printLine('Nieuw papier diameter:')
        printLine(str(huidigeDiameterRol))
        printLine('Bestellings counter reset')
        printLine('Aantal Prints over:')
        printLine(str(papierOp))
        printSterLijn(2)
        printLegeLijnen(4)
        
def LegeLijnDebug():
    print(' ')
    print('---')
    print(' ')

def UpdateOverigBestellingen():
    print('Update overige prints...')
    overigeBestellingMogelijk = papierOp - algemeneBestellingCounter
    print('Overige prints mogelijk:')
    print(overigeBestellingMogelijk)
    
def StartMessage():
    global version
    
    #BestellingenMogelijk = algemeneBestellingCounter / 2
    printSterLijn(2)
    printLine('Welkom, printer wordt opgestart.')
    printSterLijn(1)
    printLine('PRINTER INFO')
    printLegeLijnen(1)
    
    printLine('Software versie:')
    printLine(version)
    printLegeLijnen(1)
    
    printLine('Print teller:')
    printLine(str(algemeneBestellingCounter))
    printLegeLijnen(1)
    
    #printLine('Bestelling mogelijk:')
    #printLine(str(BestellingenMogelijk))
    #printLegeLijnen(1)
    
    printLine('Overige prints mogelijk:')
    printLine(str(overigeBestellingMogelijk))
    printLegeLijnen(1)
    
    printLine('Uitlijning:')
    printCijferLijn(1)
    printLegeLijnen(1)
    printSterLijn(2)
    printLegeLijnen(4)
    
# MAIN LOOP -----------------------------------------       
while True:
    if (startMessage == False):
        # eerste start bericht printen
        StartMessage()
        print('start bericht wordt geprint')
        startMessage = True
        LegeLijnDebug()
        
    #check voor debug email
    EmailAlignment()
    LegeLijnDebug()
    #check of de papier diameter moet worden geupdate worden
    EmailDiameterRol()
    LegeLijnDebug()
    #check of er laatst bestelling moet geprint worden 
    EmailLastMessageChecker()
    LegeLijnDebug()
    #check bestellingen
    EmailByGmail()
    LegeLijnDebug()
    
    #PapierCheck
    PaperCheck()
    LegeLijnDebug()
    
    UpdateOverigBestellingen()
    print('variabelen opslagen in pickle file')
    pickle.dump((algemeneBestellingCounter, huidigeDiameterRol, papierOp), open("newsave.p","wb"))
    
    sleepTime = 20
    for i in range(sleepTime+1):
        print(i)
        #check buttonpress
        buttonValue = GPIO.input(buttonPin)
        if(buttonValue == False):
            # check laatste email
            print('check laatste mail')
            CheckLastmessage(1)
            #print("knop is ingedrukt - start uitlijnings procedure")
            # de knop werd ingedrukt - laat dit wetten door te printen
            #knopEersteKeerIngedrukt()
            
            #procedure wordt gestart 
            #uitlijningProcedure()
        time.sleep(1)
    
