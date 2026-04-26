# Real SLIIT Data for Testing Local Models

**Source**: 600 papers from SLIIT Research Repository (rda.sliit.lk)
**Total Available**: 4,219 papers in repository

---

## Real SLIIT Citations (For Citation NER Testing)

Copy and paste these REAL citations into the Citation Parser to test:

### Citation 1: Business/Management
```
De Silva,M, Vilasa,S, Bandara,A (2022). Impact of Terminal Handling Charges on the Performance of Non-Vessel Operating Common Carriers with Special Reference to the 2013 Government Regulation.
```
**Expected Extraction**:
- Authors: De Silva,M; Vilasa,S; Bandara,A
- Year: 2022
- Title: Impact of Terminal Handling Charges...

---

### Citation 2: Social Media Marketing
```
Bandara,G, Jayasuriya, N, Nimnajith,M (2022). Effect of Social Media Influencers' Attributes on Customer Purchasing Behavior in Sri Lankan Context (Special References to Facebook and Instagram).
```
**Expected Extraction**:
- Authors: Bandara,G; Jayasuriya, N; Nimnajith,M
- Year: 2022
- Title: Effect of Social Media Influencers' Attributes...

---

### Citation 3: Supply Chain
```
Dassanayake,A, Gamaarachchi,T, Ranathunge ,I (2022). The Role of Green Supply Chain Practices on Environmental Sustainability.
```
**Expected Extraction**:
- Authors: Dassanayake,A; Gamaarachchi,T; Ranathunge,I
- Year: 2022
- Title: The Role of Green Supply Chain Practices...

---

### Citation 4: Transportation/Accessibility
```
Suraweera, T., Bandara, S., Wickramaarachchi, C. (2022). Challenges of Mobility and Access to Transport for People with Visual Impairment and Blindness: An Exploratory Study.
```
**Expected Extraction**:
- Authors: Suraweera, T.; Bandara, S.; Wickramaarachchi, C.
- Year: 2022
- Title: Challenges of Mobility and Access to Transport...

---

### Citation 5: Finance/Investment
```
Saliya, C. A (2022). Impact of Psychosocial Factors on Sustainability of Stock Investors' Inclination: A Case of the South Pacific Stock Market.
```
**Expected Extraction**:
- Authors: Saliya, C. A
- Year: 2022
- Title: Impact of Psychosocial Factors on Sustainability...

---

### Citation 6: Cryptocurrency
```
Maduranga H.A.C.P, Bandara H.M.C, Nipuna Ravishka E.A (2022). Study on the Behavioral Intention to use Cryptocurrency Market among Non-State University Students in Sri Lanka.
```
**Expected Extraction**:
- Authors: Maduranga H.A.C.P; Bandara H.M.C; Nipuna Ravishka E.A
- Year: 2022
- Title: Study on the Behavioral Intention...

---

### Citation 7: HR Systems
```
Gunawardane, Y, Sathiyakumar, J, Sivalingam, K (2022). Impact of the Challenges in Implementing Human Resource Information Systems in Sri Lankan MSMEs.
```
**Expected Extraction**:
- Authors: Gunawardane, Y; Sathiyakumar, J; Sivalingam, K
- Year: 2022
- Title: Impact of the Challenges in Implementing...

---

### Citation 8: Internet Service Quality
```
Rashad, M.N.M., Hansini, M.P., Muthugala, M.H.N. (2022). Analysis of Customer Satisfaction and Internet Service Quality During the Covid 19 Pandemic in Sri Lanka.
```
**Expected Extraction**:
- Authors: Rashad, M.N.M.; Hansini, M.P.; Muthugala, M.H.N.
- Year: 2022
- Title: Analysis of Customer Satisfaction...

---

### Citation 9: Hotel/Tourism
```
Nagendrakumar, N, Rathnayake, R.R.M.T.R.T. (2022). Impact of Service Quality on Tourist Satisfaction: A Case of Sri Lankan Hotels.
```
**Expected Extraction**:
- Authors: Nagendrakumar, N; Rathnayake, R.R.M.T.R.T.
- Year: 2022
- Title: Impact of Service Quality on Tourist Satisfaction...

---

### Citation 10: Consumer Behavior
```
Jayasuriya, N.A., Wijesekara,T., Tennakoon, T.M.A.P. (2022). Does Culture Impact on Impulse Buying Behaviour? A Study on Fast Moving Consumer Good Industry.
```
**Expected Extraction**:
- Authors: Jayasuriya, N.A.; Wijesekara, T.; Tennakoon, T.M.A.P.
- Year: 2022
- Title: Does Culture Impact on Impulse Buying Behaviour?...

---

## Real SLIIT Abstracts (For Plagiarism Testing)

### Abstract 1: Terminal Handling Charges
```
Before the imposition of the regulation, terminal handling charges for containerized cargo were included in the all-inclusive freight listed in the bill of lading and were recovered from consumers at discharging ports. Since the regulation's implementation in 2013, terminal handling charges for containerized cargo have to be separately and explicitly invoiced and should be recovered from shippers at loading ports. The present study focuses on the effect of the 2013 Myitsone government regulation on terminal handling charges for containerized cargo and the performance of NVOCCs...
```

---

### Abstract 2: Social Media Influencers
```
This study aims to identify how social media influencer's attributes can be useful to tune the customer purchasing behavior. Since social media influence highly affects the day-to-day life of people, he/she highly impacts on decision making of customers to purchase products in the market. Therefore, this study was conducted to identify the impact of social media influencer's attributes such as trustworthiness, attractiveness, expertise, and credibility on customer purchasing behavior in the Sri Lankan context with special references to Facebook and Instagram...
```

---

### Abstract 3: Green Supply Chain
```
In the past decade environmental sustainability is one of the major considerations in supply chains all around the world. With noticeable environmental changes, companies couldn't look past the negative environmental impact of their supply chains. Many customers expect companies to adhere to these standards. Previous research has largely ignored the relationship between green supply chain practices and environmental sustainability. Hence, this research aims to understand the role of green supply chain practices on environmental sustainability with special reference to manufacturing companies in Sri Lanka...
```

---

### Abstract 4: Mobility and Transport
```
The ability to move around to get things done to fulfil one's wants, and needs is critical for independent living, irrespective of his or her age or existence of impairments or disabilities. Safe and efficient mobility with confidence is widely recognized as influential factors of the positive wellbeing of individuals. However, People with Visual Impairment and Blindness (PVIBs) face many challenges in accessing and using transport facilities due to the built environment and vehicle design not catering to their needs...
```

---

### Abstract 5: Stock Market Investment
```
Previous research has documented that psycho-cognitive resources and socioeconomic status have significant influences on investment behavior in financial assets. Drawing from the positive psychosocial perspective, I hypothesized that positive enterprising personality mediates the influence of individual resources on sustainably investing in the stock market. This study examined the behavioral intention of investors through a sample of 287 investors from the South Pacific Stock Market. The analysis of structural equation modeling suggests that positive personality traits have both direct and indirect effects...
```

---

## How to Use for Testing

### Test 1: Citation NER
1. Go to: `http://localhost:3000/MODULE-1/citations/parser`
2. Paste **any citation from above** into the textarea
3. Click "Parse Citation"
4. Should extract: Authors, Title, Year, etc.

**Example Test**:
```
Input: Dassanayake,A, Gamaarachchi,T, Ranathunge ,I (2022). The Role of Green Supply Chain Practices on Environmental Sustainability.

Expected Output:
- Authors: Dassanayake,A; Gamaarachchi,T; Ranathunge,I
- Year: 2022
- Title: The Role of Green Supply Chain Practices on Environmental Sustainability
- Confidence: 1.0
```

---

### Test 2: Plagiarism Detection
1. Go to: `http://localhost:3000/MODULE-1/plagiarism`
2. Paste **Abstract 2** in Text 1
3. Paste a modified version in Text 2 (change a few words)
4. Should detect high similarity (75-90%)

**Example Test**:
```
Text 1: "This study aims to identify how social media influencer's attributes can be useful to tune the customer purchasing behavior..."

Text 2: "This research seeks to determine how attributes of social media influencers can influence customer purchasing behavior in the market..."

Expected: Similarity ~80% (similar but paraphrased)
```

---

### Test 3: Comparing Different Topics (Should show low similarity)
1. Paste **Abstract 3** (Green Supply Chain) in Text 1
2. Paste **Abstract 1** (Terminal Handling) in Text 2
3. Should detect low similarity (<30%) - completely different topics

**Example Test**:
```
Text 1: "...environmental sustainability is one of the major considerations in supply chains..."

Text 2: "...terminal handling charges for containerized cargo were included in the all-inclusive freight..."

Expected: Similarity ~15% (different topics)
```

---

## Test Verification Checklist

### Citation NER Tests
- [ ] Citation 1 → Extracts all 3 authors ✓
- [ ] Citation 3 → Extracts "Green Supply Chain" title ✓
- [ ] Citation 5 → Handles single author correctly ✓
- [ ] Citation 8 → Handles 3 authors with initials ✓
- [ ] All citations → Year extracted as 2022 ✓

### Plagiarism/Similarity Tests
- [ ] Same abstract → ~100% similarity
- [ ] Paraphrased abstract → 75-85% similarity
- [ ] Different topic → <30% similarity
- [ ] All tests complete in <1 second

---

## Expected Performance

| Model | Task | Expected Result |
|-------|------|-----------------|
| Citation NER | Parse SLIIT citation | Extract AUTHOR, TITLE, YEAR (F1=99.45%) |
| SBERT | Compare similar abstracts | 75-95% similarity |
| SBERT | Compare different topics | <30% similarity |

---

## Sample Output Format

### Citation Parser Output
```
[✓] PARSED CITATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Authors: Dassanayake,A; Gamaarachchi,T; Ranathunge,I
Title: The Role of Green Supply Chain Practices on Environmental Sustainability
Year: 2022
Confidence: 1.0 (100%)

[+] APA Format:
Dassanayake,A., Gamaarachchi,T., & Ranathunge,I. (2022). 
The Role of Green Supply Chain Practices on Environmental Sustainability.

[+] IEEE Format:
Dassanayake,A., Gamaarachchi,T., Ranathunge,I., "The Role of 
Green Supply Chain Practices on Environmental Sustainability," 2022.
```

### Plagiarism Checker Output
```
[SIMILARITY ANALYSIS]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Similarity Score: 0.8234 (82.34%)
Status: SIMILAR - Potential plagiarism detected
Confidence: HIGH

Common Topics:
- Supply chain management
- Environmental practices
- Sustainability

Recommendation: Review for proper citation/paraphrase
```

---

## All Available Test Data

Total SLIIT papers: **4,219**
Scraped for testing: **600**
Citations formatted: **539**
Abstracts available: **542**

All data from: `ml/data/raw/sliit_papers/papers_raw_sliit.json`

---

**Test with REAL SLIIT data to verify models work with actual university research!** 🎓
