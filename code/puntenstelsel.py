# -*- coding: utf-8 -*-
"""
Created on Mon Sep 27 12:52:35 2021

@author: r.tromp
"""
import pandas as pd
import numpy as np
# from .code.woningdetails_todict import rows
import os
import pprint
import csv
import json
import pprint
import csv
import json
pd.options.mode.chained_assignment = None  # default='warn'

# Read csv van 1 dag, om te testen
# kamernet = pd.read_csv('code/kamernet/kamers1509.csv')

# Pak alle scrape csv's en merge ze tot 1 dataset
pp = pprint.PrettyPrinter(indent=4)
newFrame = pd.DataFrame()
# rows_new = []

for filename in os.listdir(r'./code/kamernet'):
    if '.csv' in filename:
        with open(f'./code/kamernet/{filename}', newline='') as file:
            rows_new = []
            reader = csv.DictReader(file)
            for row in reader:
                if 'kamers_url' in row:
                    row_new = {**row}
                    rows_new.append(row_new)
            filedata = pd.DataFrame(rows_new)
            if newFrame.empty:
                newFrame = pd.concat([newFrame, filedata])
            elif rows_new:
                # @TODO check of merge daadwerkelijk dubbelingen eruit haalt
                newFrame = newFrame.merge(filedata, how="outer")
                newFrame = newFrame.drop_duplicates('kamers_url')
                # newFrame = newFrame.drop_duplicates(subset=newFrame.columns.difference(['publicatiedatum']))
                duplicatesFrame = newFrame[newFrame['kamers_url'].duplicated(keep=False)]
                duplicatesFrame = duplicatesFrame.sort_values('kamers_url')
                # duplicatesFrame.to_csv('duplicates.csv')

# Export newFrame als csv en import als filename
newFrame.to_csv('kamers_totaal.csv', index=False)
filename = 'kamers_totaal.csv'
# filename = 'code/kamernet/kamers1509.csv'
rows = []

# Read file en maak van dict 'woningdetails' aparte columns
with open(filename, newline='') as file:
    reader = csv.DictReader(file)
    for row in reader:
        # Format string to be json
        adProperties = row['woningdetails'].replace("'", '"')
        adProperties = json.loads(adProperties)

        # Make keys lowercase
        adProperties = dict((k.lower(), v) for k,v in adProperties.items())

        del row['woningdetails']
        # pp.pprint(adProperties)
        row = { **row,
                **adProperties }

        # Add row to list of rows
        rows.append(row)
#TODO hier misschien een if-statement van maken: if in variable explore        
del(adProperties, file, filename, pp, reader, row, filedata, row_new, rows_new, newFrame)

# Make df
kamernet = pd.DataFrame(rows)

# # Filter kamers op html NOG DOEN MAAR DAN OP URL voor van voor 15-09!
# kamers = kamernet[kamernet['html'].str.contains("kamer")]
# # Filter kamers op url
kamernet['woningtype'] = kamernet['kamers_url'].str.split('huren/')
woningtypes = kamernet['woningtype'].apply(pd.Series)
woningtypes = woningtypes[1].str.split('-')
woningtypes = woningtypes.apply(pd.Series)
woningtypes = woningtypes[0]
kamernet['woningtype'] = woningtypes

kamers = kamernet[kamernet['woningtype'].str.contains("kamer")]
# del(woningtypes)

# White spaces weg bij relevante columns
# kamers['keuken'] = kamers['keuken'].str.strip()

# Maak van kamerprijs een integer
length = len('Ã¢â€šÂ¬')
kamers['prijs'] = kamers['prijs'].str[length:]
kamers['prijs'] = kamers['prijs'].astype(str).astype(int)

# Punten geven aan oppervlakte
punten_m2 = 5
# Verwijder laatste letters
kamers['m2_kamer'] = kamers['oppervlakte_kamer'].str[:-1]
# Maak int
kamers['m2_kamer'] = kamers['m2_kamer'].astype(str).astype(int)
# Bereken het aantal punten per m2 en voeg toe aan df
punten_totaal = kamers['m2_kamer'] * punten_m2
kamers['punten_totaal'] = punten_totaal

# Alleen kijken naar kamers met totale oppervlakte
kamers_top = kamers[kamers['oppervlakte_subtitel'].str.contains("Totale oppervlakte")]
# Schoon kamers['oppervlakte_subtitel'] op
kamers_top['oppervlakte_subtitel'] = kamers_top['oppervlakte_subtitel'].str[:-4]
strlenght = len('totale oppervlakte:')
kamers_top['oppervlakte_subtitel'] = kamers_top['oppervlakte_subtitel'].str[strlenght:]
# Maak aparte df van de kamers die totale oppervlakte hebben en geen NaN:
# kamers['oppervlakte_subtitel'] = kamers['oppervlakte_subtitel'].replace("", np.nan, inplace=True)
# # kamers_top = kamers[kamers['oppervlakte_subtitel'].dropna(inplace = True)]
# kamers_top = kamers[kamers['oppervlakte_subtitel'].notna()]
# Maak er een integer van zodat we kunnen rekenen
kamers_top['oppervlakte_subtitel'] = kamers_top['oppervlakte_subtitel'].astype(str).astype(int)

kamers_top.loc[kamers_top['huisgenoten'].str.contains('Meer dan'), 'huisgenoten_clean'] = kamers_top['huisgenoten'].str[11:].astype(str)
kamers_top.loc[(~kamers_top['huisgenoten'].str.contains('Meer dan')) & (~kamers_top['huisgenoten'].str.contains('Onbekend')), 'huisgenoten_clean'] = kamers_top['huisgenoten']
kamers_top.loc[kamers_top['huisgenoten_clean'].notnull(), 'huisgenoten_clean'] = kamers_top['huisgenoten_clean'].astype(str).astype(float)
kamers_top.loc[kamers_top['huisgenoten'].str.contains('Meer dan'), 'huisgenoten_clean'] = kamers_top['huisgenoten_clean'] + 1

# Als de gemeenschappelijke woonruimte >15m2 is doe wat
# Schatting van de gemeenschappelijke woonruimte
# LET OP: Als huisgenoten onbekend geen berekening mogelijk en dus geen extra punten toegekend voor gemeenschappelijke ruimtes, oplossing: op basis van gedeelte ruimtes (keuken, badkamer, etc) concluderen minstens 1 huisgenoot
kamers_top.loc[kamers_top['huisgenoten_clean'].notnull(), 'm2_gemeenschappelijk'] = kamers_top['oppervlakte_subtitel'] - (kamers_top['m2_kamer'] * kamers_top['huisgenoten_clean'])
kamers_top['inwoners'] = kamers_top['huisgenoten_clean'] + 1
kamers_top.loc[kamers_top['m2_gemeenschappelijk'] > 15, 'punten_gemeenschappelijk'] = kamers_top['m2_gemeenschappelijk'] * 5 / kamers_top['inwoners']
kamers_top.loc[kamers_top['m2_gemeenschappelijk'] <= 15, 'punten_gemeenschappelijk'] = 0
kamers_top.loc[kamers_top['punten_gemeenschappelijk'].notnull(), 'punten_totaal_new'] = kamers_top['punten_totaal'] + kamers_top['punten_gemeenschappelijk'].astype(str).astype(float)
kamers_top.loc[kamers_top['punten_gemeenschappelijk'].isnull(), 'punten_totaal_new'] = kamers_top['punten_totaal']

# Neem aan dat het CV heeft
kamers_top['punten_cv'] = kamers_top['m2_kamer'] * 0.75
kamers_top['punten_totaal'] = kamers_top['punten_totaal'] + kamers_top['punten_cv']

# Kookgelegenheid
# kamers_top['punten_keuken'] = kamers_top[(kamers_top['keuken'] == " Gedeeld ") + 5
kamers_top['punten_keuken'] = 0
kamers_top.loc[((kamers_top['keuken'] == " Gedeeld ") & (kamers_top['inwoners'] <= 5)), 'punten_keuken'] + 4
kamers_top.loc[((kamers_top['keuken'] == " Gedeeld ") & (kamers_top['inwoners'] > 5)), 'punten_keuken'] + 0
kamers_top.loc[((kamers_top['keuken'] == " Eigen ") & (kamers_top['m2_kamer'] <= 25)), 'punten_keuken'] + 10
kamers_top.loc[((kamers_top['keuken'] == " Eigen ") & (kamers_top['m2_kamer'] > 25)), 'punten_keuken'] + 20


#  WC

# Douche & bad

# Wastafel 

# Bereken prijs
punt_prijs = 2.21
kamers_top['wettelijke_prijs'] = (kamers_top['punten_totaal'] * punt_prijs).round(0)
# Als prijs hoger dan kamerprijs, True anders False
kamers_top.loc[kamers_top['prijs'] > kamers_top['wettelijke_prijs'], 'te_duur'] = True
kamers_top.loc[kamers_top['prijs'] < kamers_top['wettelijke_prijs'], 'te_duur'] = False
# Hoeveel te duur
kamers_top['te_duur'].value_counts(normalize=True)

# TODO
# =============================================================================
# Alle white spaces weg in het begin
# Kijk per stad
# Als er niet aan criteria voldaan wordt, bijvoorbeeld woningdetails niet ingevuld:
# benaderen of een veilige aanname doen. 
#
#
#
#
#
# =============================================================================











 

















