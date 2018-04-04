#!/usr/bin/env python

# https://github.com/ecederstrand/exchangelib

import sys
import exchangelib
from exchangelib import (
    Account,
    Configuration,
    Credentials,
    EWSDateTime,
    EWSTimeZone,
)
from datetime import datetime, timedelta

TZ = EWSTimeZone.timezone("America/New_York")

class EWSAccount(object):
    def __init__(self, user, password):
        config = Configuration(
            server="outlook.office365.com",
            credentials=Credentials(username=user, password=password),
        )
        account = Account(
            primary_smtp_address=user,
            config=config,
            access_type=exchangelib.DELEGATE,
        )
        # could use this with Account(..., autodiscover=False)
        self.cache = {
            'ews-url': account.protocol.service_endpoint,
            'auth-type': account.protocol.auth_type,
            'primary-smtp-addr': account.primary_smtp_address,
        }
        self.account = account

    def upcomingEvents(self, window=timedelta(minutes=5)):
        start = datetime.now()
        #start = datetime(2017, 3, 17, 12, 56)
        endtm = start + window
        start = TZ.localize(EWSDateTime.from_datetime(start))
        endtm = TZ.localize(EWSDateTime.from_datetime(endtm))
        return self.account.calendar.view(start=start, end=endtm)


def main():
    act = EWSAccount("rudolph@domain", ".........")
    for event in act.upcomingEvents().all():
        tm = event.start.astimezone(TZ).strftime("%H:%M")
        print("%s - %s" % (tm, event.subject))

if __name__ == "__main__":
    sys.exit(main())
