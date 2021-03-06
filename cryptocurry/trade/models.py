from django.db import models


class Wallet(models.Model):
    pass

    class Meta:
        verbose_name = "Wallet Information Table"
        db_table = 'cryptowallet'

    def __str__(self): # Python3.x compatible
        return "%s - %s"%(self.walletname, self.wallet_uid)


class Transaction(models.Model):
    pass

    class Meta:
        verbose_name = "Transaction Information Table"
        db_table = 'cryptotransaction'

    def __str__(self): # Python3.x compatible
        return "%s"%(self.tx_uid)


class Block(models.Model):
    pass

    class Meta:
        verbose_name = "Block Information Table"
        db_table = 'cryptoblock'

    def __str__(self): # Python3.x compatible
        return "%s"%(self.block_uid)


class ExchangeRates(models.Model):
    pass

    class Meta:
        verbose_name = "Exchange Rates Table"
        db_table = 'cryptoexcehangerates'

    def __str__(self): # Python3.x compatible
        return "%s"%(self.block_uid)



