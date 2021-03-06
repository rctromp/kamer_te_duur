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
 
del (adProperties, file, filename, reader, row, mergedRows)

# # Filter kamers op url
kamernet['woningtype'] = kamernet['kamers_url'].str.split('huren/').str[1]
kamernet['woningtype'] = kamernet['woningtype'].str.split('-').str[0]

kamers = kamernet[kamernet['woningtype'].str.fullmatch("kamer")]

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
# Maak er een integer van zodat we kunnen rekenen
kamers_top['oppervlakte_subtitel'] = kamers_top['oppervlakte_subtitel'].astype(str).astype(int)

kamers_top.loc[kamers_top['huisgenoten'].str.contains('Meer dan'), 'huisgenoten_clean'] = kamers_top['huisgenoten'].str[11:].astype(str)
kamers_top.loc[(~kamers_top['huisgenoten'].str.contains('Meer dan')) & (~kamers_top['huisgenoten'].str.contains('Onbekend')), 'huisgenoten_clean'] = kamers_top['huisgenoten']
kamers_top.loc[kamers_top['huisgenoten_clean'].notnull(), 'huisgenoten_clean'] = kamers_top['huisgenoten_clean'].astype(str).astype(float)
kamers_top.loc[kamers_top['huisgenoten'].str.contains('Meer dan'), 'huisgenoten_clean'] = kamers_top['huisgenoten_clean'] + 1

kamers_top = kamers_top[kamers_top['huisgenoten_clean'].notnull()]
kamers_top['inwoners'] = kamers_top['huisgenoten_clean'] + 1

# Als de gemeenschappelijke woonruimte >15m2 is doe wat
# Schatting van de gemeenschappelijke woonruimte
# LET OP: Als huisgenoten onbekend geen berekening mogelijk en dus geen extra punten toegekend voor gemeenschappelijke ruimtes, oplossing: op basis van gedeelte ruimtes (keuken, badkamer, etc) concluderen minstens 1 huisgenoot
kamers_top['m2_gemeenschappelijk'] = kamers_top['oppervlakte_subtitel'] - (kamers_top['m2_kamer'] * kamers_top['huisgenoten_clean'])
kamers_top.loc[kamers_top['m2_gemeenschappelijk'] > 15, 'punten_gemeenschappelijk'] = kamers_top['m2_gemeenschappelijk'] * 5 / kamers_top['inwoners']
kamers_top.loc[kamers_top['m2_gemeenschappelijk'] <= 15, 'punten_gemeenschappelijk'] = 0
kamers_top['punten_totaal'] = kamers_top['punten_totaal'] + kamers_top['punten_gemeenschappelijk'].astype(str).astype(float)

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


# alles bij elkaar optellen
kamers_top['punten_totaal'] = kamers_top['punten_totaal'] + kamers_top['punten_cv'] + kamers_top['punten_keuken'] + kamers_top['punten_toilet'] + kamers_top['punten_badkamer'] + kamers_top['aftrekpunten']
kamers_top['punten_totaal'] = kamers_top['punten_totaal'].astype(int)


# Bereken prijs
# Voeg de officiele puntenstelselkaders toe aan kamers_top
df_puntprijs = pd.read_excel('src/punten_prijs_2021.xlsx')
df_puntprijs = df_puntprijs.rename(columns = {'punten': 'punten_totaal'})
df_puntprijs = df_puntprijs.rename(columns = {'prijs': 'bedrag'})
kamers_top = kamers_top.merge(df_puntprijs, how="left", on="punten_totaal")

# Wat als ik onderscheid maak tussen kale huur en g/w/l
len('p/m | incl. g/w/e')
kamers_top['GWL_kosten'] = 0
kamers_top.loc[(kamers_top['gas_water_licht'] == "p/m | incl. g/w/e"), 'GWL_kosten'] = kamers_top['GWL_kosten'] + 60
kamers_top.loc[(kamers_top['gas_water_licht'] == "p/m | excl. g/w/e"), 'GWL_kosten'] = kamers_top['GWL_kosten'] + 0
# trek af van de prijs
kamers_top['prijs'] = kamers_top['prijs'] - kamers_top['GWL_kosten'] 

# Als prijs hoger dan kamerprijs, True anders False
kamers_top.loc[kamers_top['prijs'] > kamers_top['bedrag'], 'te_duur'] = True
kamers_top.loc[kamers_top['prijs'] < kamers_top['bedrag'], 'te_duur'] = False
# Hoeveel te duur
# Drop alle kamers waar de url en wettelijke prijs hetzelfde zijn
kamers_top = kamers_top.drop_duplicates(['kamers_url', 'bedrag'])
kamers_top['te_duur'].value_counts(normalize=True)

# Deze regel checkt of er rijen zijn waar de kamers_url, oppervlakte_kamer, oppervlakte_subtitel en prijs gelijk zijn
# als dat zo is is er een andere reden waarom de wettelijke prijs afwijkt, met de huidige dataset zijn dit 0 rijen
unexplainedDuplicates = kamers_top[
    kamers_top.duplicated(['kamers_url', 'oppervlakte_kamer', 'oppervlakte_subtitel', 'prijs'], keep=False)]

# Statistieken: 
# Gemiddelde prijs per kamer
prijs_kamer_mean = kamers_top['prijs'].mean()
print('gemiddelde vraagprijs NL:',round(prijs_kamer_mean))
# Gemiddeld wat een kamer zou moeten kosten
prijs_kamer_puntenstelsel = kamers_top['bedrag'].mean()
print('wettelijke prijs NL:',round(prijs_kamer_puntenstelsel))
# Verschil te duur
kamers_top['prijsverschil'] = kamers_top['prijs'] - kamers_top['bedrag']
# Hoeveel geld totaal en gemiddeld
totaal_teveel_geld = kamers_top['prijsverschil'].sum()
print('totaal teveel huur NL:',round(totaal_teveel_geld))
te_duur_mean = kamers_top['prijsverschil'].mean()
print('gemiddele prijsverschil NL',round(te_duur_mean))
# Hoeveel procent is de prijs te duur?
procent_prijs_teduur = round((prijs_kamer_mean - prijs_kamer_puntenstelsel) / prijs_kamer_puntenstelsel * 100)
print(procent_prijs_teduur)

# Per gemeente
# maak van gemeente heldere strings
kamers_top['plaats'] = kamers_top['plaats'].str[3:]
te_duur_per_gemeente = kamers_top.groupby('plaats')['te_duur'].value_counts(normalize=True).to_frame()
# Vul df voor gemeente met relevante stats
gemeente_stats = pd.DataFrame()
gemeente_stats['prijs_gemiddeld'] = kamers_top.groupby('plaats')['prijs'].mean().round(0)
gemeente_stats['punten_bedrag_gemiddeld'] = kamers_top.groupby('plaats')['bedrag'].mean().round(0)
gemeente_stats['prijsverschil_gemiddeld'] = kamers_top.groupby('plaats')['prijsverschil'].mean().round(0)
gemeente_stats['m2_kamer'] = kamers_top.groupby('plaats')['m2_kamer'].mean().round(0)
gemeente_stats['count'] = kamers_top.groupby('plaats')['prijsverschil'].count()
gemeente_stats['prijs_teduur_procent'] =  round((gemeente_stats['prijs_gemiddeld'] - gemeente_stats['punten_bedrag_gemiddeld']) / gemeente_stats['punten_bedrag_gemiddeld'] * 100)

# Export to csv
kamers_top.to_csv('results/kamers_top.csv')
gemeente_stats.to_csv('results/kamerstats_per_gemeente.csv')
te_duur_per_gemeente.to_csv('results/gemeente_te_duur.csv')

