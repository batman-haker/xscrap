"""
SYNTEZA Analyzer - Deep Author Analysis Module
Analyzes author's tweeting patterns, market perspective, and investment insights.
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.claude_client import ClaudeAnalyst

class SyntezaAnalyzer:
    def __init__(self):
        self.claude = ClaudeAnalyst()

    def generate_analysis_prompt(self, author_data: Dict[str, Any]) -> str:
        """Generate comprehensive analysis prompt for LLM"""

        author = author_data['metadata']['author']
        tweets_count = author_data['metadata']['total_tweets']
        tweets = author_data['tweets']

        # Extract tweet texts and check for links
        tweet_analysis = []
        for i, tweet in enumerate(tweets):
            tweet_text = tweet['text']
            tweet_data = {
                'number': i+1,
                'text': tweet_text,
                'created_at': tweet['created_at'],
                'metrics': tweet.get('public_metrics', {}),
                'has_links': 't.co/' in tweet_text or 'http' in tweet_text
            }
            tweet_analysis.append(tweet_data)

        prompt = f"""
# SYNTEZA - Deep Financial Author Analysis

Analizujesz treści finansowe od autora **{author}** na podstawie {tweets_count} ostatnich tweetów.

## ZADANIE:
Przeprowadź głęboką analizę perspektywy inwestycyjnej autora, jego podejścia do rynku i wartości jego treści.

## DANE DO ANALIZY:
{chr(10).join([f"{tweet['number']}. [{tweet['created_at']}] {tweet['text']}" +
              (f" [♥️{tweet['metrics'].get('favorite_count',0)} 🔄{tweet['metrics'].get('retweet_count',0)}]" if tweet['metrics'] else "") +
              (" [🔗ZAWIERA LINK]" if tweet['has_links'] else "")
              for tweet in tweet_analysis])}

## INSTRUKCJA SPECJALNA:
⚠️ **WAŻNE**: Jeśli w tweetach są linki (oznaczone [🔗ZAWIERA LINK]), są to często kluczowe informacje.
Podczas analizy uwzględnij, że linki mogą prowadzić do:
- Artykułów gospodarczych i analiz rynkowych
- Wykresów i danych technicznych
- Raportów spółek i wyników finansowych
- Newsy i wydarzenia rynkowe
- Inne ważne źródła informacji

Traktuj posty z linkami jako potencjalnie najważniejsze dla zrozumienia perspektywy autora.

## PYTANIA ANALITYCZNE:

### 1. PROFIL INWESTYCYJNY AUTORA
- Jaki jest główny styl inwestycyjny autora? (swing trading, long-term, day trading)
- Na jakich sektorach/instrumentach się koncentruje?
- Czy preferuje analizę techniczną czy fundamentalną?
- Jaki jest jego stosunek do ryzyka?

### 2. PERSPEKTYWA RYNKOWA
- Jaki jest obecny sentiment autora wobec rynku? (bullish/bearish/neutral)
- Jakie trendy makroekonomiczne identyfikuje?
- Na które zagrożenia/okazje zwraca uwagę?
- Czy jego perspektywa jest krótko- czy długoterminowa?

### 3. JAKOŚĆ ANALIZ
- Czy autor podaje konkretne poziomy cenowe/cele?
- Jak szczegółowe są jego analizy techniczne?
- Czy uwzględnia kontekst makroekonomiczny?
- Czy podaje uzasadnienia swoich przewidywań?

### 4. SYGNAŁY INWESTYCYJNE
- Jakie konkretne rekomendacje/sygnały daje autor?
- Które aktywa/sektory rekomenduje?
- Jakie poziomy stop-loss/take-profit sugeruje?
- Czy określa horyzonty czasowe inwestycji?

### 5. TRENDY I WZORCE
- Jakie główne tematy przewijają się w jego tweetach?
- Czy widać ewolucję jego poglądów w czasie?
- Na które wydarzenia rynkowe najczęściej reaguje?
- Jaki jest jego stosunek do różnych klas aktywów?

### 6. WARTOŚĆ DLA INWESTORÓW
- Jakie unikalne insights oferuje autor?
- Czy jego analizy są dostępne dla początkujących?
- Jaką wartość dodaną wnosi do dyskusji rynkowej?
- Czy warto śledzić jego rekomendacje?

## WYMAGANIA ODPOWIEDZI:

### STRUKTURA:
1. **EXECUTIVE SUMMARY** (2-3 zdania o autorze)
2. **PROFIL INWESTYCYJNY** (styl, focus, podejście)
3. **OBECNA PERSPEKTYWA RYNKOWA** (sentiment, trendy)
4. **KLUCZOWE INSIGHTS** (najważniejsze obserwacje)
5. **SYGNAŁY INWESTYCYJNE** (konkretne rekomendacje)
6. **OCENA WARTOŚCI** (przydatność dla różnych typów inwestorów)
7. **REKOMENDACJE** (jak wykorzystać treści autora)

### STYL:
- Konkretny, merytoryczny język finansowy
- Użyj konkretnych liczb i poziomów cenowych
- Wskaż mocne i słabe strony analizy autora
- Oceń na skali 1-10 jakość i przydatność treści
- Podaj praktyczne wskazówki dla inwestorów

### DŁUGOŚĆ:
- Około 1000-1500 słów
- Szczegółowa analiza z przykładami
- Cytowania z tweetów jako dowody

Przeprowadź analizę jako doświadczony analityk finansowy z perspektywy polskiego inwestora.
"""

        return prompt

    def analyze_author_data(self, json_filepath: str) -> Dict[str, Any]:
        """Analyze author data from JSON file"""

        print(f"[SYNTEZA] Analyzing data from: {json_filepath}")

        # Load author data
        with open(json_filepath, 'r', encoding='utf-8') as f:
            author_data = json.load(f)

        # Generate analysis prompt
        prompt = self.generate_analysis_prompt(author_data)

        # Send to Claude for analysis
        print("[SYNTEZA] Sending to Claude for analysis...")

        # Use Claude's client directly for custom analysis
        try:
            response = self.claude.client.messages.create(
                model="claude-3-5-haiku-20241022",  # Use working model
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            analysis_result = response.content[0].text
        except Exception as e:
            print(f"[ERROR] Claude analysis failed: {e}")
            try:
                # Fallback to different model
                response = self.claude.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=4000,
                    messages=[{"role": "user", "content": prompt}]
                )
                analysis_result = response.content[0].text
            except Exception as e2:
                print(f"[ERROR] Fallback model also failed: {e2}")
                analysis_result = "Analysis failed - Claude API error"

        # Prepare results
        result = {
            'metadata': {
                'analyzed_at': datetime.now().isoformat(),
                'author': author_data['metadata']['author'],
                'source_file': json_filepath,
                'tweets_analyzed': author_data['metadata']['total_tweets']
            },
            'analysis': analysis_result,
            'source_data_summary': {
                'total_tweets': len(author_data['tweets']),
                'date_range': {
                    'oldest': author_data['tweets'][-1]['created_at'] if author_data['tweets'] else None,
                    'newest': author_data['tweets'][0]['created_at'] if author_data['tweets'] else None
                }
            }
        }

        # Save analysis result
        author_name = author_data['metadata']['author'].replace('@', '')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"synteza_analysis_{author_name}_{timestamp}.json"
        output_path = os.path.join("data", "synteza", output_filename)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"[SYNTEZA] Analysis saved to: {output_path}")

        return result

def main():
    """Test analysis with sample data"""
    from dotenv import load_dotenv
    load_dotenv()

    try:
        analyzer = SyntezaAnalyzer()
    except ValueError as e:
        print(f"[ERROR] {e}")
        return

    # Test with Dan_Kostecki data
    sample_file = "data/synteza/synteza_advanced_Dan_Kostecki_20250925_141738.json"
    if os.path.exists(sample_file):
        result = analyzer.analyze_author_data(sample_file)
        print("\n[SYNTEZA] Analysis completed!")
        print(f"[RESULT] {result['analysis'][:200]}...")
    else:
        print(f"[ERROR] Sample file not found: {sample_file}")

if __name__ == "__main__":
    main()