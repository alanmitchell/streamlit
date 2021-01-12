"""A number of dictionaries that map IDs to a label.
"""

# Maps Device EUI to a Label
dev_lbls = dict(
    A81758FFFE0523DB = 'Tyler ELT-Lite 23DB',
    A8404173E1822CA4 = 'Alan LHT65 2CA4',
    A81758FFFE04259E = 'Alan ERS 259E',
    A8404137B182428E = 'Phil LT22222 428E',
    A840417F8182436E = 'Phil LT22222 436E',
    A81758FFFE053692 = 'Phil ELT-2 3692',
    A81758FFFE0526D8 = 'Phil CO2 26D8',
    A81758FFFE053691 = 'Peter ELT-2 3691',
    A8404175D1822CA7 = 'Peter LHT65 2CA7',
)

# Maps Device ID to Label
dev_id_lbls = {
    'boat-lt2-a8404137b182428e': 'Phil LT22222 428E',
    'ers-a81758fffe04259e': 'Alan ERS 259E',
    'ersco2-a81758fffe0526d8': 'Phil CO2 26D8',
    'elt-2_a81758fffe053692': 'Phil ELT-2 3692',
    'lht65-a8404173e1822ca4': 'Alan LHT65 2CA4',
    'elt-a81758fffe0523db': 'Tyler ELT-Lite 23DB',
    'boat-lt2-a84041552182436a': 'Phil LT22222 436A',
    'lht65-a8404175d1822ca7': 'Peter LHT65 2CA7',
    'boat-lt2-a840417f8182436e': 'Phil LT22222 436E',
    'boat-lt2-a84041599182436c': 'Phil LT22222 436C',
}

# Maps Gateway IDs to a Label
gtw_lbls = {
    'eui-00800000a00034ed': 'Kasilof',
    'eui-3235313227006100': 'Abbot/Elmore',
    'eui-323531322b004500': 'Intl/C St',
    'eui-58a0cbfffe800baf': 'SEED Lab',
    'eui-58a0cbfffe8015fd': 'Tyler Indoor',
    'eui-a840411d91b44150': 'Dragino LPS8',
    'eui-c0ee40ffff293d87': 'Laird',
    'kl4qh-mtcdt3': 'ANMC',
    'eui-24e124fffef06f56': 'Old Swd/Tudor',
    'eui-000080029c2b2b77': 'Bear Valley',
    'eui-a84041ffff1ee2b4': 'Tyler Outdoor',
    'eui-a840411eed744150': 'Phil Home',
    'eui-58a0cbfffe802c68': "Altermatt TIG",
    'eui-58a0cbfffe80326e': 'Phil TIG',
}
