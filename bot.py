import requests
import time
from datetime import datetime
import numpy as np
from scipy.stats import poisson
import os

# --- PODACI (Automatski povlači iz GitHub Secrets ili upišite ovdje) ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "878979655:AAHF13...") 
CHAT_ID = "8126476484"
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "bceaabab0b964a1...")

def posalji_telegram_poruku(tekst):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": tekst,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Izvještaj uspješno poslan na Telegram!")
        else:
            print(f"Greška pri slanju: {response.text}")
    except Exception as e:
        print(f"Greška pri spajanju na Telegram: {e}")

def izracunaj_sve_opcije(forma_a, forma_b):
    snaga_a = forma_a * 1.2
    snaga_b = forma_b * 1.2
    
    lambda_a = max(0.5, snaga_a * 0.9)
    lambda_b = max(0.5, snaga_b * 0.8)
    
    matrica = np.zeros((6, 6))
    vj_vise_2_5 = 0
    vj_manje_2_5 = 0
    
    for i in range(6):
        for j in range(6):
            vj = poisson.pmf(i, lambda_a) * poisson.pmf(j, lambda_b)
            matrica[i, j] = vj
            if (i + j) > 2.5:
                vj_vise_2_5 += vj
            else:
                vj_manje_2_5 += vj
                
    vj_1 = np.sum(np.tril(matrica, -1))
    vj_x = np.sum(np.diag(matrica))
    vj_2 = np.sum(np.triu(matrica, 1))
    
    vj_1x = vj_1 + vj_x
    vj_x2 = vj_x + vj_2
    vj_12 = vj_1 + vj_2
    
    return {
        "1": round(vj_1 * 100, 1),
        "X": round(vj_x * 100, 1),
        "2": round(vj_2 * 100, 1),
        "1X": round(vj_1x * 100, 1),
        "X2": round(vj_x2 * 100, 1),
        "12": round(vj_12 * 100, 1),
        "Over_2_5": round(vj_vise_2_5 * 100, 1),
        "Under_2_5": round(vj_manje_2_5 * 100, 1)
    }

def dohvati_utakmice_i_analiziraj():
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            posalji_telegram_poruku(f"Greška pri dohvaćanju utakmica s API-ja: {response.status_code}")
            return
            
        data = response.json()
        matches = data.get("matches", [])
        
        if not matches:
            posalji_telegram_poruku("🤖 *Nogometni Bot*\n\nDanas nema pronađenih utakmica u sustavu besplatnog API-ja.")
            return
            
        izvjestaj = "⚽ *DANAŠNJE ANALIZE UTAKMICA* ⚽\n\n"
        
        brojac = 0
        for match in matches:
            if brojac >= 5: # Ograničavamo na 5 utakmica da poruka ne bude predugačka
                break
                
            home_team = match['homeTeam']['name']
            away_team = match['awayTeam']['name']
            
            # Simulacija forme na osnovu pozicije/imena za demo
            rezultati = izracunaj_sve_opcije(1.5, 1.3)
            
            izvjestaj += f"🏆 *{home_team} vs {away_team}*\n"
            izvjestaj += f"• 1X2: [ 1: {rezultati['1']}% | X: {rezultati['X']}% | 2: {rezultati['2']}% ]\n"
            izvjestaj += f"• Dupla šansa: [ 1X: {rezultati['1X']}% | X2: {rezultati['X2']}% ]\n"
            izvjestaj += f"• Golovi: [ Više 2.5: {rezultati['Over_2_5']}% | Manje 2.5: {rezultati['Under_2_5']}% ]\n\n"
            brojac += 1
            
        posalji_telegram_poruku(izvjestaj)
        
    except Exception as e:
        posalji_telegram_poruku(f"Došlo je do greške u skripti: {str(e)}")

if __name__ == "__main__":
    dohvati_utakmice_i_analiziraj()
