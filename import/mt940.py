import re
import sys
import getopt
import datetime
from decimal import Decimal

# parser states
IN_HEADER = 1
MESSAGE_HEADER = 2
RECORDS = 3
MESSAGE_CLOSE = 4

balance_re = re.compile(r"([CD])([0-9]{2})([0-9]{2})([0-9]{2})(\D{3})([0-9,]{1,15})")
record_re = re.compile(r"([0-9]{2})([0-9]{2})([0-9]{2})([0-9]{0,4})([CD])(\D?)([0-9,]{1,15})N(.{3})([\w\s]{0,16})(\/\/[\w\s]{16})?(.*)")

# references:
# http://www.ing.nl/Images/MT940_Technische_handleiding_Mijn_ING_Zakelijk_tcm7-117274.pdf
# http://architome.nl/mt940/documents/SW4CORP_FINIMPGUIDE_June2008_MT_940_SEPA.pdf

class MT940:
    """  """
    

    def __init__(self,data=""):
        self.headers = []
        self.messages = []

        self.set_data(data)


    def set_data(self,data):
        self.rawdata = data
        return self.parse_lines( data.split('\r\n') )


    def parse_lines(self,lines):
        state = IN_HEADER
        currentmsg = None 
        current = None

        for line in lines:

            if state==IN_HEADER:
                self.headers.append(line)
                if line =='940 00' or line == ':940:' or line == '940':
                    state=MESSAGE_HEADER
            else:
                m = re.match(r":([0-9]{2}[A-Z]?):(.*)", line)
                if m:
                    field = m.group(1)
                    data = m.group(2)

                    if field == '20':
                        state = MESSAGE_HEADER
                        if currentmsg:
                            if current:
                                currentmsg.append(current)
                                current = None
                            self.sets.append(currentmsg)
                        currentmsg = MT940Message()
                        currentmsg.take_data(field, data)
                    elif field in ['25','28C','60F', '62F']:
                        currentmsg.take_data(field, data)
                        if field == '62F':
                            state = MESSAGE_CLOSE

                    elif field in ['61']:
                        state = RECORDS
                        if current:
                            currentmsg.records.append(current)
                        if not currentmsg:
                            currentmsg = MT940Message()
                        current = MT940Record()
                        current.take_data(field, data)
                    else:
                        if state == MESSAGE_CLOSE:
                            currentmsg.take_data(field, data)
                        else:
                            current.take_data(field, data)
        # last one
        if currentmsg and current:
            currentmsg.records.append(current)
        if currentmsg:
            self.messages.append(currentmsg)


    def __str__(self):
        return '<MT940 [' + ", ".join([str(x) for x in self.messages ])  + ']>';

class MT940Message:
    def __init__(self):
        self.transaction_reference = ""
        self.acccount_id = ""
        self.seq = ""
        self.open_date = None
        self.open_amount = None
        self.records=[]
        self.info = ""

    def take_data(self,field,data):
        if field == '20':
            self.transaction_reference = data
        elif field == '25':
            self.account_id = data
        elif field == '28C' or field == '28':
            self.seq = data
        elif field == '60F':
            m = balance_re.match(data)
            if m:
                (decr, yy,mm,dd, curcode, amount ) = m.groups()
                self.open_date = datetime.date(2000 + int(yy), int(mm), int(dd))
                self.open_amount = Decimal(amount.replace(',','.'))
                self.open_currency = curcode
                if decr == 'D':
                    self.open_amount = -self.open_amount
        elif field == '62F':
            m = balance_re.match(data)
            if m:
                (decr, yy,mm,dd, curcode, amount ) = m.groups()
                self.close_date = datetime.date(2000 + int(yy), int(mm), int(dd))
                self.close_amount = Decimal(amount.replace(',','.'))
                self.close_currency = curcode
                if decr == 'D':
                    self.close_amount = -self.close_amount

        elif field == '86':
            self.info += data


    def __str__(self):
        return '<MT940Message [open: '  + str(self.open_date)+ " " +self.open_currency+ str(self.open_amount) + " ; ".join([str(x) for x in self.records ])  + '; close: '+ str(self.close_date) + ' '+self.close_currency+str(self.close_amount)+']>';



class MT940Record:
    def __init__(self):
        self.amount = 0
        self.debitcredit = 'credit'
        self.fundscode = "" 
        self.date = None
        self.entrydate = None
        self.reference = ""
        self.servicer_reference = ""
        self.additional = ""
        self.description = []

    def take_data(self, field, data):
        
        if field == '61':
            m = record_re.match(data)
            if m:
                (yy,mm,dd, entrydate, decr, fundscode, amount, transtype, ref, accref, additional ) = m.groups()
                self.date = datetime.date(2000 + int(yy), int(mm), int(dd))
                if entrydate:
                    self.entrydate = datetime.date(2000 + int(yy), int(entrydate[0:2]), int(entrydate[2:]))
                self.debitcredit =  'credit' if decr=='C' else 'debit'
                self.amount = Decimal(amount.replace(',','.'))
                self.fundscode = fundscode
                self.transactiontype = transtype
                self.reference = ref
                self.servicer_reference = accref
                self.additional = additional

            

            
        elif field == '86':
            self.description.append(data)
        
        

    def __str__(self):
        return '<MT940Record '+ self.debitcredit+ str(self.amount) + '; '+ str(self.date) + '; '+ self.reference + ' ; '+ self.additional + '; ' + ", ".join(self.description)  + '>';



def main(argv=None):
    if argv is None:
      argv = sys.argv
  
    #try:
    data = open(argv[1], 'rb').read()
    mt940 = MT940(data)
    print mt940



if __name__ == "__main__":
  sys.exit(main())
