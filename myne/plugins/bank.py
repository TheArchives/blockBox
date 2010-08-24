#    iCraft is Copyright 2010 both
#
#    The Archives team:
#                   <Adam Guy> adam@adam-guy.com AKA "Adam01"
#                   <Andrew Godwin> andrew@aeracode.org AKA "Aera"
#                   <Dylan Lukes> lukes.dylan@gmail.com AKA "revenant"
#                   <Gareth Coles> colesgareth2@hotmail.com AKA "gdude2002"
#
#    And,
#
#    The iCraft team:
#                   <Andrew Dolgov> fox@bah.org.ru AKA "gothfox"
#                   <Andrew Horn> Andrew@GJOCommunity.com AKA "AndrewPH"
#                   <Brad Reardon> brad@bradness.co.cc AKA "PixelEater"
#                   <Clay Sweetser> CDBKJmom@aol.com AKA "Varriount"
#                   <James Kirslis> james@helplarge.com AKA "iKJames"
#                   <Jason Sayre> admin@erronjason.com AKA "erronjason"
#                   <Joseph Connor> destroyerx100@gmail.com AKA "destroyerx1"
#                   <Nick Tolrud> ntolrud@yahoo.com AKA "ntfwc"
#                   <Noel Benzinger> ronnygmod@gmail.com AKA "Dwarfy"
#                   <Randy Lyne> qcksilverdragon@gmail.com AKA "goober"
#                   <Willem van der Ploeg> willempieeploeg@live.nl AKA "willempiee"
#
#    iCraft is licensed under the Creative Commons
#    Attribution-NonCommercial-ShareAlike 3.0 Unported License. 
#    To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#    Or, send a letter to Creative Commons, 171 2nd Street,
#    Suite 300, San Francisco, California, 94105, USA.

from myne.plugins import ProtocolPlugin
from myne.decorators import *
import cPickle #Now using the MUCH faster, optimized cPickle
import logging

class MoneyPlugin(ProtocolPlugin):
    
    commands = {
        "bank":     "commandBalance",
        "balance":     "commandBalance",
        "pay":        "commandPay",
        "setbank":        "commandSetAccount",
        "removebank":    "commandRemoveAccount",
    }

    money_logger = logging.getLogger('TransactionLogger')
    
    #System methods, not for commands
    def loadBank(self):
        file = open('balances.dat', 'r')
        bank_dic = cPickle.load(file)
        file.close()
        return bank_dic
    
    def dumpBank(self, bank_dic):
        file = open('balances.dat', 'w')
        cPickle.dump(bank_dic, file)
        file.close()
    
    def commandBalance(self, parts, byuser, overriderank):    
        "/bank - Guest\nAliases: balance\nFirst time: Creates you a account.\nOtherwise: Checks your balance."
        bank = self.loadBank()
        user = self.client.username.lower()
        if user in bank:
            self.client.sendServerMessage("Welcome to the Bank!")
            self.client.sendServerMessage("Your current balance is M%d." % bank[user])
        else:
            bank[user] = 5000
            self.dumpBank(bank)
            self.client.sendServerMessage("Welcome to the Bank!")
            self.client.sendServerMessage("We have created your account for %s." % user)
            self.client.sendServerMessage("Your balance is now %d Minecash." % bank[user])
            self.money_logger.info("%s created a new account!" % user)

    @director_only
    def commandSetAccount(self, parts, byuser, overriderank):
        "/setbank username amount - Director\nEdits Bank Account"
        if len(parts) != 3:
            self.client.sendServerMessage("Syntax: /set <target> <amount>")    
            return False
        bank = self.loadBank()
        target = parts[1]
        if target not in bank:
            self.client.sendServerMessage("Invalid target")
            return False
        try:
            amount = int(parts[2])
        except ValueError:
            self.client.sendServerMessage("Invalid amount")
            return False
        if self.client.username.lower() in bank:
            bank[target] = amount
            self.dumpBank(bank)
            self.client.sendServerMessage("Set player balance to M%d" % amount)
        else:
            self.client.sendServerMessage("You don't have bank account, use /bank to make one!")
            
    def commandPay(self, parts, byuser, overriderank):
        "/pay username amount - Guest\nThis lets you send money to other people."
        if len(parts) != 3:
            self.client.sendServerMessage("/pay <target> <amount>")
            return False
        user = self.client.username.lower()
        target = parts[1].lower()
        bank = self.loadBank()
        if target not in bank:
            self.client.sendServerMessage("Error: Invalid Target")
            return False
        try:
            amount = int(parts[2])
        except ValueError:
            self.client.sendServerMessage("Error: Invalid Amount")
            return False
        if user not in bank:
            self.client.sendServerMessage("Error: You don't have an account.")
            self.client.sendServerMessage("Notice: Might want to do /bank")
            return False
        elif amount < 0 and not self.client.isDirector():
            self.client.sendServerMessage("Error: Amount must be positive.")
            return False        
        elif amount > bank[user] or amount < -(bank[target]):
            self.client.sendServerMessage("Error: Not enough Minecash.")
            return False
        elif user in bank:
            bank[target] = bank[target] + amount
            bank[user] = bank[user] - amount
            self.dumpBank(bank)
            self.client.sendServerMessage("You sent M%d." % amount)
            self.money_logger.info("%(user)s sent %(amount)d to %(target)s" % {'user': user, 'amount': amount, 'target': target})
            #factory.usernames uses all lowercased for some reason
            if target in self.client.factory.usernames:
                self.client.factory.usernames[target].sendServerMessage("You received M%(amount)d from %(user)s." % {'amount': amount, 'user': user})

    @director_only
    def commandRemoveAccount(self, parts, byuser, overriderank):
        "/removebank username - Director\nRemoves Bank Account"
        if len(parts) != 2:
            self.client.sendServerMessage("Syntax: /remove <target>")    
            return False
        bank = self.loadBank()
        target = parts[1]
        if target not in bank:
            self.client.sendServerMessage("Invalid target")
            return False
        bank.pop(target)
        self.dumpBank(bank)
        self.client.sendServerMessage("Account Deleted")
