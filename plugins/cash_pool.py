"""
You can ask me to "show the cash pool" if you would like to see your debts. You
can also ask me to "show the cash pool history", if you'd prefer.
Alternatively, you may inform me that "Tom sent $42 to Dick" or that "Tom paid
$333 for Dick and Harry". Of course, I will always assume that Tom also paid
for himself.
"""
from collections import defaultdict
import cPickle as pickle
import re


crontable = []
outputs = []


SENT = re.compile(r'jarvis.* (\w+) sent \$([\d\.]+) to (\w+)')
PAID = re.compile(r'jarvis.* (\w+) paid \$([\d\.]+) for ([ \w]+)')


PICKLE_FILE = 'cash_pool.pickle'
try:
    pool = pickle.load(open(PICKLE_FILE, 'rb'))
except IOError:
    pool = defaultdict(int)

PICKLE_HISTORY_FILE = 'cash_pool_history.pickle'
try:
    history = pickle.load(open(PICKLE_HISTORY_FILE, 'rb'))
except IOError:
    history = list()


def process_message(data):
    if 'explain the cash pool' in data['text']:
        outputs.append([data['channel'], 'Very well, sir.'])
        outputs.append([data['channel'], __doc__.replace('\n', ' ')])

        return

    if 'show the cash pool' in data['text']:
        if 'history' in data['text']:
            if history:
                outputs.append([
                    data['channel'],
                    'Very good, sir, displaying your history now:'])
            else:
                outputs.append([data['channel'],
                                'I have no record of a cash pool, sir.'])

            for line in history:
                outputs.append([data['channel'], line.replace('jarvis, ', '')])

            return

        outputs.append([data['channel'], "I've analyzed your cash pool."])
        for person, value in sorted(pool.iteritems()):
            outputs.append([data['channel'],
                            '%s %s $%s' % ('owes' if value > 0 else 'is owed',
                                              person.title(), round(abs(value), 2))])


        if not pool:
            outputs.append([data['channel'], 'All appears to be settled.'])

        return

    did_send = SENT.match(data['text'])
    if did_send:
        sender, value, sendee = did_send.groups()
        sender = sender.lower()
        sendee = sendee.lower()
        value = float(value)

        pool[sender] -= value
        if -0.01 < pool[sender] < 0.01:
            pool[sender] = 0
        pool[sendee] += value
        if -0.01 < pool[sendee] < 0.01:
            pool[sendee] = 0

        history.append(data['text'])

        pickle.dump(history, open(PICKLE_HISTORY_FILE, 'wb'))
        pickle.dump(pool, open(PICKLE_FILE, 'wb'))

        outputs.append([data['channel'], 'Very good, sir.'])
        return

    did_pay = PAID.match(data['text'])
    if did_pay:
        payer, value, payees = did_pay.groups()
        payer = payer.lower()
        payees = payees.lower().split(' and ')
        value = float(value)
        num_payees = len([x for x in payees if x != payer])

        pool[payer] -= value * num_payees / (num_payees + 1)
        if -0.01 < pool[payer] < 0.01:
            pool[payer] = 0
        for payee in payees:
            pool[payee] += value / (num_payees + 1)
            if -0.01 < pool[payee] < 0.01:
                pool[payee] = 0

        history.append(data['text'])

        pickle.dump(history, open(PICKLE_HISTORY_FILE, 'wb'))
        pickle.dump(pool, open(PICKLE_FILE, 'wb'))

        outputs.append([data['channel'], 'Very good, sir.'])
        return
