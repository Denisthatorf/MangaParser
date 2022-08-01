## Manga parger from mangalib website
#

### Now it only work with firefox driver
### To use it you need to do:

1. `python -m venv venv`

2. `source virtualenv_name/bin/activate`

3. Donwload driver for firefox in internet : https://github.com/mozilla/geckodriver/releases

4. Create drivers folder and unzip driver there

5. `pip install -r requirements.txt`

6. `python parser.py`

7. Read manga

#

If you interested why I use selenium and control of keyboard, but not download image directly by request module. The answer is firewall.