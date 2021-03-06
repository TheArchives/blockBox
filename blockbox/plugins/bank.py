# blockBox is copyright 2009-2011 the Arc Team, the blockBox Team and other contributors.
# blockBox is licensed under the BSD 3-Clause Modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from __future__ import with_statement

from blockbox.constants import *
from blockbox.decorators import *
from blockbox.irc_client import *
from blockbox.persistence import PersistenceEngine as Persist
from blockbox.plugins import ProtocolPlugin

class BankPlugin(ProtocolPlugin):
    "An ingame bank."

    commands = {
        "bank": "commandBalance",
        "balance": "commandBalance",
        "pay": "commandPay",
        "setbank": "commandSetAccount",
        "removebank": "commandRemoveAccount",
    }

    def commandBalance(self, parts, fromloc, overriderank):
        "/bank - Guest\nAliases: balance\nFirst time: Creates you a account.\nOtherwise: Checks your balance."
        if self.client.persist.int("bank", "balance", -1) is not -1:
            self.client.sendServerMessage("Welcome to the bank!")
            self.client.sendServerMessage("Your current balance is %d %s." % (self.client.persist.int("bank", "balance", -1), self.client.factory.config["credit_name"]))
        else:
            self.client.persist.set("bank", "balance", self.client.factory.config["initial_amount"])
            self.client.sendServerMessage("Welcome to the bank!")
            self.client.sendServerMessage("We have created your account.")
            self.client.sendServerMessage("Your current balance is %d %s." % (self.client.persist.int("bank", "balance", -1), self.client.factory.config["credit_name"]))
            self.client.sendServerMessage("NOTE: We CAN detect cheating. Do NOT try it.")
            self.money_logger.info("%s has created an account." % self.client.username)

    @config("rank", "director")
    def commandSetAccount(self, parts, fromloc, overriderank):
        "/setbank username amount - Director\nEdits Bank Account"
        if len(parts) != 3:
            self.client.sendServerMessage("Syntax: /set <target> <amount>")
            return False
        target = parts[1]
        with Persist(target) as p:
            tbalance = p.int("bank", "balance", -1)
        if tbalance is -1:
            self.client.sendServerMessage("Invalid target.")
            return False
        try:
            amount = int(parts[2])
        except ValueError:
            self.client.sendServerMessage("Invalid amount.")
            return False
        with Persist(target) as p:
            p.set("bank", "balance", amount)
        self.client.sendServerMessage("Set player balance to %d %s." % (amount, self.client.factory.config["credit_name"]))

    def commandPay(self, parts, fromloc, overriderank):
        "/pay username amount - Guest\nThis lets you send money to other people."
        if len(parts) != 3:
            self.client.sendServerMessage("/pay <target> <amount>")
            return False
        user = self.client.username.lower()
        ubalance = self.client.persist.int("bank", "balance", -1)
        target = parts[1].lower()
        with Persist(target) as p:
            tbalance = p.int("bank", "balance", -1)
        if tbalance is -1:
            self.client.sendServerMessage("Error: Invalid target.")
            return False
        try:
            amount = int(parts[2])
        except ValueError:
            self.client.sendServerMessage("Error: Invalid amount.")
            return False
        if ubalance is -1:
            self.client.sendServerMessage("Error: You don't have an account.")
            self.client.sendServerMessage("Notice: Do /bank to create one.")
            return False
        elif amount < 0 and not self.client.theRank() >= 9:
            self.client.sendServerMessage("Error: Amount must be positive.")
            return False
        elif amount > ubalance or amount < -(tbalance):
            self.client.sendServerMessage("Error: Not enough %s." % self.client.factory.config["credit_name"])
            return False
        else:
            with Persist(target) as p:
                p.set("bank", "balance", tbalance + amount)
            self.client.persist.set("bank", "balance", ubalance - amount)
            self.client.sendServerMessage("You sent %d ." % amount)
            if target in self.client.factory.usernames:
                self.client.factory.usernames[target].sendServerMessage("You received %(amount)d %(creditname)s from %(user)s." % {'amount': amount, 'creditname': self.client.factory.config["credit_name"], 'user': user})
            self.money_logger.info("%(user)s sent %(amount)d to %(target)s" % {'user': user, 'amount': amount, 'target': target})

    @config("rank", "director")
    def commandRemoveAccount(self, parts, fromloc, overriderank):
        "/removebank username - Director\nRemoves Bank Account"
        if len(parts) != 2:
            self.client.sendServerMessage("Syntax: /removebank <target>")
            return False
        target = parts[1]
        with Persist(target) as p:
            if p.int("bank", "balance", -1) is -1:
                self.client.sendServerMessage("Invalid target.")
                return False
            p.set("bank", "balance", -1)
        self.client.sendServerMessage("Account deleted.")