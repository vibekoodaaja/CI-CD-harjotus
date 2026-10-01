# CI/CD-harjoitus

[![Python CI](https://github.com/vibekoodaaja/CI-CD-harjotus/actions/workflows/ci.yml/badge.svg)](https://github.com/vibekoodaaja/CI-CD-harjotus/actions/workflows/ci.yml)

Pieni Python-projekti, jolle GitHub Actions ajaa automaattisesti linttauksen, testit ja paketoinnin jokaisesta pushista ja pull requestista `main`-haaraan.

## Rakenne

```
app.py                      sovelluslogiikka (add, classify_temperature)
test_app.py                 yksikkötestit (pytest), mukana raja-arvotesti
requirements.txt            työkalut: pytest ja ruff
.github/workflows/ci.yml    CI-putki
```

## Ajo-ohjeet paikallisesti

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
ruff check .
pytest -q
python app.py
```

## CI-putki

Workflow `Python CI` käynnistyy `push`- ja `pull_request`-tapahtumista `main`-haaraan ja suorittaa järjestyksessä:

1. Checkout ja Python 3.13 (pip-välimuisti)
2. Riippuvuuksien asennus
3. Linttaus: `ruff check .`
4. Testit: `pytest -q`
5. Paketointi: `dist/demo-app.zip`
6. Artifactin tallennus nimellä `demo-app-<commit-sha>` (säilytys 7 päivää)

Jos jokin vaihe epäonnistuu, myöhemmät vaiheet eivät suoritu eikä artifactia synny.

## Linkit ajoihin

- Onnistunut ajo (#1, commit `e4be656`): https://github.com/vibekoodaaja/CI-CD-harjotus/actions/runs/36853572918
- Epäonnistunut ajo (#2, commit `38beb94`): https://github.com/vibekoodaaja/CI-CD-harjotus/actions/runs/36854156364
- Korjauksen jälkeinen ajo (#3): ks. [Actions](https://github.com/vibekoodaaja/CI-CD-harjotus/actions)

## Lokianalyysi: tahallinen virhe

**Muutos:** testissä `test_add` odotusarvo vaihdettiin tahallaan: `assert add(2, 3) == 6`.

**Havainnot lokista (ajo #2):**
1. *Trigger:* `push` mainiin, commit `38beb94`, eli tapahtuma oli odotettu.
2. *Job:* `Lint, test and package` käynnistyi normaalisti, ei skipattu.
3. *Ensimmäinen punainen step:* **Run unit tests**. Sitä edeltävät stepit (checkout, Python, riippuvuudet, Ruff) olivat vihreitä, joten vika ei ole ympäristössä eikä koodityylissä.
4. *Varsinainen virhe:*
   ```
   test_app.py:5: AssertionError
   FAILED test_app.py::test_add - assert 5 == 6
   1 failed, 2 passed
   ```
   `add(2, 3)` palautti **5** (toteutunut), testi odotti **6** (odotettu). Funktio toimii oikein, joten vika on testin odotusarvossa.
5. *Seurannaisvaikutus:* paketointi- ja upload-stepit skipattiin, joten rikkinäisestä commitista **ei syntynyt artifactia**. Juuri näin laatuportin kuuluukin toimia.
6. *Paikallinen toisto:* `pytest -q` antoi saman virheen.

**Korjaus:** odotusarvo palautettiin muotoon `== 5`. Paikallisesti `3 passed`, ja seuraava CI-ajo on taas vihreä ja tuottaa artifactin.

## Branch protection

`main`-haaralle on asetettu sääntö: muutokset vain pull requestin kautta, ja status check **Lint, test and package** pitää mennä läpi ennen mergeä. Suorat pushit ja force-pushit on estetty.

## Turvallisuus- ja kustannusreflektio

**Turvallisuus**
- `permissions: contents: read`: workflow'n `GITHUB_TOKEN` saa vain lukuoikeuden repoon, joten vaikka jokin step olisi haavoittuva, se ei voi muokata koodia tai julkaisuja.
- Repossa ei ole salaisuuksia eikä pilviavaimia. Mahdollinen deployment tehtäisiin OIDC:llä (alla), jolloin pitkäikäisiä avaimia ei tarvita lainkaan.
- Käytössä vain GitHubin viralliset actionit (`actions/*`). Tuotannossa ne kannattaisi lukita commit-SHA:han tagin sijaan supply chain -riskin pienentämiseksi.
- Ei `pull_request_target`-triggeriä, joten forkeista tuleva epäluotettu koodi ei saa repon oikeuksia.
- Branch protection varmistaa, ettei rikkinäistä koodia päädy mainiin.

**Kustannukset**
- Julkisessa repossa GitHubin hostatut runnerit ovat ilmaisia, yksityisessä kuluu kuukausittaista minuuttikiintiötä.
- `timeout-minutes: 10` estää jumiin jääneen ajon polttamasta minuutteja.
- pip-välimuisti nopeuttaa ajoa ja `retention-days: 7` rajaa artifact-tallennustilan käyttöä.
- Branch- ja event-rajaukset estävät turhat ajot.

## Valinnainen: avaimeton deployment (suunnitelma)

Esimerkkinä AWS Lambda:

1. AWS:ään luodaan IAM OIDC identity provider `token.actions.githubusercontent.com`.
2. Luodaan IAM-rooli, jonka trust policy sallii vain tämän repon `main`-haaran (`sub: repo:vibekoodaaja/CI-CD-harjotus:ref:refs/heads/main`) ja jonka oikeudet rajataan yhden Lambda-funktion koodin päivitykseen (`lambda:UpdateFunctionCode`).
3. Workflow'hun lisätään erillinen `deploy`-job, joka:
   - riippuu build-jobista (`needs: quality-and-build`) ja ajetaan vain pushista mainiin
   - käyttää GitHub Environmentia `production` (vaadittu hyväksyjä → Continuous Delivery)
   - saa oikeuden `id-token: write` vain tässä jobissa
   - hakee väliaikaiset tunnukset `aws-actions/configure-aws-credentials`-actionilla (`role-to-assume`)
   - lataa build-jobin artifactin ja päivittää Lambdan
4. Budjettihälytys AWS:ään ja resurssien poisto harjoituksen jälkeen.

Näin pilveen ei tallenneta yhtään pysyvää avainta, ja käyttöoikeus on lyhytikäinen ja sidottu tiettyyn repoon ja haaraan.
