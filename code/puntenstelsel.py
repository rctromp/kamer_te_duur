# -*- coding: utf-8 -*-
"""
Created on Mon Sep 27 12:52:35 2021

@author: r.tromp
"""
import pandas as pd
import os
import csv
import json
pd.options.mode.chained_assignment = None  # default='warn'

# Pak alle scrape csv's en merge ze tot 1 dataset
mergedRows = []

for filename in os.listdir(r'./code/kamernet'):
    if '.csv' in filename:
        with open(f'./code/kamernet/{filename}', newline='') as file:
            reader = csv.DictReader(file)

            for row in reader:
                if 'kamers_url' in row:
                    # Format string to be json
                    adProperties = row['woningdetails'].replace("'", '"')
                    adProperties = json.loads(adProperties)

                    # Make keys lowercase
                    adProperties = dict((k.lower(), v) for k, v in adProperties.items())

                    del row['woningdetails']
                    row = {**row, **adProperties}

                    # Add row to list of rows
                    mergedRows.append(row)

kamernet = pd.DataFrame(mergedRows)
kamernet = kamernet.drop_duplicates(subset=kamernet.columns.difference(['publicatiedatum', 'html']))

#TODO hier misschien een if-statement van maken: if in variable explore        
del (adProperties, file, filename, reader, row, mergedRows)

# # Filter kamers op url
kamernet['woningtype'] = kamernet['kamers_url'].str.split('huren/').str[1]
kamernet['woningtype'] = kamernet['woningtype'].str.split('-').str[0]

kamers = kamernet[kamernet['woningtype'].str.fullmatch("kamer")]

# White spaces weg bij relevante columns
# kamers['keuken'] = kamers['keuken'].str.strip()

# Maak van kamerprijs een integer
kamers['prijs'] = kamers['prijs'].str.split(' ').str[1].astype(int)

# Verwijder laatste letters en maak integer
kamers['m2_kamer'] = kamers['oppervlakte_kamer'].str[:-1].astype(int)
# Bereken het aantal punten per m2 en voeg toe aan df
kamers['punten_totaal'] = kamers['m2_kamer'] * 5

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


# Kookgelegenheid
kamers_top['punten_keuken'] = 0
kamers_top.loc[((kamers_top['keuken'] == " Gedeeld ") & (kamers_top['inwoners'] <= 5)), 'punten_keuken'] = kamers_top['punten_keuken'] + 4
kamers_top.loc[((kamers_top['keuken'] == " Gedeeld ") & (kamers_top['inwoners'] > 5)), 'punten_keuken'] = kamers_top['punten_keuken'] + 0
kamers_top.loc[((kamers_top['keuken'] == " Eigen ") & (kamers_top['m2_kamer'] <= 25)), 'punten_keuken'] = kamers_top['punten_keuken'] + 10
kamers_top.loc[((kamers_top['keuken'] == " Eigen ") & (kamers_top['m2_kamer'] > 25)), 'punten_keuken'] = kamers_top['punten_keuken'] + 20


#  WC 
kamers_top['punten_toilet'] = 0
kamers_top.loc[((kamers_top['toilet'] == " Gedeeld ") & (kamers_top['inwoners'] > 5)), 'punten_toilet'] = kamers_top['punten_keuken'] + 0
kamers_top.loc[((kamers_top['toilet'] == " Gedeeld ") & (kamers_top['inwoners'] <= 5)), 'punten_toilet'] = kamers_top['punten_keuken'] + 2
kamers_top.loc[(kamers_top['toilet'] == " Eigen "), 'punten_toilet'] = kamers_top['punten_keuken'] + 2

# Douche & bad & wastafel
kamers_top['punten_badkamer'] = 0
kamers_top.loc[((kamers_top['badkamer'] == " Gedeeld ") & (kamers_top['inwoners'] > 8)), 'punten_badkamer'] = kamers_top['punten_badkamer'] + 0
kamers_top.loc[((kamers_top['badkamer'] == " Gedeeld ") & (kamers_top['inwoners'] <= 8)), 'punten_badkamer'] = kamers_top['punten_badkamer'] + 3
kamers_top.loc[(kamers_top['badkamer'] == " Eigen "), 'punten_badkamer'] = kamers_top['punten_badkamer'] + 15 + 10
kamers_top.loc[((kamers_top['badkamer'] == " Gedeeld ") & (kamers_top['inwoners'] <= 5)), 'punten_badkamer'] = kamers_top['punten_badkamer'] + 2

# Aftrekpunten
kamers_top['aftrekpunten'] = 0
kamers_top.loc[(kamers_top['m2_kamer'] < 10), 'aftrekpunten'] = kamers_top['aftrekpunten'] - 15 
# WC via andere kamer kan ik niet zien

# Bereken prijs
kamers_top['punten_totaal'] = kamers_top['punten_totaal'] + kamers_top['punten_cv'] + kamers_top['punten_keuken'] + kamers_top['punten_toilet'] + kamers_top['punten_badkamer'] + kamers_top['aftrekpunten']
punt_prijs = 2.21
kamers_top['wettelijke_prijs'] = (kamers_top['punten_totaal'] * punt_prijs).round(0)
# Als prijs hoger dan kamerprijs, True anders False
kamers_top.loc[kamers_top['prijs'] > kamers_top['wettelijke_prijs'], 'te_duur'] = True
kamers_top.loc[kamers_top['prijs'] < kamers_top['wettelijke_prijs'], 'te_duur'] = False
# Hoeveel te duur
# Drop alle kamers waar de url en wettelijke prijs hetzelfde zijn
kamers_top = kamers_top.drop_duplicates(['kamers_url', 'wettelijke_prijs'])
kamers_top['te_duur'].value_counts(normalize=True)
 
# Deze regel checkt of er rijen zijn waar de kamers_url, oppervlakte_kamer, oppervlakte_subtitel en prijs gelijk zijn
# als dat zo is is er een andere reden waarom de wettelijke prijs afwijkt, met de huidige dataset zijn dit 0 rijen
unexplainedDuplicates = kamers_top[
    kamers_top.duplicated(['kamers_url', 'oppervlakte_kamer', 'oppervlakte_subtitel', 'prijs'], keep=False)]

# TODO
# =============================================================================
# Alle white spaces weg in het begin
# Kijk per stad
# Als er niet aan criteria voldaan wordt, bijvoorbeeld woningdetails niet ingevuld:
# benaderen of een veilige aanname doen. (ik denk een gemiddelde bij 'onbekend')
# Hoeveel is de punt_prijs? Ik snap het niet zo goed in de rekentool.
# 
# aannames
# Geen Rijksmomunment (+50)
# Geen wc via een andere kamer -15
# =============================================================================
